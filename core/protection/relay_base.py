```python
"""
GridForge Relay Base Class
==========================

Common interface for all protection relays.

Derived classes may include:

    OvercurrentRelay
    DistanceRelay
    DirectionalRelay
    DifferentialRelay

Responsibilities
----------------
RelayBase provides the common protection-relay contract:

    - relay identification
    - measured electrical quantities
    - pickup state
    - trip state
    - measurement input
    - pickup interface
    - trip state transition
    - reset
    - status reporting

Architecture
------------

    Measurement Source
            |
            v
       RelayBase
            |
            v
      Relay-specific
      protection logic
            |
            v
       Trip Decision
            |
            v
    ProtectionSystem
            |
            v
      BreakerManager

RelayBase MUST NOT:

    - calculate network electrical quantities
    - build Ybus
    - solve power flow
    - calculate fault current
    - operate breakers directly
    - modify authoritative Network topology

Measurement Contract
--------------------

Voltage:
    volts (V)

Current:
    amperes (A)

Angle:
    degrees (deg)

The relay base class stores measured values only.
It does not derive or calculate them.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class RelayBase(ABC):
    """
    Abstract base class for all GridForge protection relays.

    Parameters
    ----------
    relay_id:
        Unique identifier of the relay.

    Notes
    -----
    RelayBase contains protection state and the latest supplied
    measurements. It does not own network state and does not
    perform electrical-system calculations.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(self, relay_id: Any) -> None:
        if relay_id is None:
            raise ValueError(
                "relay_id cannot be None."
            )

        self.id = relay_id

        # ---------------------------------------------------------
        # Relay state
        # ---------------------------------------------------------

        self.picked_up: bool = False
        self.tripped: bool = False

        # ---------------------------------------------------------
        # Measured electrical quantities
        #
        # Voltage : volts
        # Current : amperes
        # Angle   : degrees
        # ---------------------------------------------------------

        self.voltage: float = 0.0
        self.current: float = 0.0
        self.angle: float = 0.0

    # =============================================================
    # MEASUREMENT INPUT
    # =============================================================

    def measure(
        self,
        voltage: float,
        current: float,
        angle: float = 0.0,
    ) -> None:
        """
        Update relay measurements.

        Parameters
        ----------
        voltage:
            Measured voltage in volts (V).

        current:
            Measured current in amperes (A).

        angle:
            Measured electrical angle in degrees (deg).

        Notes
        -----
        This method accepts measurements supplied by an external
        measurement/analysis/simulation layer.

        It does not calculate the electrical quantities itself.
        """

        try:
            voltage_value = float(voltage)
            current_value = float(current)
            angle_value = float(angle)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Relay measurements must be numeric."
            ) from exc

        self.voltage = voltage_value
        self.current = current_value
        self.angle = angle_value

    # =============================================================
    # PICKUP LOGIC
    # =============================================================

    @abstractmethod
    def check_pickup(self) -> bool:
        """
        Evaluate relay-specific pickup logic.

        Derived relay classes must implement this method.

        Returns
        -------
        bool
            True when the relay pickup condition is satisfied.

        Notes
        -----
        The derived relay is responsible for applying its own
        protection characteristic.

        Examples include:

            - overcurrent pickup
            - directional pickup
            - distance-zone pickup
            - differential pickup

        This method must not operate a breaker.
        """

        raise NotImplementedError

    # =============================================================
    # TRIP LOGIC
    # =============================================================

    def trip(self) -> bool:
        """
        Set the relay trip state when the relay has picked up.

        Returns
        -------
        bool
            Current trip state.

        Notes
        -----
        This method represents the relay's trip decision/state.

        It does NOT operate a physical breaker.

        Breaker operation belongs to the protection-system /
        breaker-management layer.
        """

        if self.picked_up:
            self.tripped = True

        return self.tripped

    # =============================================================
    # RESET
    # =============================================================

    def reset(self) -> None:
        """
        Reset relay operating state and measurements.

        The relay returns to its initial state.
        """

        self.picked_up = False
        self.tripped = False

        self.voltage = 0.0
        self.current = 0.0
        self.angle = 0.0

    # =============================================================
    # STATUS
    # =============================================================

    def status(self) -> Dict[str, Any]:
        """
        Return the current relay status.

        Returns
        -------
        dict
            Diagnostic relay state and latest measurements.
        """

        return {
            "id": self.id,
            "pickup": self.picked_up,
            "trip": self.tripped,
            "voltage": self.voltage,
            "current": self.current,
            "angle": self.angle,
        }


__all__ = [
    "RelayBase",
]
```
