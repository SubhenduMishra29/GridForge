"""Project-owned Control engineering configuration.

Author: Subhendu Mishra

The configuration is the persistence authority for Control. Runtime engines are
reconstructed from this object and never persist their own database/state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Mapping

from .action import ControlActionBinding
from .decision import ControlActionType
from .interlock import ControlInterlock
from .logic import LadderProgram
from .logic.contacts import NormallyClosedContact, NormallyOpenContact
from .logic.coils import LogicCoil, LogicResetCoil, LogicSetCoil
from .logic.gates.and_gate import ANDGate
from .logic.gates.not_gate import NOTGate
from .logic.gates.or_gate import ORGate
from .logic.gates.xor_gate import XORGate
from .logic.interlocks import LogicInterlock
from .logic.latches import LogicLatch, LogicRSLatch, LogicSRLatch
from .logic.timers import LogicTOFTimer, LogicTONTimer, LogicTPTimer

@dataclass(frozen=True, slots=True)
class InterlockConfiguration:
    """Persistable project definition of an action interlock."""
    interlock_id: str
    required_inputs: tuple[str, ...] = ()
    condition: str = "all_required_inputs_true"
    quality_policy: str = "require_valid_fresh"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ident = str(self.interlock_id).strip()
        if not ident:
            raise ValueError("interlock_id must be non-empty.")
        inputs = tuple(str(item).strip() for item in self.required_inputs)
        if any(not item for item in inputs):
            raise ValueError("required_inputs cannot contain empty identities.")
        object.__setattr__(self, "interlock_id", ident)
        object.__setattr__(self, "required_inputs", inputs)
        object.__setattr__(self, "condition", str(self.condition).strip())
        object.__setattr__(self, "quality_policy", str(self.quality_policy).strip())
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        return {"interlock_id": self.interlock_id, "required_inputs": list(self.required_inputs), "condition": self.condition, "quality_policy": self.quality_policy, "metadata": dict(self.metadata)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "InterlockConfiguration":
        return cls(interlock_id=str(data["interlock_id"]), required_inputs=tuple(data.get("required_inputs", ())), condition=str(data.get("condition", "all_required_inputs_true")), quality_policy=str(data.get("quality_policy", "require_valid_fresh")), metadata=dict(data.get("metadata") or {}))

    def runtime(self) -> ControlInterlock:
        return ControlInterlock(self.interlock_id, required_inputs=self.required_inputs)

@dataclass(frozen=True, slots=True)
class DynamicControlAssociation:
    """Persistable identifier-only association between a machine and a controller."""
    association_id: str
    machine_id: str
    controller_id: str
    controller_type: str
    plugin_id: str
    plugin_version: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)
    input_mappings: Mapping[str, str] = field(default_factory=dict)
    output_mappings: Mapping[str, str] = field(default_factory=dict)
    initialization_policy: str = "operating_point"
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name in ("association_id", "machine_id", "controller_id", "controller_type", "plugin_id"):
            value = str(getattr(self, name)).strip()
            if not value:
                raise ValueError(f"{name} must be non-empty.")
            object.__setattr__(self, name, value)
        if self.plugin_version is not None:
            object.__setattr__(self, "plugin_version", str(self.plugin_version).strip() or None)
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
        object.__setattr__(self, "input_mappings", MappingProxyType({str(k): str(v) for k, v in self.input_mappings.items()}))
        object.__setattr__(self, "output_mappings", MappingProxyType({str(k): str(v) for k, v in self.output_mappings.items()}))
        object.__setattr__(self, "initialization_policy", str(self.initialization_policy).strip())
        version = int(self.schema_version)
        if version < 1:
            raise ValueError("schema_version must be positive.")
        object.__setattr__(self, "schema_version", version)

    def to_dict(self) -> dict[str, Any]:
        return {"association_id": self.association_id, "machine_id": self.machine_id, "controller_id": self.controller_id, "controller_type": self.controller_type, "plugin_id": self.plugin_id, "plugin_version": self.plugin_version, "parameters": dict(self.parameters), "input_mappings": dict(self.input_mappings), "output_mappings": dict(self.output_mappings), "initialization_policy": self.initialization_policy, "schema_version": self.schema_version}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DynamicControlAssociation":
        return cls(association_id=str(data["association_id"]), machine_id=str(data["machine_id"]), controller_id=str(data["controller_id"]), controller_type=str(data["controller_type"]), plugin_id=str(data["plugin_id"]), plugin_version=data.get("plugin_version"), parameters=dict(data.get("parameters") or {}), input_mappings=dict(data.get("input_mappings") or {}), output_mappings=dict(data.get("output_mappings") or {}), initialization_policy=str(data.get("initialization_policy", "operating_point")), schema_version=int(data.get("schema_version", 1)))

def _component_configuration(component: Any) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name in ("contact_type", "mode", "preset", "condition_count"):
        if hasattr(component, name):
            value = getattr(component, name)
            values[name] = getattr(value, "value", value)
    return values

def _component_factory(component_type: str) -> Callable[..., Any] | None:
    return {"normally_open_contact": NormallyOpenContact, "normally_closed_contact": NormallyClosedContact, "and_gate": ANDGate, "or_gate": ORGate, "not_gate": NOTGate, "xor_gate": XORGate, "coil": LogicCoil, "set_coil": LogicSetCoil, "reset_coil": LogicResetCoil, "timer": LogicTONTimer, "ton_timer": LogicTONTimer, "tof_timer": LogicTOFTimer, "tp_timer": LogicTPTimer, "latch": LogicLatch, "sr_latch": LogicSRLatch, "rs_latch": LogicRSLatch, "interlock": LogicInterlock}.get(component_type)

@dataclass
class ControlConfiguration:
    """Single project-owned Control aggregate."""
    project_id: str
    program: LadderProgram
    action_bindings: tuple[ControlActionBinding, ...] = ()
    interlocks: tuple[InterlockConfiguration, ...] = ()
    dynamic_control_associations: tuple[DynamicControlAssociation, ...] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        project_id = str(self.project_id).strip()
        if not project_id:
            raise ValueError("project_id must be non-empty.")
        if not isinstance(self.program, LadderProgram):
            raise TypeError("program must be a LadderProgram.")
        self.project_id = project_id
        self.action_bindings = tuple(self.action_bindings)
        self.interlocks = tuple(self.interlocks)
        self.dynamic_control_associations = tuple(self.dynamic_control_associations)
        self.validate()

    @classmethod
    def empty(cls, project_id: str) -> "ControlConfiguration":
        return cls(project_id=project_id, program=LadderProgram("control"))

    def validate(self) -> None:
        if len({item.control_id for item in self.action_bindings}) != len(self.action_bindings):
            raise ValueError("Control binding IDs must be unique.")
        if len({item.interlock_id for item in self.interlocks}) != len(self.interlocks):
            raise ValueError("Control interlock IDs must be unique.")
        if len({item.association_id for item in self.dynamic_control_associations}) != len(self.dynamic_control_associations):
            raise ValueError("Dynamic Control association IDs must be unique.")
        component_ids = {record.component_id for record in self.program.engine.records()}
        interlock_ids = {item.interlock_id for item in self.interlocks}
        for binding in self.action_bindings:
            if binding.source_component not in component_ids:
                raise ValueError(f"Action binding {binding.control_id!r} references a missing source component.")
            if binding.interlock_id is not None and binding.interlock_id not in interlock_ids:
                raise ValueError(f"Action binding {binding.control_id!r} references missing interlock {binding.interlock_id!r}.")
        for rung in self.program.rungs():
            for element in rung.elements:
                if element.component_id not in component_ids:
                    raise ValueError(f"Rung {rung.rung_id!r} references missing component {element.component_id!r}.")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        components = [{"component_id": record.component_id, "component_type": record.component_type, "order": record.order, "configuration": _component_configuration(record.component)} for record in self.program.engine.records()]
        rungs = [{"rung_id": rung.rung_id, "order": rung.order, "enabled": rung.enabled, "elements": [{"component_id": e.component_id, "position": e.position} for e in rung.elements]} for rung in self.program.rungs()]
        return {"schema_version": self.schema_version, "project_id": self.project_id, "program": {"program_id": self.program.program_id, "rungs": rungs, "components": components, "connections": [{"source_component": c.source_component, "source_output": c.source_output, "target_component": c.target_component, "target_input": c.target_input} for c in self.program.connections()], "dependencies": [{"source_component": d.source_component, "target_component": d.target_component} for d in self.program.engine.explicit_dependencies()]}, "action_bindings": [{"control_id": b.control_id, "source_component": b.source_component, "source_output": b.source_output, "target_equipment_id": b.target_equipment_id, "action_type": b.action_type.value, "reason": b.reason, "target_equipment_type": b.target_equipment_type, "interlock_id": b.interlock_id} for b in self.action_bindings], "interlocks": [item.to_dict() for item in self.interlocks], "dynamic_control_associations": [item.to_dict() for item in self.dynamic_control_associations]}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ControlConfiguration":
        project_id = str(data["project_id"]).strip()
        program_data = dict(data.get("program") or {})
        program = LadderProgram(str(program_data.get("program_id", "control")))
        rung_data = tuple(program_data.get("rungs", ()))
        for rung in sorted(rung_data, key=lambda item: (int(item["order"]), str(item["rung_id"]))):
            program.add_rung(str(rung["rung_id"]), order=int(rung["order"]), enabled=bool(rung.get("enabled", True)))
        for item in sorted(program_data.get("components", ()), key=lambda item: (int(item.get("order", 0)), str(item["component_id"]))):
            component_id = str(item["component_id"])
            component_type = str(item["component_type"])
            configuration = dict(item.get("configuration") or {})
            if component_type in {"timer", "ton_timer", "tof_timer", "tp_timer"}:
                mode = str(configuration.get("mode", "ton")).lower()
                timer_factory = {
                    "ton": LogicTONTimer,
                    "tof": LogicTOFTimer,
                    "tp": LogicTPTimer,
                }.get(mode)
                if timer_factory is None:
                    raise ValueError(f"Unsupported persisted timer mode {mode!r}.")
                component = timer_factory(component_id, preset=float(configuration.get("preset", 1.0)))
            else:
                factory = _component_factory(component_type)
                if factory is None:
                    raise ValueError(f"Unsupported persisted Control component type {component_type!r}.")
                if factory is LogicInterlock:
                component = factory(component_id, condition_count=int(configuration.get("condition_count", 1)))
            else:
                component = factory(component_id)
            rung = next((r for r in rung_data if any(str(e["component_id"]) == component_id for e in r.get("elements", ()))), None)
            if rung is None:
                raise ValueError(f"Persisted Control component {component_id!r} is not placed in a rung.")
            element = next(e for e in rung.get("elements", ()) if str(e["component_id"]) == component_id)
            program.restore_component(component, rung_id=str(rung["rung_id"]), position=int(element["position"]), order=int(item.get("order", 0)), state=component.initial_state())
        for connection in program_data.get("connections", ()):
            program.engine.connect(**dict(connection))
        for dependency in program_data.get("dependencies", ()):
            program.engine.add_dependency(**dict(dependency))
        bindings = tuple(ControlActionBinding(control_id=str(item["control_id"]), source_component=str(item["source_component"]), source_output=str(item["source_output"]), target_equipment_id=str(item["target_equipment_id"]), action_type=ControlActionType(item["action_type"]), reason=str(item.get("reason", "Control action")), target_equipment_type=str(item.get("target_equipment_type", "breaker")), interlock_id=item.get("interlock_id")) for item in data.get("action_bindings", ()))
        interlocks = tuple(InterlockConfiguration.from_dict(item) for item in data.get("interlocks", ()))
        associations = tuple(DynamicControlAssociation.from_dict(item) for item in data.get("dynamic_control_associations", ()))
        return cls(project_id=project_id, program=program, action_bindings=bindings, interlocks=interlocks, dynamic_control_associations=associations, schema_version=int(data.get("schema_version", 1)))

__all__ = ["ControlConfiguration", "InterlockConfiguration", "DynamicControlAssociation"]