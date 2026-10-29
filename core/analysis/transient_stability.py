# ============================================================
# File: core/analysis/transient_stability.py
# GridForge V2 — Transient Stability Analysis Facade
# Author: Subhendu Mishra
# ============================================================
"""Public Core Analysis facade for transient-stability studies."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Any, Callable, Mapping

from core.solver.dynamics import TransientStabilityResult, TransientStabilitySolver
from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration


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
        self.provenance = MappingProxyType(dict(provenance or {}))
        self.result: TransientStabilityStudyResult | None = None

    def run(
        self,
        *,
        should_cancel: Callable[[], bool] | None = None,
    ) -> TransientStabilityStudyResult:
        """Apply the immutable study configuration and execute the study."""
        self.solver.start_time = self.configuration.start_time
        self.solver.end_time = self.configuration.end_time
        self.solver.dt = self.configuration.dt
        self.solver.initialize(self.initial_state, time=self.configuration.start_time)
        numerical = self.solver.run(record_initial=True, should_cancel=should_cancel)
        # Keep project/snapshot identity attached to the immutable result rather
        # than losing it at the solver/Analysis boundary.
        from dataclasses import replace
        self.result = replace(numerical, provenance=self.provenance)
        return self.result


__all__ = [
    "TransientStabilityStudyConfiguration",
    "TransientStabilityStudyResult",
    "TransientStabilityAnalysis",
]
