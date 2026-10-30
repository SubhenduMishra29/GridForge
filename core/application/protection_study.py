# ============================================================
# File: core/application/protection_study.py
# GridForge V2 — Unified Protection Study Application Contract
# Author: Subhendu Mishra
# ============================================================

"""Typed Protection Study configuration, result, and StudyService handler.

The handler supports either one coherent live measurement-snapshot evaluation
or explicit short-circuit fault scenarios converted through configured
instrument/channel bindings into detached Application-authorized RelayInput
snapshots. Unsupported instrument/result paths fail closed. The Study never
dispatches trip commands or mutates breaker state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from core.analysis.short_circuit import ShortCircuitAnalysis
from core.analysis.short_circuit_configuration import ShortCircuitStudyConfiguration
from core.analysis.short_circuit_preparation import ShortCircuitPreparation
from core.solver.short_circuit.result import ContributionStatus, ShortCircuitResult, ShortCircuitStatus
from core.application.services.ct_measurement_association_service import CTMeasurementAssociationService
from core.measurement.protection_scenario_measurement import ProtectionScenarioMeasurementAdapter

from core.application.protection_execution import ProtectionExecutionResult
from core.application.revision import ProjectRevision
from core.protection.configuration_fingerprint import canonical_configuration_value
from core.protection.decision import ProtectionDecision
from core.protection.project_configuration import ProtectionProjectConfiguration


def _freeze_mapping(value: Any, field_name: str) -> Any:
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"{field_name} keys must be non-empty strings.")
            normalized_key = key.strip()
            if normalized_key in normalized:
                raise ValueError(f"{field_name} contains duplicate normalized key {normalized_key!r}.")
            normalized[normalized_key] = _freeze_mapping(item, field_name)
        return MappingProxyType(normalized)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_mapping(item, field_name) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_mapping(item, field_name) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class ProtectionFaultScenario:
    """One explicitly configured fault case evaluated from a detached project snapshot."""

    scenario_id: str
    configuration: ShortCircuitStudyConfiguration

    def __post_init__(self) -> None:
        if not isinstance(self.scenario_id, str) or not self.scenario_id.strip():
            raise ValueError("scenario_id must be a non-empty string.")
        object.__setattr__(self, "scenario_id", self.scenario_id.strip())
        if not isinstance(self.configuration, ShortCircuitStudyConfiguration):
            raise TypeError("configuration must be a ShortCircuitStudyConfiguration.")


@dataclass(frozen=True, slots=True)
class ProtectionFaultScenarioResult:
    """Immutable short-circuit result correlated to one Protection Study scenario."""

    scenario_id: str
    configuration: ShortCircuitStudyConfiguration
    short_circuit_result: ShortCircuitResult
    execution: ProtectionExecutionResult = field(default_factory=ProtectionExecutionResult)

    def __post_init__(self) -> None:
        if not isinstance(self.scenario_id, str) or not self.scenario_id.strip():
            raise ValueError("scenario_id must be a non-empty string.")
        object.__setattr__(self, "scenario_id", self.scenario_id.strip())
        if not isinstance(self.configuration, ShortCircuitStudyConfiguration):
            raise TypeError("configuration must be a ShortCircuitStudyConfiguration.")
        if not isinstance(self.short_circuit_result, ShortCircuitResult):
            raise TypeError("short_circuit_result must be a ShortCircuitResult.")
        if not isinstance(self.execution, ProtectionExecutionResult):
            raise TypeError("execution must be a ProtectionExecutionResult.")
        if self.short_circuit_result.fault_type is not self.configuration.fault_type:
            raise ValueError("Short-circuit result fault type does not match its scenario configuration.")
        if str(self.short_circuit_result.fault_bus_id) != self.configuration.fault_bus_id:
            raise ValueError("Short-circuit result fault Bus does not match its scenario configuration.")

    @property
    def status(self) -> ShortCircuitStatus:
        return self.short_circuit_result.status

    @property
    def success(self) -> bool:
        return self.short_circuit_result.success

    @property
    def contribution_status(self) -> ContributionStatus:
        return self.short_circuit_result.contribution_status

    @property
    def measurement_contributions_complete(self) -> bool:
        """Whether branch/source current contributions are complete enough for mapping."""
        return self.contribution_status is ContributionStatus.COMPLETE

    @property
    def diagnostics(self) -> tuple[str, ...]:
        return tuple(self.short_circuit_result.diagnostics)


@dataclass(frozen=True, slots=True)
class ProtectionStudyConfiguration:
    """Immutable inputs for one Protection Study evaluation mode.

    The project protection configuration is captured by value when the Study
    Case is defined. A Study Case selects either a validated live measurement
    snapshot or explicit detached short-circuit fault scenarios.
    """

    evaluation_time: float
    protection_configuration: Mapping[str, Any]
    timestep: float | None = None
    event_id: str | None = None
    event_type: str | None = "STUDY"
    scenario_id: str | None = None
    supervision: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    fault_scenarios: tuple[ProtectionFaultScenario, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.evaluation_time, bool):
            raise TypeError("evaluation_time must be a finite numeric value.")
        try:
            evaluation_time = float(self.evaluation_time)
        except (TypeError, ValueError) as exc:
            raise TypeError("evaluation_time must be a finite numeric value.") from exc
        if not isfinite(evaluation_time) or evaluation_time < 0.0:
            raise ValueError("evaluation_time must be finite and non-negative.")
        object.__setattr__(self, "evaluation_time", evaluation_time)

        if self.timestep is not None:
            if isinstance(self.timestep, bool):
                raise TypeError("timestep must be a finite non-negative numeric value or None.")
            try:
                timestep = float(self.timestep)
            except (TypeError, ValueError) as exc:
                raise TypeError("timestep must be a finite non-negative numeric value or None.") from exc
            if not isfinite(timestep) or timestep < 0.0:
                raise ValueError("timestep must be finite and non-negative.")
            object.__setattr__(self, "timestep", timestep)

        for name in ("event_id", "event_type", "scenario_id"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{name} must be a non-empty string or None.")
                object.__setattr__(self, name, value.strip())

        if not isinstance(self.protection_configuration, Mapping):
            raise TypeError("protection_configuration must be a serialized ProtectionProjectConfiguration mapping.")
        snapshot = ProtectionProjectConfiguration.from_dict(self.protection_configuration)
        object.__setattr__(self, "protection_configuration", _freeze_mapping(snapshot.to_dict(), "protection_configuration"))

        for name in ("supervision", "metadata"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise TypeError(f"{name} must be a mapping.")
            object.__setattr__(self, name, _freeze_mapping(value, name))

        scenarios = tuple(self.fault_scenarios)
        if any(not isinstance(item, ProtectionFaultScenario) for item in scenarios):
            raise TypeError("fault_scenarios must contain only ProtectionFaultScenario values.")
        scenario_ids = tuple(item.scenario_id for item in scenarios)
        if len(set(scenario_ids)) != len(scenario_ids):
            raise ValueError("fault_scenarios must not contain duplicate scenario IDs.")
        object.__setattr__(self, "fault_scenarios", scenarios)

    @classmethod
    def from_project_configuration(
        cls,
        configuration: ProtectionProjectConfiguration,
        *,
        evaluation_time: float,
        timestep: float | None = None,
        event_id: str | None = None,
        event_type: str | None = "STUDY",
        scenario_id: str | None = None,
        supervision: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
        fault_scenarios: tuple[ProtectionFaultScenario, ...] = (),
    ) -> "ProtectionStudyConfiguration":
        if not isinstance(configuration, ProtectionProjectConfiguration):
            raise TypeError("configuration must be a ProtectionProjectConfiguration.")
        return cls(
            evaluation_time=evaluation_time,
            timestep=timestep,
            event_id=event_id,
            event_type=event_type,
            scenario_id=scenario_id,
            protection_configuration=configuration.to_dict(),
            supervision={} if supervision is None else supervision,
            metadata={} if metadata is None else metadata,
            fault_scenarios=fault_scenarios,
        )

    @property
    def configuration_fingerprint(self) -> Any:
        return canonical_configuration_value(self.protection_configuration)


@dataclass(frozen=True, slots=True)
class ProtectionStudyResult:
    """Immutable, provenance-bound result of one Protection Study evaluation."""

    study_id: UUID
    project_id: str
    activation_generation: int
    source_revision: ProjectRevision
    topology_revision: int
    evaluation_time: float
    scenario_id: str | None
    configuration_fingerprint: Any
    execution: ProtectionExecutionResult
    fault_scenarios: tuple[ProtectionFaultScenarioResult, ...] = ()
    measurement_snapshot_evaluated: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.study_id, UUID):
            raise TypeError("study_id must be a UUID.")
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be a non-empty string.")
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if not isinstance(self.source_revision, ProjectRevision):
            raise TypeError("source_revision must be a ProjectRevision.")
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int) or self.topology_revision < 0:
            raise ValueError("topology_revision must be a non-negative integer.")
        if not isinstance(self.execution, ProtectionExecutionResult):
            raise TypeError("execution must be a ProtectionExecutionResult.")
        if isinstance(self.evaluation_time, bool) or not isfinite(float(self.evaluation_time)) or float(self.evaluation_time) < 0.0:
            raise ValueError("evaluation_time must be finite and non-negative.")
        if not isinstance(self.measurement_snapshot_evaluated, bool):
            raise TypeError("measurement_snapshot_evaluated must be a boolean.")
        scenarios = tuple(self.fault_scenarios)
        if any(not isinstance(item, ProtectionFaultScenarioResult) for item in scenarios):
            raise TypeError("fault_scenarios must contain ProtectionFaultScenarioResult values.")
        scenario_ids = tuple(item.scenario_id for item in scenarios)
        if len(set(scenario_ids)) != len(scenario_ids):
            raise ValueError("fault_scenarios result IDs must be unique.")
        if bool(scenarios) == self.measurement_snapshot_evaluated:
            raise ValueError(
                "Protection Study result must represent either fault-scenario mode "
                "or measurement-snapshot mode, not both or neither."
            )
        for scenario in scenarios:
            provenance = scenario.short_circuit_result.provenance
            expected = {
                "project_id": self.project_id,
                "activation_generation": self.activation_generation,
                "topology_revision": self.topology_revision,
            }
            for key, value in expected.items():
                if provenance.get(key) != value:
                    raise ValueError(
                        f"Fault scenario {scenario.scenario_id!r} result has mismatched {key} provenance."
                    )
        object.__setattr__(self, "fault_scenarios", scenarios)

    @property
    def decisions(self) -> tuple[ProtectionDecision, ...]:
        scenario_decisions = tuple(
            decision
            for scenario in self.fault_scenarios
            for decision in scenario.execution.decisions
        )
        return self.execution.decisions + scenario_decisions

    @property
    def diagnostics(self) -> tuple[str, ...]:
        scenario_diagnostics = tuple(
            f"scenario={scenario.scenario_id!r}: {message}"
            for scenario in self.fault_scenarios
            for message in scenario.execution.diagnostics
        )
        return self.execution.diagnostics + scenario_diagnostics

    @property
    def status(self) -> str:
        if self.measurement_snapshot_evaluated and self.execution.diagnostics:
            return "blocked"
        if any(
            not item.success
            or item.status is not ShortCircuitStatus.COMPLETE
            or not item.measurement_contributions_complete
            or bool(item.execution.diagnostics)
            for item in self.fault_scenarios
        ):
            return "partial"
        if self.fault_scenarios and not self.measurement_snapshot_evaluated:
            return (
                "evaluated"
                if any(item.execution.decisions for item in self.fault_scenarios)
                else "fault_scenarios_calculated"
            )
        return "evaluated" if self.measurement_snapshot_evaluated else "not_evaluated"


class ProtectionStudyHandler:
    """Run a non-operating protection evaluation through the existing StudyService."""

    def __init__(self, application: Any) -> None:
        if application is None or not callable(getattr(application, "evaluate_protection_cycle", None)):
            raise TypeError("application must expose evaluate_protection_cycle().")
        self._application = application

    def __call__(self, request: Any, execution_context: Any, cancellation: Any) -> ProtectionStudyResult | None:
        if getattr(request, "study_type", None) != "protection":
            raise ValueError("ProtectionStudyHandler only accepts study_type='protection'.")
        configuration = request.configuration.get("configuration")
        if not isinstance(configuration, ProtectionStudyConfiguration):
            raise TypeError("protection StudyRequest requires ProtectionStudyConfiguration.")
        if cancellation.cancelled:
            return None
        if (
            execution_context.project_id != request.project_id
            or execution_context.activation_generation != request.activation_generation
            or execution_context.source_revision != request.source_revision
        ):
            raise ValueError("Protection Study execution snapshot does not match its request provenance.")

        application = self._application
        lifecycle = application.project_lifecycle
        project = lifecycle.context
        if (
            lifecycle.state != "ACTIVE"
            or not lifecycle.has_project
            or project is None
            or project.project_id != request.project_id
            or lifecycle.activation_generation != request.activation_generation
            or application.revision != request.source_revision
        ):
            raise RuntimeError("Protection Study source project changed before evaluation.")

        configuration_service = getattr(application, "protection_configuration_service", None)
        active_configuration = getattr(configuration_service, "configuration", None)
        if not isinstance(active_configuration, ProtectionProjectConfiguration):
            raise RuntimeError("Active project ProtectionProjectConfiguration is unavailable.")
        if active_configuration.project_id != request.project_id:
            raise RuntimeError("Protection configuration belongs to a different project.")
        active_fingerprint = canonical_configuration_value(active_configuration.to_dict())
        if active_fingerprint != configuration.configuration_fingerprint:
            raise RuntimeError("Protection configuration changed after the Protection Study Case was defined; recreate the Study Case.")

        fault_scenario_results: list[ProtectionFaultScenarioResult] = []
        detached_network = execution_context.project_snapshot.network
        for scenario in configuration.fault_scenarios:
            if cancellation.cancelled:
                return None
            if scenario.configuration.fault_bus_id not in execution_context.topology_snapshot.bus_ids:
                raise ValueError(
                    f"Protection fault scenario {scenario.scenario_id!r} references Bus "
                    f"{scenario.configuration.fault_bus_id!r} outside the captured topology snapshot."
                )
            preparation = ShortCircuitPreparation(
                detached_network,
                base_mva=scenario.configuration.base_mva,
            )
            prepared_input = preparation.prepare(
                scenario.configuration.fault_type,
                scenario.configuration.fault_bus_id,
                scenario.configuration.fault_impedance,
                elements=scenario.configuration.element_ids or None,
                topology_snapshot=execution_context.topology_snapshot,
            )
            short_circuit_result = ShortCircuitAnalysis.from_prepared(prepared_input).run()
            expected_provenance = {
                "project_id": request.project_id,
                "activation_generation": request.activation_generation,
                "topology_revision": request.source_revision.topology_revision,
            }
            for provenance_key, expected_value in expected_provenance.items():
                if short_circuit_result.provenance.get(provenance_key) != expected_value:
                    raise RuntimeError(
                        f"Protection fault scenario {scenario.scenario_id!r} returned mismatched "
                        f"short-circuit {provenance_key} provenance."
                    )
            if cancellation.cancelled:
                return None

            sample_adapter = ProtectionScenarioMeasurementAdapter()
            ct_associations: dict[str, Any] = {}
            association_service = CTMeasurementAssociationService()
            scenario_samples = []
            conversion_diagnostics: list[str] = []
            measurement_service = application.measurement_channel_service
            configured_elements = {
                item.element_id: item
                for item in active_configuration.elements
                if item.enabled
            }
            for binding in active_configuration.measurement_bindings:
                if binding.protection_element_id not in configured_elements:
                    continue
                prefix = (
                    f"element={binding.protection_element_id!r}, "
                    f"input={binding.relay_input_id!r}, binding={binding.binding_id!r}"
                )
                try:
                    if binding.measurement_type.strip().lower() != "current":
                        raise ValueError(
                            "Scenario voltage conversion is not implemented; PT/CVT samples are not inferred."
                        )
                    channel = measurement_service.require(binding.channel_id)
                    instrument = detached_network.get_by_identity(binding.instrument_id)
                    if binding.instrument_id not in ct_associations:
                        ct_associations[binding.instrument_id] = association_service.resolve(
                            execution_context.project_snapshot,
                            binding.instrument_id,
                        )
                    scenario_samples.append(sample_adapter.convert_branch_ct_sample(
                        scenario_id=scenario.scenario_id,
                        binding=binding,
                        result=short_circuit_result,
                        instrument=instrument,
                        channel=channel,
                        ct_association=ct_associations[binding.instrument_id],
                    ))
                except Exception as exc:
                    conversion_diagnostics.append(
                        f"{prefix}: scenario measurement conversion refused: {type(exc).__name__}: {exc}"
                    )

            if cancellation.cancelled:
                return None
            if conversion_diagnostics:
                scenario_execution = ProtectionExecutionResult(
                    diagnostics=tuple(conversion_diagnostics)
                )
            else:
                scenario_execution = application.evaluate_protection_scenario(
                    scenario_id=scenario.scenario_id,
                    samples=tuple(scenario_samples),
                    evaluation_time=configuration.evaluation_time,
                    evaluation_timestep=configuration.timestep,
                    event_id=configuration.event_id,
                    event_type=configuration.event_type,
                    supervision=configuration.supervision,
                    evaluation_metadata={
                        **dict(configuration.metadata),
                        "study_id": str(request.study_id),
                        "study_type": "protection",
                        "scenario_id": scenario.scenario_id,
                        "source_model_revision": request.source_revision.model_revision,
                        "source_topology_revision": request.source_revision.topology_revision,
                    },
                    network_state=execution_context.topology_snapshot,
                )
            fault_scenario_results.append(ProtectionFaultScenarioResult(
                scenario_id=scenario.scenario_id,
                configuration=scenario.configuration,
                short_circuit_result=short_circuit_result,
                execution=scenario_execution,
            ))
            if cancellation.cancelled:
                return None
            if (
                application.revision != request.source_revision
                or application.project_lifecycle.context is not project
                or application.project_lifecycle.activation_generation != request.activation_generation
            ):
                raise RuntimeError("Project or topology provenance changed during fault-scenario calculation.")

        measurement_snapshot_evaluated = not bool(configuration.fault_scenarios)
        if measurement_snapshot_evaluated:
            measurement_service = application.measurement_channel_service
            if (
                measurement_service.project_id != request.project_id
                or measurement_service.activation_generation != request.activation_generation
                or measurement_service.network is not lifecycle.network
            ):
                raise RuntimeError("Measurement channel authority is stale for the Protection Study project snapshot.")
            if cancellation.cancelled:
                return None
            execution = application.evaluate_protection_cycle(
                configuration.evaluation_time,
                action_resolver=lambda _decision: None,
                evaluation_metadata={
                    **dict(configuration.metadata),
                    "study_id": str(request.study_id),
                    "study_type": "protection",
                    "scenario_id": configuration.scenario_id,
                    "source_model_revision": request.source_revision.model_revision,
                    "source_topology_revision": request.source_revision.topology_revision,
                },
                evaluation_timestep=configuration.timestep,
                event_id=configuration.event_id,
                event_type=configuration.event_type,
                supervision=configuration.supervision,
                network_state=execution_context.topology_snapshot,
            )
        else:
            # Fault-current results are not yet converted through configured
            # CT/PT/CVT paths into scenario-specific RelayInput samples.
            # Never reuse live channel samples as if they represented a fault.
            execution = ProtectionExecutionResult()
        if cancellation.cancelled:
            return None
        if (
            application.revision != request.source_revision
            or application.project_lifecycle.context is not project
            or application.project_lifecycle.activation_generation != request.activation_generation
        ):
            raise RuntimeError("Project or protection-study source revision changed during evaluation.")

        return ProtectionStudyResult(
            study_id=request.study_id,
            project_id=request.project_id,
            activation_generation=request.activation_generation,
            source_revision=request.source_revision,
            topology_revision=execution_context.topology_snapshot.topology_revision,
            evaluation_time=configuration.evaluation_time,
            scenario_id=configuration.scenario_id,
            configuration_fingerprint=configuration.configuration_fingerprint,
            execution=execution,
            fault_scenarios=tuple(fault_scenario_results),
            measurement_snapshot_evaluated=measurement_snapshot_evaluated,
        )


__all__ = [
    "ProtectionFaultScenario",
    "ProtectionFaultScenarioResult",
    "ProtectionStudyConfiguration",
    "ProtectionStudyResult",
    "ProtectionStudyHandler",
]
