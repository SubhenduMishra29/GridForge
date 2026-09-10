from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping


@dataclass(frozen=True, slots=True)
class InterlockResult:
    allowed: bool
    diagnostic: str


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

    def evaluate(self, inputs: Mapping[str, bool], simulation_time: float) -> InterlockResult:
        """Return a deterministic permissive/blocked result without mutating Core."""
        if not isfinite(float(simulation_time)):
            raise ValueError("simulation_time must be finite.")
        blocked = tuple(name for name in self.required_inputs if inputs.get(name) is not True)
        if blocked:
            return InterlockResult(False, f"Interlock '{self.interlock_id}' blocked by: {', '.join(blocked)}")
        return InterlockResult(True, f"Interlock '{self.interlock_id}' permissive")


__all__ = ["ControlInterlock", "InterlockResult"]
