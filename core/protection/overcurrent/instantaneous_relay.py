# ============================================================
# File: core/protection/overcurrent/instantaneous_relay.py
# GridForge V2 — ANSI 50 Instantaneous Overcurrent
# Author: Subhendu Mishra
# ============================================================

"""Canonical ANSI 50 instantaneous overcurrent protection function.

The implementation consumes one authoritative current MeasurementChannel
through RelayInput and produces the canonical ProtectionDecision. It has no
breaker, topology, solver, simulation-clock, or UI responsibility.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from core.protection.context import ProtectionContext
from core.protection.decision import ProtectionDecision
from core.protection.relay_base import RelayBase
from core.protection.relay_input import RelayInput


FUNCTION_CODE = "50"
FUNCTION_NAME = "INSTANTANEOUS OVERCURRENT"
CURRENT_INPUT = "current"


@dataclass(frozen=True, slots=True)
class InstantaneousOvercurrentSettings:
    """Immutable engineering settings for one ANSI 50 function."""

    pickup: float

    def __post_init__(self) -> None:
        try:
            pickup = float(self.pickup)
        except (TypeError, ValueError) as exc:
            raise ValueError("pickup must be numeric.") from exc
        if not math.isfinite(pickup) or pickup <= 0.0:
            raise ValueError("pickup must be finite and positive.")
        object.__setattr__(self, "pickup", pickup)


class InstantaneousOvercurrentRelay(RelayBase):
    """IEC/ANSI 50 instantaneous overcurrent protection function.

    The operating criterion is:

        |I| >= pickup

    Once the criterion is satisfied, the decision has zero modeled
    protection delay. Physical breaker operation remains an Application
    concern.
    """

    CURRENT_INPUT = CURRENT_INPUT
    FUNCTION_CODE = FUNCTION_CODE
    FUNCTION_NAME = FUNCTION_NAME

    def __init__(
        self,
        relay: Any,
        *,
        element_id: str,
        relay_inputs: Mapping[str, RelayInput] | None = None,
        settings: InstantaneousOvercurrentSettings,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:
        if not isinstance(settings, InstantaneousOvercurrentSettings):
            raise TypeError(
                "settings must be an InstantaneousOvercurrentSettings instance."
            )
        super().__init__(
            relay=relay,
            element_id=element_id,
            function_code=self.FUNCTION_CODE,
            function_name=self.FUNCTION_NAME,
            relay_inputs=relay_inputs,
            settings={"pickup": settings.pickup},
            enabled=enabled,
            blocked=blocked,
        )
        self._settings_50 = settings
        self.require_inputs(self.CURRENT_INPUT)

    @property
    def instantaneous_settings(self) -> InstantaneousOvercurrentSettings:
        """Return the immutable typed ANSI 50 settings."""
        return self._settings_50

    @property
    def pickup(self) -> float:
        """Return configured instantaneous pickup current."""
        return self._settings_50.pickup

    def current_signal(self) -> Any:
        """Read current exclusively through the assigned RelayInput."""
        relay_input = self.get_input(self.CURRENT_INPUT)
        value = getattr(relay_input, "value", None)
        if value is None:
            raise AttributeError("RelayInput does not expose a current value.")
        return value() if callable(value) else value

    def current_value(self) -> float:
        """Return the finite magnitude of the authoritative current signal."""
        value = self.current_signal()
        if isinstance(value, bool):
            raise TypeError("Current measurement cannot be bool.")
        try:
            phasor = complex(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Current measurement must be numeric.") from exc
        if not math.isfinite(phasor.real) or not math.isfinite(phasor.imag):
            raise ValueError("Current measurement must be finite.")
        return abs(phasor)

    def evaluate(self, context: ProtectionContext | None = None) -> ProtectionDecision:
        """Evaluate ANSI 50 without operating equipment."""
        timestamp = None if context is None else context.time
        if timestamp is not None:
            try:
                timestamp = float(timestamp)
            except (TypeError, ValueError) as exc:
                raise ValueError("Protection evaluation timestamp must be numeric.") from exc
            if not math.isfinite(timestamp):
                raise ValueError("Protection evaluation timestamp must be finite.")

        if not self.operational:
            return self.no_operation(
                reason=self._inactive_reason(),
                timestamp=timestamp,
                operating_time=None,
            )

        try:
            current = self.current_value()
            usable = self.get_input(self.CURRENT_INPUT).usable
        except (TypeError, ValueError, AttributeError, KeyError) as exc:
            return self.invalid_decision(
                reason=f"Invalid current measurement: {exc}",
                timestamp=timestamp,
                metadata={"input": self.CURRENT_INPUT},
            )

        if not usable:
            return self.invalid_decision(
                reason="Current measurement is not usable.",
                timestamp=timestamp,
                metadata={
                    "input": self.CURRENT_INPUT,
                    "current": current,
                    "pickup": self.pickup,
                },
            )

        picked_up = current >= self.pickup
        metadata = {
            "current": current,
            "pickup": self.pickup,
            "criterion": "|I| >= pickup",
            "instantaneous": True,
        }
        if not picked_up:
            return self.no_operation(
                reason="Current below instantaneous overcurrent pickup.",
                timestamp=timestamp,
                operating_time=None,
                metadata=metadata,
            )

        return self.trip_decision(
            reason="ANSI 50 instantaneous overcurrent pickup reached.",
            timestamp=timestamp,
            operating_time=0.0,
            metadata=metadata,
        )

    def _inactive_reason(self) -> str:
        if not self.enabled:
            return "ANSI 50 function is disabled."
        if self.blocked:
            return "ANSI 50 function is statically blocked."
        if not bool(getattr(self.relay, "operational", True)):
            return "Authoritative relay is not operational."
        return "ANSI 50 function is not operational."


__all__ = [
    "FUNCTION_CODE",
    "FUNCTION_NAME",
    "CURRENT_INPUT",
    "InstantaneousOvercurrentSettings",
    "InstantaneousOvercurrentRelay",
]
