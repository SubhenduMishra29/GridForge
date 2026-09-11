"""
GridForge - Power Flow Study Configuration
==========================================

Defines explicit study-side Power Flow intent independently of the
physical electrical model and numerical solver.

Author: Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping

from core.solver.power_flow.input import PowerFlowBusType


@dataclass(frozen=True, slots=True)
class PowerFlowStudyConfiguration:
    """Immutable engineering definition for one Power Flow study.

    The configuration is the single study-side source for system base,
    bus operating modes and numerical execution options. It refers to bus
    IDs rather than live Core objects.
    """

    bus_types: Mapping[str, PowerFlowBusType | str]
    base_mva: float
    tolerance: float = 1e-8
    max_iterations: int = 50
    voltage_bases_kv: Mapping[str, float] = field(default_factory=dict)
    numerical_options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        base_mva = float(self.base_mva)
        tolerance = float(self.tolerance)
        max_iterations = int(self.max_iterations)

        if not math.isfinite(base_mva) or base_mva <= 0.0:
            raise ValueError("base_mva must be finite and > 0.")
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("tolerance must be finite and > 0.")
        if max_iterations <= 0:
            raise ValueError("max_iterations must be > 0.")

        normalized_bus_types = {
            str(bus_id): (
                value
                if isinstance(value, PowerFlowBusType)
                else PowerFlowBusType(value)
            )
            for bus_id, value in dict(self.bus_types).items()
        }
        normalized_bases = {
            str(bus_id): float(value)
            for bus_id, value in dict(self.voltage_bases_kv).items()
        }
        for bus_id, value in normalized_bases.items():
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(
                    f"voltage base for '{bus_id}' must be finite and > 0."
                )

        object.__setattr__(self, "base_mva", base_mva)
        object.__setattr__(self, "tolerance", tolerance)
        object.__setattr__(self, "max_iterations", max_iterations)
        object.__setattr__(
            self,
            "bus_types",
            MappingProxyType(normalized_bus_types),
        )
        object.__setattr__(
            self,
            "voltage_bases_kv",
            MappingProxyType(normalized_bases),
        )
        object.__setattr__(
            self,
            "numerical_options",
            MappingProxyType(dict(self.numerical_options)),
        )
