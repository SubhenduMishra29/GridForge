"""Typed, immutable intent produced by the Control domain.

Author: Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


class ControlActionType(str, Enum):
    """Physical intent categories understood by the Application boundary."""

    TRIP = "trip"
    OPEN = "open"
    CLOSE = "close"
    START = "start"
    STOP = "stop"
    BLOW = "blow"
    RESET = "reset"
    PUT_IN_SERVICE = "put_in_service"
    TAKE_OUT_OF_SERVICE = "take_out_of_service"


class ControlTargetType(str, Enum):
    """Equipment classes that may receive Control intent."""

    BREAKER = "breaker"
    SWITCH = "switch"
    DISCONNECTOR = "disconnector"
    FUSE = "fuse"
    MOTOR = "motor"
    CONTACTOR = "contactor"
    ACTUATOR = "actuator"
    GENERATOR = "generator"
    PLANT_CONTROLLER_OUTPUT = "plant_controller_output"


@dataclass(frozen=True, slots=True)
class ControlDecision:
    """Immutable Control intent; it never contains Core objects."""

    control_id: str
    action_type: ControlActionType
    target_equipment_id: str
    reason: str
    simulation_time: float
    target_equipment_type: str = ControlTargetType.BREAKER.value
    triggered_by: str | None = None
    valid: bool = True
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        control_id = str(self.control_id).strip()
        target = str(self.target_equipment_id).strip()
        target_type = str(self.target_equipment_type).strip().lower()
        reason = str(self.reason).strip()
        if not control_id:
            raise ValueError("control_id must be a non-empty string.")
        if not target:
            raise ValueError("target_equipment_id must be a non-empty string.")
        if not target_type:
            raise ValueError("target_equipment_type must be a non-empty string.")
        try:
            target_type = ControlTargetType(target_type).value
        except ValueError as exc:
            raise ValueError(
                f"Unsupported Control target equipment type: {target_type!r}."
            ) from exc
        if not reason:
            raise ValueError("reason must be a non-empty string.")
        if not isinstance(self.action_type, ControlActionType):
            object.__setattr__(self, "action_type", ControlActionType(self.action_type))
        simulation_time = float(self.simulation_time)
        if not math.isfinite(simulation_time):
            raise ValueError("simulation_time must be finite.")
        object.__setattr__(self, "control_id", control_id)
        object.__setattr__(self, "target_equipment_id", target)
        object.__setattr__(self, "target_equipment_type", target_type)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "simulation_time", simulation_time)
        if self.triggered_by is not None:
            object.__setattr__(self, "triggered_by", str(self.triggered_by).strip() or None)
        if self.diagnostic is not None:
            object.__setattr__(self, "diagnostic", str(self.diagnostic).strip() or None)

    @classmethod
    def trip(
        cls,
        *,
        control_id: str,
        target_equipment_id: str,
        reason: str,
        simulation_time: float,
        triggered_by: str | None = None,
    ) -> "ControlDecision":
        """Create a breaker trip intent."""
        return cls(
            control_id=control_id,
            action_type=ControlActionType.TRIP,
            target_equipment_id=target_equipment_id,
            target_equipment_type=ControlTargetType.BREAKER.value,
            reason=reason,
            simulation_time=simulation_time,
            triggered_by=triggered_by,
        )

    @classmethod
    def blocked(
        cls,
        *,
        control_id: str,
        action_type: ControlActionType,
        target_equipment_id: str,
        reason: str,
        simulation_time: float,
        diagnostic: str,
        target_equipment_type: str = ControlTargetType.BREAKER.value,
    ) -> "ControlDecision":
        """Create an explicit blocked intent for diagnostics."""
        return cls(
            control_id=control_id,
            action_type=action_type,
            target_equipment_id=target_equipment_id,
            target_equipment_type=target_equipment_type,
            reason=reason,
            simulation_time=simulation_time,
            valid=False,
            diagnostic=diagnostic,
        )


__all__ = ["ControlActionType", "ControlTargetType", "ControlDecision"]
