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
        if not self.bus_types:
            raise ValueError(
                "Power Flow study configuration requires at least one bus classification."
            )

        base_mva = float(self.base_mva)
        if not math.isfinite(base_mva) or base_mva <= 0.0:
            raise ValueError("Power Flow study base MVA must be finite and positive.")
        object.__setattr__(self, "base_mva", base_mva)

        tolerance = float(self.tolerance)
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("Power Flow tolerance must be finite and positive.")
        object.__setattr__(self, "tolerance", tolerance)

        if isinstance(self.max_iterations, bool) or not isinstance(self.max_iterations, int):
            raise TypeError("Power Flow max_iterations must be an integer.")
        if self.max_iterations <= 0:
            raise ValueError("Power Flow max_iterations must be positive.")

        normalized: dict[str, PowerFlowBusType] = {}
        for bus_id, value in self.bus_types.items():
            if not isinstance(bus_id, str) or not bus_id:
                raise ValueError("Power Flow configuration bus IDs must be non-empty strings.")
            try:
                classification = (
                    value
                    if isinstance(value, PowerFlowBusType)
                    else PowerFlowBusType(str(value).upper())
                )
            except ValueError as exc:
                raise ValueError(
                    f"Invalid Power Flow bus classification for {bus_id!r}: {value!r}."
                ) from exc
            normalized[bus_id] = classification

        slack_count = sum(
            value is PowerFlowBusType.SLACK
            for value in normalized.values()
        )
        if slack_count != 1:
            raise ValueError(
                "Power Flow study configuration must contain exactly one SLACK bus; "
                f"found {slack_count}."
            )

        voltage_bases: dict[str, float] = {}
        for bus_id, value in self.voltage_bases_kv.items():
            if not isinstance(bus_id, str) or not bus_id:
                raise ValueError("Voltage-base bus IDs must be non-empty strings.")
            voltage = float(value)
            if not math.isfinite(voltage) or voltage <= 0.0:
                raise ValueError(f"Voltage base for bus {bus_id!r} must be finite and positive.")
            voltage_bases[bus_id] = voltage

        object.__setattr__(self, "bus_types", MappingProxyType(normalized))
        object.__setattr__(self, "voltage_bases_kv", MappingProxyType(voltage_bases))
        object.__setattr__(self, "numerical_options", MappingProxyType(dict(self.numerical_options)))

    @classmethod
    def from_mapping(
        cls,
        bus_types: Mapping[str, PowerFlowBusType | str],
        *,
        base_mva: float,
        tolerance: float = 1e-8,
        max_iterations: int = 50,
        voltage_bases_kv: Mapping[str, float] | None = None,
        numerical_options: Mapping[str, Any] | None = None,
    ) -> "PowerFlowStudyConfiguration":
        """Create a configuration from explicit study-side inputs."""
        return cls(
            bus_types=bus_types,
            base_mva=base_mva,
            tolerance=tolerance,
            max_iterations=max_iterations,
            voltage_bases_kv={} if voltage_bases_kv is None else voltage_bases_kv,
            numerical_options={} if numerical_options is None else numerical_options,
        )

    @property
    def slack_bus_id(self) -> str:
        """Return the configured SLACK bus ID."""
        for bus_id, bus_type in self.bus_types.items():
            if bus_type is PowerFlowBusType.SLACK:
                return bus_id
        raise RuntimeError("Power Flow configuration has no SLACK bus.")

    @property
    def bus_type_mapping(self) -> dict[str, PowerFlowBusType]:
        """Return a detached mapping of configured bus operating modes."""
        return dict(self.bus_types)

    @property
    def voltage_base_mapping(self) -> dict[str, float]:
        """Return detached declared bus voltage bases in kV."""
        return dict(self.voltage_bases_kv)

    def type_of(self, bus_id: str) -> PowerFlowBusType:
        """Return the configured study classification for a bus ID."""
        return self.bus_types[bus_id]

    def voltage_base_of(self, bus_id: str) -> float:
        """Return the explicitly declared study voltage base for a bus."""
        return self.voltage_bases_kv[bus_id]

    def __repr__(self) -> str:
        return (
            "PowerFlowStudyConfiguration("
            f"buses={len(self.bus_types)}, "
            f"slack_bus_id={self.slack_bus_id!r}, "
            f"base_mva={self.base_mva:g}, "
            f"tolerance={self.tolerance:g}, "
            f"max_iterations={self.max_iterations}"
            ")"
        )


__all__ = ["PowerFlowStudyConfiguration"]
