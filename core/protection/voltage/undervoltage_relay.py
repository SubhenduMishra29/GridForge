# ============================================================
# File: core/protection/voltage/undervoltage_relay.py
# GridForge V2 — ANSI 27 Under-Voltage
# Author: Subhendu Mishra
# ============================================================

"""Canonical ANSI 27 undervoltage protection function."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from core.protection.context import ProtectionContext
from core.protection.relay_base import RelayBase
from core.protection.relay_input import RelayInput


FUNCTION_CODE = "27"
FUNCTION_NAME = "UNDER-VOLTAGE"
VOLTAGE_INPUT = "voltage"


@dataclass(frozen=True, slots=True)
class UnderVoltageSettings:
    """Configuration for instantaneous ANSI 27 voltage supervision."""

    pickup: float

    def __post_init__(self) -> None:
        try:
            pickup = float(self.pickup)
        except (TypeError, ValueError) as exc:
            raise ValueError("pickup must be numeric.") from exc
        if not math.isfinite(pickup) or pickup <= 0.0:
            raise ValueError("pickup must be finite and positive.")
        object.__setattr__(self, "pickup", pickup)


class UnderVoltageRelay(RelayBase):
    """Evaluate ANSI 27 from one authoritative voltage RelayInput.

    The function uses voltage magnitude and operates instantaneously
    when ``|V| <= pickup``. It produces only a ProtectionDecision;
    breaker operation remains outside the protection function.
    """

    VOLTAGE_INPUT = VOLTAGE_INPUT
    FUNCTION_CODE = FUNCTION_CODE
    FUNCTION_NAME = FUNCTION_NAME

    def __init__(
        self,
        relay: Any,
        *,
        element_id: str,
        relay_inputs: Mapping[str, RelayInput] | None = None,
        settings: UnderVoltageSettings,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:
        if not isinstance(settings, UnderVoltageSettings):
            raise TypeError("settings must be an UnderVoltageSettings instance.")
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
        self._settings_27 = settings
        self.require_inputs(self.VOLTAGE_INPUT)

    @property
    def pickup(self) -> float:
        """Return the configured undervoltage threshold."""

        return self._settings_27.pickup

    def voltage_signal(self) -> Any:
        """Read the live engineering voltage from the assigned input."""

        return self.get_input(self.VOLTAGE_INPUT).value

    def voltage_value(self) -> float:
        """Return validated voltage magnitude from the authoritative input."""

        value = self.voltage_signal()
        if isinstance(value, bool):
            raise TypeError("Voltage measurement cannot be bool.")
        try:
            phasor = complex(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Voltage measurement must be numeric.") from exc
        if not math.isfinite(phasor.real) or not math.isfinite(phasor.imag):
            raise ValueError("Voltage measurement must be finite.")
        return abs(phasor)

    def evaluate(self, context: ProtectionContext) -> Any:
        """Evaluate the ANSI 27 pickup criterion and return a decision."""

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
            voltage = self.voltage_value()
            usable = self.get_input(self.VOLTAGE_INPUT).usable
        except (TypeError, ValueError, AttributeError, KeyError) as exc:
            return self.invalid_decision(
                reason=f"Invalid voltage measurement: {exc}",
                timestamp=timestamp,
                metadata={"input": self.VOLTAGE_INPUT},
            )

        if not usable:
            return self.invalid_decision(
                reason="Voltage measurement is not usable.",
                timestamp=timestamp,
                metadata={"input": self.VOLTAGE_INPUT, "voltage": voltage, "pickup": self.pickup},
            )

        metadata = {
            "voltage": voltage,
            "pickup": self.pickup,
            "criterion": "|V| <= pickup",
            "undervoltage": True,
            "instantaneous": True,
        }
        if voltage > self.pickup:
            return self.no_operation(
                reason="Voltage above ANSI 27 pickup threshold.",
                timestamp=timestamp,
                operating_time=None,
                metadata=metadata,
            )

        return self.trip_decision(
            reason="ANSI 27 undervoltage pickup threshold reached.",
            timestamp=timestamp,
            operating_time=0.0,
            metadata=metadata,
        )

    def _inactive_reason(self) -> str:
        if not self.enabled:
            return "ANSI 27 function is disabled."
        if self.blocked:
            return "ANSI 27 function is statically blocked."
        if not bool(getattr(self.relay, "operational", True)):
            return "Authoritative relay is not operational."
        return "ANSI 27 function is not operational."


__all__ = [
    "FUNCTION_CODE",
    "FUNCTION_NAME",
    "VOLTAGE_INPUT",
    "UnderVoltageSettings",
    "UnderVoltageRelay",
]
