# ============================================================
# File: core/protection/voltage/overvoltage_relay.py
# GridForge V2 — ANSI 59 Over-Voltage
# Author: Subhendu Mishra
# ============================================================

"""Canonical ANSI 59 overvoltage protection function."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from core.protection.context import ProtectionContext
from core.protection.decision import ProtectionDecision
from core.protection.relay_base import RelayBase
from core.protection.relay_input import RelayInput


FUNCTION_CODE = "59"
FUNCTION_NAME = "OVER-VOLTAGE"
VOLTAGE_INPUT = "voltage"


@dataclass(frozen=True, slots=True)
class OverVoltageSettings:
    """Configuration for instantaneous ANSI 59 voltage supervision."""

    pickup: float

    def __post_init__(self) -> None:
        try:
            pickup = float(self.pickup)
        except (TypeError, ValueError) as exc:
            raise ValueError("pickup must be numeric.") from exc
        if not math.isfinite(pickup) or pickup <= 0.0:
            raise ValueError("pickup must be finite and positive.")
        object.__setattr__(self, "pickup", pickup)


class OverVoltageRelay(RelayBase):
    """Evaluate ANSI 59 from one authoritative voltage RelayInput.

    The function uses voltage magnitude and operates instantaneously
    when ``|V| >= pickup``. It produces only a ProtectionDecision;
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
        settings: OverVoltageSettings,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:
        if not isinstance(settings, OverVoltageSettings):
            raise TypeError("settings must be an OverVoltageSettings instance.")
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
        self._settings_59 = settings
        self.require_inputs(self.VOLTAGE_INPUT)

    @property
    def pickup(self) -> float:
        """Return the configured overvoltage threshold."""

        return self._settings_59.pickup

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

    def evaluate(self, context: ProtectionContext) -> ProtectionDecision:
        """Evaluate the ANSI 59 pickup criterion and return a decision."""

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
            "criterion": "|V| >= pickup",
            "overvoltage": True,
            "instantaneous": True,
        }
        if voltage < self.pickup:
            return self.no_operation(
                reason="Voltage below ANSI 59 pickup threshold.",
                timestamp=timestamp,
                operating_time=None,
                metadata=metadata,
            )

        return self.trip_decision(
            reason="ANSI 59 overvoltage pickup threshold reached.",
            timestamp=timestamp,
            operating_time=0.0,
            metadata=metadata,
        )

    def _inactive_reason(self) -> str:
        if not self.enabled:
            return "ANSI 59 function is disabled."
        if self.blocked:
            return "ANSI 59 function is statically blocked."
        if not bool(getattr(self.relay, "operational", True)):
            return "Authoritative relay is not operational."
        return "ANSI 59 function is not operational."


__all__ = [
    "FUNCTION_CODE",
    "FUNCTION_NAME",
    "VOLTAGE_INPUT",
    "OverVoltageSettings",
    "OverVoltageRelay",
]
