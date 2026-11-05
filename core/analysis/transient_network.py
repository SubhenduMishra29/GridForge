# Author: Subhendu Mishra
"""Detached transient-network state and machine/network algebraic coupling."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
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
from core.solver.dynamics.dae_solver import AlgebraicNetworkSolution
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
    switch_available_states: Mapping[str, bool] = MappingProxyType({})
    switch_connections: Mapping[str, tuple[str, str]] = MappingProxyType({})
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
        if any(type(value) is not bool for value in self.breaker_states.values()):
            raise TypeError("Detached transient breaker states must be explicit bool values.")
        if any(type(value) is not bool for value in self.switch_available_states.values()):
            raise TypeError("Detached transient switch-availability states must be explicit bool values.")
        breaker_states = {str(k): v for k, v in self.breaker_states.items()}
        switch_available_states = {str(k): v for k, v in self.switch_available_states.items()}
        switch_connections = {}
        for switch_id, raw_buses in self.switch_connections.items():
            if isinstance(raw_buses, (str, bytes)):
                raise TypeError(f"Switch '{switch_id}' connection must contain two Bus IDs.")
            buses = tuple(str(item).strip() for item in raw_buses)
            if len(buses) != 2 or any(not item for item in buses) or buses[0] == buses[1]:
                raise ValueError(f"Switch '{switch_id}' must connect exactly two distinct Bus IDs.")
            if any(bus_id not in bus_ids for bus_id in buses):
                raise ValueError(f"Switch '{switch_id}' references a Bus outside the detached transient snapshot.")
            switch_connections[str(switch_id)] = buses
        if set(switch_connections) != set(breaker_states) or set(switch_connections) != set(switch_available_states):
            raise ValueError(
                "Detached transient switch connections, conduction states and availability states "
                "must cover exactly the same canonical switching-equipment identities."
            )
        equipment_states = {str(k): bool(v) for k, v in self.equipment_states.items()}
        paths = {}
        for machine_id, raw_path in self.machine_connection_paths.items():
            key = str(machine_id).strip()
            if isinstance(raw_path, (str, bytes)):
                raise TypeError(f"Machine '{key}' connection path must be an ordered sequence of switch IDs.")
            path = tuple(str(item).strip() for item in raw_path)
            if not key or not path or any(not item for item in path):
                raise ValueError(f"Machine '{key or machine_id}' requires a non-empty explicit switching path.")
            if len(path) != len(set(path)):
                raise ValueError(f"Machine '{key}' connection path contains duplicate switching equipment IDs.")
            missing = tuple(item for item in path if item not in breaker_states)
            unavailable_missing = tuple(item for item in path if item not in switch_available_states)
            if missing or unavailable_missing:
                raise ValueError(
                    f"Machine '{key}' connection path has incomplete captured switch state; "
                    f"missing_conduction={missing!r}, missing_availability={unavailable_missing!r}."
                )
            paths[key] = path
        policies = {str(k): str(v) for k, v in self.machine_rotor_policies.items()}
        if set(policies) != set(paths):
            raise ValueError("Machine rotor-disconnection policies must cover exactly the machine connection-path identities.")
        for machine_id, policy in policies.items():
            if policy != "continue_with_zero_electrical_power":
                raise ValueError(f"Machine '{machine_id}' has unsupported disconnected rotor policy {policy!r}.")
        object.__setattr__(self, "breaker_states", MappingProxyType(breaker_states))
        object.__setattr__(self, "switch_available_states", MappingProxyType(switch_available_states))
        object.__setattr__(self, "switch_connections", MappingProxyType(switch_connections))
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
        return all(self.breaker_states.get(item, False) and self.switch_available_states.get(item, False) for item in path)


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
    model_types: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    base_mva: float | None = None
    bus_voltage_bases_kv: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))
    nominal_frequency_hz: float | None = None
    canonical_topology_fingerprint: str | None = None

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
        model_types = {str(key): str(value).strip() for key, value in self.model_types.items()}
        if any(not value for value in model_types.values()):
            raise ValueError("Prepared transient declared model types must be non-empty.")
        object.__setattr__(self, "model_types", MappingProxyType(model_types))
        if self.base_mva is not None:
            base_mva = float(self.base_mva)
            if not np.isfinite(base_mva) or base_mva <= 0.0:
                raise ValueError("Prepared transient base MVA must be positive and finite.")
            object.__setattr__(self, "base_mva", base_mva)
        voltage_bases = {str(key): float(value) for key, value in self.bus_voltage_bases_kv.items()}
        if voltage_bases and set(voltage_bases) != set(self.network.bus_ids):
            raise ValueError("Prepared transient voltage bases must cover the detached network Bus identities exactly.")
        if any(not np.isfinite(value) or value <= 0.0 for value in voltage_bases.values()):
            raise ValueError("Prepared transient voltage bases must be positive and finite.")
        object.__setattr__(self, "bus_voltage_bases_kv", MappingProxyType(voltage_bases))
        if self.nominal_frequency_hz is not None:
            frequency = float(self.nominal_frequency_hz)
            if not np.isfinite(frequency) or frequency <= 0.0:
                raise ValueError("Prepared transient nominal frequency must be positive and finite.")
            object.__setattr__(self, "nominal_frequency_hz", frequency)
        if self.canonical_topology_fingerprint is not None:
            fingerprint = str(self.canonical_topology_fingerprint).strip()
            if len(fingerprint) != 64 or any(character not in "0123456789abcdef" for character in fingerprint):
                raise ValueError("Prepared canonical topology fingerprint must be a lowercase SHA-256 digest.")
            object.__setattr__(self, "canonical_topology_fingerprint", fingerprint)
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
        if self.model_types and set(machine_ids) != set(self.model_types):
            raise ValueError("Prepared transient declared model types must match its machine identities.")

    @property
    def provenance(self) -> Mapping[str, object]:
        """Return the canonical, detached identity and model manifest for this run."""
        state_signals: list[Mapping[str, object]] = []
        machine_models: list[Mapping[str, object]] = []
        global_index = 0
        for machine in self.machines:
            parameters = machine.parameters
            model_type = f"{type(machine).__module__}.{type(machine).__qualname__}"
            machine_models.append(MappingProxyType({
                "machine_id": machine.machine_id,
                "bus_id": machine.bus_id,
                "declared_model_type": self.model_types.get(machine.machine_id),
                "executable_model_type": model_type,
                "parameters": MappingProxyType({
                    "H": parameters.H,
                    "Xd_prime": parameters.Xd_prime,
                    "D": parameters.D,
                    "Efd": parameters.Efd,
                }),
                "mechanical_power": self.mechanical_powers[machine.machine_id],
            }))
            # The currently prepared production path constructs the classical
            # second-order model. Do not infer labels for a future model whose
            # state semantics have not been declared by its implementation.
            if type(machine) is ClassicalSynchronousMachine and machine.state_size == 2:
                state_signals.extend((
                    MappingProxyType({
                        "signal_id": f"machine:{machine.machine_id}:rotor_angle",
                        "global_index": global_index,
                        "label": f"{machine.machine_id} — Rotor angle",
                        "state_name": "rotor_angle",
                        "unit": "rad",
                        "machine_id": machine.machine_id,
                        "quantity": "rotor_angle",
                        "component": "scalar",
                    }),
                    MappingProxyType({
                        "signal_id": f"machine:{machine.machine_id}:speed_deviation",
                        "global_index": global_index + 1,
                        "label": f"{machine.machine_id} — Speed deviation",
                        "state_name": "speed_deviation",
                        "unit": "p.u.",
                        "machine_id": machine.machine_id,
                        "quantity": "speed_deviation",
                        "component": "scalar",
                    }),
                ))
            global_index += int(machine.state_size)
        # Fingerprint the prepared electrical topology, not project revision
        # counters or mutable UI state. Numerical parameters and PU bases are
        # intentionally excluded: those are separate compatibility dimensions.
        topology_payload = {
            "schema_version": 1,
            "bus_ids": tuple(sorted(self.network.bus_ids)),
            "branches": tuple(sorted(
                (item.branch_id, item.from_bus_id, item.to_bus_id)
                for item in self.network.branches
            )),
            "transformers": tuple(sorted(
                (item.branch_id, item.from_bus_id, item.to_bus_id)
                for item in self.network.transformers
            )),
            "shunts": tuple(sorted(
                (item.shunt_id, item.bus_id)
                for item in self.network.shunts
            )),
            "equipment_states": tuple(sorted(self.network.equipment_states.items())),
            "switch_states": tuple(sorted(self.network.breaker_states.items())),
            "switch_availability_states": tuple(sorted(self.network.switch_available_states.items())),
            "switch_connections": tuple(sorted(
                (key, tuple(value)) for key, value in self.network.switch_connections.items()
            )),
            "machine_connections": tuple(sorted(
                (key, tuple(value)) for key, value in self.network.machine_connection_paths.items()
            )),
            "machine_rotor_policies": tuple(sorted(self.network.machine_rotor_policies.items())),
        }
        topology_fingerprint = hashlib.sha256(
            json.dumps(topology_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        manifest = {
            "schema_version": 1,
            "model_family": "synchronous_machine",
            "machine_models": tuple(machine_models),
        }
        result: dict[str, object] = {
            "project_id": self.project_id,
            "activation_generation": self.activation_generation,
            "source_revision": self.source_revision,
            "topology_revision": self.network.topology_revision,
            "power_base_mva": self.base_mva,
            "bus_voltage_bases_kv": MappingProxyType(dict(self.bus_voltage_bases_kv)),
            "nominal_frequency_hz": self.nominal_frequency_hz,
            "canonical_topology_fingerprint": self.canonical_topology_fingerprint,
            "prepared_network_topology_fingerprint": MappingProxyType({
                "schema_version": 1,
                "algorithm": "sha256",
                "value": topology_fingerprint,
            }),
            "machine_connections": {
                machine_id: {
                    "switching_path": self.network.machine_connection_paths[machine_id],
                    "disconnected_rotor_policy": self.network.machine_rotor_policies[machine_id],
                }
                for machine_id in sorted(self.network.machine_connection_paths)
            },
            "initial_switch_states": dict(self.network.breaker_states),
            "switch_availability_states": dict(self.network.switch_available_states),
            "switch_connections": dict(self.network.switch_connections),
            "machine_model_manifest": MappingProxyType(manifest),
        }
        if len(state_signals) == global_index:
            result["state_signals"] = tuple(state_signals)
        return MappingProxyType(result)

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
        switch_available_states: Mapping[str, bool],
        switch_connections: Mapping[str, tuple[str, str]],
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
        missing_switch_ids = expected_switch_ids - set(switch_states)
        if missing_switch_ids:
            raise ValueError(
                "Captured switch states are missing machine-path targets: "
                f"{sorted(missing_switch_ids)!r}."
            )
        if any(type(value) is not bool for value in switch_states.values()):
            raise TypeError("Captured detached switch states must be explicit bool values.")
        if set(switch_available_states) != set(switch_states):
            raise ValueError("Switch conduction and availability states must cover identical canonical switch identities.")
        if any(type(value) is not bool for value in switch_available_states.values()):
            raise TypeError("Captured detached switch-availability states must be explicit bool values.")
        if set(switch_connections) != set(switch_states):
            raise ValueError("Switch Bus connections, conduction states and availability states must have identical identities.")

        definitions: list[DynamicMachineModelDefinition] = []
        for association in associations:
            definitions.append(
                DynamicMachineModelDefinition(
                    machine_id=association.machine_id,
                    bus_id=association.bus_id,
                    parameters=association.parameters,
                    mechanical_power=association.mechanical_power,
                    model_type=association.model_type,
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
            switch_available_states=switch_available_states,
            switch_connections=switch_connections,
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
        return cls(
            network,
            project_id,
            activation_generation,
            source_revision,
            tuple(machines),
            mechanical,
            tuple(initial_states),
            {definition.machine_id: definition.model_type for definition in definitions},
            prepared_power_flow.base_mva,
            prepared_power_flow.bus_voltage_bases,
            prepared_power_flow.nominal_frequency_hz,
            prepared_power_flow.canonical_topology_fingerprint,
        )


class _PreparedTransientPassiveView:
    def __init__(self, state: DetachedTransientNetworkState) -> None:
        self.bus_ids = state.bus_ids
        self.branches = tuple(branch for branch in state.branches if state.is_element_conducting(branch.branch_id, branch.in_service))
        self.transformers = tuple(transformer for transformer in state.transformers if state.is_element_conducting(transformer.branch_id, transformer.in_service))
        self.shunts = tuple(shunt for shunt in state.shunts if state.is_element_conducting(shunt.shunt_id, shunt.in_service))
        self.topology_revision = state.topology_revision


class TransientNetworkSolver:
    """Solve detached passive network plus classical-machine Norton injections."""

    def __init__(
        self,
        network_state: DetachedTransientNetworkState,
        machine_system: MultiMachineSystem,
        *,
        residual_tolerance: float = 1e-10,
        condition_limit: float = 1e12,
    ) -> None:
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
        if not np.isfinite(residual_tolerance) or residual_tolerance <= 0.0:
            raise ValueError("residual_tolerance must be finite and positive.")
        if not np.isfinite(condition_limit) or condition_limit <= 1.0:
            raise ValueError("condition_limit must be finite and greater than one.")
        self.network_state = network_state
        self.machine_system = machine_system
        self.residual_tolerance = float(residual_tolerance)
        self.condition_limit = float(condition_limit)

    def solve(self, state: np.ndarray, time: float) -> AlgebraicNetworkSolution:
        evaluation_time = float(time)
        if not np.isfinite(evaluation_time):
            raise ValueError("Transient algebraic evaluation time must be finite.")
        dynamic_state = self.machine_system.validate_global_state(np.asarray(state, dtype=float))
        passive = YBusBuilder().build(_PreparedTransientPassiveView(self.network_state))
        matrix = passive.matrix.toarray().astype(np.complex128, copy=True)
        matrix, bus_to_index, reduced_bus_ids = self._contract_closed_switches(
            matrix,
            passive.bus_ids,
        )
        source = np.zeros(len(reduced_bus_ids), dtype=np.complex128)

        self._apply_active_fault(matrix, self.network_state.active_fault, bus_to_index)

        source_ids: list[str] = []
        offset = 0
        for machine in self.machine_system.machines:
            local_state = dynamic_state[offset:offset + machine.state_size]
            offset += machine.state_size
            bus_id = str(machine.bus_id)
            if bus_id not in bus_to_index:
                raise ValueError(f"Machine '{machine.machine_id}' references unknown bus '{bus_id}'.")
            # Rotor state is always retained in the global differential state.
            # The electrical Norton equivalent is included only while every
            # explicitly captured breaker-controlled path component conducts.
            if not self.network_state.is_machine_connected(machine.machine_id):
                continue
            index = bus_to_index[bus_id]
            delta = float(local_state[0])
            e_internal = float(machine.parameters.Efd) * np.exp(1j * delta)
            admittance = 1.0 / (1j * float(machine.parameters.Xd_prime))
            matrix[index, index] += admittance
            source[index] += admittance * e_internal
            source_ids.append(str(machine.machine_id))

        # A disconnected generator terminal can become an isolated Bus after
        # its breaker opens. Such a node has no defined network voltage and
        # contributes no coupling to any other node; pin only that zero row /
        # column to 0 pu so it cannot make the remaining energized network
        # singular. This is a numerical reference for a floating isolated
        # node, not an electrical shunt or a live-project mutation.
        for index in range(matrix.shape[0]):
            if (
                not np.any(np.abs(matrix[index, :]) > 1e-14)
                and not np.any(np.abs(matrix[:, index]) > 1e-14)
            ):
                matrix[index, index] = 1.0 + 0.0j
                source[index] = 0.0 + 0.0j

        context = {
            "topology_revision": self.network_state.topology_revision,
            "simulation_time": evaluation_time,
            "bus_ids": tuple(reduced_bus_ids),
            "source_ids": tuple(source_ids),
            "active_fault_id": getattr(self.network_state.active_fault, "fault_id", None),
            "active_fault_bus_id": getattr(self.network_state.active_fault, "bus_id", None),
            "active_fault_type": (
                str(getattr(getattr(self.network_state.active_fault, "fault_type", None), "value",
                            getattr(self.network_state.active_fault, "fault_type", None)))
                if self.network_state.active_fault is not None else None
            ),
            "study_provenance": {
                "project_id": self.network_state.project_id,
                "activation_generation": self.network_state.activation_generation,
                "source_revision": self.network_state.source_revision,
            },
        }
        if not np.all(np.isfinite(matrix.real)) or not np.all(np.isfinite(matrix.imag)):
            raise ValueError(
                f"Transient algebraic matrix contains non-finite coefficients; "
                f"buses={tuple(reduced_bus_ids)}, topology_revision={self.network_state.topology_revision}."
            )
        if not np.all(np.isfinite(source.real)) or not np.all(np.isfinite(source.imag)):
            raise ValueError(
                f"Transient algebraic source vector contains non-finite values; "
                f"buses={tuple(reduced_bus_ids)}, topology_revision={self.network_state.topology_revision}."
            )

        try:
            condition_number = float(np.linalg.cond(matrix, p=np.inf))
        except np.linalg.LinAlgError as exc:
            return AlgebraicNetworkSolution(
                bus_voltages={},
                status="SINGULAR",
                accepted=False,
                quality_verified=True,
                solver_name="numpy.linalg.solve",
                condition_number=float("inf"),
                condition_limit=self.condition_limit,
                diagnostics=(f"Condition estimation failed: {exc}",),
                **context,
            )
        if not np.isfinite(condition_number):
            return AlgebraicNetworkSolution(
                bus_voltages={},
                status="SINGULAR",
                accepted=False,
                quality_verified=True,
                solver_name="numpy.linalg.solve",
                condition_number=condition_number,
                condition_limit=self.condition_limit,
                diagnostics=("The assembled algebraic matrix is singular (infinite condition estimate).",),
                **context,
            )

        try:
            voltages = np.linalg.solve(matrix, source)
        except np.linalg.LinAlgError as exc:
            return AlgebraicNetworkSolution(
                bus_voltages={},
                status="SINGULAR",
                accepted=False,
                quality_verified=True,
                solver_name="numpy.linalg.solve",
                condition_number=condition_number,
                condition_limit=self.condition_limit,
                diagnostics=(f"Direct algebraic solve failed: {exc}",),
                **context,
            )

        if not np.all(np.isfinite(voltages.real)) or not np.all(np.isfinite(voltages.imag)):
            return AlgebraicNetworkSolution(
                bus_voltages={},
                status="NON_FINITE",
                accepted=False,
                quality_verified=True,
                solver_name="numpy.linalg.solve",
                condition_number=condition_number,
                condition_limit=self.condition_limit,
                diagnostics=("Direct algebraic solve returned non-finite bus voltages.",),
                **context,
            )

        residual = matrix @ voltages - source
        absolute_residual = float(np.linalg.norm(residual, ord=np.inf))
        matrix_norm = float(np.linalg.norm(matrix, ord=np.inf))
        voltage_norm = float(np.linalg.norm(voltages, ord=np.inf))
        source_norm = float(np.linalg.norm(source, ord=np.inf))
        scale = matrix_norm * voltage_norm + source_norm
        normalized_residual = (
            absolute_residual / scale if scale > 0.0
            else (0.0 if absolute_residual == 0.0 else float("inf"))
        )

        diagnostics: list[str] = []
        status = "ACCEPTED"
        if condition_number > self.condition_limit:
            status = "ILL_CONDITIONED"
            diagnostics.append(
                f"Matrix condition estimate {condition_number:.6g} exceeds configured limit "
                f"{self.condition_limit:.6g}."
            )
        if normalized_residual > self.residual_tolerance:
            if status == "ACCEPTED":
                status = "RESIDUAL_REJECTED"
            diagnostics.append(
                f"Normalized backward error {normalized_residual:.6g} exceeds tolerance "
                f"{self.residual_tolerance:.6g}."
            )

        return AlgebraicNetworkSolution(
            bus_voltages={
                bus_id: complex(voltages[bus_to_index[bus_id]])
                for bus_id in passive.bus_ids
            },
            status=status,
            accepted=status == "ACCEPTED",
            quality_verified=True,
            solver_name="numpy.linalg.solve",
            absolute_residual_norm=absolute_residual,
            normalized_residual=normalized_residual,
            residual_tolerance=self.residual_tolerance,
            condition_number=condition_number,
            condition_limit=self.condition_limit,
            diagnostics=tuple(diagnostics),
            **context,
        )

    def _contract_closed_switches(
        self,
        matrix: np.ndarray,
        bus_ids: tuple[str, ...],
    ) -> tuple[np.ndarray, dict[str, int], tuple[str, ...]]:
        """Contract closed ideal-switch edges into common numerical Bus nodes."""
        parent = {bus_id: bus_id for bus_id in bus_ids}

        def find(bus_id: str) -> str:
            while parent[bus_id] != bus_id:
                parent[bus_id] = parent[parent[bus_id]]
                bus_id = parent[bus_id]
            return bus_id

        for switch_id, (from_bus, to_bus) in self.network_state.switch_connections.items():
            if not (
                self.network_state.breaker_states[switch_id]
                and self.network_state.switch_available_states[switch_id]
            ):
                continue
            first = find(from_bus)
            second = find(to_bus)
            if first != second:
                low, high = sorted((first, second))
                parent[high] = low

        roots = tuple(sorted({find(bus_id) for bus_id in bus_ids}))
        root_index = {root: index for index, root in enumerate(roots)}
        bus_to_index = {bus_id: root_index[find(bus_id)] for bus_id in bus_ids}
        reduced = np.zeros((len(roots), len(roots)), dtype=np.complex128)
        for row, row_bus in enumerate(bus_ids):
            reduced_row = bus_to_index[row_bus]
            for column, column_bus in enumerate(bus_ids):
                reduced_column = bus_to_index[column_bus]
                reduced[reduced_row, reduced_column] += matrix[row, column]
        return reduced, bus_to_index, roots

    @staticmethod
    def _apply_active_fault(
        matrix: np.ndarray,
        fault: object | None,
        bus_to_index: Mapping[str, int],
    ) -> None:
        if fault is None:
            return
        if not isinstance(fault, TransientFault):
            raise TypeError("Detached transient active_fault must be TransientFault.")
        if fault.bus_id not in bus_to_index:
            raise ValueError(f"Transient fault references unknown bus '{fault.bus_id}'.")
        impedance = complex(fault.impedance)
        if abs(impedance) <= 1e-15:
            admittance = 1e12 + 0.0j
        else:
            admittance = 1.0 / impedance
        index = bus_to_index[fault.bus_id]
        matrix[index, index] += admittance


__all__ = ["DetachedTransientNetworkState", "PreparedTransientStability", "TransientNetworkSolver"]
