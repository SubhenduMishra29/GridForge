# ============================================================
# File: core/protection/thermal/thermal_overload_relay.py
# GridForge V2 — ANSI 49 Thermal Overload
# Author: Subhendu Mishra
# ============================================================

"""Canonical bounded ANSI 49 thermal-overload protection."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from core.measurement.measurement_channel import MeasurementSignalType
from core.protection.context import ProtectionContext
from core.protection.decision import ProtectionDecision
from core.protection.relay_base import RelayBase
from core.protection.relay_input import RelayInput


FUNCTION_CODE = "49"
FUNCTION_NAME = "THERMAL OVERLOAD"
TEMPERATURE_INPUT = "temperature"


@dataclass(frozen=True, slots=True)
class ThermalOverloadSettings:
    """Configuration for bounded instantaneous ANSI 49 thermal pickup."""

    pickup: float

    def __post_init__(self) -> None:
        try:
            pickup = float(self.pickup)
        except (TypeError, ValueError) as exc:
            raise ValueError("pickup must be numeric.") from exc
        if not math.isfinite(pickup):
            raise ValueError("pickup must be finite.")
        object.__setattr__(self, "pickup", pickup)


class ThermalOverloadRelay(RelayBase):
    """Evaluate ANSI 49 from an authoritative temperature measurement.

    This first bounded implementation deliberately models the protection
    boundary only: a temperature pickup threshold produces an immediate
    ProtectionDecision. Thermal memory, heating/cooling constants and
    IEC thermal curves remain future extensions rather than being
    fabricated here.
    """

    TEMPERATURE_INPUT = TEMPERATURE_INPUT
    FUNCTION_CODE = FUNCTION_CODE
    FUNCTION_NAME = FUNCTION_NAME

    def __init__(
        self,
        relay: Any,
        *,
        element_id: str,
        relay_inputs: Mapping[str, RelayInput] | None = None,
        settings: ThermalOverloadSettings,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:
        if not isinstance(settings, ThermalOverloadSettings):
            raise TypeError("settings must be a ThermalOverloadSettings instance.")
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
        self._settings_49 = settings
        self.require_inputs(self.TEMPERATURE_INPUT)

    @property
    def pickup(self) -> float:
        return self._settings_49.pickup

    def temperature_signal(self) -> Any:
        return self.get_input(self.TEMPERATURE_INPUT).value

    def temperature_value(self) -> float:
        value = self.temperature_signal()
        if isinstance(value, bool):
            raise TypeError("Temperature measurement cannot be bool.")
        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Temperature measurement must be numeric.") from exc
        if not math.isfinite(value):
            raise ValueError("Temperature measurement must be finite.")
        return value

    def _validate_input_semantics(self) -> None:
        channel = self.get_input(self.TEMPERATURE_INPUT).channel
        if channel.signal_type is not MeasurementSignalType.CUSTOM:
            raise ValueError("ANSI 49 input must be a CUSTOM temperature measurement channel.")

    def evaluate(self, context: ProtectionContext) -> ProtectionDecision:
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
                reason=self._inactive_reason(), timestamp=timestamp, operating_time=None
            )

        try:
            self._validate_input_semantics()
            temperature = self.temperature_value()
            usable = self.get_input(self.TEMPERATURE_INPUT).usable
        except (TypeError, ValueError, AttributeError, KeyError) as exc:
            return self.invalid_decision(
                reason=f"Invalid thermal measurement: {exc}",
                timestamp=timestamp,
                metadata={"input": self.TEMPERATURE_INPUT},
            )

        if not usable:
            return self.invalid_decision(
                reason="Temperature measurement is not usable.",
                timestamp=timestamp,
                metadata={"input": self.TEMPERATURE_INPUT, "temperature": temperature, "pickup": self.pickup},
            )

        metadata = {
            "temperature": temperature,
            "pickup": self.pickup,
            "criterion": "temperature >= pickup",
            "instantaneous": True,
        }
        if temperature < self.pickup:
            return self.no_operation(
                reason="Temperature below ANSI 49 pickup threshold.",
                timestamp=timestamp, operating_time=None, metadata=metadata
            )

        return self.trip_decision(
            reason="ANSI 49 thermal pickup threshold reached.",
            timestamp=timestamp, operating_time=0.0, metadata=metadata
        )

    def _inactive_reason(self) -> str:
        if not self.enabled:
            return "ANSI 49 function is disabled."
        if self.blocked:
            return "ANSI 49 function is statically blocked."
        if not bool(getattr(self.relay, "operational", True)):
            return "Authoritative relay is not operational."
        return "ANSI 49 function is not operational."


__all__ = [
    "FUNCTION_CODE", "FUNCTION_NAME", "TEMPERATURE_INPUT",
    "ThermalOverloadSettings", "ThermalOverloadRelay",
]
