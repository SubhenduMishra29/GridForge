"""
GridForge - Power Flow Result Conversion
=========================================

Converts numerical Power Flow results into immutable engineering
quantities for Analysis consumers, UI projections, and reporting.

This module is deliberately separate from the numerical result contract.
It does not create display strings and it does not mutate Core Bus state.

Author: Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable

from core.base.per_unit import PerUnitSystem
from core.solver.power_flow.result import PowerFlowResult


@dataclass(frozen=True, slots=True)
class EngineeringPowerFlowBusResult:
    """Immutable engineering quantities for one solved Bus."""

    bus_id: str
    voltage_pu: float
    voltage_kv: float
    angle_rad: float
    angle_deg: float


@dataclass(frozen=True, slots=True)
class EngineeringPowerFlowResult:
    """Immutable structured engineering result derived from numerical PU data."""

    numerical_result: PowerFlowResult
    buses: tuple[EngineeringPowerFlowBusResult, ...]


class PowerFlowResultConverter:
    """Convert numerical PU voltage results using explicit Bus voltage bases."""

    @staticmethod
    def to_engineering(
        result: PowerFlowResult,
        buses: Iterable[Any],
    ) -> EngineeringPowerFlowResult:
        """Convert PU voltage magnitudes to kV using each Bus nominal voltage."""
        if not isinstance(result, PowerFlowResult):
            raise TypeError("result must be a PowerFlowResult instance.")

        bus_sequence = tuple(buses)
        if len(bus_sequence) != len(result.voltage_magnitudes):
            raise ValueError(
                "Power Flow result voltage count must match the supplied Bus count."
            )

        converted: list[EngineeringPowerFlowBusResult] = []
        for bus, voltage_pu, angle_rad in zip(
            bus_sequence,
            result.voltage_magnitudes,
            result.voltage_angles,
        ):
            bus_id = getattr(bus, "id", None)
            if not isinstance(bus_id, str) or not bus_id:
                raise ValueError("Each result Bus must provide a non-empty string id.")

            try:
                nominal_voltage_kv = float(getattr(bus, "nominal_voltage_kv"))
            except (TypeError, ValueError, AttributeError) as exc:
                raise ValueError(
                    f"Bus '{bus_id}' must provide nominal_voltage_kv."
                ) from exc

            if not math.isfinite(nominal_voltage_kv) or nominal_voltage_kv <= 0.0:
                raise ValueError(
                    f"Bus '{bus_id}' nominal_voltage_kv must be finite and positive."
                )

            voltage_pu = float(voltage_pu)
            angle_rad = float(angle_rad)
            if not math.isfinite(voltage_pu) or voltage_pu <= 0.0:
                raise ValueError(
                    f"Power Flow result voltage for Bus '{bus_id}' must be finite and positive."
                )
            if not math.isfinite(angle_rad):
                raise ValueError(
                    f"Power Flow result angle for Bus '{bus_id}' must be finite."
                )

            per_unit = PerUnitSystem(1.0)
            voltage_kv = per_unit.from_pu_voltage(
                voltage_pu,
                nominal_voltage_kv,
            )
            converted.append(
                EngineeringPowerFlowBusResult(
                    bus_id=bus_id,
                    voltage_pu=voltage_pu,
                    voltage_kv=voltage_kv,
                    angle_rad=angle_rad,
                    angle_deg=math.degrees(angle_rad),
                )
            )

        return EngineeringPowerFlowResult(
            numerical_result=result,
            buses=tuple(converted),
        )


__all__ = [
    "EngineeringPowerFlowBusResult",
    "EngineeringPowerFlowResult",
    "PowerFlowResultConverter",
]
