# ============================================================
# File: core/protection/overcurrent/earth_instantaneous_relay.py
# GridForge V2 — ANSI 50N Earth Instantaneous Overcurrent
# Author: Subhendu Mishra
# ============================================================

"""Canonical ANSI 50N residual/earth instantaneous overcurrent function."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from core.protection.context import ProtectionContext
from core.protection.decision import ProtectionDecision
from core.protection.relay_base import RelayBase
from core.protection.relay_input import RelayInput


FUNCTION_CODE = "50N"
FUNCTION_NAME = "EARTH INSTANTANEOUS OVERCURRENT"
RESIDUAL_CURRENT_INPUT = "residual_current"


@dataclass(frozen=True, slots=True)
class EarthInstantaneousOvercurrentSettings:
    """Immutable engineering settings for ANSI 50N."""

    pickup: float

    def __post_init__(self) -> None:
        try:
            pickup = float(self.pickup)
        except (TypeError, ValueError) as exc:
            raise ValueError("pickup must be numeric.") from exc
        if not math.isfinite(pickup) or pickup <= 0.0:
            raise ValueError("pickup must be finite and positive.")
        object.__setattr__(self, "pickup", pickup)


class EarthInstantaneousOvercurrentRelay(RelayBase):
    """ANSI 50N instantaneous protection using an explicit residual-current input."""

    CURRENT_INPUT = RESIDUAL_CURRENT_INPUT
    FUNCTION_CODE = FUNCTION_CODE
    FUNCTION_NAME = FUNCTION_NAME

    def __init__(
        self,
        relay: Any,
        *,
        element_id: str,
        relay_inputs: Mapping[str, RelayInput] | None = None,
        settings: EarthInstantaneousOvercurrentSettings,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:
        if not isinstance(settings, EarthInstantaneousOvercurrentSettings):
            raise TypeError("settings must be an EarthInstantaneousOvercurrentSettings instance.")
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
        self._settings_50n = settings
        self.require_inputs(self.CURRENT_INPUT)

    @property
    def pickup(self) -> float:
        return self._settings_50n.pickup

    def current_signal(self) -> Any:
        relay_input = self.get_input(self.CURRENT_INPUT)
        value = getattr(relay_input, "value", None)
        if value is None:
            raise AttributeError("RelayInput does not expose a residual-current value.")
        return value() if callable(value) else value

    def residual_current_value(self) -> float:
        value = self.current_signal()
        if isinstance(value, bool):
            raise TypeError("Residual current measurement cannot be bool.")
        try:
            phasor = complex(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Residual current measurement must be numeric.") from exc
        if not math.isfinite(phasor.real) or not math.isfinite(phasor.imag):
            raise ValueError("Residual current measurement must be finite.")
        return abs(phasor)

    def evaluate(self, context: ProtectionContext | None = None) -> ProtectionDecision:
        timestamp = None if context is None else context.time
        if timestamp is not None:
            try:
                timestamp = float(timestamp)
            except (TypeError, ValueError) as exc:
                raise ValueError("Protection evaluation timestamp must be numeric.") from exc
            if not math.isfinite(timestamp):
                raise ValueError("Protection evaluation timestamp must be finite.")

        if not self.operational:
            return self.no_operation(reason=self._inactive_reason(), timestamp=timestamp, operating_time=None)

        try:
            current = self.residual_current_value()
            usable = self.get_input(self.CURRENT_INPUT).usable
        except (TypeError, ValueError, AttributeError, KeyError) as exc:
            return self.invalid_decision(
                reason=f"Invalid residual current measurement: {exc}",
                timestamp=timestamp,
                metadata={"input": self.CURRENT_INPUT},
            )

        if not usable:
            return self.invalid_decision(
                reason="Residual current measurement is not usable.",
                timestamp=timestamp,
                metadata={"input": self.CURRENT_INPUT, "current": current, "pickup": self.pickup},
            )

        metadata = {
            "current": current,
            "pickup": self.pickup,
            "criterion": "|I0| >= pickup",
            "earth_fault": True,
            "instantaneous": True,
        }
        if current < self.pickup:
            return self.no_operation(
                reason="Residual current below ANSI 50N pickup.",
                timestamp=timestamp,
                operating_time=None,
                metadata=metadata,
            )

        return self.trip_decision(
            reason="ANSI 50N earth instantaneous overcurrent pickup reached.",
            timestamp=timestamp,
            operating_time=0.0,
            metadata=metadata,
        )

    def _inactive_reason(self) -> str:
        if not self.enabled:
            return "ANSI 50N function is disabled."
        if self.blocked:
            return "ANSI 50N function is statically blocked."
        if not bool(getattr(self.relay, "operational", True)):
            return "Authoritative relay is not operational."
        return "ANSI 50N function is not operational."


__all__ = [
    "FUNCTION_CODE",
    "FUNCTION_NAME",
    "RESIDUAL_CURRENT_INPUT",
    "EarthInstantaneousOvercurrentSettings",
    "EarthInstantaneousOvercurrentRelay",
]
