"""Immutable Application commands for Logic Control and Ladder editing.

Author: Subhendu Mishra
"""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID, uuid4

from ..command import Command

ADD_CONTROL_COMPONENT = "control.add_component"
REMOVE_CONTROL_COMPONENT = "control.remove_component"
CONNECT_CONTROL_SIGNALS = "control.connect_signals"
DISCONNECT_CONTROL_SIGNALS = "control.disconnect_signals"
ADD_LOGIC_DEPENDENCY = "control.add_dependency"
REMOVE_LOGIC_DEPENDENCY = "control.remove_dependency"
ADD_LADDER_RUNG = "control.add_rung"
REMOVE_LADDER_RUNG = "control.remove_rung"
MOVE_LADDER_ELEMENT = "control.move_element"
ADD_CONTROL_ACTION_BINDING = "control.add_action_binding"
REMOVE_CONTROL_ACTION_BINDING = "control.remove_action_binding"
ADD_CONTROL_INTERLOCK = "control.add_interlock"
REMOVE_CONTROL_INTERLOCK = "control.remove_interlock"
ADD_DYNAMIC_CONTROL_ASSOCIATION = "control.add_dynamic_association"
REMOVE_DYNAMIC_CONTROL_ASSOCIATION = "control.remove_dynamic_association"


def _envelope(command_type: str, payload: Mapping[str, Any], *, command_id: UUID | None,
              correlation_id: UUID | None, causation_id: UUID | None) -> dict[str, Any]:
    return {
        "command_type": command_type,
        "payload": dict(payload),
        "command_id": command_id or uuid4(),
        "correlation_id": correlation_id,
        "causation_id": causation_id,
    }


class AddControlComponent(Command):
    def __init__(self, *, component_id: str, component_type: str, rung_id: str,
                 configuration: Mapping[str, Any] | None = None, position: int | None = None,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not str(component_id).strip() or not str(component_type).strip() or not str(rung_id).strip():
            raise ValueError("component_id, component_type and rung_id are required.")
        payload = {"component_id": component_id, "component_type": component_type,
                   "rung_id": rung_id, "configuration": dict(configuration or {})}
        if position is not None:
            payload["position"] = int(position)
        super().__init__(**_envelope(ADD_CONTROL_COMPONENT, payload,
                                     command_id=command_id, correlation_id=correlation_id,
                                     causation_id=causation_id))


class RemoveControlComponent(Command):
    def __init__(self, *, component_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_envelope(REMOVE_CONTROL_COMPONENT, {"component_id": component_id},
                                     command_id=command_id, correlation_id=correlation_id,
                                     causation_id=causation_id))


class ConnectControlSignals(Command):
    def __init__(self, *, source_component: str, source_output: str, target_component: str,
                 target_input: str, command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        payload = {"source_component": source_component, "source_output": source_output,
                   "target_component": target_component, "target_input": target_input}
        super().__init__(**_envelope(CONNECT_CONTROL_SIGNALS, payload,
                                     command_id=command_id, correlation_id=correlation_id,
                                     causation_id=causation_id))


class DisconnectControlSignals(Command):
    def __init__(self, *, source_component: str, source_output: str, target_component: str, target_input: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        payload = {"source_component": source_component, "source_output": source_output, "target_component": target_component, "target_input": target_input}
        super().__init__(**_envelope(DISCONNECT_CONTROL_SIGNALS, payload, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class AddLogicDependency(Command):
    def __init__(self, *, source_component: str, target_component: str,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(**_envelope(ADD_LOGIC_DEPENDENCY,
                                     {"source_component": source_component, "target_component": target_component},
                                     command_id=command_id, correlation_id=correlation_id,
                                     causation_id=causation_id))


class RemoveLogicDependency(Command):
    def __init__(self, *, source_component: str, target_component: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_envelope(REMOVE_LOGIC_DEPENDENCY, {"source_component": source_component, "target_component": target_component}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class AddLadderRung(Command):
    def __init__(self, *, rung_id: str, order: int | None = None, enabled: bool = True,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        payload: dict[str, Any] = {"rung_id": rung_id, "enabled": enabled}
        if order is not None:
            payload["order"] = int(order)
        super().__init__(**_envelope(ADD_LADDER_RUNG, payload,
                                     command_id=command_id, correlation_id=correlation_id,
                                     causation_id=causation_id))


class RemoveLadderRung(Command):
    def __init__(self, *, rung_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_envelope(REMOVE_LADDER_RUNG, {"rung_id": rung_id},
                                     command_id=command_id, correlation_id=correlation_id,
                                     causation_id=causation_id))


class MoveLadderElement(Command):
    def __init__(self, *, component_id: str, rung_id: str, position: int,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(**_envelope(MOVE_LADDER_ELEMENT,
                                     {"component_id": component_id, "rung_id": rung_id, "position": int(position)},
                                     command_id=command_id, correlation_id=correlation_id,
                                     causation_id=causation_id))


class AddControlActionBinding(Command):
    def __init__(self, *, binding: Mapping[str, Any], command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_envelope(ADD_CONTROL_ACTION_BINDING, {"binding": dict(binding)}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class RemoveControlActionBinding(Command):
    def __init__(self, *, binding_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_envelope(REMOVE_CONTROL_ACTION_BINDING, {"binding_id": str(binding_id)}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class AddControlInterlock(Command):
    def __init__(self, *, configuration: Mapping[str, Any], command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_envelope(ADD_CONTROL_INTERLOCK, {"configuration": dict(configuration)}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class RemoveControlInterlock(Command):
    def __init__(self, *, interlock_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_envelope(REMOVE_CONTROL_INTERLOCK, {"interlock_id": str(interlock_id)}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class AddDynamicControlAssociation(Command):
    def __init__(self, *, association: Mapping[str, Any], command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_envelope(ADD_DYNAMIC_CONTROL_ASSOCIATION, {"association": dict(association)}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class RemoveDynamicControlAssociation(Command):
    def __init__(self, *, association_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_envelope(REMOVE_DYNAMIC_CONTROL_ASSOCIATION, {"association_id": str(association_id)}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

__all__ = [name for name in globals() if name.isupper() or name in {
    "AddControlComponent", "RemoveControlComponent", "ConnectControlSignals",
    "DisconnectControlSignals", "AddLogicDependency", "RemoveLogicDependency",
    "AddLadderRung", "RemoveLadderRung", "MoveLadderElement",
}]
