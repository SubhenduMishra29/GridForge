```python
"""
GridForge Directional Relay
===========================

File:
    core/protection/directional/directional_relay.py

Purpose
-------
Directional protection element.

Functions
---------
- Current pickup
- Directional decision
- Forward/reverse discrimination
- Trip permission

The authoritative relay device model is:

    core/model/relay.py

The common protection interface is:

    core/protection/relay_base.py

This module does NOT:
- Calculate system-wide faults.
- Operate circuit breakers.
- Coordinate multiple relays.
- Modify the network model.

Notes
-----
The locked Relay model does not store voltage/current phase angles.
Therefore phase-angle inputs are supplied directly to the directional
evaluation methods.

Future extensions
-----------------
- Polarizing memory voltage
- Negative-sequence directional element
- Zero-sequence directional element
- IEC directional overcurrent coordination

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from typing import Optional

from core.protection.relay_base import RelayBase


class DirectionalRelay(RelayBase):
    """
    Directional protection algorithm.

    Parameters
    ----------
    relay:
        Authoritative Relay model from core.model.relay.

    forward_angle:
        Maximum-torque / forward reference angle in degrees.

    tolerance:
        Acceptable angular deviation from the forward reference
        angle in degrees.

    Notes
    -----
    Relay pickup is obtained from:

        relay.pickup

    Relay current is obtained from:

        relay.current

    Relay service and trip state remain owned by the Relay model.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        relay,
        forward_angle: float = 90.0,
        tolerance: float = 90.0,
    ) -> None:

        super().__init__(
            relay
        )

        self.forward_angle = float(
            forward_angle
        )

        self.tolerance = float(
            tolerance
        )

        self.direction: Optional[str] = None

        self._validate_settings()

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_settings(
        self,
    ) -> None:
        """
        Validate directional protection settings.
        """

        if not (
            0.0 <= self.tolerance <= 180.0
        ):
            raise ValueError(
                "Directional tolerance must be "
                "between 0 and 180 degrees."
            )

    # =============================================================
    # ANGLE NORMALIZATION
    # =============================================================

    @staticmethod
    def _normalize_angle(
        angle: float,
    ) -> float:
        """
        Normalize an angle to the range [-180, 180].
        """

        normalized = (
            float(angle) + 180.0
        ) % 360.0 - 180.0

        return normalized

    # =============================================================
    # CURRENT PICKUP
    # =============================================================

    def check_pickup(
        self,
    ) -> bool:
        """
        Evaluate the current pickup condition.

        The authoritative pickup setting and current measurement
        are obtained from the Relay model.
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
    # DIRECTIONAL ELEMENT
    # =============================================================

    def check_direction(
        self,
        voltage_angle: float,
        current_angle: float,
    ) -> str:
        """
        Determine forward or reverse direction.

        Parameters
        ----------
        voltage_angle:
            Polarizing voltage angle in degrees.

        current_angle:
            Current angle in degrees.

        Returns
        -------
        str
            "FORWARD" or "REVERSE".

        Notes
        -----
        The directional criterion is based on the angular
        relationship between voltage and current.

        The phase angles are evaluation inputs and are not stored
        as competing relay-model state.
        """

        angle_difference = (
            float(voltage_angle)
            - float(current_angle)
        )

        angle_difference = (
            self._normalize_angle(
                angle_difference
            )
        )

        reference_difference = (
            self._normalize_angle(
                angle_difference
                - self.forward_angle
            )
        )

        if abs(
            reference_difference
        ) <= self.tolerance:

            self.direction = "FORWARD"

        else:

            self.direction = "REVERSE"

        return self.direction

    # =============================================================
    # TRIP PERMISSION
    # =============================================================

    def evaluate(
        self,
        voltage_angle: float,
        current_angle: float,
    ) -> bool:
        """
        Evaluate the complete directional protection element.

        Returns
        -------
        bool
            True when current pickup and forward direction
            conditions are both satisfied.

        The authoritative Relay.trip state is updated through
        Relay.set_trip().
        """

        if not self.relay.in_service:

            self.direction = None

            self.relay.set_trip(
                False
            )

            return False

        pickup = self.check_pickup()

        direction = self.check_direction(
            voltage_angle=voltage_angle,
            current_angle=current_angle,
        )

        operates = (
            pickup
            and direction == "FORWARD"
        )

        self.relay.set_trip(
            operates
        )

        return operates

    # =============================================================
    # RESET
    # =============================================================

    def reset(
        self,
    ) -> None:
        """
        Reset directional operating state.

        Protection settings are retained.
        """

        self.direction = None

        self.relay.reset()

    # =============================================================
    # STATUS
    # =============================================================

    def status(
        self,
    ) -> dict:
        """
        Return directional protection status.
        """

        return {
            "relay_id": self.relay.id,
            "pickup": self.relay.pickup,
            "current": self.relay.current,
            "in_service": self.relay.in_service,
            "direction": self.direction,
            "trip": self.relay.trip,
            "forward_angle": self.forward_angle,
            "tolerance": self.tolerance,
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
            f"<DirectionalRelay "
            f"relay={self.relay.id}, "
            f"direction={self.direction}, "
            f"trip={self.relay.trip}>"
        )


__all__ = [
    "DirectionalRelay",
]
```
