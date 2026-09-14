# ============================================================
# File: ui/projection/selection_projection_coordinator.py
# GridForge V2 — Selection Projection Coordinator
# ============================================================
"""Project transient UI selection into the PropertiesPanel through Application."""

from __future__ import annotations

from typing import Any

from core.application.events import (
    ElementRemoved,
    ElementUpdated,
    NetworkChanged,
    ProjectClosed,
    ProjectLoaded,
)

from .projection_state import ProjectionState


class SelectionProjectionCoordinator:
    """Coordinate SelectionManager, Application reads, and PropertiesPanel.

    This coordinator is presentation infrastructure. It never accesses Core
    directly and never publishes transient selection as an Application/Core
    event. Selected IDs are resolved through ``Application.read_network`` and
    ``Application.read_element`` before a presentation state is assigned.
    """

    def __init__(
        self,
        *,
        selection_manager: Any,
        application: Any = None,
        properties_panel: Any = None,
    ) -> None:
        if selection_manager is None:
            raise ValueError("selection_manager must not be None.")
        self.selection_manager = selection_manager
        self.application = None
        self.properties_panel = properties_panel
        self._disposed = False
        self._application_event_bus = None

        selection_changed = getattr(selection_manager, "selection_changed", None)
        if selection_changed is None or not callable(getattr(selection_changed, "connect", None)):
            raise TypeError("selection_manager must expose a selection_changed signal.")
        selection_changed.connect(self._on_selection_changed)

        if application is not None:
            self.attach_application(application)

    def attach_application(self, application: Any) -> None:
        self._ensure_active()
        if application is None:
            raise ValueError("application must not be None.")
        if not callable(getattr(application, "read_element", None)):
            raise TypeError("application must provide read_element().")
        if not callable(getattr(application, "read_network", None)):
            raise TypeError("application must provide read_network().")
        event_bus = getattr(application, "event_bus", None)
        if event_bus is None:
            raise TypeError("application must expose event_bus.")

        self._unsubscribe_application_events()
        self.application = application
        self._application_event_bus = event_bus
        event_bus.subscribe(ElementUpdated, self._on_element_updated)
        event_bus.subscribe(ElementRemoved, self._on_element_removed)
        event_bus.subscribe(NetworkChanged, self._on_network_changed)
        event_bus.subscribe(ProjectLoaded, self._on_project_loaded)
        event_bus.subscribe(ProjectClosed, self._on_project_closed)
        self.refresh()

    def detach_application(self) -> Any:
        self._unsubscribe_application_events()
        application = self.application
        self.application = None
        self._application_event_bus = None
        self.clear_projection()
        return application

    def set_properties_panel(self, properties_panel: Any) -> None:
        self._ensure_active()
        self.properties_panel = properties_panel
        self.refresh()

    def refresh(self) -> None:
        self._ensure_active()
        selected_ids = tuple(self.selection_manager.get_selected_ids())
        if not selected_ids or self.application is None:
            self.clear_projection()
            return

        # PropertiesPanel is a singular inspector. Multiple selection remains
        # authoritative in SelectionManager; the first selected ID is the
        # deterministic inspection target until a multi-selection inspector is
        # introduced.
        object_id = selected_ids[0]
        element = self._read_selected_element(object_id)
        if element is None:
            self.clear_projection()
            return

        state = ProjectionState(
            object_id=element.object_id,
            display_type=element.element_type,
            labels=tuple(str(value) for value in element.labels.values()),
            connectivity_refs=tuple(element.connectivity_refs),
            status=self._status(element.attributes),
        )
        self._set_panel_target(state)

    def clear_projection(self) -> None:
        panel = self.properties_panel
        if panel is None:
            return
        clear = getattr(panel, "clear_target", None)
        if callable(clear):
            clear()
            return
        setter = getattr(panel, "set_target", None)
        if callable(setter):
            setter(None)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._unsubscribe_application_events()
        signal = getattr(self.selection_manager, "selection_changed", None)
        disconnect = getattr(signal, "disconnect", None)
        if callable(disconnect):
            try:
                disconnect(self._on_selection_changed)
            except (RuntimeError, TypeError):
                pass
        self.clear_projection()
        self.application = None
        self.properties_panel = None
        self._application_event_bus = None
        self._disposed = True

    def _on_selection_changed(self, selected_ids: Any) -> None:
        del selected_ids
        if not self._disposed:
            self.refresh()

    def _on_element_updated(self, event: ElementUpdated) -> None:
        if self._selected_event_id(event) in self.selection_manager.get_selected_ids():
            self.refresh()

    def _on_element_removed(self, event: ElementRemoved) -> None:
        object_id = self._selected_event_id(event)
        if object_id not in self.selection_manager.get_selected_ids():
            return
        self.selection_manager.clear()
        self.clear_projection()

    def _on_network_changed(self, event: NetworkChanged) -> None:
        del event
        if self.selection_manager.has_selection():
            self.refresh()

    def _on_project_loaded(self, event: ProjectLoaded) -> None:
        del event
        self.selection_manager.clear()
        self.clear_projection()

    def _on_project_closed(self, event: ProjectClosed) -> None:
        del event
        self.selection_manager.clear()
        self.clear_projection()

    def _read_selected_element(self, object_id: Any) -> Any | None:
        if self.application is None:
            return None
        network = self.application.read_network()
        elements = getattr(network, "elements", ())
        for element in elements:
            if getattr(element, "object_id", None) == object_id:
                element_type = getattr(element, "element_type", None)
                if not element_type:
                    return None
                return self.application.read_element(element_type, str(object_id))
        return None

    def _set_panel_target(self, state: ProjectionState) -> None:
        panel = self.properties_panel
        if panel is None:
            return
        setter = getattr(panel, "set_target", None)
        if not callable(setter):
            raise TypeError("properties_panel must provide set_target().")
        setter(state)

    @staticmethod
    def _status(attributes: Any) -> str | None:
        if not hasattr(attributes, "get"):
            return None
        value = attributes.get("status")
        if value is not None:
            return str(value)
        if "in_service" in attributes:
            return "in_service" if attributes.get("in_service") else "out_of_service"
        return None

    @staticmethod
    def _selected_event_id(event: Any) -> Any:
        payload = getattr(event, "payload", {})
        return payload.get("element_id")

    def _unsubscribe_application_events(self) -> None:
        bus = self._application_event_bus
        if bus is None:
            return
        for event_type, handler in (
            (ElementUpdated, self._on_element_updated),
            (ElementRemoved, self._on_element_removed),
            (NetworkChanged, self._on_network_changed),
            (ProjectLoaded, self._on_project_loaded),
            (ProjectClosed, self._on_project_closed),
        ):
            bus.unsubscribe(event_type, handler)
        self._application_event_bus = None

    def _ensure_active(self) -> None:
        if self._disposed:
            raise RuntimeError("SelectionProjectionCoordinator has been disposed.")


__all__ = ["SelectionProjectionCoordinator"]
