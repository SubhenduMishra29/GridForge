# ============================================================
# File: core/analysis/transient_stability.py
# GridForge V2 — Transient Stability Analysis Facade
# Author: Subhendu Mishra
# ============================================================
"""Public Core Analysis facade for transient-stability studies."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from core.solver.dynamics import TransientStabilityResult, TransientStabilitySolver


@dataclass(frozen=True, slots=True)
class TransientStabilityStudyConfiguration:
    """Immutable transient-stability study configuration."""

    start_time: float = 0.0
    end_time: float = 10.0
    dt: float = 0.01
    metadata: Mapping[str, Any] = MappingProxyType({})

    def __post_init__(self) -> None:
        start = float(self.start_time)
        end = float(self.end_time)
        dt = float(self.dt)
        if start < 0.0:
            raise ValueError("start_time cannot be negative.")
        if end <= start:
            raise ValueError("end_time must be greater than start_time.")
        if dt <= 0.0:
            raise ValueError("dt must be greater than zero.")
        object.__setattr__(self, "start_time", start)
        object.__setattr__(self, "end_time", end)
        object.__setattr__(self, "dt", dt)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class TransientStabilityStudyResult:
    """Immutable analysis result independent of Core object lifetime."""

    result: TransientStabilityResult

    def __post_init__(self) -> None:
        if not isinstance(self.result, TransientStabilityResult):
            raise TypeError("result must be TransientStabilityResult.")


class TransientStabilityAnalysis:
    """Analysis-level orchestration around the low-level transient solver."""

    def __init__(self, solver: TransientStabilitySolver,
                 configuration: TransientStabilityStudyConfiguration,
                 initial_state) -> None:
        if not isinstance(solver, TransientStabilitySolver):
            raise TypeError("solver must be TransientStabilitySolver.")
        if not isinstance(configuration, TransientStabilityStudyConfiguration):
            raise TypeError("configuration must be TransientStabilityStudyConfiguration.")
        self.solver = solver
        self.configuration = configuration
        self.initial_state = tuple(float(value) for value in initial_state)
        self.result: TransientStabilityStudyResult | None = None

    def run(self) -> TransientStabilityStudyResult:
        """Initialize the configured solver and execute the study."""
        self.solver.initialize(self.initial_state, time=self.configuration.start_time)
        numerical = self.solver.run(record_initial=True)
        self.result = TransientStabilityStudyResult(numerical)
        return self.result


__all__ = [
    "TransientStabilityStudyConfiguration",
    "TransientStabilityStudyResult",
    "TransientStabilityAnalysis",
]
