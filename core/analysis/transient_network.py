# Author: Subhendu Mishra
"""Detached transient-network state and machine/network algebraic coupling."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np

from core.analysis.dynamic_initial_state import (
    DynamicInitialStatePreparation,
    DynamicMachineModelDefinition,
)
from core.analysis.dynamic_model_association import DynamicMachineModelRegistry
from core.analysis.power_flow_preparation import (
    PreparedBranch,
    PreparedPowerFlow,
    PreparedShunt,
    PreparedTransformer,
)
from core.analysis.transient_fault import TransientFault
from core.numerical.ybus import YBusBuilder
from core.solver.dynamics.machine_models import ClassicalSynchronousMachine
from core.solver.dynamics.multimachine import MultiMachineSystem
from core.solver.power_flow.result import PowerFlowResult


@dataclass(frozen=True, slots=True)
class DetachedTransientNetworkState:
    """Immutable passive/network switching snapshot owned by one study run."""

    bus_ids: tuple[str, ...]
    branches: tuple[PreparedBranch, ...] = ()
    transformers: tuple[PreparedTransformer, ...] = ()
    shunts: tuple[PreparedShunt, ...] = ()
    breaker_states: Mapping[str, bool] = MappingProxyType({})
    equipment_states: Mapping[str, bool] = MappingProxyType({})
    machine_connection_paths: Mapping[str, tuple[str, ...]] = MappingProxyType({})
    machine_rotor_policies: Mapping[str, str] = MappingProxyType({})
    project_id: str | None = None
    activation_generation: int | None = None
    source_revision: tuple[int, int, int, int] | None = None
    active_fault: object | None = None
    topology_revision: int | None = None

    def __post_init__(self) -> None:
        bus_ids = tuple(str(bus_id) for bus_id in self.bus_ids)
        if not bus_ids or len(set(bus_ids)) != len(bus_ids):
            raise ValueError("Transient network requires unique bus IDs.")
        object.__setattr__(self, "bus_ids", bus_ids)
        object.__setattr__(self, "branches", tuple(self.branches))
        object.__setattr__(self, "transformers", tuple(self.transformers))
        object.__setattr__(self, "shunts", tuple(self.shunts))
        breaker_states = {str(k): bool(v) for k, v in self.breaker_states.items()}
        equipment_states = {str(k): bool(v) for k, v in self.equipment_states.items()}
        paths = {}
        for machine_id, raw_path in self.machine_connection_paths.items():
            key = str(machine_id).strip()
            path = tuple(str(item).strip() for item in raw_path)
            if not key or not path or any(not item for item in path):
                raise ValueError(f"Machine '{key or machine_id}' requires a non-empty explicit switching path.")
            if len(path) != len(set(path)):
                raise ValueError(f"Machine '{key}' connection path contains duplicate switching equipment IDs.")
            missing = tuple(item for item in path if item not in breaker_states)
            if missing:
                raise ValueError(
                    f"Machine '{key}' connection path references switch IDs without captured detached states: {missing!r}."
                )
            paths[key] = path
        policies = {str(k): str(v) for k, v in self.machine_rotor_policies.items()}
        if set(policies) != set(paths):
            raise ValueError("Machine rotor-disconnection policies must cover exactly the machine connection-path identities.")
        for machine_id, policy in policies.items():
            if policy != "continue_with_zero_electrical_power":
                raise ValueError(f"Machine '{machine_id}' has unsupported disconnected rotor policy {policy!r}.")
        object.__setattr__(self, "breaker_states", MappingProxyType(breaker_states))
        object.__setattr__(self, "equipment_states", MappingProxyType(equipment_states))
        object.__setattr__(self, "machine_connection_paths", MappingProxyType(paths))
        object.__setattr__(self, "machine_rotor_policies", MappingProxyType(policies))
        if self.project_id is not None and (not isinstance(self.project_id, str) or not self.project_id.strip()):
            raise ValueError("Detached transient project_id must be non-empty when supplied.")
        if self.activation_generation is not None and (
            isinstance(self.activation_generation, bool)
            or not isinstance(self.activation_generation, int)
            or self.activation_generation < 1
        ):
            raise ValueError("Detached transient activation_generation must be a positive integer.")
        if self.source_revision is not None and (
            len(self.source_revision) != 4
            or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in self.source_revision)
        ):
            raise ValueError("Detached transient source_revision must contain four non-negative revision integers.")
        if self.project_id is not None:
            object.__setattr__(self, "project_id", self.project_id.strip())
        if self.source_revision is not None:
            object.__setattr__(self, "source_revision", tuple(self.source_revision))

    def is_element_conducting(self, element_id: str, default: bool = True) -> bool:
        return self.equipment_states.get(str(element_id), default)

    def is_machine_connected(self, machine_id: str) -> bool:
        key = str(machine_id)
        try:
            path = self.machine_connection_paths[key]
        except KeyError as exc:
            raise ValueError(f"Dynamic machine '{key}' has no validated detached connection path.") from exc
        # Fail closed if a state key disappears from a detached event view.
        return all(self.breaker_states.get(item, False) for item in path)


@dataclass(frozen=True, slots=True)
class PreparedTransientStability:
    """Complete detached input bundle for one transient-stability execution."""

    network: DetachedTransientNetworkState
    project_id: str
    activation_generation: int
    source_revision: tuple[int, int, int, int]
    machines: tuple[ClassicalSynchronousMachine, ...]
    mechanical_powers: Mapping[str, float]
    initial_state: tuple[float, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be a non-empty string.")
        if not isinstance(self.activation_generation, int) or isinstance(self.activation_generation, bool) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if len(self.source_revision) != 4 or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in self.source_revision):
            raise ValueError("source_revision must contain four non-negative revision integers.")
        object.__setattr__(self, "project_id", self.project_id.strip())
        object.__setattr__(self, "source_revision", tuple(self.source_revision))
        object.__setattr__(self, "machines", tuple(self.machines))
        object.__setattr__(self, "mechanical_powers", MappingProxyType({str(k): float(v) for k, v in self.mechanical_powers.items()}))
        object.__setattr__(self, "initial_state", tuple(float(v) for v in self.initial_state))
        if self.network.project_id != self.project_id:
            raise ValueError("Detached transient Network project identity does not match PreparedTransientStability.")
        if self.network.activation_generation != self.activation_generation:
            raise ValueError("Detached transient Network activation generation does not match PreparedTransientStability.")
        if self.network.source_revision != self.source_revision:
            raise ValueError("Detached transient Network source revision does not match PreparedTransientStability.")
        if self.network.topology_revision != self.source_revision[1]:
            raise ValueError("Detached transient Network topology revision does not match its source revision.")
        machine_ids = tuple(machine.machine_id for machine in self.machines)
        if len(machine_ids) != len(set(machine_ids)):
            raise ValueError("Prepared transient machine identities must be unique.")
        if set(machine_ids) != set(self.network.machine_connection_paths):
            raise ValueError(
                "Prepared transient machine identities must match the validated detached connection-path identities."
            )
        if set(machine_ids) != set(self.mechanical_powers):
            raise ValueError("Prepared transient mechanical-power identities must match its machine identities.")

    @property
    def provenance(self) -> Mapping[str, object]:
        return MappingProxyType({
            "project_id": self.project_id,
            "activation_generation": self.activation_generation,
            "source_revision": self.source_revision,
            "topology_revision": self.network.topology_revision,
            "machine_connections": {
                machine_id: {
                    "switching_path": self.network.machine_connection_paths[machine_id],
                    "disconnected_rotor_policy": self.network.machine_rotor_policies[machine_id],
                }
                for machine_id in sorted(self.network.machine_connection_paths)
            },
        })

    @classmethod
    def from_power_flow(
        cls,
        prepared_power_flow: PreparedPowerFlow,
        power_flow_result: PowerFlowResult,
        dynamic_models: DynamicMachineModelRegistry,
        *,
        project_id: str,
        activation_generation: int,
        source_revision: tuple[int, int, int, int],
        machine_connection_paths: Mapping[str, tuple[str, ...]],
        machine_rotor_policies: Mapping[str, str],
        switch_states: Mapping[str, bool],
    ) -> "PreparedTransientStability":
        if not isinstance(prepared_power_flow, PreparedPowerFlow):
            raise TypeError("prepared_power_flow must be PreparedPowerFlow.")
        if not isinstance(power_flow_result, PowerFlowResult):
            raise TypeError("power_flow_result must be PowerFlowResult.")
        if not isinstance(dynamic_models, DynamicMachineModelRegistry):
            raise TypeError("dynamic_models must be DynamicMachineModelRegistry.")
        if not power_flow_result.success:
            raise ValueError("Transient stability requires a successful Power Flow operating point.")
        if not power_flow_result.bus_ids:
            raise ValueError("Transient stability requires Power Flow result bus identities.")
        if power_flow_result.bus_ids != prepared_power_flow.bus_ids:
            raise ValueError("Power Flow result bus ordering must match the prepared Power Flow snapshot.")
        if power_flow_result.snapshot_id is None or power_flow_result.snapshot_id != prepared_power_flow.input.snapshot_id:
            raise ValueError("Power Flow result must originate from the exact prepared snapshot used for transient stability.")
        # Project activation provenance must agree with the prepared operating point.
        # Optional metadata is tolerated only for legacy detached snapshots that
        # genuinely lack that field; supplied caller values never override it.
        if prepared_power_flow.project_id is not None:
            if project_id.strip() != prepared_power_flow.project_id.strip():
                raise ValueError(
                    "Transient project_id must match the project that produced the prepared Power Flow snapshot."
                )
        if prepared_power_flow.activation_generation is not None:
            if activation_generation != prepared_power_flow.activation_generation:
                raise ValueError(
                    "Transient activation_generation must match the prepared Power Flow snapshot."
                )
        bus_count = len(prepared_power_flow.bus_ids)
        if len(power_flow_result.voltage_magnitudes) != bus_count or len(power_flow_result.voltage_angles) != bus_count:
            raise ValueError("Power Flow result dimensions must match the prepared Power Flow snapshot.")
        if any(value <= 0.0 for value in power_flow_result.voltage_magnitudes):
            raise ValueError("Power Flow voltage magnitudes must be positive for transient initialization.")

        associations = dynamic_models.all()
        expected_machine_ids = {association.machine_id for association in associations}
        if set(machine_connection_paths) != expected_machine_ids:
            raise ValueError(
                "Detached machine connection paths must cover exactly the dynamic-model association identities."
            )
        if set(machine_rotor_policies) != expected_machine_ids:
            raise ValueError(
                "Disconnected rotor policies must cover exactly the dynamic-model association identities."
            )
        expected_switch_ids = {
            switch_id
            for path in machine_connection_paths.values()
            for switch_id in path
        }
        if set(switch_states) != expected_switch_ids:
            raise ValueError(
                "Captured switch states must cover exactly the switching IDs in the explicit machine paths; "
                f"missing={sorted(expected_switch_ids - set(switch_states))!r}, "
                f"unexpected={sorted(set(switch_states) - expected_switch_ids)!r}."
            )
        if any(type(value) is not bool for value in switch_states.values()):
            raise TypeError("Captured detached switch states must be explicit bool values.")

        definitions: list[DynamicMachineModelDefinition] = []
        for association in associations:
            definitions.append(
                DynamicMachineModelDefinition(
                    machine_id=association.machine_id,
                    bus_id=association.bus_id,
                    parameters=association.parameters,
                    mechanical_power=association.mechanical_power,
                )
            )

        machines: list[ClassicalSynchronousMachine] = []
        initial_states: list[float] = []
        mechanical: dict[str, float] = {}
        for definition in definitions:
            prepared_initial = DynamicInitialStatePreparation.prepare(
                power_flow_result,
                prepared_power_flow.input,
                definition,
            )
            machines.append(
                ClassicalSynchronousMachine(
                    definition.machine_id,
                    definition.bus_id,
                    H=definition.parameters.H,
                    Xd_prime=definition.parameters.Xd_prime,
                    D=definition.parameters.D,
                    Efd=definition.parameters.Efd,
                    initial_delta=prepared_initial.rotor_angle,
                    initial_omega=prepared_initial.speed_deviation,
                )
            )
            initial_states.extend(prepared_initial.state_vector)
            mechanical[definition.machine_id] = definition.mechanical_power

        network = DetachedTransientNetworkState(
            bus_ids=prepared_power_flow.bus_ids,
            branches=prepared_power_flow.branches,
            transformers=prepared_power_flow.transformers,
            shunts=prepared_power_flow.shunts,
            breaker_states=switch_states,
            machine_connection_paths=machine_connection_paths,
            machine_rotor_policies=machine_rotor_policies,
            project_id=project_id,
            activation_generation=activation_generation,
            source_revision=source_revision,
            equipment_states={

                element.branch_id: bool(element.in_service)
                for element in (*prepared_power_flow.branches, *prepared_power_flow.transformers)
            } | {
                element.shunt_id: bool(element.in_service)
                for element in prepared_power_flow.shunts
            },
            topology_revision=prepared_power_flow.topology_revision,
        )
        return cls(network, project_id, activation_generation, source_revision, tuple(machines), mechanical, tuple(initial_states))


class _PreparedTransientPassiveView:
    def __init__(self, state: DetachedTransientNetworkState) -> None:
        self.bus_ids = state.bus_ids
        self.branches = tuple(branch for branch in state.branches if state.is_element_conducting(branch.branch_id, branch.in_service))
        self.transformers = tuple(transformer for transformer in state.transformers if state.is_element_conducting(transformer.branch_id, transformer.in_service))
        self.shunts = tuple(shunt for shunt in state.shunts if state.is_element_conducting(shunt.shunt_id, shunt.in_service))
        self.topology_revision = state.topology_revision


class TransientNetworkSolver:
    """Solve detached passive network plus classical-machine Norton injections."""

    def __init__(self, network_state: DetachedTransientNetworkState, machine_system: MultiMachineSystem) -> None:
        if not isinstance(network_state, DetachedTransientNetworkState):
            raise TypeError("network_state must be DetachedTransientNetworkState.")
        if not isinstance(machine_system, MultiMachineSystem):
            raise TypeError("machine_system must be MultiMachineSystem.")
        machine_ids = tuple(machine.machine_id for machine in machine_system.machines)
        if len(machine_ids) != len(set(machine_ids)):
            raise ValueError("Transient network solver received duplicate dynamic machine identities.")
        if set(machine_ids) != set(network_state.machine_connection_paths):
            missing = sorted(set(machine_ids) - set(network_state.machine_connection_paths))
            unexpected = sorted(set(network_state.machine_connection_paths) - set(machine_ids))
            raise ValueError(
                "Transient Norton-source gating requires exactly one validated detached connection path "
                f"per machine; missing={missing!r}, unexpected={unexpected!r}."
            )
        self.network_state = network_state
        self.machine_system = machine_system

    def solve(self, state: np.ndarray, time: float) -> dict[str, complex]:
        del time
        dynamic_state = self.machine_system.validate_global_state(np.asarray(state, dtype=float))
        passive = YBusBuilder().build(_PreparedTransientPassiveView(self.network_state))
        matrix = passive.matrix.toarray().astype(np.complex128, copy=True)
        source = np.zeros(len(passive.bus_ids), dtype=np.complex128)

        self._apply_active_fault(matrix, self.network_state.active_fault, passive.bus_ids)

        offset = 0
        for machine in self.machine_system.machines:
            local_state = dynamic_state[offset:offset + machine.state_size]
            offset += machine.state_size
            bus_id = str(machine.bus_id)
            if bus_id not in passive.bus_ids:
                raise ValueError(f"Machine '{machine.machine_id}' references unknown bus '{bus_id}'.")
            # Rotor state is always retained in the global differential state.
            # The electrical Norton equivalent is included only while every
            # explicitly captured breaker-controlled path component conducts.
            if not self.network_state.is_machine_connected(machine.machine_id):
                continue
            index = passive.index_of(bus_id)
            delta = float(local_state[0])
            e_internal = float(machine.parameters.Efd) * np.exp(1j * delta)
            admittance = 1.0 / (1j * float(machine.parameters.Xd_prime))
            matrix[index, index] += admittance
            source[index] += admittance * e_internal

        try:
            voltages = np.linalg.solve(matrix, source)
        except np.linalg.LinAlgError as exc:
            raise ValueError("Transient algebraic network matrix is singular.") from exc

        if not np.all(np.isfinite(voltages.real)) or not np.all(np.isfinite(voltages.imag)):
            raise ValueError("Transient algebraic network solution contains non-finite voltages.")
        return {bus_id: complex(voltages[index]) for index, bus_id in enumerate(passive.bus_ids)}

    @staticmethod
    def _apply_active_fault(matrix: np.ndarray, fault: object | None, bus_ids: tuple[str, ...]) -> None:
        if fault is None:
            return
        if not isinstance(fault, TransientFault):
            raise TypeError("Detached transient active_fault must be TransientFault.")
        if fault.bus_id not in bus_ids:
            raise ValueError(f"Transient fault references unknown bus '{fault.bus_id}'.")
        impedance = complex(fault.impedance)
        if abs(impedance) <= 1e-15:
            admittance = 1e12 + 0.0j
        else:
            admittance = 1.0 / impedance
        matrix[bus_ids.index(fault.bus_id), bus_ids.index(fault.bus_id)] += admittance


__all__ = ["DetachedTransientNetworkState", "PreparedTransientStability", "TransientNetworkSolver"]
