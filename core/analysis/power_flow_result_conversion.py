"""
GridForge - Power Flow Result Conversion
=========================================

Converts numerical Power Flow results into immutable engineering
quantities for Analysis consumers, UI projections, and reporting.

This module is deliberately separate from the numerical result contract.
It does not create display strings and it does not retain Core model state.

Author: Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from core.base.per_unit import PerUnitSystem
from core.solver.power_flow.result import PowerFlowResult


@dataclass(frozen=True, slots=True)
class EngineeringPowerFlowBusResult:
    """Immutable engineering quantities for one solved bus."""

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
    """Convert numerical PU voltage results using detached voltage bases."""

    @staticmethod
    def to_engineering(
        result: PowerFlowResult,
        bus_ids: Sequence[str],
        bus_voltage_bases: Mapping[str, float],
        *,
        expected_snapshot_id: str | None = None,
    ) -> EngineeringPowerFlowResult:
        """Convert PU voltage magnitudes using a detached bus/base snapshot."""
        if not isinstance(result, PowerFlowResult):
            raise TypeError("result must be a PowerFlowResult instance.")

        if not result.success:
            raise ValueError("An unsuccessful Power Flow result cannot be converted to engineering quantities.")

        ids = tuple(bus_ids)
        if not result.bus_ids:
            raise ValueError("Power Flow result must identify its bus ordering before engineering conversion.")
        if result.bus_ids != ids:
            raise ValueError(
                "Power Flow result bus ordering must match the supplied bus IDs."
            )
        if result.snapshot_id is None:
            raise ValueError("Power Flow result must carry its originating input snapshot identity.")
        if expected_snapshot_id is not None:
            if not isinstance(expected_snapshot_id, str) or not expected_snapshot_id.strip():
                raise ValueError("expected_snapshot_id must be a non-empty string when supplied.")
            if result.snapshot_id != expected_snapshot_id.strip():
                raise ValueError("Power Flow result snapshot identity does not match the expected prepared input snapshot.")
        if len(ids) != len(result.voltage_magnitudes):
            raise ValueError(
                "Power Flow result voltage count must match the supplied bus IDs."
            )
        if len(result.voltage_angles) != len(ids):
            raise ValueError(
                "Power Flow result angle count must match the supplied bus IDs."
            )
        if len(set(ids)) != len(ids) or any(not isinstance(bus_id, str) or not bus_id for bus_id in ids):
            raise ValueError("Supplied bus IDs must be unique, non-empty strings.")

        try:
            bases = {str(bus_id): float(value) for bus_id, value in bus_voltage_bases.items()}
        except (TypeError, ValueError, AttributeError) as exc:
            raise TypeError("bus_voltage_bases must be a mapping of bus ID to voltage base.") from exc
        if set(bases) != set(ids):
            raise ValueError("Supplied voltage bases must match the supplied bus IDs.")
        if any(not math.isfinite(value) or value <= 0.0 for value in bases.values()):
            raise ValueError("Supplied voltage bases must be finite and positive.")

        per_unit = PerUnitSystem(1.0)
        converted: list[EngineeringPowerFlowBusResult] = []
        for bus_id, voltage_pu, angle_rad in zip(
            ids,
            result.voltage_magnitudes,
            result.voltage_angles,
        ):
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

            voltage_kv = per_unit.from_pu_voltage(voltage_pu, bases[bus_id])
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
