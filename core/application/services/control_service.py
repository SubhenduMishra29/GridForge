"""Application boundary for Logic Control and Ladder editing.

Author: Subhendu Mishra

This service is the only Application-owned orchestration surface used by
Control commands. It delegates semantic mutation to the Core LadderProgram /
LogicEngine and exposes immutable read snapshots for UI projections.
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


@dataclass(frozen=True, slots=True)
class ControlProgramReadModel:
    program_id: str
    rungs: tuple[LadderRungReadModel, ...]
    components: tuple[ControlComponentReadModel, ...]
    connections: tuple[ControlConnectionReadModel, ...]
    dependencies: tuple[LogicDependency, ...]


class ControlApplicationService:
    """Application orchestration service for one Ladder Control program."""

    _FACTORIES = {
        "normally_open_contact": NormallyOpenContact,
        "normally_closed_contact": NormallyClosedContact,
        "and_gate": ANDGate,
        "or_gate": ORGate,
        "not_gate": NOTGate,
        "xor_gate": XORGate,
        "coil": LogicCoil,
        "set_coil": LogicSetCoil,
        "reset_coil": LogicResetCoil,
        "timer": LogicTONTimer,
        "ton_timer": LogicTONTimer,
        "tof_timer": LogicTOFTimer,
        "tp_timer": LogicTPTimer,
        "latch": LogicLatch,
        "sr_latch": LogicSRLatch,
        "rs_latch": LogicRSLatch,
        "interlock": LogicInterlock,
    }

    def __init__(self, program: LadderProgram | None = None) -> None:
        self._program = program if program is not None else LadderProgram("control")

    @property
    def program(self) -> LadderProgram:
        return self._program

    def add_component(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        component_id = str(payload["component_id"]).strip()
        component_type = str(payload["component_type"]).strip()
        rung_id = str(payload["rung_id"]).strip()
        configuration = dict(payload.get("configuration") or {})
        position = payload.get("position")
        rung_exists = rung_id in {r.rung_id for r in self._program.rungs()}
        if not rung_exists:
            self._program.add_rung(rung_id)
        component = self._create_component(component_id, component_type, configuration)
        self._program.add_component(component, rung_id=rung_id, position=position)

        def undo() -> None:
            self._program.remove_component(component_id)
            if not rung_exists and not self._program.rung(rung_id).elements:
                self._program.remove_rung(rung_id)

        transaction.record_undo(undo)
        return ApplicationResult.success_result(
            value=component,
            message=f"Control component '{component_id}' created.",
            metadata={"component_id": component_id, "component_type": component_type},
        )

    def remove_component(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        component_id = str(payload["component_id"]).strip()
        engine = self._program.engine
        record = next((record for record in engine.records() if record.component_id == component_id), None)
        if record is None:
            raise ValueError(f"Unknown control component '{component_id}'.")

        component = record.component
        order = record.order
        previous_state = dict(engine.state(component_id))
        source_rung = next(
            (r for r in self._program.rungs() if any(e.component_id == component_id for e in r.elements)),
            None,
        )
        if source_rung is None:
            raise ValueError(f"Control component '{component_id}' is not placed in a Ladder rung.")
        position = next(e.position for e in source_rung.elements if e.component_id == component_id)
        affected_connections = tuple(
            connection
            for connection in engine.connections()
            if connection.source_component == component_id or connection.target_component == component_id
        )
        affected_dependencies = tuple(
            dependency
            for dependency in engine.dependencies()
            if dependency.source_component == component_id or dependency.target_component == component_id
        )

        self._program.remove_component(component_id)

        def undo() -> None:
            engine.register(component, order=order, initial_state=previous_state)
            self._program.add_component(component, rung_id=source_rung.rung_id, position=position)
            for connection in affected_connections:
                if engine.contains(connection.source_component) and engine.contains(connection.target_component):
                    engine.connect(
                        connection.source_component,
                        connection.source_output,
                        connection.target_component,
                        connection.target_input,
                    )
            for dependency in affected_dependencies:
                if dependency not in engine.dependencies():
                    engine.add_dependency(dependency.source_component, dependency.target_component)

        transaction.record_undo(undo)
        return ApplicationResult.success_result(
            value=component,
            message=f"Control component '{component_id}' removed.",
            metadata={"component_id": component_id},
        )

    def connect_signals(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        connection = self._program.engine.connect(**payload)
        transaction.record_undo(
            lambda: self._program.engine.disconnect(
                connection.source_component,
                connection.source_output,
                connection.target_component,
                connection.target_input,
            )
        )
        return ApplicationResult.success_result(value=connection, message="Control signal connection created.", metadata={"connection": connection})

    def disconnect_signals(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        existing = self._program.engine.connection_for_input(payload["target_component"], payload["target_input"])
        if existing is None or existing != LogicConnection(**payload):
            raise ValueError("Control signal connection does not exist.")
        self._program.engine.disconnect(**payload)
        transaction.record_undo(lambda: self._program.engine.connect(**payload))
        return ApplicationResult.success_result(value=existing, message="Control signal connection removed.", metadata={"connection": existing})

    def add_dependency(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        dependency = self._program.engine.add_dependency(**payload)
        transaction.record_undo(lambda: self._program.engine.remove_dependency(dependency.source_component, dependency.target_component))
        return ApplicationResult.success_result(value=dependency, message="Control execution dependency created.", metadata={"dependency": dependency})

    def remove_dependency(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        removed = self._program.engine.remove_dependency(**payload)
        if not removed:
            raise ValueError("Control execution dependency does not exist.")
        transaction.record_undo(lambda: self._program.engine.add_dependency(**payload))
        return ApplicationResult.success_result(value=None, message="Control execution dependency removed.", metadata={"source_component": payload["source_component"], "target_component": payload["target_component"]})

    def add_rung(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        rung = self._program.add_rung(payload["rung_id"], order=payload.get("order"), enabled=payload.get("enabled", True))
        transaction.record_undo(lambda: self._program.remove_rung(rung.rung_id))
        return ApplicationResult.success_result(value=rung, message=f"Ladder rung '{rung.rung_id}' created.", metadata={"rung_id": rung.rung_id})

    def remove_rung(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        rung = self._program.remove_rung(payload["rung_id"])
        if rung.elements:
            raise ValueError("Cannot remove a non-empty Ladder rung; remove its components first.")
        transaction.record_undo(lambda: self._program.add_rung(rung.rung_id, order=rung.order, enabled=rung.enabled))
        return ApplicationResult.success_result(value=rung, message=f"Ladder rung '{rung.rung_id}' removed.", metadata={"rung_id": rung.rung_id})

    def move_element(self, transaction: Transaction, **payload: Any) -> ApplicationResult:
        component_id = payload["component_id"]
        old_rung = next(r for r in self._program.rungs() if any(e.component_id == component_id for e in r.elements))
        old_position = next(e.position for e in old_rung.elements if e.component_id == component_id)
        self._program.move_component(component_id, rung_id=payload["rung_id"], position=int(payload["position"]))
        transaction.record_undo(lambda: self._program.move_component(component_id, rung_id=old_rung.rung_id, position=old_position))
        return ApplicationResult.success_result(value=None, message=f"Ladder element '{component_id}' moved.", metadata={"component_id": component_id})

    def read(self) -> ControlProgramReadModel:
        components = []
        for component in self._program.engine.components():
            components.append(ControlComponentReadModel(
                component_id=component.component_id,
                component_type=component.component_type,
                inputs=tuple(signal.name for signal in component.input_definition()),
                outputs=tuple(signal.name for signal in component.output_definition()),
                state=self._program.engine.state(component.component_id),
                configuration=self._configuration(component),
            ))
        rungs = tuple(LadderRungReadModel(r.rung_id, r.order, r.enabled, tuple(e.component_id for e in r.elements)) for r in self._program.rungs())
        connections = tuple(ControlConnectionReadModel(c.source_component, c.source_output, c.target_component, c.target_input) for c in self._program.engine.connections())
        return ControlProgramReadModel(self._program.program_id, rungs, tuple(components), connections, self._program.engine.dependencies())

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
    "ControlComponentReadModel",
    "ControlConnectionReadModel",
    "LadderRungReadModel",
    "ControlProgramReadModel",
    "ControlApplicationService",
]
