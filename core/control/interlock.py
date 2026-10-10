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


SUPPORTED_INTERLOCK_CONDITIONS = frozenset({"all_required_inputs_true"})
SUPPORTED_INTERLOCK_QUALITY_POLICIES = frozenset({"require_valid_fresh"})


@dataclass(frozen=True, slots=True)
class InterlockResult:
    allowed: bool
    diagnostic: str
    quality: SignalQuality = SignalQuality.VALID


@dataclass(frozen=True, slots=True)
class ControlInterlock:
    """Immutable configuration gate; runtime input values remain external.

    Only explicitly implemented condition and quality policies are accepted.
    The quality policy requires an explicit `valid` quality marker for each
    required input; unqualified raw values are not considered trustworthy.
    """

    interlock_id: str
    required_inputs: tuple[str, ...] = ()
    condition: str = "all_required_inputs_true"
    quality_policy: str = "require_valid_fresh"

    def __post_init__(self) -> None:
        interlock_id = str(self.interlock_id).strip()
        if not interlock_id:
            raise ValueError("interlock_id cannot be empty.")
        inputs = tuple(str(name).strip() for name in self.required_inputs)
        if any(not name for name in inputs):
            raise ValueError("required_inputs cannot contain empty names.")
        condition = str(self.condition).strip()
        quality_policy = str(self.quality_policy).strip()
        if condition not in SUPPORTED_INTERLOCK_CONDITIONS:
            raise ValueError(
                f"Unsupported interlock condition {condition!r}; supported values: "
                f"{', '.join(sorted(SUPPORTED_INTERLOCK_CONDITIONS))}."
            )
        if quality_policy not in SUPPORTED_INTERLOCK_QUALITY_POLICIES:
            raise ValueError(
                f"Unsupported interlock quality_policy {quality_policy!r}; supported values: "
                f"{', '.join(sorted(SUPPORTED_INTERLOCK_QUALITY_POLICIES))}."
            )
        object.__setattr__(self, "interlock_id", interlock_id)
        object.__setattr__(self, "required_inputs", inputs)
        object.__setattr__(self, "condition", condition)
        object.__setattr__(self, "quality_policy", quality_policy)

    def evaluate(self, inputs: Mapping[str, Any], simulation_time: float) -> InterlockResult:
        try:
            current_time = float(simulation_time)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("simulation_time must be finite.") from exc
        if not isfinite(current_time):
            raise ValueError("simulation_time must be finite.")
        if not isinstance(inputs, Mapping):
            return InterlockResult(
                False,
                f"Interlock '{self.interlock_id}' blocked: inputs must be a mapping.",
                SignalQuality.INVALID,
            )

        blocked: list[str] = []
        for name in self.required_inputs:
            if name not in inputs:
                return InterlockResult(
                    False,
                    f"Interlock '{self.interlock_id}' blocked: required input '{name}' is missing.",
                    SignalQuality.MISSING,
                )
            signal = inputs[name]
            if not isinstance(signal, Mapping):
                return InterlockResult(
                    False,
                    f"Interlock '{self.interlock_id}' input '{name}' is malformed; "
                    "expected a mapping with 'value' and 'quality'.",
                    SignalQuality.INVALID,
                )
            if "quality" not in signal:
                return InterlockResult(
                    False,
                    f"Interlock '{self.interlock_id}' input '{name}' has no quality marker.",
                    SignalQuality.MISSING,
                )
            raw_quality = signal["quality"]
            try:
                quality = SignalQuality(raw_quality)
            except (ValueError, TypeError):
                return InterlockResult(
                    False,
                    f"Interlock '{self.interlock_id}' input '{name}' has unsupported quality "
                    f"{raw_quality!r}; expected one of "
                    f"{', '.join(item.value for item in SignalQuality)}.",
                    SignalQuality.INVALID,
                )
            if quality is not SignalQuality.VALID:
                return InterlockResult(
                    False,
                    f"Interlock '{self.interlock_id}' input '{name}' quality is {quality.value}.",
                    quality,
                )
            if "value" not in signal:
                return InterlockResult(
                    False,
                    f"Interlock '{self.interlock_id}' input '{name}' has no value.",
                    SignalQuality.MISSING,
                )
            if signal["value"] is not True:
                blocked.append(name)

        if blocked:
            return InterlockResult(
                False,
                f"Interlock '{self.interlock_id}' blocked by: {', '.join(blocked)}.",
                SignalQuality.VALID,
            )
        return InterlockResult(True, f"Interlock '{self.interlock_id}' permissive.", SignalQuality.VALID)


__all__ = [
    "ControlInterlock",
    "InterlockResult",
    "SignalQuality",
    "SUPPORTED_INTERLOCK_CONDITIONS",
    "SUPPORTED_INTERLOCK_QUALITY_POLICIES",
]
