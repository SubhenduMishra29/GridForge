"""
GridForge - Power Flow Study Configuration
==========================================

Defines explicit study-side Power Flow intent independently of the
physical electrical model and numerical solver.

Author: Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping

from core.solver.power_flow.input import PowerFlowBusType


@dataclass(frozen=True, slots=True)
class PowerFlowStudyConfiguration:
    """Immutable engineering definition for a Power Flow study.

    ``bus_types`` is the authoritative study-side PQ/PV/SLACK assignment.
    It refers to bus IDs rather than live Core Bus objects.

    ``base_mva`` is the explicit system MVA base used by the preparation
    boundary to normalize engineering power quantities into PU values.
    """

    bus_types: Mapping[str, PowerFlowBusType | str]
    base_mva: float

    def __post_init__(self) -> None:
        if not self.bus_types:
            raise ValueError(
                "Power Flow study configuration requires at least one bus classification."
            )

        base_mva = float(self.base_mva)
        if not math.isfinite(base_mva) or base_mva <= 0.0:
            raise ValueError("Power Flow study base MVA must be finite and positive.")
        object.__setattr__(self, "base_mva", base_mva)

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

    @classmethod
    def from_mapping(
        cls,
        bus_types: Mapping[str, PowerFlowBusType | str],
        *,
        slack_bus_id: str,
        base_mva: float,
    ) -> "PowerFlowStudyConfiguration":
        """Create a configuration from an explicit bus-ID/type mapping."""
        if not isinstance(slack_bus_id, str) or not slack_bus_id:
            raise ValueError("slack_bus_id must be a non-empty string.")
        return cls(bus_types=bus_types, base_mva=base_mva)

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

    def type_of(self, bus_id: str) -> PowerFlowBusType:
        """Return the configured study classification for a bus ID."""
        return self.bus_types[bus_id]

    def __repr__(self) -> str:
        return (
            "PowerFlowStudyConfiguration("
            f"buses={len(self.bus_types)}, "
            f"slack_bus_id={self.slack_bus_id!r}, "
            f"base_mva={self.base_mva:g}"
            ")"
        )


__all__ = ["PowerFlowStudyConfiguration"]
