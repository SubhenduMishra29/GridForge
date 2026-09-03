"""
GridForge - Power Flow Study Configuration
==========================================

Defines explicit study-side Power Flow intent independently of the
physical electrical model and numerical solver.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from core.solver.power_flow.input import PowerFlowBusType


@dataclass(frozen=True, slots=True)
class PowerFlowStudyConfiguration:
    """Immutable engineering definition for a Power Flow study.

    ``bus_types`` is the authoritative study-side PQ/PV/SLACK assignment.
    It refers to bus IDs rather than live Core Bus objects.
    """

    bus_types: Mapping[str, PowerFlowBusType | str]

    def __post_init__(self) -> None:
        if not self.bus_types:
            raise ValueError(
                "Power Flow study configuration requires at least one bus classification."
            )

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

        object.__setattr__(self, "bus_types", MappingProxyType(normalized))

    def type_of(self, bus_id: str) -> PowerFlowBusType:
        """Return the configured study classification for a bus ID."""
        return self.bus_types[bus_id]


__all__ = ["PowerFlowStudyConfiguration"]
