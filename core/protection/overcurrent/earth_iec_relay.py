# ============================================================
# File: core/protection/overcurrent/earth_iec_relay.py
# GridForge V2 — ANSI 51N Earth Inverse-Time Overcurrent
# Author: Subhendu Mishra
# ============================================================

"""Canonical ANSI 51N residual/earth inverse-time overcurrent function.

The IEC inverse-time mathematics remains centralized in the canonical
51 implementation. This specialization changes only the protection
identity and measurement binding from phase current to residual current.
"""

from __future__ import annotations

from typing import Any

from core.protection.overcurrent.iec_relay import (
    IECOvercurrentRelay,
    IECOvercurrentSettings,
)


FUNCTION_CODE = "51N"
FUNCTION_NAME = "IEC EARTH INVERSE-TIME OVERCURRENT"
RESIDUAL_CURRENT_INPUT = "residual_current"


EarthIECOvercurrentSettings = IECOvercurrentSettings


class EarthIECOvercurrentRelay(IECOvercurrentRelay):
    """IEC 51N inverse-time earth-fault overcurrent function.

    Residual current is consumed exclusively through the explicit
    ``residual_current`` RelayInput. The inherited IEC 51 timing,
    pickup, validation, latching, and reset semantics are retained.
    """

    CURRENT_INPUT = RESIDUAL_CURRENT_INPUT
    FUNCTION_CODE = FUNCTION_CODE
    FUNCTION_NAME = FUNCTION_NAME

    def current_signal(self) -> Any:
        """Read residual current exclusively through RelayInput."""
        relay_input = self.get_input(self.CURRENT_INPUT)
        if hasattr(relay_input, "value"):
            value = getattr(relay_input, "value")
            return value() if callable(value) else value
        if hasattr(relay_input, "signal"):
            signal = getattr(relay_input, "signal")
            return signal() if callable(signal) else signal
        if hasattr(relay_input, "read"):
            return relay_input.read()
        raise AttributeError(
            "RelayInput does not expose a supported residual-current accessor."
        )

    def residual_current_value(self) -> float:
        """Return the validated magnitude of the residual current."""
        return self.current_value()


__all__ = [
    "FUNCTION_CODE",
    "FUNCTION_NAME",
    "RESIDUAL_CURRENT_INPUT",
    "EarthIECOvercurrentSettings",
    "EarthIECOvercurrentRelay",
]
