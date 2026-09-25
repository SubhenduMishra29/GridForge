# ============================================================
# File: core/application/study_preparation.py
# GridForge V2 — Application Study Preparation Boundary
# Author: Subhendu Mishra
# ============================================================
"""Application-owned bridge from active project state to detached study inputs."""

from __future__ import annotations

from core.analysis.dynamic_model_association import DynamicMachineModelRegistry
from core.analysis.power_flow_preparation import PreparedPowerFlow, PowerFlowPreparation
from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.short_circuit_preparation import ShortCircuitPreparation
from core.analysis.short_circuit_configuration import ShortCircuitStudyConfiguration
from core.analysis.transient_network import PreparedTransientStability
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
        return PowerFlowPreparation.prepare(
            self._execution_context.project_snapshot.network,
            configuration,
            topology_snapshot=self.topology,
        )

    def prepare_short_circuit(self, configuration: ShortCircuitStudyConfiguration) -> ShortCircuitInput:
        if not isinstance(configuration, ShortCircuitStudyConfiguration):
            raise TypeError("configuration must be ShortCircuitStudyConfiguration.")
        preparation = ShortCircuitPreparation(
            self._execution_context.project_snapshot.network,
            base_mva=configuration.metadata.get("base_mva"),
        )
        return preparation.prepare(
            configuration.fault_type,
            configuration.fault_bus_id,
            configuration.fault_impedance,
            elements=configuration.element_ids or None,
            topology_snapshot=self.topology,
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

        # Dynamics inherits canonical Bus identity from the same topology
        # snapshot used to prepare Power Flow. Dynamic-model associations
        # contain engineering configuration only; they cannot introduce an
        # alternate electrical attachment.
        canonical_buses = set(self.topology.bus_ids)
        attachments = {
            (record.equipment_id, record.terminal_role): record.bus_id
            for record in self.topology.equipment_bus_attachments
        }
        for association in dynamic_models.all():
            bus_id = str(association.bus_id)
            if bus_id not in canonical_buses:
                raise ValueError(
                    f"Dynamic machine '{association.machine_id}' references "
                    f"unknown Bus '{bus_id}' in the canonical TopologySnapshot."
                )
            attached_bus_id = attachments.get((str(association.machine_id), "terminal"))
            if attached_bus_id is None:
                raise ValueError(
                    f"Dynamic machine '{association.machine_id}' has no "
                    "canonical terminal attachment in the TopologySnapshot."
                )
            if attached_bus_id != bus_id:
                raise ValueError(
                    f"Dynamic machine '{association.machine_id}' bus '{bus_id}' "
                    f"does not match canonical topology attachment '{attached_bus_id}'."
                )

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
        )


__all__ = ["StudyPreparationService"]
