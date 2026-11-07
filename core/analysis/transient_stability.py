# ============================================================
# File: core/analysis/transient_stability.py
# GridForge V2 — Transient Stability Analysis Facade
# Author: Subhendu Mishra
# ============================================================
"""Public Core Analysis facade for transient-stability studies."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Callable, Mapping

from core.solver.dynamics import TransientStabilityResult, TransientStabilitySolver
from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.transient_scenario import TransientEventScenario


def _freeze_metadata_value(value: Any) -> Any:
    """Recursively freeze built-in metadata containers without changing typed objects."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_metadata_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_metadata_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_metadata_value(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class TransientStabilityStudyConfiguration:
    """Immutable transient-stability study configuration."""

    start_time: float = 0.0
    end_time: float = 10.0
    dt: float = 0.01
    metadata: Mapping[str, Any] = MappingProxyType({})
    power_flow_configuration: PowerFlowStudyConfiguration | None = None
    event_scenario: TransientEventScenario = field(default_factory=TransientEventScenario)

    def __post_init__(self) -> None:
        start = float(self.start_time)
        end = float(self.end_time)
        dt = float(self.dt)
        if not all(math.isfinite(value) for value in (start, end, dt)):
            raise ValueError("Transient Stability times and step size must be finite.")
        if start < 0.0:
            raise ValueError("start_time cannot be negative.")
        if end <= start:
            raise ValueError("end_time must be greater than start_time.")
        if dt <= 0.0:
            raise ValueError("dt must be greater than zero.")
        object.__setattr__(self, "start_time", start)
        object.__setattr__(self, "end_time", end)
        object.__setattr__(self, "dt", dt)
        object.__setattr__(self, "metadata", _freeze_metadata_value(self.metadata))
        if self.power_flow_configuration is not None and not isinstance(
            self.power_flow_configuration, PowerFlowStudyConfiguration
        ):
            raise TypeError("power_flow_configuration must be PowerFlowStudyConfiguration or None.")
        if not isinstance(self.event_scenario, TransientEventScenario):
            raise TypeError("event_scenario must be a TransientEventScenario.")


# Compatibility alias: the solver's immutable TransientStabilityResult is
# the single canonical dynamic-study result authority. The analysis layer does
# not wrap it in a second executable result representation.
TransientStabilityStudyResult = TransientStabilityResult


class TransientStabilityAnalysis:
    """Analysis-level orchestration around the low-level transient solver."""

    def __init__(self, solver: TransientStabilitySolver,
                 configuration: TransientStabilityStudyConfiguration,
                 initial_state, *, provenance: Mapping[str, Any] | None = None) -> None:
        if not isinstance(solver, TransientStabilitySolver):
            raise TypeError("solver must be TransientStabilitySolver.")
        if not isinstance(configuration, TransientStabilityStudyConfiguration):
            raise TypeError("configuration must be TransientStabilityStudyConfiguration.")
        self.solver = solver
        self.configuration = configuration
        self.initial_state = tuple(float(value) for value in initial_state)
        prepared_provenance = dict(provenance or {})
        prepared_provenance.setdefault("event_scenario", configuration.event_scenario.as_dict())
        self.provenance = MappingProxyType(prepared_provenance)
        self.result: TransientStabilityStudyResult | None = None

    def _validate_event_scenario(self) -> None:
        """Fail closed unless runtime event registrations exactly match prepared scenario intent."""
        manifest = self.provenance.get("event_scenario")
        if not isinstance(manifest, Mapping) or manifest.get("schema_version") != 1:
            raise ValueError("Transient execution requires a versioned prepared event-scenario manifest.")
        expected = manifest.get("events")
        if not isinstance(expected, (tuple, list)):
            raise ValueError("Prepared event-scenario manifest must contain an ordered events sequence.")
        actual = self.solver.event_manager.events
        if len(actual) != len(expected):
            raise ValueError(
                "Runtime transient event registrations do not match the prepared event scenario "
                f"(expected {len(expected)}, received {len(actual)})."
            )
        for index, (declared, registered) in enumerate(zip(expected, actual)):
            if not isinstance(declared, Mapping):
                raise ValueError(f"Prepared event scenario entry {index} is not a mapping.")
            operation = registered.operation
            actual_operation = None if operation is None else {
                "target_kind": operation.target_kind,
                "target_id": operation.target_id,
                "operation": operation.operation,
            }
            checks = (
                declared.get("event_id") == registered.event_id,
                declared.get("event_type") == registered.event_type,
                math.isclose(float(declared.get("time")), float(registered.time), rel_tol=0.0, abs_tol=1e-12),
                declared.get("priority") == registered.priority,
                declared.get("enabled") == registered.enabled,
                declared.get("description") == registered.description,
                declared.get("metadata") == dict(registered.metadata),
                declared.get("operation") == actual_operation,
            )
            if not all(checks):
                raise ValueError(
                    "Runtime transient event registration differs from the immutable prepared "
                    f"scenario at ordered event index {index} (event_id={registered.event_id!r})."
                )

    def run(
        self,
        *,
        should_cancel: Callable[[], bool] | None = None,
    ) -> TransientStabilityStudyResult:
        """Apply the immutable study configuration and execute the study."""
        self.solver.start_time = self.configuration.start_time
        self.solver.end_time = self.configuration.end_time
        self.solver.dt = self.configuration.dt
        self._validate_event_scenario()
        self.solver.initialize(self.initial_state, time=self.configuration.start_time)
        numerical = self.solver.run(record_initial=True, should_cancel=should_cancel)
        # The solver owns numerical/runtime provenance (including detached
        # event-state and switching evidence). Analysis adds the execution
        # context, but must never replace evidence already captured by Solver.
        # A duplicate key is accepted only when both boundaries agree.
        from dataclasses import replace
        result_provenance = dict(numerical.provenance)
        for key, value in self.provenance.items():
            if key in result_provenance:
                if result_provenance[key] != value:
                    raise ValueError(
                        f"Transient solver and analysis provenance disagree for {key!r}."
                    )
                continue
            result_provenance[key] = value
        self.result = replace(numerical, provenance=result_provenance)
        return self.result


__all__ = [
    "TransientStabilityStudyConfiguration",
    "TransientStabilityStudyResult",
    "TransientStabilityAnalysis",
]
