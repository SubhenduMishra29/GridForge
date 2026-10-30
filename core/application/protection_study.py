# ============================================================
# File: core/application/protection_study.py
# GridForge V2 — Unified Protection Study Application Contract
# Author: Subhendu Mishra
# ============================================================

"""Typed Protection Study configuration, result, and StudyService handler.

This first lifecycle slice evaluates the configured protection system against
one coherent, validated measurement snapshot. It deliberately does not dispatch
trip commands and does not claim fault-scenario, coordination, or settings-study
coverage; those are subsequent Protection Study work packages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

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
            normalized[key.strip()] = _freeze_mapping(item, field_name)
        return MappingProxyType(normalized)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_mapping(item, field_name) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_mapping(item, field_name) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class ProtectionStudyConfiguration:
    """Immutable inputs for one Protection Study measurement-snapshot evaluation.

    The project protection configuration is captured by value when the Study
    Case is defined. Runtime MeasurementChannel samples are validated and
    sealed by Application at execution time; they are not persisted here.
    """

    evaluation_time: float
    protection_configuration: Mapping[str, Any]
    timestep: float | None = None
    event_id: str | None = None
    event_type: str | None = "STUDY"
    scenario_id: str | None = None
    supervision: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

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
            supervision=supervision or {},
            metadata=metadata or {},
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

    @property
    def decisions(self) -> tuple[ProtectionDecision, ...]:
        return self.execution.decisions

    @property
    def diagnostics(self) -> tuple[str, ...]:
        return self.execution.diagnostics

    @property
    def status(self) -> str:
        return "blocked" if self.execution.diagnostics else "evaluated"


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
        )


__all__ = [
    "ProtectionStudyConfiguration",
    "ProtectionStudyResult",
    "ProtectionStudyHandler",
]
