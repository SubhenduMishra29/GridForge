"""Project-owned Control configuration aggregate.

Author: Subhendu Mishra

The aggregate contains only persistable engineering configuration. Runtime
objects are reconstructed from it and are never used as persistence state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from core.control.action import ControlActionBinding
from core.control.interlock import ControlInterlock
from core.control.logic.ladder import LadderProgram


@dataclass(frozen=True, slots=True)
class DynamicControlAssociation:
    """Stable project binding between a machine and one dynamic controller."""

    association_id: str
    machine_id: str
    controller_id: str
    controller_type: str
    plugin_type: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    input_mappings: Mapping[str, str] = field(default_factory=dict)
    output_mappings: Mapping[str, str] = field(default_factory=dict)
    initialization_policy: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "association_id", "machine_id", "controller_id",
            "controller_type", "plugin_type",
        ):
            value = str(getattr(self, name)).strip()
            if not value:
                raise ValueError(f"{name} must be non-empty.")
            object.__setattr__(self, name, value)
        for name in (
            "parameters", "input_mappings", "output_mappings",
            "initialization_policy",
        ):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

    def to_dict(self) -> dict[str, Any]:
        return {
            "association_id": self.association_id,
            "machine_id": self.machine_id,
            "controller_id": self.controller_id,
            "controller_type": self.controller_type,
            "plugin_type": self.plugin_type,
            "parameters": dict(self.parameters),
            "input_mappings": dict(self.input_mappings),
            "output_mappings": dict(self.output_mappings),
            "initialization_policy": dict(self.initialization_policy),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DynamicControlAssociation":
        if not isinstance(data, Mapping):
            raise TypeError("Dynamic Control association must be a mapping.")
        return cls(
            association_id=str(data.get("association_id", "")),
            machine_id=str(data.get("machine_id", "")),
            controller_id=str(data.get("controller_id", "")),
            controller_type=str(data.get("controller_type", "")),
            plugin_type=str(data.get("plugin_type", "")),
            parameters=data.get("parameters", {}),
            input_mappings=data.get("input_mappings", {}),
            output_mappings=data.get("output_mappings", {}),
            initialization_policy=data.get("initialization_policy", {}),
        )


@dataclass(frozen=True, slots=True)
class ControlConfiguration:
    """Single project-owned, persistable Control configuration."""

    project_id: str
    schema_version: int = 1
    program: LadderProgram = field(default_factory=lambda: LadderProgram("control"))
    action_bindings: tuple[ControlActionBinding, ...] = ()
    interlocks: tuple[ControlInterlock, ...] = ()
    dynamic_control_associations: tuple[DynamicControlAssociation, ...] = ()

    def __post_init__(self) -> None:
        project_id = str(self.project_id).strip()
        if not project_id:
            raise ValueError("project_id must be non-empty.")
        if int(self.schema_version) < 1:
            raise ValueError("schema_version must be positive.")
        if not isinstance(self.program, LadderProgram):
            raise TypeError("program must be a LadderProgram.")
        object.__setattr__(self, "project_id", project_id)
        object.__setattr__(self, "schema_version", int(self.schema_version))
        object.__setattr__(self, "action_bindings", tuple(self.action_bindings))
        object.__setattr__(self, "interlocks", tuple(self.interlocks))
        object.__setattr__(
            self,
            "dynamic_control_associations",
            tuple(self.dynamic_control_associations),
        )
        self.validate()

    def validate(self) -> None:
        if self.program.program_id == "":
            raise ValueError("Control program identity is required.")
        ids = [b.control_id for b in self.action_bindings]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate Control action binding identity.")
        interlock_ids = [i.interlock_id for i in self.interlocks]
        if len(interlock_ids) != len(set(interlock_ids)):
            raise ValueError("Duplicate Control interlock identity.")
        association_ids = [a.association_id for a in self.dynamic_control_associations]
        if len(association_ids) != len(set(association_ids)):
            raise ValueError("Duplicate Dynamic Control association identity.")
        component_ids = {c.component_id for c in self.program.engine.components()}
        for binding in self.action_bindings:
            if binding.source_component not in component_ids:
                raise ValueError(
                    f"Action binding '{binding.control_id}' references missing "
                    f"component '{binding.source_component}'."
                )
        interlock_set = set(interlock_ids)
        for binding in self.action_bindings:
            if binding.interlock_id is not None and binding.interlock_id not in interlock_set:
                raise ValueError(
                    f"Action binding '{binding.control_id}' references missing "
                    f"interlock '{binding.interlock_id}'."
                )
        machines = [a.machine_id for a in self.dynamic_control_associations]
        if len(machines) != len(set(machines)):
            raise ValueError("A machine may have only one Dynamic Control association.")

    def to_dict(self) -> dict[str, Any]:
        components = []
        for record in self.program.engine.records():
            component = record.component
            config = {}
            for name in ("contact_type", "mode", "preset", "condition_count"):
                if hasattr(component, name):
                    value = getattr(component, name)
                    config[name] = getattr(value, "value", value)
            components.append({
                "component_id": record.component_id,
                "component_type": record.component_type,
                "order": record.order,
                "state": dict(self.program.engine.state(record.component_id)),
                "configuration": config,
            })
        rungs = [{
            "rung_id": rung.rung_id,
            "order": rung.order,
            "enabled": rung.enabled,
            "elements": [
                {"component_id": e.component_id, "position": e.position}
                for e in rung.elements
            ],
        } for rung in self.program.rungs()]
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "program_id": self.program.program_id,
            "rungs": rungs,
            "components": components,
            "connections": [
                {
                    "source_component": c.source_component,
                    "source_output": c.source_output,
                    "target_component": c.target_component,
                    "target_input": c.target_input,
                }
                for c in self.program.connections()
            ],
            "dependencies": [
                {
                    "source_component": d.source_component,
                    "target_component": d.target_component,
                }
                for d in self.program.engine.explicit_dependencies()
            ],
            "action_bindings": [
                {
                    "control_id": b.control_id,
                    "source_component": b.source_component,
                    "source_output": b.source_output,
                    "target_equipment_id": b.target_equipment_id,
                    "target_equipment_type": b.target_equipment_type,
                    "action_type": b.action_type.value,
                    "reason": b.reason,
                    "interlock_id": b.interlock_id,
                }
                for b in self.action_bindings
            ],
            "interlocks": [
                {
                    "interlock_id": i.interlock_id,
                    "required_inputs": list(i.required_inputs),
                }
                for i in self.interlocks
            ],
            "dynamic_control_associations": [
                a.to_dict() for a in self.dynamic_control_associations
            ],
        }


__all__ = ["ControlConfiguration", "DynamicControlAssociation"]
