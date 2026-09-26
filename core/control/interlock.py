# Author: Subhendu Mishra
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from enum import Enum
from typing import Any, Mapping


class InterlockInputQuality(str, Enum):
    VALID="valid"; INVALID="invalid"; STALE="stale"; UNAVAILABLE="unavailable"; WRONG_TYPE="wrong_type"; MISSING="missing"

@dataclass(frozen=True, slots=True)
class InterlockResult:
    allowed: bool
    diagnostic: str
    quality: InterlockInputQuality = InterlockInputQuality.VALID
    evaluated_time: float = 0.0


class ControlInterlock:
    """Headless permissive gate evaluated before a control action is emitted."""

    def __init__(self, interlock_id: str, *, required_inputs: tuple[str, ...] = ()) -> None:
        interlock_id = str(interlock_id).strip()
        if not interlock_id:
            raise ValueError("interlock_id cannot be empty.")
        self.interlock_id = interlock_id
        self.required_inputs = tuple(str(name).strip() for name in required_inputs)
        if any(not name for name in self.required_inputs):
            raise ValueError("required_inputs cannot contain empty names.")

    def evaluate(self, inputs: Mapping[str, Any], simulation_time: float) -> InterlockResult:
        if not isfinite(float(simulation_time)): raise ValueError("simulation_time must be finite.")
        blocked=[]; quality=InterlockInputQuality.VALID
        for name in self.required_inputs:
            raw=inputs.get(name)
            if raw is None: blocked.append(name); quality=InterlockInputQuality.MISSING; continue
            if isinstance(raw, Mapping):
                try: item_quality=InterlockInputQuality(str(raw.get("quality","valid")))
                except ValueError: item_quality=InterlockInputQuality.WRONG_TYPE
                value=raw.get("value")
                if item_quality is not InterlockInputQuality.VALID:
                    blocked.append(name)
                    if quality is InterlockInputQuality.VALID: quality=item_quality
                    continue
            else: value=raw
            if value is not True: blocked.append(name)
        if blocked: return InterlockResult(False, f"Interlock '{self.interlock_id}' blocked by: {', '.join(blocked)}", quality, float(simulation_time))
        return InterlockResult(True, f"Interlock '{self.interlock_id}' permissive", InterlockInputQuality.VALID, float(simulation_time))


__all__ = ["ControlInterlock", "InterlockResult", "InterlockInputQuality"]
