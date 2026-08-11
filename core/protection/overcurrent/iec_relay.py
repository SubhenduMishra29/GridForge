```python
"""
GridForge IEC Inverse-Time Overcurrent Relay
=============================================

File:
    core/protection/overcurrent/iec_relay.py

Purpose
-------
IEC inverse-time overcurrent protection algorithm.

Implements IEC inverse-time characteristics:

    - Standard / Normal Inverse
    - Very Inverse
    - Extremely Inverse

The authoritative relay device model is:

    core/model/relay.py

The common protection interface is:

    core/protection/relay_base.py

IEC curve mathematics are provided by:

    core/protection/relay_functions.py

Architecture
------------

    core/model/relay.py
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
            |
            v
    core/model/breaker.py

Important
---------
This class does NOT maintain an independent relay state.

The following remain owned by the authoritative Relay model:

    relay.id
    relay.type
    relay.pickup
    relay.current
    relay.voltage
    relay.impedance
    relay.in_service
    relay.trip
    relay.time_delay

Protection-specific settings such as IEC curve selection and TMS
remain in this protection-layer class.

The IEC operating-time calculation does not directly operate a
circuit breaker. Breaker operation belongs to:

    ProtectionSystem
        ->
    BreakerManager
        ->
    Breaker

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from typing import Optional

from core.protection.relay_base import RelayBase
from core.protection.relay_functions import iec_time


class IECOvercurrentRelay(RelayBase):
    """
    IEC inverse-time overcurrent protection algorithm.

    Parameters
    ----------
    relay:
        Authoritative Relay object from core.model.relay.

    curve:
        IEC inverse-time characteristic.

        Supported values:

            SI
            VI
            EI

        Descriptive aliases:

            STANDARD_INVERSE
            NORMAL_INVERSE
            VERY_INVERSE
            EXTREMELY_INVERSE

    TMS:
        Time Multiplier Setting.

    Notes
    -----
    Pickup current is obtained from:

        relay.pickup

    Measured current is obtained from:

        relay.current

    No independent pickup/current/trip state is maintained here.
    """

    # =============================================================
    # IEC CURVE ALIASES
    # =============================================================

    CURVE_ALIASES = {
        "SI": "SI",
        "STANDARD_INVERSE": "SI",
        "NORMAL_INVERSE": "SI",

        "VI": "VI",
        "VERY_INVERSE": "VI",

        "EI": "EI",
        "EXTREMELY_INVERSE": "EI",
    }

    VALID_CURVES = frozenset(
        {
            "SI",
            "VI",
            "EI",
        }
    )

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        relay,
        curve: str = "SI",
        TMS: float = 1.0,
    ) -> None:
        """
        Initialize the IEC overcurrent protection algorithm.
        """

        super().__init__(
            relay
        )

        curve_name = str(
            curve
        ).upper()

        if curve_name not in self.CURVE_ALIASES:
            raise ValueError(
                f"Unsupported IEC curve '{curve_name}'. "
                "Supported curves: "
                "SI, VI, EI, "
                "STANDARD_INVERSE, NORMAL_INVERSE, "
                "VERY_INVERSE, EXTREMELY_INVERSE."
            )

        self.curve = (
            self.CURVE_ALIASES[curve_name]
        )

        self.TMS = float(
            TMS
        )

        if self.TMS < 0.0:
            raise ValueError(
                "TMS must be >= 0."
            )

    # =============================================================
    # PICKUP CHECK
    # =============================================================

    def check_pickup(
        self,
    ) -> bool:
        """
        Evaluate the authoritative relay pickup condition.

        Returns
        -------
        bool
            True when measured current exceeds pickup current.
        """

        if not self.relay.in_service:
            return False

        if self.relay.pickup <= 0.0:
            return False

        return (
            abs(self.relay.current)
            > self.relay.pickup
        )

    # =============================================================
    # OPERATING TIME
    # =============================================================

    def operating_time(
        self,
    ) -> Optional[float]:
        """
        Calculate IEC inverse-time operating time.

        Returns
        -------
        float or None
            Operating time in seconds.

            None:
                Relay is out of service or below pickup.

        Notes
        -----
        The IEC calculation is delegated to:

            core.protection.relay_functions.iec_time

        The authoritative relay pickup and current values are used
        directly from the Relay model.
        """

        if not self.relay.in_service:
            return None

        if self.relay.pickup <= 0.0:
            return None

        return iec_time(
            abs(self.relay.current),
            self.relay.pickup,
            self.curve,
            self.TMS,
        )

    # =============================================================
    # EVALUATION
    # =============================================================

    def evaluate(
        self,
    ) -> bool:
        """
        Evaluate the IEC overcurrent protection element.

        Returns
        -------
        bool
            True when the relay is above pickup and therefore has
            an IEC operating condition.

        Important
        ---------
        This method establishes the protection operating decision.

        The IEC operating time is calculated separately by
        operating_time().

        Actual delayed breaker operation belongs to the higher-level
        protection/simulation layer.
        """

        if not self.relay.in_service:

            self.relay.set_trip(
                False
            )

            return False

        if not self.check_pickup():

            self.relay.set_trip(
                False
            )

            return False

        operating_time = (
            self.operating_time()
        )

        if operating_time is None:
            self.relay.set_trip(
                False
            )
            return False

        if operating_time == float("inf"):

            self.relay.set_trip(
                False
            )

            return False

        self.relay.set_trip(
            True
        )

        return True

    # =============================================================
    # RESET
    # =============================================================

    def reset(
        self,
    ) -> None:
        """
        Reset the authoritative Relay operating state.

        IEC curve and TMS settings are retained.
        """

        self.relay.reset()

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(
        self,
    ) -> dict:
        """
        Return structured IEC overcurrent information.
        """

        return {
            "relay_id": self.relay.id,
            "relay_type": self.relay.type,
            "curve": self.curve,
            "TMS": self.TMS,
            "pickup": self.relay.pickup,
            "current": self.relay.current,
            "operating_time": self.operating_time(),
            "in_service": self.relay.in_service,
            "trip": self.relay.trip,
        }

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(
        self,
    ) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<IECOvercurrentRelay "
            f"relay={self.relay.id}, "
            f"curve={self.curve}, "
            f"pickup={self.relay.pickup:.6f}, "
            f"TMS={self.TMS:.6f}, "
            f"trip={self.relay.trip}>"
        )


__all__ = [
    "IECOvercurrentRelay",
]
```
