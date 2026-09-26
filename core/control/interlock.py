"""Project-owned immutable Control interlock contract.

Author: Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any, Mapping


class SignalQuality(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    WRONG_TYPE = "wrong_type"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class InterlockResult:
    allowed: bool
    diagnostic: str
    quality: SignalQuality = SignalQuality.VALID


@dataclass(frozen=True, slots=True)
class ControlInterlock:
    """Immutable configuration gate; runtime input values remain external."""

    interlock_id: str
    required_inputs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        interlock_id = str(self.interlock_id).strip()
        if not interlock_id:
            raise ValueError("interlock_id cannot be empty.")
        inputs = tuple(str(name).strip() for name in self.required_inputs)
        if any(not name for name in inputs):
            raise ValueError("required_inputs cannot contain empty names.")
        object.__setattr__(self, "interlock_id", interlock_id)
        object.__setattr__(self, "required_inputs", inputs)

    def evaluate(self, inputs: Mapping[str, Any], simulation_time: float) -> InterlockResult:
        if not isfinite(float(simulation_time)):
            raise ValueError("simulation_time must be finite.")
        blocked = []
        for name in self.required_inputs:
            if name not in inputs:
                blocked.append(name)
                continue
            value = inputs[name]
            if isinstance(value, Mapping):
                quality = str(value.get("quality", SignalQuality.VALID.value))
                if quality != SignalQuality.VALID.value:
                    return InterlockResult(False, f"Interlock '{self.interlock_id}' input '{name}' quality is {quality}.", SignalQuality(quality))
                value = value.get("value")
            if value is not True:
                blocked.append(name)
        if blocked:
            return InterlockResult(False, f"Interlock '{self.interlock_id}' blocked by: {', '.join(blocked)}.", SignalQuality.VALID)
        return InterlockResult(True, f"Interlock '{self.interlock_id}' permissive.", SignalQuality.VALID)


__all__ = ["ControlInterlock", "InterlockResult", "SignalQuality"]
