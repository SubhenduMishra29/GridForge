# ============================================================
# File: ui/projection/selection_projection_coordinator.py
# GridForge V2 — Selection Projection Coordinator
# ============================================================
"""Project transient UI selection into the PropertiesPanel through Application."""

from __future__ import annotations

from typing import Any

from core.application.events import (
    ApplicationEvent,
    ElementRemoved,
    ElementUpdated,
    NetworkChanged,
    ProjectClosed,
    ProjectLoaded,
)

from .projection_state import EngineeringParameterState, ProjectionState


class SelectionProjectionCoordinator:
    """Project selection state using Application read models.

    Application events arrive through ``UIProjectionCoordinator``. The only
    direct event source retained here is ``SelectionManager.selection_changed``
    because selection is transient UI interaction state rather than a domain
    event.
    """

    event_types = (
        ElementUpdated,
        ElementRemoved,
        NetworkChanged,
        ProjectLoaded,
        ProjectClosed,
    )

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

        signal = getattr(selection_manager, "selection_changed", None)
        if signal is None or not callable(getattr(signal, "connect", None)):
            raise TypeError("selection_manager must expose a selection_changed signal.")
        signal.connect(self._on_selection_changed)

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
        self.application = application
        self.refresh()

    def detach_application(self) -> Any:
        application = self.application
        self.application = None
        self.clear_projection()
        return application

    def set_properties_panel(self, properties_panel: Any) -> None:
        self._ensure_active()
        self.properties_panel = properties_panel
        self.refresh()

    def refresh(self, event: ApplicationEvent | None = None) -> None:
        self._ensure_active()
        if isinstance(event, (ProjectLoaded, ProjectClosed)):
            self.selection_manager.clear()
            self.clear_projection()
            return

        selected_ids = tuple(self.selection_manager.get_selected_ids())
        if not selected_ids or self.application is None:
            self.clear_projection()
            return

        object_id = selected_ids[0]
        if isinstance(event, ElementRemoved) and self._selected_event_id(event) == object_id:
            self.selection_manager.clear()
            self.clear_projection()
            return

        if isinstance(event, ElementUpdated) and self._selected_event_id(event) not in selected_ids:
            return

        if isinstance(event, NetworkChanged) and not self.selection_manager.has_selection():
            return

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
            engineering_parameters=tuple(EngineeringParameterState(parameter_id=item.parameter_id, value=item.value, unit=item.unit, datatype=item.datatype, choices=item.choices, editable=item.editable, derived=item.derived, validation=item.validation, coupling_group=item.coupling_group, topology_impact=item.topology_impact, study_impact=item.study_impact) for item in getattr(element, "engineering_parameters", ())),
            engineering_parameters=tuple(
                EngineeringParameterState(
                    parameter_id=item.parameter_id,
                    value=item.value,
                    unit=item.unit,
                    datatype=item.datatype,
                    choices=item.choices,
                    editable=item.editable,
                    derived=item.derived,
                    validation=item.validation,
                    coupling_group=item.coupling_group,
                    topology_impact=item.topology_impact,
                    study_impact=item.study_impact,
                )
                for item in getattr(element, "engineering_parameters", ())
            ),
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
        self._disposed = True

    def _on_selection_changed(self, selected_ids: Any) -> None:
        del selected_ids
        if not self._disposed:
            self.refresh()

    def _read_selected_element(self, object_id: Any) -> Any | None:
        if self.application is None:
            return None
        network = self.application.read_network()
        for element in getattr(network, "elements", ()):
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

    def _ensure_active(self) -> None:
        if self._disposed:
            raise RuntimeError("SelectionProjectionCoordinator has been disposed.")


__all__ = ["SelectionProjectionCoordinator"]
