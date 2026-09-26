"""Transient Ladder interaction boundary.

Author: Subhendu Mishra

Preview and selection state are presentation-only. Persistent mutations are
immutable Application commands executed through Application.execute().
"""

from __future__ import annotations

from uuid import uuid4
from typing import Any, Callable

from core.application.commands.control_commands import (
    AddControlComponent,
    ConnectControlSignals,
    DisconnectControlSignals,
    MoveLadderElement,
    RemoveControlComponent,
)
from ui.control.control_tool_palette import ControlToolDescriptor
from ui.items.control_items import ControlPortDirection, ControlPortPresentation
from ui.control.ladder.ladder_geometry import LadderGeometryPolicy


class LadderInteraction:
    def __init__(
        self,
        *,
        application: Any,
        canvas: Any,
        on_rung_selected: Callable[[str | None], None] | None = None,
        on_component_selected: Callable[[str | None], None] | None = None,
        on_connection_selected: Callable[[tuple[str, str, str, str] | None], None] | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        self._application = application
        self._canvas = canvas
        self._active: ControlToolDescriptor | None = None
        self._signal_source: ControlPortPresentation | None = None
        self._move_source: str | None = None
        self._selected_rung_id: str | None = None
        self._selected_component_id: str | None = None
        self._selected_connection: tuple[str, str, str, str] | None = None
        self._on_rung_selected = on_rung_selected
        self._on_component_selected = on_component_selected
        self._on_connection_selected = on_connection_selected
        self._on_status = on_status

    @property
    def active_tool(self) -> ControlToolDescriptor | None:
        return self._active

    @property
    def selected_rung_id(self) -> str | None:
        return self._selected_rung_id

    @property
    def selected_component_id(self) -> str | None:
        return self._selected_component_id

    def activate(self, descriptor: ControlToolDescriptor) -> None:
        self.cancel()
        self._active = descriptor
        self._status(f"Tool: {descriptor.display_name}")

    def cancel(self) -> None:
        self._canvas.clear_transient_preview()
        self._active = None
        self._signal_source = None
        self._move_source = None

    def clear_project_state(self) -> None:
        self.cancel()
        self._selected_rung_id = None
        self._selected_component_id = None
        self._selected_connection = None
        self._canvas.clear_graphical_selection()
        if self._on_rung_selected:
            self._on_rung_selected(None)
        if self._on_component_selected:
            self._on_component_selected(None)
        if self._on_connection_selected:
            self._on_connection_selected(None)

    def select_at(self, x: float, y: float) -> None:
        component = self._canvas.component_at(x, y)
        if component is not None:
            self._select_component(str(component.object_id))
            return
        rung = self._canvas.rung_at(y)
        if rung is not None:
            self._select_rung(str(rung.rung_id))
            self._status(f"Selected rung {rung.rung_id}.")
            return
        self._select_rung(None)
        self._select_component(None)

    def preview(self, x: float, y: float) -> None:
        descriptor = self._active
        if descriptor is None:
            return

        if descriptor.component_type is not None:
            rung = LadderGeometryPolicy.snap_rung(y, self._application.read_control().rungs)
            if rung is None:
                self._canvas.clear_transient_preview()
                self._status("No ladder rung at the cursor.")
                return
            position = LadderGeometryPolicy.snap_position(x)
            self._canvas.create_semantic_preview(descriptor.component_type)
            self._canvas.update_semantic_preview(order=rung.order, position=position)
            self._status(f"Place {descriptor.display_name} on {rung.rung_id}, position {position}.")
            return

        if descriptor.tool_id == "signal.connect" and self._signal_source is not None:
            target = self._canvas.port_at(x, y, direction=ControlPortDirection.INPUT)
            self._canvas.show_connection_preview(self._signal_source.scene_position, (float(x), float(y)))
            if target is None:
                self._status("Connect Signal: hover an INPUT port.")
                return
            valid, reason = self._validate_connection(self._signal_source, target)
            self._status(
                f"Valid target: {target.component_id}.{target.port_name}"
                if valid else f"Invalid target: {reason}"
            )

    def place(self, x: float, y: float) -> Any:
        descriptor = self._active
        if descriptor is None:
            self.select_at(x, y)
            return None

        if descriptor.tool_id in {"component.move", "component.remove"}:
            item = self._canvas.component_at(x, y)
            if item is None:
                self._status("Select a ladder component.")
                return None
            component_id = str(item.object_id)
            self._select_component(component_id)
            if descriptor.tool_id == "component.remove":
                result = self._application.execute(RemoveControlComponent(component_id=component_id))
                self.cancel()
                return result
            if self._move_source is None:
                self._move_source = component_id
                self._status(f"Move source selected: {component_id}.")
                return None
            source_id = self._move_source
            self._move_source = None
            rung = LadderGeometryPolicy.snap_rung(y, self._application.read_control().rungs)
            if rung is None:
                self._status("Move target is not on a ladder rung.")
                return None
            position = LadderGeometryPolicy.snap_position(x)
            result = self._application.execute(
                MoveLadderElement(component_id=source_id, rung_id=rung.rung_id, position=position)
            )
            self.cancel()
            return result

        if descriptor.tool_id == "signal.disconnect":
            identity = self._canvas.connection_at(x, y)
            if identity is None or not self._canvas.connection_identity_exists(identity):
                self._status("Select an existing Control connection.")
                return None
            self._select_connection(identity)
            result = self._application.execute(
                DisconnectControlSignals(
                    source_component=identity[0],
                    source_output=identity[1],
                    target_component=identity[2],
                    target_input=identity[3],
                )
            )
            self.cancel()
            return result

        if descriptor.tool_id == "signal.connect":
            if self._signal_source is None:
                source = self._canvas.port_at(x, y, direction=ControlPortDirection.OUTPUT)
                if source is None:
                    self._status("Select an OUTPUT port.")
                    return None
                self._signal_source = source
                self._select_component(source.component_id)
                self._status(f"Output selected: {source.component_id}.{source.port_name}.")
                return None

            target = self._canvas.port_at(x, y, direction=ControlPortDirection.INPUT)
            if target is None:
                self._status("Select an INPUT port.")
                return None
            valid, reason = self._validate_connection(self._signal_source, target)
            if not valid:
                self._status(f"Connection rejected before command: {reason}")
                return None

            source = self._signal_source
            result = self._application.execute(
                ConnectControlSignals(
                    source_component=source.component_id,
                    source_output=source.port_name,
                    target_component=target.component_id,
                    target_input=target.port_name,
                )
            )
            self.cancel()
            return result

        if descriptor.component_type is None:
            self._status(f"{descriptor.display_name} uses configuration/selection workflow.")
            return None

        rung = LadderGeometryPolicy.snap_rung(y, self._application.read_control().rungs)
        if rung is None:
            self._status("Select a ladder rung before placing a component.")
            return None
        self._select_rung(str(rung.rung_id))
        position = LadderGeometryPolicy.snap_position(x)
        result = self._application.execute(
            AddControlComponent(
                component_id=f"control-{uuid4().hex[:12]}",
                component_type=descriptor.component_type,
                rung_id=str(rung.rung_id),
                position=position,
            )
        )
        self.cancel()
        return result

    def _validate_connection(
        self,
        source: ControlPortPresentation,
        target: ControlPortPresentation,
    ) -> tuple[bool, str]:
        if source.direction is not ControlPortDirection.OUTPUT:
            return False, "source must be an OUTPUT port"
        if target.direction is not ControlPortDirection.INPUT:
            return False, "target must be an INPUT port"
        if source.component_id == target.component_id:
            return False, "self-connections are not allowed"
        source_type = source.signal_type
        target_type = target.signal_type
        numeric = {"int", "float"}
        if source_type == target_type:
            return True, ""
        if source_type in numeric and target_type in numeric:
            return True, ""
        return False, f"{source_type} cannot feed {target_type}"

    def _select_rung(self, rung_id: str | None) -> None:
        self._selected_rung_id = rung_id
        if self._on_rung_selected:
            self._on_rung_selected(rung_id)

    def _select_component(self, component_id: str | None) -> None:
        self._selected_component_id = component_id
        if component_id is not None:
            self._selected_connection = None
            if self._on_connection_selected:
                self._on_connection_selected(None)
        if self._on_component_selected:
            self._on_component_selected(component_id)
        if component_id is not None:
            model = self._application.read_control()
            component = next((c for c in model.components if c.component_id == component_id), None)
            if component is not None and component.rung_id is not None:
                self._select_rung(component.rung_id)

    def _select_connection(self, identity: tuple[str, str, str, str] | None) -> None:
        self._selected_connection = identity
        if self._on_connection_selected:
            self._on_connection_selected(identity)

    def _status(self, message: str) -> None:
        if self._on_status:
            self._on_status(str(message))


__all__ = ["LadderInteraction"]
