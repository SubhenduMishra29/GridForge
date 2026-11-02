# ============================================================
# File: core/application/study_preparation.py
# GridForge V2 — Application Study Preparation Boundary
# Author: Subhendu Mishra
# ============================================================
"""Application-owned bridge from active project state to detached study inputs."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from core.analysis.dynamic_model_association import DynamicMachineModelRegistry
from core.analysis.power_flow_preparation import PreparedPowerFlow, PowerFlowPreparation
from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.short_circuit_preparation import ShortCircuitPreparation
from core.analysis.short_circuit_configuration import ShortCircuitStudyConfiguration
from core.analysis.transient_network import PreparedTransientStability
from core.network.electrical_boundary import conduction_state
from core.analysis.transient_stability import TransientStabilityStudyConfiguration
from core.solver.power_flow.result import PowerFlowResult
from core.solver.short_circuit.input import ShortCircuitInput

from .project import ProjectSnapshot
from .study import StudyExecutionContext


class StudyPreparationService:
    """Prepare detached Core study snapshots without exposing live Core objects to handlers."""

    def __init__(self, execution_context: StudyExecutionContext) -> None:
        if not isinstance(execution_context, StudyExecutionContext):
            raise TypeError("execution_context must be StudyExecutionContext.")
        self._execution_context = execution_context

    @property
    def snapshot(self) -> ProjectSnapshot:
        return self._execution_context.project_snapshot

    @property
    def topology(self):
        return self._execution_context.topology_snapshot

    def prepare_power_flow(self, configuration: PowerFlowStudyConfiguration) -> PreparedPowerFlow:
        if not isinstance(configuration, PowerFlowStudyConfiguration):
            raise TypeError("configuration must be PowerFlowStudyConfiguration.")
        prepared = PowerFlowPreparation.prepare(
            self._execution_context.project_snapshot.network,
            configuration,
            topology_snapshot=self.topology,
        )
        revision = self._execution_context.source_revision
        return replace(
            prepared,
            source_revision=(
                revision.model_revision,
                revision.topology_revision,
                revision.presentation_revision,
                revision.persisted_revision,
            ),
        )

    def prepare_short_circuit(self, configuration: ShortCircuitStudyConfiguration) -> ShortCircuitInput:
        if not isinstance(configuration, ShortCircuitStudyConfiguration):
            raise TypeError("configuration must be ShortCircuitStudyConfiguration.")
        preparation = ShortCircuitPreparation(
            self._execution_context.project_snapshot.network,
            base_mva=(configuration.base_mva if configuration.base_mva is not None else configuration.metadata.get("base_mva")),
        )
        return preparation.prepare(
            configuration.fault_type,
            configuration.fault_bus_id,
            configuration.fault_impedance,
            elements=configuration.element_ids or None,
            topology_snapshot=self.topology,
            phase_domain_case=configuration.phase_domain_case,
            phase_domain_sources=configuration.phase_domain_sources or None,
            phase_domain_faults=configuration.phase_domain_faults or None,
        )

    def prepare_transient_stability(
        self,
        configuration: TransientStabilityStudyConfiguration,
        prepared_power_flow: PreparedPowerFlow,
        power_flow_result: PowerFlowResult,
        dynamic_models: DynamicMachineModelRegistry,
    ) -> PreparedTransientStability:
        """Prepare a detached transient study from an already-solved PF operating point."""
        if not isinstance(configuration, TransientStabilityStudyConfiguration):
            raise TypeError("configuration must be TransientStabilityStudyConfiguration.")
        if not isinstance(prepared_power_flow, PreparedPowerFlow):
            raise TypeError("prepared_power_flow must be PreparedPowerFlow.")
        if not isinstance(power_flow_result, PowerFlowResult):
            raise TypeError("power_flow_result must be PowerFlowResult.")
        if not isinstance(dynamic_models, DynamicMachineModelRegistry):
            raise TypeError("dynamic_models must be DynamicMachineModelRegistry.")

        revision = self._execution_context.source_revision
        expected_revision = (
            revision.model_revision,
            revision.topology_revision,
            revision.presentation_revision,
            revision.persisted_revision,
        )
        if prepared_power_flow.source_revision is None:
            raise ValueError(
                "Transient stability requires a Power Flow snapshot prepared by the active "
                "Application study context; unversioned operating points are not accepted."
            )
        # Presentation and persistence revisions do not change electrical inputs.
        if prepared_power_flow.source_revision[:2] != expected_revision[:2]:
            raise ValueError(
                "Power Flow operating point model/topology revision does not match the active "
                "StudyExecutionContext; rerun Power Flow before transient stability."
            )
        if prepared_power_flow.project_id != self._execution_context.project_id:
            raise ValueError("Power Flow operating point belongs to a different project.")
        if prepared_power_flow.activation_generation != self._execution_context.activation_generation:
            raise ValueError("Power Flow operating point belongs to a different project activation.")
        if prepared_power_flow.topology_revision != self.topology.topology_revision:
            raise ValueError("Power Flow operating point topology revision is stale.")

        # A transient operating point is valid only when the successful
        # numerical result belongs to this exact detached Power Flow input.
        # Bus ordering alone is insufficient: separate snapshots can share
        # identical Bus IDs while carrying different model parameters.
        if not power_flow_result.success:
            raise ValueError(
                "Transient Stability requires a converged initial Power Flow result."
            )
        if power_flow_result.bus_ids != prepared_power_flow.bus_ids:
            raise ValueError(
                "Initial Power Flow result bus ordering does not match the "
                "prepared Power Flow snapshot."
            )
        expected_snapshot_id = prepared_power_flow.input.snapshot_id
        if power_flow_result.snapshot_id != expected_snapshot_id:
            raise ValueError(
                "Initial Power Flow result snapshot identity does not match "
                "the prepared Power Flow input."
            )

        # Dynamics inherits canonical Bus identity from the same topology
        # snapshot used to prepare Power Flow. Dynamic-model associations
        # contain engineering configuration only; they cannot introduce an
        # alternate electrical attachment.
        canonical_buses = set(self.topology.bus_ids)
        attachments = {
            (record.equipment_id, record.terminal_role): record.bus_id
            for record in self.topology.equipment_bus_attachments
        }
        attachments_by_equipment: dict[str, list[Any]] = {}
        for record in self.topology.equipment_bus_attachments:
            attachments_by_equipment.setdefault(record.equipment_id, []).append(record)
        machine_connection_paths: dict[str, tuple[str, ...]] = {}
        machine_rotor_policies: dict[str, str] = {}
        switch_states: dict[str, bool] = {}
        switching_types = {"breaker", "switch", "disconnector", "fuse"}
        registry = getattr(self._execution_context.project_snapshot.network, "registry", None)
        if registry is None or not callable(getattr(registry, "get_by_identity", None)):
            raise ValueError(
                "Transient stability requires the detached ProjectSnapshot Network registry "
                "to capture canonical switching-device states."
            )
        for association in dynamic_models.all():
            machine_id = str(association.machine_id)
            bus_id = str(association.bus_id)
            if association.project_id != self._execution_context.project_id:
                raise ValueError(
                    f"Dynamic machine '{machine_id}' association belongs to project "
                    f"'{association.project_id}', not active project '{self._execution_context.project_id}'."
                )
            if association.activation_generation != self._execution_context.activation_generation:
                raise ValueError(
                    f"Dynamic machine '{machine_id}' association belongs to activation "
                    f"{association.activation_generation}, not active activation "
                    f"{self._execution_context.activation_generation}."
                )
            if bus_id not in canonical_buses:
                raise ValueError(
                    f"Dynamic machine '{machine_id}' references unknown Bus '{bus_id}' "
                    "in the canonical TopologySnapshot."
                )
            attached_bus_id = attachments.get((machine_id, "terminal"))
            if attached_bus_id is None:
                raise ValueError(
                    f"Dynamic machine '{machine_id}' has no canonical terminal attachment "
                    "in the TopologySnapshot."
                )
            if attached_bus_id != bus_id:
                raise ValueError(
                    f"Dynamic machine '{machine_id}' bus '{bus_id}' does not match "
                    f"canonical topology attachment '{attached_bus_id}'."
                )

            # The ordered path is a persisted engineering identity, not a
            # display-name heuristic. Resolve each switch from canonical
            # terminal-to-Bus attachments and require a contiguous path.
            current_bus = bus_id
            visited_buses = {current_bus}
            for switch_id in association.connection_path:
                switch_attachments = attachments_by_equipment.get(switch_id, ())
                if len(switch_attachments) != 2:
                    raise ValueError(
                        f"Dynamic machine '{machine_id}' connection path target "
                        f"'{switch_id}' must have exactly two canonical terminal attachments; "
                        f"found {len(switch_attachments)}."
                    )
                equipment_types = {item.equipment_type for item in switch_attachments}
                path_buses = {item.bus_id for item in switch_attachments}
                if len(equipment_types) != 1 or next(iter(equipment_types)) not in switching_types:
                    raise ValueError(
                        f"Dynamic machine '{machine_id}' path target '{switch_id}' is not "
                        "a canonical breaker/switch/disconnector/fuse."
                    )
                if len(path_buses) != 2:
                    raise ValueError(
                        f"Dynamic machine '{machine_id}' path target '{switch_id}' "
                        "does not connect two distinct Buses."
                    )
                if current_bus not in path_buses:
                    raise ValueError(
                        f"Dynamic machine '{machine_id}' connection path is discontinuous "
                        f"at switch '{switch_id}': current Bus '{current_bus}' is not one "
                        f"of {sorted(path_buses)!r}."
                    )
                next_bus = next(item for item in path_buses if item != current_bus)
                if next_bus in visited_buses:
                    raise ValueError(
                        f"Dynamic machine '{machine_id}' connection path loops at "
                        f"switch '{switch_id}' and Bus '{next_bus}'."
                    )
                try:
                    switch = registry.get_by_identity(switch_id)
                except KeyError as exc:
                    raise ValueError(
                        f"Dynamic machine '{machine_id}' connection path references "
                        f"unregistered switching target '{switch_id}'."
                    ) from exc
                if str(getattr(switch, "id", "")) != switch_id:
                    raise ValueError(
                        f"Dynamic machine '{machine_id}' path target '{switch_id}' "
                        "does not resolve to the same canonical object identity."
                    )
                switch_states[switch_id] = bool(conduction_state(switch))
                current_bus = next_bus
                visited_buses.add(current_bus)

            machine_connection_paths[machine_id] = tuple(association.connection_path)
            machine_rotor_policies[machine_id] = association.disconnected_rotor_policy

        if prepared_power_flow.bus_ids != self.topology.bus_ids:
            raise ValueError(
                "Prepared Power Flow bus ordering does not match the canonical "
                "TopologySnapshot used by this StudyExecutionContext."
            )

        return PreparedTransientStability.from_power_flow(
            prepared_power_flow,
            power_flow_result,
            dynamic_models,
            project_id=self._execution_context.project_id,
            activation_generation=self._execution_context.activation_generation,
            source_revision=(
                self._execution_context.source_revision.model_revision,
                self._execution_context.source_revision.topology_revision,
                self._execution_context.source_revision.presentation_revision,
                self._execution_context.source_revision.persisted_revision,
            ),
            machine_connection_paths=machine_connection_paths,
            machine_rotor_policies=machine_rotor_policies,
            switch_states=switch_states,
        )


__all__ = ["StudyPreparationService"]
