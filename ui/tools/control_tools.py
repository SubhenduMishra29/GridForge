"""Control/Ladder interaction tools.

Author: Subhendu Mishra

Tools translate UI intent into immutable Application commands. They never
instantiate or mutate Core logic components directly.
"""

from __future__ import annotations

from typing import Any, Mapping

from core.application.commands.control_commands import (
    AddControlComponent, ConnectControlSignals, DisconnectControlSignals,
    RemoveControlComponent, AddLogicDependency, RemoveLogicDependency,
    AddLadderRung, RemoveLadderRung, MoveLadderElement,
)
from .tool_base import ToolBase


class ControlToolBase(ToolBase):
    """Shared command-producing Control tool base."""

    def execute(self, command: Any) -> Any:
        self._ensure_active()
        return self.controller.execute_command(command)


class ControlPlacementTool(ControlToolBase):
    TOOL_ID = "control_place"

    def place(self, component_id: str, component_type: str, rung_id: str,
              *, configuration: Mapping[str, Any] | None = None, position: int | None = None) -> Any:
        return self.execute(AddControlComponent(component_id=component_id, component_type=component_type,
                                                 rung_id=rung_id, configuration=configuration, position=position))


class ControlWiringTool(ControlToolBase):
    TOOL_ID = "control_wire"

    def connect(self, source_component: str, source_output: str, target_component: str, target_input: str) -> Any:
        return self.execute(ConnectControlSignals(source_component=source_component, source_output=source_output,
                                                  target_component=target_component, target_input=target_input))

    def disconnect(self, source_component: str, source_output: str, target_component: str, target_input: str) -> Any:
        return self.execute(DisconnectControlSignals(source_component=source_component, source_output=source_output,
                                                     target_component=target_component, target_input=target_input))


class ControlDeleteTool(ControlToolBase):
    TOOL_ID = "control_delete"

    def delete_component(self, component_id: str) -> Any:
        return self.execute(RemoveControlComponent(component_id=component_id))

    def delete_rung(self, rung_id: str) -> Any:
        return self.execute(RemoveLadderRung(rung_id=rung_id))


class ControlMoveTool(ControlToolBase):
    TOOL_ID = "control_move"

    def move(self, component_id: str, rung_id: str, position: int) -> Any:
        return self.execute(MoveLadderElement(component_id=component_id, rung_id=rung_id, position=position))


class ControlDependencyTool(ControlToolBase):
    TOOL_ID = "control_dependency"

    def add(self, source_component: str, target_component: str) -> Any:
        return self.execute(AddLogicDependency(source_component=source_component, target_component=target_component))

    def remove(self, source_component: str, target_component: str) -> Any:
        return self.execute(RemoveLogicDependency(source_component=source_component, target_component=target_component))


class LadderRungTool(ControlToolBase):
    TOOL_ID = "ladder_rung"

    def add(self, rung_id: str, *, order: int | None = None, enabled: bool = True) -> Any:
        return self.execute(AddLadderRung(rung_id=rung_id, order=order, enabled=enabled))


__all__ = [
    "ControlToolBase", "ControlPlacementTool", "ControlWiringTool", "ControlDeleteTool",
    "ControlMoveTool", "ControlDependencyTool", "LadderRungTool",
]
