```python
"""
GridForge IEC Overcurrent Protection
====================================

File:
    core/protection/overcurrent/iec_relay.py

Purpose
-------
IEC 60255 overcurrent protection-function implementation for the
GridForge V2 protection architecture.

Architecture
------------

    CT / Measurement Source
            |
            v
    MeasurementChannel
            |
            v
        RelayInput
            |
            v
      IECOvercurrentRelay
            |
            v
     ProtectionElement
            |
            v
     ProtectionSystem
            |
            v
      BreakerManager

The authoritative physical/configuration/state object remains:

    core.model.relay.Relay

This class is a protection-function implementation and is NOT a
second Relay model.

Design Principles
-----------------
- Electrical signals are consumed through RelayInput.
- MeasurementChannel remains authoritative for measurement state.
- IEC mathematics is delegated to relay_functions.py.
- RelayBase owns the common protection execution contract.
- Relay model owns relay-level protection state.
- ProtectionElement owns multifunction-relay composition.
- ProtectionSystem owns system-level orchestration.
- BreakerManager owns physical breaker operation.

Supported Operating Modes
--------------------------
INVERSE
    IEC inverse-time characteristic.

DEFINITE_TIME
    Fixed operating delay after pickup.

INSTANTANEOUS
    Immediate operation after pickup.

IEC Curves
----------
SI
    Standard / Normal Inverse.

VI
    Very Inverse.

EI
    Extremely Inverse.

Future Extension
----------------
The class deliberately separates:

    pickup
    curve
    TMS
    operating mode
    definite-time delay
    instantaneous pickup

This allows future extension toward:

- IEC 60255 variants;
- ANSI/IEEE inverse curves;
- high-set stages;
- low-set/high-set protection;
- phase-specific elements;
- residual/earth-fault elements;
- directional supervision;
- blocking;
- breaker-failure interaction;
- event/time-domain execution.

Those features should be added as separate capabilities rather than
turning this class into a monolithic protection system.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from enum import Enum
from math import isfinite
from typing import Any, Optional

from ..relay_base import RelayBase
from ..relay_functions import (
    current_multiplier,
    iec_pickup,
    iec_time,
    normalize_iec_curve,
)


# =====================================================================
# OPERATING MODE
# =====================================================================


class OvercurrentOperatingMode(Enum):
    """
    Operating characteristic of an overcurrent protection element.
    """

    INVERSE = "INVERSE"
    DEFINITE_TIME = "DEFINITE_TIME"
    INSTANTANEOUS = "INSTANTANEOUS"


# =====================================================================
# IEC OVERCURRENT RELAY
# =====================================================================


class IECOvercurrentRelay(RelayBase):
    """
    GridForge IEC inverse-time overcurrent protection function.

    Parameters
    ----------
    relay:
        Authoritative GridForge Relay model.

    relay_inputs:
        Mapping containing the measurement inputs required by this
        function.

        By default the function expects:

            "current"

        The associated RelayInput must expose the signal supplied by
        the measurement architecture.

    pickup:
        Pickup current in the same engineering convention as the
        current MeasurementChannel.

    curve:
        IEC curve identifier.

        Supported:

            SI
            VI
            EI

    TMS:
        IEC Time Multiplier Setting.

    mode:
        Protection operating mode.

    definite_time:
        Operating delay in seconds when ``mode`` is
        ``DEFINITE_TIME``.

    name:
        Optional protection-function name.

    Notes
    -----
    The class does not read:

        relay.current

    and does not directly access a CT/PT/CVT.

    The current must arrive through:

        RelayInput -> MeasurementChannel
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        relay: Any,
        relay_inputs: Optional[dict[str, Any]] = None,
        *,
        pickup: float,
        curve: str = "SI",
        TMS: float = 1.0,
        mode: OvercurrentOperatingMode = (
            OvercurrentOperatingMode.INVERSE
        ),
        definite_time: float = 0.0,
    ) -> None:

        super().__init__(
            relay=relay,
            relay_inputs=relay_inputs,
        )

        self.require_inputs(
            "current"
        )

        self.pickup = self._validate_pickup(
            pickup
        )

        self.curve = normalize_iec_curve(
            curve
        )

        self.TMS = self._validate_nonnegative(
            TMS,
            "TMS",
        )

        if not isinstance(
            mode,
            OvercurrentOperatingMode,
        ):
            raise TypeError(
                "mode must be an "
                "OvercurrentOperatingMode."
            )

        self.mode = mode

        self.definite_time = (
            self._validate_nonnegative(
                definite_time,
                "definite_time",
            )
        )

        # -------------------------------------------------------------
        # Function-specific transient information.
        #
        # These are NOT duplicate Relay states.
        # -------------------------------------------------------------

        self._last_current: float | None = None
        self._last_multiple: float | None = None
        self._last_operating_time: float | None = None
        self._last_measurement_valid: bool = False

    # =================================================================
    # VALIDATION
    # =================================================================

    @staticmethod
    def _validate_pickup(
        pickup: float,
    ) -> float:
        """
        Validate overcurrent pickup.
        """

        pickup = float(
            pickup
        )

        if not isfinite(pickup):
            raise ValueError(
                "pickup must be finite."
            )

        if pickup <= 0.0:
            raise ValueError(
                "pickup must be positive."
            )

        return pickup

    # -----------------------------------------------------------------

    @staticmethod
    def _validate_nonnegative(
        value: float,
        name: str,
    ) -> float:
        """
        Validate a finite non-negative numerical setting.
        """

        value = float(
            value
        )

        if not isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        if value < 0.0:
            raise ValueError(
                f"{name} must be >= 0."
            )

        return value

    # =================================================================
    # SETTINGS
    # =================================================================

    def set_pickup(
        self,
        pickup: float,
    ) -> None:
        """
        Set the protection-function pickup setting.

        This is algorithm configuration.

        It is intentionally separate from RelayBase.set_pickup(),
        which controls the relay's protection operating state.
        """

        self.pickup = self._validate_pickup(
            pickup
        )

    # -----------------------------------------------------------------

    def set_curve(
        self,
        curve: str,
    ) -> None:
        """
        Set the IEC characteristic.
        """

        self.curve = normalize_iec_curve(
            curve
        )

    # -----------------------------------------------------------------

    def set_TMS(
        self,
        TMS: float,
    ) -> None:
        """
        Set the IEC Time Multiplier Setting.
        """

        self.TMS = self._validate_nonnegative(
            TMS,
            "TMS",
        )

    # -----------------------------------------------------------------

    def set_mode(
        self,
        mode: OvercurrentOperatingMode,
    ) -> None:
        """
        Set the operating mode.
        """

        if not isinstance(
            mode,
            OvercurrentOperatingMode,
        ):
            raise TypeError(
                "mode must be an "
                "OvercurrentOperatingMode."
            )

        self.mode = mode

    # -----------------------------------------------------------------

    def set_definite_time(
        self,
        delay: float,
    ) -> None:
        """
        Set definite-time operating delay.
        """

        self.definite_time = (
            self._validate_nonnegative(
                delay,
                "definite_time",
            )
        )

    # =================================================================
    # MEASUREMENT ACCESS
    # =================================================================

    def current_signal(self) -> Any:
        """
        Return the current supplied by the configured current
        RelayInput.

        The signal remains owned by the measurement architecture.
        """

        return self.input_signal(
            "current"
        )

    # -----------------------------------------------------------------

    def _extract_current(
        self,
    ) -> float:
        """
        Extract a scalar current magnitude from the configured
        measurement signal.

        Complex current is supported because protection simulations
        commonly represent phasors.

        The magnitude is used for IEC overcurrent pickup.
        """

        signal = self.current_signal()

        # -------------------------------------------------------------
        # RelayInput / MeasurementChannel validity
        # -------------------------------------------------------------

        input_object = self.get_input(
            "current"
        )

        channel = getattr(
            input_object,
            "channel",
            None,
        )

        if channel is None:
            channel = getattr(
                input_object,
                "measurement_channel",
                None,
            )

        if channel is not None:

            usable = getattr(
                channel,
                "is_usable",
                None,
            )

            if usable is not None:

                if callable(usable):
                    usable = usable()

                if not bool(usable):
                    raise ValueError(
                        f"Current measurement channel for "
                        f"relay '{self.id}' is not usable."
                    )

        # -------------------------------------------------------------
        # Signal conversion
        # -------------------------------------------------------------

        if isinstance(
            signal,
            bool,
        ):
            raise TypeError(
                "Current measurement cannot be bool."
            )

        try:
            if isinstance(
                signal,
                complex,
            ):
                current = abs(signal)
            else:
                current = abs(
                    float(signal)
                )
        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"Current measurement for relay "
                f"'{self.id}' is not numeric."
            ) from exc

        if not isfinite(current):
            raise ValueError(
                "Current measurement must be finite."
            )

        return current

    # =================================================================
    # PICKUP
    # =================================================================

    def check_pickup(self) -> bool:
        """
        Evaluate the instantaneous overcurrent pickup criterion.

        Returns
        -------
        bool
            True when measured current is strictly above pickup.

        Notes
        -----
        Measurement validity is part of the protection boundary.

        An unavailable/invalid signal must not produce a protection
        operation.
        """

        try:
            current = self._extract_current()

        except (
            TypeError,
            ValueError,
        ):

            self._last_current = None
            self._last_multiple = None
            self._last_measurement_valid = False

            return False

        self._last_current = current

        self._last_multiple = (
            current_multiplier(
                current,
                self.pickup,
            )
        )

        self._last_measurement_valid = True

        return iec_pickup(
            current,
            self.pickup,
        )

    # =================================================================
    # OPERATING TIME
    # =================================================================

    @property
    def operating_time(self) -> float:
        """
        Calculate the current protection operating time.

        Returns
        -------
        float
            Operating time in seconds.

            math.inf indicates that pickup has not occurred.

        Notes
        -----
        This property performs a numerical calculation from the
        latest measurement.

        It does not schedule an event or operate a breaker.
        """

        if (
            self._last_current is None
            or not self._last_measurement_valid
        ):
            return float("inf")

        current = self._last_current

        if not iec_pickup(
            current,
            self.pickup,
        ):
            return float("inf")

        if (
            self.mode
            == OvercurrentOperatingMode.INSTANTANEOUS
        ):
            return 0.0

        if (
            self.mode
            == OvercurrentOperatingMode.DEFINITE_TIME
        ):
            return self.definite_time

        return iec_time(
            current=current,
            pickup=self.pickup,
            curve=self.curve,
            TMS=self.TMS,
        )

    # =================================================================
    # EVALUATION
    # =================================================================

    def evaluate(
        self,
    ) -> bool:
        """
        Execute one overcurrent protection evaluation cycle.

        The method:

        1. validates service state;
        2. obtains the current from RelayInput;
        3. evaluates pickup;
        4. calculates operating time;
        5. updates the authoritative Relay protection state.

        It does NOT schedule delayed operation.

        A non-zero operating time is returned through
        ``operating_time`` and must be handled by the appropriate
        protection-event/simulation layer.
        """

        if not self.in_service:

            self.set_pickup(
                False
            )

            self.set_operated(
                False
            )

            self.reset_trip()

            self._last_measurement_valid = False

            return False

        operates = self.check_pickup()

        self.set_pickup(
            operates
        )

        # -------------------------------------------------------------
        # The base execution decision represents pickup/operation of
        # the protection element for this evaluation instant.
        #
        # Actual intentional delay must be handled externally.
        # -------------------------------------------------------------

        self.set_operated(
            operates
        )

        if operates:

            self._last_operating_time = (
                self.operating_time
            )

            # Instantaneous operation can assert trip immediately.
            #
            # Inverse/definite-time elements expose their delay to
            # the event/simulation layer rather than pretending that
            # a delayed trip occurred at this instant.
            if (
                self._last_operating_time
                == 0.0
            ):
                self.trip()
            else:
                self.reset_trip()

        else:

            self._last_operating_time = float(
                "inf"
            )

            self.reset_trip()

        return operates

    # =================================================================
    # RESET
    # =================================================================

    def reset(
        self,
    ) -> None:
        """
        Reset relay-level and algorithm-specific transient state.
        """

        super().reset()

        self._last_current = None
        self._last_multiple = None
        self._last_operating_time = None
        self._last_measurement_valid = False

    # =================================================================
    # STATUS
    # =================================================================

    def status(
        self,
    ) -> dict[str, Any]:
        """
        Return structured IEC overcurrent protection status.
        """

        status = super().status()

        status.update(
            {
                "function": "IEC_OVERCURRENT",
                "pickup_setting": self.pickup,
                "curve": self.curve,
                "TMS": self.TMS,
                "mode": self.mode.value,
                "definite_time": (
                    self.definite_time
                ),
                "last_current": (
                    self._last_current
                ),
                "current_multiple": (
                    self._last_multiple
                ),
                "operating_time": (
                    self._last_operating_time
                ),
                "measurement_valid": (
                    self._last_measurement_valid
                ),
            }
        )

        return status

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
        """

        return (
            f"<IECOvercurrentRelay "
            f"relay_id={self.id}, "
            f"pickup={self.pickup}, "
            f"curve={self.curve}, "
            f"TMS={self.TMS}, "
            f"mode={self.mode.value}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "OvercurrentOperatingMode",
    "IECOvercurrentRelay",
]
```
