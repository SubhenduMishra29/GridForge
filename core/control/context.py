"""Detached input context supplied to one Control evaluation cycle."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ControlExecutionContext:
    """Immutable evaluation snapshot; Control does not own simulation time."""

    simulation_time: float
    external_inputs: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        simulation_time = float(self.simulation_time)
        if not math.isfinite(simulation_time):
            raise ValueError("simulation_time must be finite.")
        object.__setattr__(self, "simulation_time", simulation_time)
        object.__setattr__(
            self,
            "external_inputs",
            {str(component): dict(values) for component, values in self.external_inputs.items()},
        )
        object.__setattr__(self, "metadata", dict(self.metadata))


__all__ = ["ControlExecutionContext"]
