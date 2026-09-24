# ============================================================
# File: ui/events/sld_update_coordinator.py
# GridForge V2 — SLD Update Coordinator
# Author: Subhendu Mishra
# ============================================================

"""Coordinate Application semantic events into the active SLD projection."""

from __future__ import annotations

from collections.abc import Callable

from core.application.application import Application
from core.application.commands.sld_commands import AddSLDNodeCommand, RemoveSLDNodeCommand
from core.application.events import (
    ApplicationEvent,
    ElementCreated,
    ElementRemoved,
    ElementUpdated,
    NetworkChanged,
    ProjectLoaded,
    ProjectClosed,
    ProtectionChanged,
    SLDPresentationChanged,
    TopologyChanged,
)

from ui.sld.sld_read_synchronizer import SLDReadSynchronizer
from ui.sld.sld_document import SLDDocument

CanvasRefresh = Callable[[], None]


class SLDUpdateCoordinator:
    """Project Application read state into domain-scoped SLD projections."""

    event_types = (
        ElementCreated,
        ElementUpdated,
        ElementRemoved,
        TopologyChanged,
        NetworkChanged,
        ProtectionChanged,
        SLDPresentationChanged,
        ProjectLoaded,
        ProjectClosed,
    )

    def __init__(
        self,
        *,
        application: Application,
        synchronizer: SLDReadSynchronizer,
        canvas_refresh: CanvasRefresh,
    ) -> None:
        if not isinstance(application, Application):
            raise TypeError("application must be an Application")
        if not isinstance(synchronizer, SLDReadSynchronizer):
            raise TypeError("synchronizer must be an SLDReadSynchronizer")
        if not callable(canvas_refresh):
            raise TypeError("canvas_refresh must be callable")
        if synchronizer.application is not None and synchronizer.application is not application:
            raise RuntimeError("SLDReadSynchronizer is already attached to another Application")
        if synchronizer.application is None:
            synchronizer.attach_application(application)
        self._application = application
        self._synchronizer = synchronizer
        # Reuse the synchronizer-owned projection manager. The coordinator
        # must never construct or retain a second projection authority.
        self._projection_manager = synchronizer.projection_manager
        self._canvas_refresh = canvas_refresh
        self._document: SLDDocument | None = None
        self._disposed = False
        self._last_reconciliation_error: Exception | None = None

    @property
    def document(self) -> SLDDocument | None:
        """Return the currently bound presentation document."""
        if self._disposed:
            return None
        presentation = self._application.presentation
        if isinstance(presentation, SLDDocument):
            self._document = presentation
        return self._document

    def bind_document(self, document: SLDDocument) -> None:
        """Explicitly bind a newly active SLD document."""
        if self._disposed:
            raise RuntimeError("SLDUpdateCoordinator has been disposed")
        if not isinstance(document, SLDDocument):
            raise TypeError("document must be an SLDDocument")
        self._document = document

    def detach_document(self) -> None:
        """Drop the cached presentation reference during project close."""
        self._document = None


    @property
    def last_reconciliation_error(self) -> Exception | None:
        """Return the most recent reconciliation failure, if any."""
        return self._last_reconciliation_error

    def reconcile_current_state(self) -> None:
        """Reconcile projections from current Application state without replaying events.

        This is the deterministic bootstrap path for projections that become ready
        after ProjectLoaded has already been emitted.
        """
        if self._disposed:
            return
        presentation = self._application.presentation
        if not isinstance(presentation, SLDDocument):
            self.detach_document()
            return
        self.bind_document(presentation)
        self._synchronizer.synchronize_network(presentation, self._application.read_network())
        self._synchronizer.synchronize_protection(presentation, self._application.read_protection())
        self._last_reconciliation_error = None
        self._canvas_refresh()

    def refresh(self, event: ApplicationEvent) -> None:
        """Refresh read-only projections after an authoritative Application fact."""
        if self._disposed:
            return
        if not isinstance(event, ApplicationEvent):
            raise TypeError("event must be an ApplicationEvent")

        if isinstance(event, ProjectClosed):
            # ProjectClosed is the authoritative successful transition boundary.
            # Clear all projection-domain state so the next project cannot
            # inherit registry entries from the closed project.
            self._projection_manager.clear()
            self.detach_document()
            self._canvas_refresh()
            return

        if isinstance(event, ProjectLoaded):
            # ProjectLoaded is emitted only after Application activation
            # succeeds. Reset registry state here for new-project and
            # project-replacement transitions while preserving old state
            # during activation rollback (no ProjectLoaded event is emitted).
            self._projection_manager.clear()
            presentation = self._application.presentation
            if isinstance(presentation, SLDDocument):
                self.bind_document(presentation)

        document = self.document
        if document is None:
            return

        try:
            if isinstance(event, ProtectionChanged):
                self._synchronizer.synchronize_protection(
                    document,
                    self._application.read_protection(),
                )
            elif isinstance(event, SLDPresentationChanged):
                # The SLD service already owns presentation mutation. This
                # event only invalidates the canvas; it must not rebuild the
                # network projection.
                self._canvas_refresh()
                return
            elif isinstance(event, (ElementCreated, ElementUpdated, ElementRemoved)):
                element_type = str(event.payload.get("element_type", "")).strip().upper()
                element_id = event.payload.get("element_id")
                if not isinstance(element_id, str) or not element_id:
                    raise ValueError("Element lifecycle event must contain a canonical element_id.")

                if isinstance(event, ElementCreated):
                    self._consume_placement_coordinates(document, element_id, element_type, event)
                elif isinstance(event, ElementRemoved):
                    self._remove_projection_node(document, element_id, element_type)

                if element_type == "RELAY":
                    self._synchronizer.synchronize_protection(
                        document,
                        self._application.read_protection(),
                    )
                else:
                    initial_positions = {}
                    if isinstance(event, ElementCreated):
                        x = event.payload.get("presentation_x")
                        y = event.payload.get("presentation_y")
                        if x is not None and y is not None:
                            initial_positions[element_id] = (float(x), float(y))
                    self._synchronizer.synchronize_network(
                        document,
                        self._application.read_network(),
                        initial_positions=initial_positions,
                    )
            elif isinstance(event, (TopologyChanged, NetworkChanged)):
                self._synchronizer.synchronize_network(
                    document,
                    self._application.read_network(),
                )
            elif isinstance(event, ProjectLoaded):
                # Project activation crosses both Application read domains.
                # Reconcile each authoritative read model directly; do not
                # synthesize another event bus or rebuild network state from
                # protection changes.
                self._synchronizer.synchronize_network(
                    document,
                    self._application.read_network(),
                )
                self._synchronizer.synchronize_protection(
                    document,
                    self._application.read_protection(),
                )
            else:
                return
        except Exception as exc:
            self._last_reconciliation_error = exc
            raise
        self._last_reconciliation_error = None
        self._canvas_refresh()

    def _consume_placement_coordinates(self, document: SLDDocument, element_id: str, element_type: str, event: ApplicationEvent) -> None:
        """Consume placement metadata at the Application presentation boundary.

        The PlacementTool only contributes immutable command payload metadata.
        This coordinator is the explicit consumer that converts committed Core
        creation into a projection-owned SLD node through the Application SLD
        command path.
        """
        existing = document.model.get_node_by_equipment_id_optional(element_id)
        if existing is not None:
            return
        x = event.payload.get("presentation_x", 0.0)
        y = event.payload.get("presentation_y", 0.0)
        source = "protection_read_model" if element_type == "RELAY" else "application_read_model"
        result = self._application.execute(
            AddSLDNodeCommand(
                node_id=f"sld-node-{element_id}",
                equipment_id=element_id,
                x=float(x),
                y=float(y),
                presentation_owner="projection",
                projection_source=source,
            )
        )
        if not result.success:
            raise RuntimeError(result.message)

    def _remove_projection_node(self, document: SLDDocument, element_id: str, element_type: str) -> None:
        """Remove only the projection owned by the removed Core element."""
        node = document.model.get_node_by_equipment_id_optional(element_id)
        if node is None:
            return
        source = node.properties.get("projection_source")
        expected = "protection_read_model" if element_type == "RELAY" else "application_read_model"
        if source != expected:
            return
        result = self._application.execute(
            RemoveSLDNodeCommand(
                node_id=node.node_id,
                projection_source=source,
            )
        )
        if not result.success:
            raise RuntimeError(result.message)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._canvas_refresh = lambda: None
        self._last_reconciliation_error = None
        self._disposed = True


__all__ = ["SLDUpdateCoordinator", "CanvasRefresh"]
