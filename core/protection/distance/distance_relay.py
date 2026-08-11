```python
"""
GridForge Distance Relay
========================

File:
    core/protection/distance/distance_relay.py

Purpose
-------
Transmission-line impedance protection algorithm.

Functions
---------
- Calculate apparent impedance.
- Determine active protection zone.
- Determine pickup condition.
- Determine operating time.
- Set the authoritative Relay trip state.

The authoritative relay device model is:

    core/model/relay.py

The common protection interface is:

    core/protection/relay_base.py

This module does NOT:
- Calculate system-wide faults.
- Operate circuit breakers.
- Coordinate multiple relays.
- Modify the network model.

Future extensions
-----------------
- Mho characteristic
- Quadrilateral characteristic
- Load encroachment
- Power swing blocking
- Out-of-step protection

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

import cmath
from typing import Optional

from core.protection.relay_base import RelayBase


class DistanceRelay(RelayBase):
    """
    Distance protection algorithm.

    Parameters
    ----------
    relay:
        Authoritative Relay model from core.model.relay.

    zone1_reach:
        Zone-1 impedance reach.

    zone2_reach:
        Zone-2 impedance reach.

    zone3_reach:
        Zone-3 impedance reach.

    zone1_time:
        Zone-1 operating time in seconds.

    zone2_time:
        Zone-2 operating time in seconds.

    zone3_time:
        Zone-3 operating time in seconds.

    Notes
    -----
    Zone settings belong to the protection algorithm layer.

    Relay identity, measurements and trip state remain owned by
    core.model.relay.Relay.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        relay,
        zone1_reach: complex,
        zone2_reach: complex,
        zone3_reach: complex,
        zone1_time: float = 0.0,
        zone2_time: float = 0.3,
        zone3_time: float = 1.0,
    ) -> None:

        super().__init__(
            relay
        )

        self.zone1_reach = complex(
            zone1_reach
        )

        self.zone2_reach = complex(
            zone2_reach
        )

        self.zone3_reach = complex(
            zone3_reach
        )

        self.zone_times = {
            "ZONE1": float(
                zone1_time
            ),
            "ZONE2": float(
                zone2_time
            ),
            "ZONE3": float(
                zone3_time
            ),
        }

        self.active_zone: Optional[
            str
        ] = None

        self._validate_settings()

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_settings(
        self,
    ) -> None:
        """
        Validate distance-zone settings.
        """

        reaches = {
            "zone1_reach": self.zone1_reach,
            "zone2_reach": self.zone2_reach,
            "zone3_reach": self.zone3_reach,
        }

        for name, reach in reaches.items():

            if abs(reach) <= 0.0:
                raise ValueError(
                    f"{name} must be non-zero."
                )

        if not (
            abs(self.zone1_reach)
            < abs(self.zone2_reach)
            < abs(self.zone3_reach)
        ):
            raise ValueError(
                "Distance zone reaches must satisfy "
                "|Z1| < |Z2| < |Z3|."
            )

        for zone, operating_time in (
            self.zone_times.items()
        ):

            if operating_time < 0.0:
                raise ValueError(
                    f"{zone} operating time "
                    "must be >= 0."
                )

    # =============================================================
    # IMPEDANCE MEASUREMENT
    # =============================================================

    @staticmethod
    def calculate_impedance(
        voltage,
        current,
    ) -> complex:
        """
        Calculate apparent impedance:

            Z = V / I

        Parameters
        ----------
        voltage:
            Measured voltage phasor.

        current:
            Measured current phasor.

        Returns
        -------
        complex
            Apparent impedance.

        Notes
        -----
        Near-zero current is treated as infinite impedance.
        """

        if abs(current) < 1e-12:
            return complex(
                float("inf"),
                0.0,
            )

        return complex(
            voltage / current
        )

    # =============================================================
    # MEASUREMENT UPDATE
    # =============================================================

    def measure(
        self,
        voltage,
        current,
    ) -> complex:
        """
        Calculate apparent impedance and update the
        authoritative Relay model.

        Returns
        -------
        complex
            Calculated apparent impedance.
        """

        impedance = (
            self.calculate_impedance(
                voltage,
                current,
            )
        )

        self.relay.measure(
            voltage=abs(voltage),
            current=abs(current),
            impedance=impedance,
        )

        return impedance

    # =============================================================
    # ZONE DETECTION
    # =============================================================

    def check_zone(
        self,
    ) -> Optional[str]:
        """
        Determine the active distance protection zone.

        The current implementation uses impedance magnitude
        comparison.

        Returns
        -------
        str or None
            ZONE1, ZONE2, ZONE3 or None.
        """

        Z = abs(
            self.relay.impedance
        )

        if Z <= abs(
            self.zone1_reach
        ):

            self.active_zone = "ZONE1"

        elif Z <= abs(
            self.zone2_reach
        ):

            self.active_zone = "ZONE2"

        elif Z <= abs(
            self.zone3_reach
        ):

            self.active_zone = "ZONE3"

        else:

            self.active_zone = None

        return self.active_zone

    # =============================================================
    # PICKUP
    # =============================================================

    def check_pickup(
        self,
    ) -> bool:
        """
        Determine whether the distance element has picked up.

        Pickup occurs when the apparent impedance falls inside
        one of the configured protection zones.
        """

        if not self.relay.in_service:
            return False

        return (
            self.check_zone()
            is not None
        )

    # =============================================================
    # OPERATING TIME
    # =============================================================

    def operating_time(
        self,
    ) -> Optional[float]:
        """
        Return operating time for the active zone.

        Returns
        -------
        float or None
            Zone operating time, or None when no zone operates.
        """

        if self.active_zone is None:
            self.check_zone()

        if self.active_zone is None:
            return None

        return self.zone_times[
            self.active_zone
        ]

    # =============================================================
    # EVALUATION
    # =============================================================

    def evaluate(
        self,
    ) -> bool:
        """
        Evaluate the distance protection element.

        Returns
        -------
        bool
            True when the distance element operates.

        Notes
        -----
        The method sets the trip state on the authoritative
        Relay model.

        Actual time-domain delay execution belongs to the
        protection/simulation layer.
        """

        if not self.relay.in_service:

            self.active_zone = None

            self.relay.set_trip(
                False
            )

            return False

        zone = self.check_zone()

        if zone is None:

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
        Reset relay operating state.

        Protection settings are retained.
        """

        self.active_zone = None

        self.relay.reset()

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(
        self,
    ) -> dict:
        """
        Return structured distance-relay information.
        """

        return {
            "relay_id": self.relay.id,
            "zone1_reach": self.zone1_reach,
            "zone2_reach": self.zone2_reach,
            "zone3_reach": self.zone3_reach,
            "zone1_time": self.zone_times["ZONE1"],
            "zone2_time": self.zone_times["ZONE2"],
            "zone3_time": self.zone_times["ZONE3"],
            "impedance": self.relay.impedance,
            "active_zone": self.active_zone,
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
            f"<DistanceRelay "
            f"relay={self.relay.id}, "
            f"zone={self.active_zone}, "
            f"Z={self.relay.impedance}>"
        )


__all__ = [
    "DistanceRelay",
]
```
