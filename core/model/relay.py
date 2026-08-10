```python
"""
GridForge Relay Model
=====================

File:
    core/model/relay.py

Defines the electrical protection Relay model.

A Relay represents a protection-device model attached to an
electrical measurement point.

Responsibilities
----------------
- Store relay identity and type.
- Store relay settings.
- Store measured electrical quantities.
- Maintain relay operating state.
- Provide basic pickup evaluation.

The Relay model does NOT:
- Perform system-wide fault analysis.
- Perform relay coordination.
- Calculate TCC curves.
- Coordinate multiple relays.
- Control circuit breakers.
- Perform protection optimization.

Those responsibilities belong to:

    core/protection
    core/analysis
    core/simulation

Supported relay types
---------------------
- OVER_CURRENT
- DISTANCE
- DIFFERENTIAL
- VOLTAGE
- FREQUENCY

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from .base import ElectricalObject


class Relay(ElectricalObject):
    """
    GridForge protection relay model.

    Parameters
    ----------
    id:
        Unique relay identifier.

    relay_type:
        Protection function type.

    name:
        Human-readable relay name.

    pickup:
        Primary pickup/threshold setting.

    time_delay:
        Basic operating delay in seconds.
    """

    # =========================================================
    # SUPPORTED RELAY TYPES
    # =========================================================

    VALID_TYPES = frozenset(
        {
            "OVER_CURRENT",
            "DISTANCE",
            "DIFFERENTIAL",
            "VOLTAGE",
            "FREQUENCY",
        }
    )

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        id: str,
        relay_type: str,
        name: str = "",
        pickup: float = 1.0,
        time_delay: float = 0.0,
    ):
        """
        Initialize a GridForge relay.
        """

        super().__init__(
            id=id,
            name=name
        )

        # -----------------------------------------------------
        # Relay type
        # -----------------------------------------------------

        relay_type = str(
            relay_type
        ).upper()

        if relay_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid relay type '{relay_type}'. "
                f"Supported types: "
                f"{sorted(self.VALID_TYPES)}"
            )

        self.type = relay_type

        # -----------------------------------------------------
        # Relay settings
        # -----------------------------------------------------

        self.pickup = float(
            pickup
        )

        self.time_delay = float(
            time_delay
        )

        # -----------------------------------------------------
        # Measurements
        # -----------------------------------------------------

        self.current = 0.0

        self.voltage = 1.0

        self.impedance = 0.0

        # -----------------------------------------------------
        # Operational state
        # -----------------------------------------------------

        self.in_service = True

        self.trip = False

        self._validate_settings()

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_settings(self) -> None:
        """
        Validate relay settings.
        """

        if self.pickup < 0.0:
            raise ValueError(
                "Relay pickup must be >= 0"
            )

        if self.time_delay < 0.0:
            raise ValueError(
                "Relay time delay must be >= 0"
            )

    # =========================================================
    # MEASUREMENT UPDATE
    # =========================================================

    def measure(
        self,
        current: float = 0.0,
        voltage: float = 1.0,
        impedance: complex = 0.0,
    ) -> None:
        """
        Update measured electrical quantities.

        Parameters
        ----------
        current:
            Measured current.

        voltage:
            Measured voltage magnitude.

        impedance:
            Measured apparent impedance.
        """

        self.current = float(
            current
        )

        self.voltage = float(
            voltage
        )

        self.impedance = complex(
            impedance
        )

    # =========================================================
    # BASIC PICKUP EVALUATION
    # =========================================================

    def evaluate(self) -> bool:
        """
        Evaluate the basic relay pickup condition.

        This is intentionally a minimal device-level operation.

        Detailed protection algorithms belong in core/protection.

        Returns
        -------
        bool
            True when the relay pickup condition is satisfied.
        """

        if not self.in_service:
            self.trip = False
            return False

        operated = False

        # -----------------------------------------------------
        # Overcurrent
        # -----------------------------------------------------

        if self.type == "OVER_CURRENT":

            operated = (
                abs(self.current)
                > self.pickup
            )

        # -----------------------------------------------------
        # Distance
        # -----------------------------------------------------

        elif self.type == "DISTANCE":

            operated = (
                abs(self.impedance)
                < self.pickup
            )

        # -----------------------------------------------------
        # Other relay functions
        # -----------------------------------------------------
        #
        # Detailed algorithms are deliberately not embedded
        # in the model layer.
        # -----------------------------------------------------

        else:

            operated = False

        self.trip = operated

        return self.trip

    # =========================================================
    # TRIP CONTROL
    # =========================================================

    def set_trip(
        self,
        state: bool
    ) -> None:
        """
        Explicitly set relay trip state.
        """

        self.trip = bool(
            state
        )

    # =========================================================
    # RESET
    # =========================================================

    def reset(self) -> None:
        """
        Reset relay operating state and measurements.
        """

        self.trip = False

        self.current = 0.0

        self.voltage = 1.0

        self.impedance = 0.0

    # =========================================================
    # STATUS CONTROL
    # =========================================================

    def trip_out(self) -> None:
        """
        Remove relay from service.

        The relay will not operate while out of service.
        """

        self.in_service = False

        self.trip = False

    def close(self) -> None:
        """
        Return relay to service.
        """

        self.in_service = True

    # =========================================================
    # SETTINGS
    # =========================================================

    def set_pickup(
        self,
        pickup: float
    ) -> None:
        """
        Update relay pickup setting.
        """

        pickup = float(
            pickup
        )

        if pickup < 0.0:
            raise ValueError(
                "Relay pickup must be >= 0"
            )

        self.pickup = pickup

    def set_time_delay(
        self,
        time_delay: float
    ) -> None:
        """
        Update relay operating delay.
        """

        time_delay = float(
            time_delay
        )

        if time_delay < 0.0:
            raise ValueError(
                "Relay time delay must be >= 0"
            )

        self.time_delay = time_delay

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(self) -> dict:
        """
        Return structured relay information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "pickup": self.pickup,
            "time_delay": self.time_delay,
            "current": self.current,
            "voltage": self.voltage,
            "impedance": self.impedance,
            "in_service": self.in_service,
            "trip": self.trip,
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(self) -> str:
        return (
            f"<Relay "
            f"id={self.id}, "
            f"type={self.type}, "
            f"pickup={self.pickup:.6f}, "
            f"trip={self.trip}, "
            f"in_service={self.in_service}>"
        )
```
