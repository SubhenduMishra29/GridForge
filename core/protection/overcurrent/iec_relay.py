```python
"""
GridForge IEC Overcurrent Protection Function
==============================================

File:
    core/protection/overcurrent/iec_relay.py

Purpose
-------
Implements an IEC 60255 inverse-time overcurrent protection
function for GridForge V2.

Architectural Position
-----------------------

    CurrentTransformer
            |
            v
    MeasurementChannel
            |
            v
       RelayInput
            |
            v
       RelayBase
            |
            v
    IECOvercurrentRelay
            |
            v
    ProtectionSystem
            |
            v
      BreakerManager


Important V2 Principle
----------------------
This class represents a PROTECTION FUNCTION / ELEMENT.

It is not a second relay model.

A physical GridForge Relay may contain multiple protection
functions, for example:

    50       Instantaneous phase overcurrent
    51       IEC inverse-time overcurrent
    50N/50G  Instantaneous earth fault
    51N/51G  Earth-fault inverse time
    67       Directional overcurrent

Therefore this implementation deliberately does not assume that
one Relay object equals one protection algorithm.

Responsibilities
----------------
This module is responsible for:

    - consuming a configured current RelayInput;
    - validating the measurement signal;
    - evaluating pickup;
    - evaluating IEC inverse-time operation;
    - maintaining algorithm-specific timing state;
    - exposing protection-function status;
    - requesting the authoritative Relay protection state.

It does NOT:

    - create CTs;
    - create MeasurementChannels;
    - calculate fault current;
    - access Network topology;
    - perform load flow;
    - perform short-circuit calculations;
    - coordinate multiple relays;
    - operate breakers;
    - schedule system-wide protection events;
    - modify Relay configuration outside its supported API.

Timing Boundary
---------------
IEC inverse-time mathematics is provided by:

    core.protection.relay_functions

The protection function records elapsed operating time only when
a caller supplies a simulation/evaluation timestamp.

The class does not own the global simulation clock.

A higher-level simulation/protection event engine remains
responsible for actual event scheduling.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Optional

from core.protection.relay_base import RelayBase
from core.protection.relay_functions import (
    current_multiplier,
    iec_pickup,
    iec_time,
    normalize_iec_curve,
)


# =====================================================================
# DEFAULTS
# =====================================================================

DEFAULT_CURVE = "SI"
DEFAULT_TMS = 1.0


# =====================================================================
# ELEMENT SETTINGS
# =====================================================================


@dataclass(frozen=True)
class IECOvercurrentSettings:
    """
    Immutable settings for one IEC overcurrent protection element.

    Parameters
    ----------
    pickup:
        Pickup current in the measurement channel's configured
        engineering convention.

    curve:
        IEC inverse-time characteristic.

    TMS:
        Time Multiplier Setting.

    Notes
    -----
    This object contains algorithm settings.

    It does not replace the authoritative Relay model.
    """

    pickup: float
    curve: str = DEFAULT_CURVE
    TMS: float = DEFAULT_TMS

    def __post_init__(self) -> None:

        pickup = float(
            self.pickup
        )

        if not math.isfinite(
            pickup
        ) or pickup <= 0.0:
            raise ValueError(
                "pickup must be finite and positive."
            )

        curve = normalize_iec_curve(
            self.curve
        )

        TMS = float(
            self.TMS
        )

        if not math.isfinite(
            TMS
        ) or TMS < 0.0:
            raise ValueError(
                "TMS must be finite and >= 0."
            )

        # Dataclass is frozen, therefore canonicalize the curve
        # explicitly at construction time.
        object.__setattr__(
            self,
            "pickup",
            pickup,
        )

        object.__setattr__(
            self,
            "curve",
            curve,
        )

        object.__setattr__(
            self,
            "TMS",
            TMS,
        )


# =====================================================================
# IEC OVERCURRENT RELAY
# =====================================================================


class IECOvercurrentRelay(RelayBase):
    """
    GridForge V2 IEC inverse-time overcurrent protection function.

    Parameters
    ----------
    relay:
        Authoritative GridForge Relay model.

    relay_inputs:
        Mapping containing the current RelayInput.

        By default the function expects:

            "current"

        Example:

            IECOvercurrentRelay(
                relay=relay,
                relay_inputs={
                    "current": current_input,
                },
                settings=IECOvercurrentSettings(
                    pickup=5.0,
                    curve="SI",
                    TMS=0.10,
                ),
            )

    settings:
        IEC overcurrent element settings.

    Notes
    -----
    The protection function reads the current from RelayInput.

    It does not read:

        relay.current

    and does not calculate current itself.
    """

    CURRENT_INPUT = "current"

    # ================================================================
    # INITIALIZATION
    # ================================================================

    def __init__(
        self,
        relay: Any,
        relay_inputs: Optional[
            dict[str, Any]
        ] = None,
        *,
        settings: IECOvercurrentSettings,
    ) -> None:

        super().__init__(
            relay=relay,
            relay_inputs=relay_inputs,
        )

        if not isinstance(
            settings,
            IECOvercurrentSettings,
        ):
            raise TypeError(
                "settings must be an "
                "IECOvercurrentSettings instance."
            )

        self.settings = settings

        # Algorithm-specific transient state.
        #
        # This is deliberately NOT duplicated Relay state.
        self._pickup_start_time: float | None = None
        self._last_timestamp: float | None = None
        self._last_current: float | None = None
        self._last_operating_time: float = math.inf

        self.require_inputs(
            self.CURRENT_INPUT
        )

    # ================================================================
    # SETTINGS
    # ================================================================

    @property
    def pickup(self) -> float:
        """Return configured element pickup."""

        return self.settings.pickup

    @property
    def curve(self) -> str:
        """Return canonical IEC curve identifier."""

        return self.settings.curve

    @property
    def TMS(self) -> float:
        """Return configured Time Multiplier Setting."""

        return self.settings.TMS

    # ================================================================
    # MEASUREMENT
    # ================================================================

    def current_signal(self) -> Any:
        """
        Obtain the current signal from the configured RelayInput.

        No measurement is cached by this method.
        """

        return self.input_signal(
            self.CURRENT_INPUT
        )

    # ---------------------------------------------------------------

    def current_value(self) -> float:
        """
        Return a validated scalar current magnitude.

        Complex current values are accepted because protection
        measurement chains may expose phasors.

        For the IEC magnitude characteristic, abs(I) is used.
        """

        value = self.current_signal()

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                "Current measurement cannot be bool."
            )

        try:
            value = complex(
                value
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Current measurement must be numeric."
            ) from exc

        if not (
            math.isfinite(value.real)
            and math.isfinite(value.imag)
        ):
            raise ValueError(
                "Current measurement must be finite."
            )

        return abs(value)

    # ================================================================
    # PICKUP
    # ================================================================

    def check_pickup(self) -> bool:
        """
        Evaluate the IEC overcurrent pickup criterion.

        Returns
        -------
        bool
            True when measured current exceeds pickup.
        """

        current = self.current_value()

        return iec_pickup(
            current=current,
            pickup=self.pickup,
        )

    # ================================================================
    # CURRENT MULTIPLE
    # ================================================================

    def current_multiple(self) -> float:
        """
        Return current multiple M.
        """

        return current_multiplier(
            current=self.current_value(),
            pickup=self.pickup,
        )

    # ================================================================
    # OPERATING TIME
    # ================================================================

    def operating_time(
        self,
    ) -> float:
        """
        Calculate the instantaneous IEC characteristic operating
        time for the present current.

        Returns math.inf when the element is not picked up.
        """

        current = self.current_value()

        return iec_time(
            current=current,
            pickup=self.pickup,
            curve=self.curve,
            TMS=self.TMS,
        )

    # ================================================================
    # EVALUATION
    # ================================================================

    def evaluate(
        self,
        *,
        timestamp: float | None = None,
    ) -> bool:
        """
        Evaluate one IEC overcurrent protection cycle.

        Parameters
        ----------
        timestamp:
            Optional simulation/event timestamp.

        Behaviour
        ---------
        The method:

            1. validates service state;
            2. reads current from RelayInput;
            3. evaluates pickup;
            4. calculates IEC operating time;
            5. records algorithm-specific timing state;
            6. updates the authoritative Relay protection state.

        Important
        ---------
        This method does not operate a breaker.

        The returned bool represents the protection function's
        instantaneous decision boundary.

        Actual delayed event execution belongs to the higher-level
        protection/simulation event layer.
        """

        if timestamp is not None:
            timestamp = self._validate_timestamp(
                timestamp
            )

        self._last_timestamp = timestamp

        if not self.in_service:

            self._last_current = None
            self._last_operating_time = math.inf
            self._pickup_start_time = None

            self.set_pickup(False)
            self.set_operated(False)
            self.reset_trip()

            return False

        current = self.current_value()

        self._last_current = current

        picked_up = iec_pickup(
            current=current,
            pickup=self.pickup,
        )

        self.set_pickup(
            picked_up
        )

        if not picked_up:

            self._last_operating_time = math.inf
            self._pickup_start_time = None

            self.set_operated(False)
            self.reset_trip()

            return False

        self._last_operating_time = iec_time(
            current=current,
            pickup=self.pickup,
            curve=self.curve,
            TMS=self.TMS,
        )

        if timestamp is not None:

            if self._pickup_start_time is None:
                self._pickup_start_time = timestamp

        self.set_operated(
            True
        )

        # Relay trip state represents a protection decision.
        #
        # Delayed event execution is intentionally outside this
        # class. A caller requiring time-domain operation should
        # use the calculated operating time with the event layer.
        self.trip()

        return True

    # ================================================================
    # RESET
    # ================================================================

    def reset(
        self,
    ) -> None:
        """
        Reset the IEC overcurrent element.
        """

        super().reset()

        self._pickup_start_time = None
        self._last_timestamp = None
        self._last_current = None
        self._last_operating_time = math.inf

    # ================================================================
    # TIMING STATE
    # ================================================================

    @property
    def pickup_start_time(self) -> float | None:
        """
        Return the timestamp at which pickup was first observed
        during the current pickup interval.
        """

        return self._pickup_start_time

    @property
    def last_timestamp(self) -> float | None:
        """
        Return the last evaluation timestamp.
        """

        return self._last_timestamp

    @property
    def last_current(self) -> float | None:
        """
        Return the last sampled current magnitude.

        This is algorithm diagnostic state, not an authoritative
        measurement state.
        """

        return self._last_current

    @property
    def last_operating_time(self) -> float:
        """
        Return the most recently calculated IEC operating time.
        """

        return self._last_operating_time

    # ================================================================
    # STATUS
    # ================================================================

    def status(self) -> dict[str, Any]:
        """
        Return protection-function diagnostic status.
        """

        result = super().status()

        result.update(
            {
                "function": (
                    "IEC_OVERCURRENT"
                ),
                "pickup": self.pickup,
                "curve": self.curve,
                "TMS": self.TMS,
                "current": self._last_current,
                "current_multiple": (
                    self.current_multiple()
                    if self._last_current is not None
                    else None
                ),
                "operating_time": (
                    self._last_operating_time
                ),
                "pickup_start_time": (
                    self._pickup_start_time
                ),
                "last_timestamp": (
                    self._last_timestamp
                ),
            }
        )

        return result

    # ================================================================
    # VALIDATION
    # ================================================================

    @staticmethod
    def _validate_timestamp(
        timestamp: float,
    ) -> float:
        """
        Validate an evaluation timestamp.
        """

        try:
            timestamp = float(
                timestamp
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "timestamp must be numeric."
            ) from exc

        if not math.isfinite(
            timestamp
        ):
            raise ValueError(
                "timestamp must be finite."
            )

        return timestamp


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "IECOvercurrentSettings",
    "IECOvercurrentRelay",
]
```
