# ============================================================
# File: core/protection/overcurrent/negative_sequence_relay.py
# GridForge V2 — ANSI 46 Negative-Sequence Overcurrent
# Author: Subhendu Mishra
# ============================================================

"""Canonical ANSI 46 negative-sequence overcurrent protection."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from core.measurement.measurement_channel import MeasurementPhase, MeasurementSignalType
from core.protection.context import ProtectionContext
from core.protection.decision import ProtectionDecision
from core.protection.relay_base import RelayBase
from core.protection.relay_input import RelayInput


FUNCTION_CODE = "46"
FUNCTION_NAME = "NEGATIVE-SEQUENCE OVERCURRENT"
NEGATIVE_SEQUENCE_CURRENT_INPUT = "negative_sequence_current"


@dataclass(frozen=True, slots=True)
class NegativeSequenceOvercurrentSettings:
    """Configuration for instantaneous ANSI 46 pickup protection."""

    pickup: float

    def __post_init__(self) -> None:
        try:
            pickup = float(self.pickup)
        except (TypeError, ValueError) as exc:
            raise ValueError("pickup must be numeric.") from exc
        if not math.isfinite(pickup) or pickup <= 0.0:
            raise ValueError("pickup must be finite and positive.")
        object.__setattr__(self, "pickup", pickup)


class NegativeSequenceOvercurrentRelay(RelayBase):
    """Evaluate ANSI 46 from one authoritative negative-sequence current input.

    The function requires a CURRENT MeasurementChannel explicitly
    designated as NEGATIVE_SEQUENCE. It operates instantaneously when
    ``|I2| >= pickup`` and produces only a ProtectionDecision.
    """

    NEGATIVE_SEQUENCE_CURRENT_INPUT = NEGATIVE_SEQUENCE_CURRENT_INPUT
    FUNCTION_CODE = FUNCTION_CODE
    FUNCTION_NAME = FUNCTION_NAME

    def __init__(
        self,
        relay: Any,
        *,
        element_id: str,
        relay_inputs: Mapping[str, RelayInput] | None = None,
        settings: NegativeSequenceOvercurrentSettings,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:
        if not isinstance(settings, NegativeSequenceOvercurrentSettings):
            raise TypeError(
                "settings must be a NegativeSequenceOvercurrentSettings instance."
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
        self._settings_46 = settings
        self.require_inputs(self.NEGATIVE_SEQUENCE_CURRENT_INPUT)

    @property
    def pickup(self) -> float:
        """Return the configured negative-sequence pickup threshold."""

        return self._settings_46.pickup

    def negative_sequence_current_signal(self) -> Any:
        """Read the live engineering negative-sequence current."""

        return self.get_input(self.NEGATIVE_SEQUENCE_CURRENT_INPUT).value

    def negative_sequence_current_value(self) -> float:
        """Return validated negative-sequence current magnitude."""

        value = self.negative_sequence_current_signal()
        if isinstance(value, bool):
            raise TypeError("Negative-sequence current measurement cannot be bool.")
        try:
            phasor = complex(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Negative-sequence current measurement must be numeric.") from exc
        if not math.isfinite(phasor.real) or not math.isfinite(phasor.imag):
            raise ValueError("Negative-sequence current measurement must be finite.")
        return abs(phasor)

    def _validate_input_semantics(self) -> None:
        """Ensure the authoritative channel is a negative-sequence current."""

        relay_input = self.get_input(self.NEGATIVE_SEQUENCE_CURRENT_INPUT)
        channel = relay_input.channel
        if channel.signal_type is not MeasurementSignalType.CURRENT:
            raise ValueError("ANSI 46 input must be a CURRENT measurement channel.")
        if channel.phase is not MeasurementPhase.NEGATIVE_SEQUENCE:
            raise ValueError(
                "ANSI 46 input must be designated as NEGATIVE_SEQUENCE."
            )

    def evaluate(self, context: ProtectionContext) -> ProtectionDecision:
        """Evaluate the ANSI 46 pickup criterion and return a decision."""

        timestamp = None if context is None else context.time
        if timestamp is not None:
            try:
                timestamp = float(timestamp)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Protection evaluation timestamp must be numeric."
                ) from exc
            if not math.isfinite(timestamp):
                raise ValueError(
                    "Protection evaluation timestamp must be finite."
                )

        if not self.operational:
            return self.no_operation(
                reason=self._inactive_reason(),
                timestamp=timestamp,
                operating_time=None,
            )

        try:
            self._validate_input_semantics()
            current = self.negative_sequence_current_value()
            usable = self.get_input(self.NEGATIVE_SEQUENCE_CURRENT_INPUT).usable
        except (TypeError, ValueError, AttributeError, KeyError) as exc:
            return self.invalid_decision(
                reason=f"Invalid negative-sequence current measurement: {exc}",
                timestamp=timestamp,
                metadata={"input": self.NEGATIVE_SEQUENCE_CURRENT_INPUT},
            )

        if not usable:
            return self.invalid_decision(
                reason="Negative-sequence current measurement is not usable.",
                timestamp=timestamp,
                metadata={
                    "input": self.NEGATIVE_SEQUENCE_CURRENT_INPUT,
                    "negative_sequence_current": current,
                    "pickup": self.pickup,
                },
            )

        metadata = {
            "negative_sequence_current": current,
            "pickup": self.pickup,
            "criterion": "|I2| >= pickup",
            "negative_sequence": True,
            "instantaneous": True,
        }
        if current < self.pickup:
            return self.no_operation(
                reason="Negative-sequence current below ANSI 46 pickup threshold.",
                timestamp=timestamp,
                operating_time=None,
                metadata=metadata,
            )

        return self.trip_decision(
            reason="ANSI 46 negative-sequence pickup threshold reached.",
            timestamp=timestamp,
            operating_time=0.0,
            metadata=metadata,
        )

    def _inactive_reason(self) -> str:
        if not self.enabled:
            return "ANSI 46 function is disabled."
        if self.blocked:
            return "ANSI 46 function is statically blocked."
        if not bool(getattr(self.relay, "operational", True)):
            return "Authoritative relay is not operational."
        return "ANSI 46 function is not operational."


__all__ = [
    "FUNCTION_CODE",
    "FUNCTION_NAME",
    "NEGATIVE_SEQUENCE_CURRENT_INPUT",
    "NegativeSequenceOvercurrentSettings",
    "NegativeSequenceOvercurrentRelay",
]
