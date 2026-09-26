"""Application boundary for the project-owned Control configuration.

Author: Subhendu Mishra

The service is Application-owned for the lifetime of the process. Its active
ControlConfiguration is replaced transactionally when the project changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from ...control.logic import LadderProgram
from ...control.logic.contacts import NormallyClosedContact, NormallyOpenContact
from ...control.logic.coils import LogicCoil, LogicResetCoil, LogicSetCoil
from ...control.logic.engine import LogicConnection, LogicDependency
from ...control.logic.gates.and_gate import ANDGate
from ...control.logic.gates.not_gate import NOTGate
from ...control.logic.gates.or_gate import ORGate
from ...control.logic.gates.xor_gate import XORGate
from ...control.logic.interlocks import LogicInterlock
from ...control.logic.latches import LogicLatch, LogicRSLatch, LogicSRLatch
from ...control.logic.timers import LogicTOFTimer, LogicTONTimer, LogicTPTimer
from ...control.action import ControlActionBinding
from ...control.configuration import ControlConfiguration, DynamicControlAssociation
from ..results import ApplicationResult
from ..transaction import Transaction


@dataclass(frozen=True, slots=True)
class ControlComponentReadModel:
    component_id: str
    component_type: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    state: Mapping[str, Any]
    configuration: Mapping[str, Any]
    rung_id: str | None = None
    position: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", MappingProxyType(dict(self.state)))
        object.__setattr__(self, "configuration", MappingProxyType(dict(self.configuration)))


@dataclass(frozen=True, slots=True)
class ControlConnectionReadModel:
    source_component: str
    source_output: str
    target_component: str
    target_input: str


@dataclass(frozen=True, slots=True)
class LadderRungReadModel:
    rung_id: str
    order: int
    enabled: bool
    component_ids: tuple[str, ...]
    positions: Mapping[str, int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "positions", MappingProxyType(dict(self.positions)))


@dataclass(frozen=True, slots=True)
class ControlActionBindingReadModel:
    binding_id: str
    source_control_id: str
    source_component_id: str
    source_output: str
    target_type: str
    target_id: str
    action: str
    interlock_id: str | None


@dataclass(frozen=True, slots=True)
class ControlInterlockReadModel:
    interlock_id: str
    required_inputs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DynamicControlAssociationReadModel:
    association_id: str
    machine_id: str
    controller_id: str
    controller_type: str
    plugin_type: str
    parameters: Mapping[str, Any]
    input_mappings: Mapping[str, str]
    output_mappings: Mapping[str, str]
    initialization_policy: Mapping[str, Any]

    def __post_init__(self) -> None:
        for name in ("parameters", "input_mappings", "output_mappings", "initialization_policy"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


@dataclass(frozen=True, slots=True)
class ControlProgramReadModel:
    project_id: str
    program_id: str
    schema_version: int
    rungs: tuple[LadderRungReadModel, ...]
    components: tuple[ControlComponentReadModel, ...]
    connections: tuple[ControlConnectionReadModel, ...]
    dependencies: tuple[LogicDependency, ...]
    action_bindings: tuple[ControlActionBindingReadModel, ...] = ()
    interlocks: tuple[ControlInterlockReadModel, ...] = ()
    dynamic_control_associations: tuple[DynamicControlAssociationReadModel, ...] = ()


class ControlApplicationService:
    """Canonical Application owner of the active project Control configuration."""

    _FACTORIES = {
        "normally_open_contact": NormallyOpenContact,
        "normally_closed_contact": NormallyClosedContact,
        "and_gate": ANDGate, "or_gate": ORGate, "not_gate": NOTGate, "xor_gate": XORGate,
        "coil": LogicCoil, "set_coil": LogicSetCoil, "reset_coil": LogicResetCoil,
        "timer": LogicTONTimer, "ton_timer": LogicTONTimer, "tof_timer": LogicTOFTimer,
        "tp_timer": LogicTPTimer, "latch": LogicLatch, "sr_latch": LogicSRLatch,
        "rs_latch": LogicRSLatch, "interlock": LogicInterlock,
    }

    def __init__(self, configuration: ControlConfiguration) -> None:
        if not isinstance(configuration, ControlConfiguration):
            raise TypeError("configuration must be a ControlConfiguration.")
        self._configuration = configuration

    @property
    def configuration(self) -> ControlConfiguration:
        return self._configuration

    @property
    def program(self) -> LadderProgram:
        return self._configuration.program

    @property
    def action_bindings(self) -> tuple[ControlActionBinding, ...]:
        return self._configuration.action_bindings

    @property
    def interlocks(self):
        return self._configuration.interlocks

    @property
    def dynamic_control_associations(self) -> tuple[DynamicControlAssociation, ...]:
        return self._configuration.dynamic_control_associations

    def activate(self, configuration: ControlConfiguration) -> None:
        if not isinstance(configuration, ControlConfiguration):
            raise TypeError("configuration must be a ControlConfiguration.")
        self._configuration = configuration

    def add_component(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        component_id = str(payload["component_id"]).strip()
        component_type = str(payload["component_type"]).strip()
        rung_id = str(payload["rung_id"]).strip()
        configuration = dict(payload.get("configuration") or {})
        position = payload.get("position")
        rung_exists = rung_id in {r.rung_id for r in self.program.rungs()}
        created_rung = False
        if not rung_exists:
            self.program.add_rung(rung_id)
            created_rung = True
        try:
            component = self._create_component(component_id, component_type, configuration)
            self.program.add_component(component, rung_id=rung_id, position=position)
        except Exception:
            if created_rung and not self.program.rung(rung_id).elements:
                self.program.remove_rung(rung_id)
            raise

        def undo() -> None:
            self.program.remove_component(component_id)
            if created_rung and not self.program.rung(rung_id).elements:
                self.program.remove_rung(rung_id)

        transaction.record_undo(undo)
        return ApplicationResult.success_result(
            value=component,
            message=f"Control component '{component_id}' created.",
            metadata={"component_id": component_id, "component_type": component_type},
        )

    def remove_component(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        component_id = str(payload["component_id"]).strip()
        engine = self.program.engine
        record = next((r for r in engine.records() if r.component_id == component_id), None)
        if record is None:
            raise ValueError(f"Unknown control component '{component_id}'.")
        source_rung = next((r for r in self.program.rungs() if any(e.component_id == component_id for e in r.elements)), None)
        if source_rung is None:
            raise ValueError(f"Control component '{component_id}' is not placed in a Ladder rung.")
        position = next(e.position for e in source_rung.elements if e.component_id == component_id)
        affected_connections = tuple(c for c in engine.connections() if c.source_component == component_id or c.target_component == component_id)
        affected_dependencies = tuple(d for d in engine.explicit_dependencies() if d.source_component == component_id or d.target_component == component_id)
        component = record.component
        order = record.order
        previous_state = dict(engine.state(component_id))
        self.program.remove_component(component_id)

        def undo() -> None:
            self.program.restore_component(component, rung_id=source_rung.rung_id, position=position, order=order, state=previous_state)
            for c in affected_connections:
                engine.connect(c.source_component, c.source_output, c.target_component, c.target_input)
            for d in affected_dependencies:
                if d not in engine.explicit_dependencies():
                    engine.add_dependency(d.source_component, d.target_component)

        transaction.record_undo(undo)
        return ApplicationResult.success_result(value=component, message=f"Control component '{component_id}' removed.", metadata={"component_id": component_id, "component_type": component.component_type})

    def connect_signals(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        connection = self.program.engine.connect(**payload)
        transaction.record_undo(lambda: self.program.engine.disconnect(connection.source_component, connection.source_output, connection.target_component, connection.target_input))
        return ApplicationResult.success_result(value=connection, message="Control signal connection created.", metadata={"connection": connection})

    def disconnect_signals(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        existing = self.program.engine.connection_for_input(payload["target_component"], payload["target_input"])
        if existing is None or existing != LogicConnection(**payload):
            raise ValueError("Control signal connection does not exist.")
        self.program.engine.disconnect(**payload)
        transaction.record_undo(lambda: self.program.engine.connect(**payload))
        return ApplicationResult.success_result(value=existing, message="Control signal connection removed.", metadata={"connection": existing})

    def add_dependency(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        dependency = self.program.engine.add_dependency(**payload)
        transaction.record_undo(lambda: self.program.engine.remove_dependency(dependency.source_component, dependency.target_component))
        return ApplicationResult.success_result(value=dependency, message="Control execution dependency created.", metadata={"dependency": dependency})

    def remove_dependency(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        removed = self.program.engine.remove_dependency(**payload)
        if not removed:
            raise ValueError("Control execution dependency does not exist.")
        transaction.record_undo(lambda: self.program.engine.add_dependency(**payload))
        return ApplicationResult.success_result(value=None, message="Control execution dependency removed.", metadata={"source_component": payload["source_component"], "target_component": payload["target_component"]})

    def add_rung(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        rung = self.program.add_rung(payload["rung_id"], order=payload.get("order"), enabled=payload.get("enabled", True))
        transaction.record_undo(lambda: self.program.remove_rung(rung.rung_id))
        return ApplicationResult.success_result(value=rung, message=f"Ladder rung '{rung.rung_id}' created.", metadata={"rung_id": rung.rung_id})

    def remove_rung(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        rung = self.program.rung(payload["rung_id"])
        if rung.elements:
            raise ValueError("Cannot remove a non-empty Ladder rung; remove its components first.")
        self.program.remove_rung(payload["rung_id"])
        transaction.record_undo(lambda: self.program.add_rung(rung.rung_id, order=rung.order, enabled=rung.enabled))
        return ApplicationResult.success_result(value=rung, message=f"Ladder rung '{rung.rung_id}' removed.", metadata={"rung_id": rung.rung_id})

    def move_element(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        component_id = payload["component_id"]
        old_rung = next(r for r in self.program.rungs() if any(e.component_id == component_id for e in r.elements))
        old_position = next(e.position for e in old_rung.elements if e.component_id == component_id)
        self.program.move_component(component_id, rung_id=payload["rung_id"], position=int(payload["position"]))
        transaction.record_undo(lambda: self.program.move_component(component_id, rung_id=old_rung.rung_id, position=old_position))
        return ApplicationResult.success_result(value=None, message=f"Ladder element '{component_id}' moved.", metadata={"component_id": component_id})

    def read(self) -> ControlProgramReadModel:
        locations = {
            element.component_id: (rung.rung_id, element.position)
            for rung in self.program.rungs()
            for element in rung.elements
        }
        components = tuple(
            ControlComponentReadModel(
                component_id=c.component_id,
                component_type=c.component_type,
                inputs=tuple(s.name for s in c.input_definition()),
                outputs=tuple(s.name for s in c.output_definition()),
                state=self.program.engine.state(c.component_id),
                configuration=self._configuration(c),
                rung_id=locations.get(c.component_id, (None, None))[0],
                position=locations.get(c.component_id, (None, None))[1],
            )
            for c in self.program.engine.components()
        )
        rungs = tuple(
            LadderRungReadModel(
                r.rung_id, r.order, r.enabled,
                tuple(e.component_id for e in r.elements),
                {e.component_id: e.position for e in r.elements},
            )
            for r in self.program.rungs()
        )
        connections = tuple(
            ControlConnectionReadModel(c.source_component, c.source_output, c.target_component, c.target_input)
            for c in self.program.connections()
        )
        bindings = tuple(
            ControlActionBindingReadModel(
                b.control_id, b.control_id, b.source_component, b.source_output,
                b.target_equipment_type, b.target_equipment_id, b.action_type.value, b.interlock_id,
            )
            for b in self.action_bindings
        )
        interlocks = tuple(ControlInterlockReadModel(i.interlock_id, i.required_inputs) for i in self.interlocks)
        dynamic = tuple(
            DynamicControlAssociationReadModel(
                a.association_id, a.machine_id, a.controller_id, a.controller_type,
                a.plugin_type, a.parameters, a.input_mappings, a.output_mappings, a.initialization_policy,
            )
            for a in self.dynamic_control_associations
        )
        return ControlProgramReadModel(
            project_id=self._configuration.project_id,
            program_id=self.program.program_id,
            schema_version=self._configuration.schema_version,
            rungs=rungs,
            components=components,
            connections=connections,
            dependencies=self.program.dependencies(),
            action_bindings=bindings,
            interlocks=interlocks,
            dynamic_control_associations=dynamic,
        )

    def _create_component(self, component_id: str, component_type: str, configuration: Mapping[str, Any]):
        factory = self._FACTORIES.get(component_type)
        if factory is None:
            raise ValueError(f"Unsupported Control component type: '{component_type}'.")
        if factory in (LogicTONTimer, LogicTOFTimer, LogicTPTimer):
            return factory(component_id, preset=float(configuration.get("preset", 1.0)))
        if factory is LogicLatch:
            return factory(component_id)
        if factory is LogicInterlock:
            return factory(component_id, condition_count=int(configuration.get("condition_count", 1)))
        return factory(component_id)

    @staticmethod
    def _configuration(component: Any) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for name in ("contact_type", "mode", "preset", "condition_count"):
            if hasattr(component, name):
                value = getattr(component, name)
                values[name] = getattr(value, "value", value)
        return values


__all__ = [
    "ControlComponentReadModel", "ControlConnectionReadModel", "LadderRungReadModel",
    "ControlActionBindingReadModel", "ControlInterlockReadModel",
    "DynamicControlAssociationReadModel", "ControlProgramReadModel", "ControlApplicationService",
]
