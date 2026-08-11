```python
"""
GridForge IEC Inverse-Time Overcurrent Relay
=============================================

File:
    core/protection/overcurrent/iec_relay.py

Purpose
-------
IEC inverse-time overcurrent protection plugin.

Implements IEC inverse-time characteristics:

    - Normal / Standard Inverse
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
This class does not maintain an independent relay state.

The following remain owned by the authoritative Relay model:

    relay.current
    relay.pickup
    relay.trip
    relay.in_service

Protection-specific settings such as IEC curve selection and TMS
remain in this protection-layer class.

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
    IEC inverse-time overcurrent relay algorithm.

    Parameters
    ----------
    relay:
        Authoritative Relay model from core.model.relay.

    curve:
        IEC curve name.

        Supported values:

            "SI"
            "VI"
            "EI"

        The following descriptive aliases are also accepted:

            "NORMAL_INVERSE"
            "VERY_INVERSE"
            "EXTREMELY_INVERSE"

    TMS:
        IEC Time Multiplier Setting.

    Notes
    -----
    The pickup current is obtained directly from:

        relay.pickup

    The measured current is obtained directly from:

        relay.current

    No duplicate relay state is maintained here.
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

        curve = str(
            curve
        ).upper()

        if curve not in self.CURVE_ALIASES:
            raise ValueError(
                f"Unsupported IEC curve '{curve}'. "
                "Supported curves: "
                "SI, VI, EI, "
                "NORMAL_INVERSE, VERY_INVERSE, "
                "EXTREMELY_INVERSE."
            )

        self.curve = (
            self.CURVE_ALIASES[curve]
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
        Evaluate the relay pickup condition.

        The authoritative pickup setting is:

            relay.pickup

        The authoritative measurement is:

            relay.current
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

            None means the relay has not picked up.
        """

        if not self.relay.in_service:
            return None

        return iec_time(
            current=self.relay.current,
            pickup=self.relay.pickup,
            curve=self.curve,
            TMS=self.TMS,
        )

    # =============================================================
    # EVALUATION
    # =============================================================

    def evaluate(
        self,
    ) -> bool:
        """
        Evaluate the IEC overcurrent element.

        Returns
        -------
        bool
            True when the relay has an operating condition.

        Notes
        -----
        This method updates the authoritative Relay model's trip
        state through Relay.set_trip().

        Actual time-domain execution remains the responsibility
        of the protection/simulation layer.
        """

        if not self.relay.in_service:
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
        Reset the authoritative relay model.

        Protection-specific settings such as curve and TMS
        are retained.
        """

        self.relay.reset()

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(
        self,
    ) -> dict:
        """
        Return structured IEC relay information.
        """

        return {
            "relay_id": self.relay.id,
            "curve": self.curve,
            "TMS": self.TMS,
            "pickup": self.relay.pickup,
            "current": self.relay.current,
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
