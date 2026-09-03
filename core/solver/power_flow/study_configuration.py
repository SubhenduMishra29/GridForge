"""Immutable study-level configuration for AC power-flow preparation."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from .input import PowerFlowBusType


@dataclass(frozen=True, slots=True)
class PowerFlowStudyConfiguration:
    """Reusable study settings with explicit bus operating modes.

    The configuration contains study choices only. It never stores a live
    Network or other mutable Core object. The bus-mode mapping is explicit so
    preparation never invents a slack/PV/PQ classification from equipment
    naming or folder structure.
    """

    bus_types: tuple[tuple[str, PowerFlowBusType], ...]
    slack_bus_id: str
    base_mva: float

    def __post_init__(self) -> None:
        if not isinstance(self.slack_bus_id, str) or not self.slack_bus_id:
            raise ValueError("slack_bus_id must be a non-empty string.")

        try:
            base_mva = float(self.base_mva)
        except (TypeError, ValueError) as exc:
            raise ValueError("base_mva must be numeric.") from exc
        if not math.isfinite(base_mva) or base_mva <= 0.0:
            raise ValueError("base_mva must be finite and greater than zero.")
        object.__setattr__(self, "base_mva", base_mva)

        normalized: list[tuple[str, PowerFlowBusType]] = []
        seen: set[str] = set()
        for bus_id, bus_type in self.bus_types:
            if not isinstance(bus_id, str) or not bus_id:
                raise ValueError("Power-flow bus IDs must be non-empty strings.")
            if bus_id in seen:
                raise ValueError(f"Duplicate power-flow bus ID: '{bus_id}'.")
            seen.add(bus_id)
            try:
                normalized_type = (
                    bus_type
                    if isinstance(bus_type, PowerFlowBusType)
                    else PowerFlowBusType(bus_type)
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid power-flow bus type for '{bus_id}': {bus_type!r}."
                ) from exc
            normalized.append((bus_id, normalized_type))

        if self.slack_bus_id not in seen:
            raise ValueError(
                f"Configured slack bus '{self.slack_bus_id}' is not in bus_types."
            )

        slack_ids = [
            bus_id for bus_id, bus_type in normalized
            if bus_type is PowerFlowBusType.SLACK
        ]
        if slack_ids != [self.slack_bus_id]:
            raise ValueError(
                "Configuration must contain exactly one SLACK bus, and it "
                "must equal slack_bus_id."
            )

        object.__setattr__(self, "bus_types", tuple(normalized))

    @classmethod
    def from_mapping(
        cls,
        bus_types: Mapping[str, PowerFlowBusType | str],
        *,
        slack_bus_id: str,
        base_mva: float,
    ) -> "PowerFlowStudyConfiguration":
        """Create a configuration from an explicit bus-ID/type mapping."""

        return cls(
            bus_types=tuple(bus_types.items()),
            slack_bus_id=slack_bus_id,
            base_mva=base_mva,
        )

    @property
    def bus_type_mapping(self) -> dict[str, PowerFlowBusType]:
        """Return a detached mapping of configured bus operating modes."""

        return dict(self.bus_types)

    def type_of(self, bus_id: str) -> PowerFlowBusType:
        """Return the configured operating type for a bus."""

        for configured_id, bus_type in self.bus_types:
            if configured_id == bus_id:
                return bus_type
        raise KeyError(f"Bus '{bus_id}' is not configured for power flow.")

    def __repr__(self) -> str:
        return (
            "PowerFlowStudyConfiguration("
            f"buses={len(self.bus_types)}, "
            f"slack_bus_id={self.slack_bus_id!r}, "
            f"base_mva={self.base_mva:g}"
            ")"
        )


__all__ = ["PowerFlowStudyConfiguration"]
