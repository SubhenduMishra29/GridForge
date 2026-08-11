```python
"""
GridForge Protection Relay Base
===============================

File:
    core/protection/relay_base.py

Purpose
-------
Common interface for protection algorithms operating on the
authoritative GridForge Relay model.

The electrical Relay device model is defined in:

    core/model/relay.py

This module MUST NOT create a second authoritative relay state.

Architecture
------------

    core/model/relay.py
            |
            | authoritative Relay object
            v
    core/protection/relay_base.py
            |
            +-- Overcurrent protection
            +-- Directional protection
            +-- Distance protection
            +-- Differential protection
            |
            v
    ProtectionSystem
            |
            v
    BreakerManager

Responsibilities
----------------
RelayBase provides:

    - access to the model Relay
    - relay identification
    - protection measurement access
    - protection pickup interface
    - protection trip decision
    - reset interface
    - status reporting

The model Relay remains authoritative for:

    - relay identity
    - relay type
    - pickup setting
    - time delay
    - measured current
    - measured voltage
    - measured impedance
    - in-service state
    - trip state

RelayBase does NOT:

    - duplicate relay state
    - calculate system-wide fault quantities
    - build Ybus
    - perform load flow
    - perform short-circuit studies
    - coordinate multiple relays
    - operate circuit breakers

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class RelayBase(ABC):
    """
    Abstract base class for GridForge protection algorithms.

    Parameters
    ----------
    relay:
        Authoritative Relay object from core.model.relay.

    Notes
    -----
    The supplied Relay object is the single source of truth for
    relay state and measurements.

    Protection subclasses should implement protection-specific
    pickup logic without creating duplicate relay state.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(self, relay: Any) -> None:
        if relay is None:
            raise ValueError(
                "relay cannot be None."
            )

        self.relay = relay

    # =============================================================
    # RELAY IDENTITY
    # =============================================================

    @property
    def id(self) -> Any:
        """
        Return the authoritative relay identifier.
        """

        return self.relay.id

    @property
    def relay_type(self) -> str:
        """
        Return the authoritative relay type.
        """

        return self.relay.type

    # =============================================================
    # MEASUREMENTS
    # =============================================================

    @property
    def current(self) -> float:
        """
        Return the latest relay current measurement.
        """

        return self.relay.current

    @property
    def voltage(self) -> float:
        """
        Return the latest relay voltage measurement.
        """

        return self.relay.voltage

    @property
    def impedance(self) -> complex:
        """
        Return the latest relay impedance measurement.
        """

        return self.relay.impedance

    def measure(
        self,
        current: float = 0.0,
        voltage: float = 1.0,
        impedance: complex = 0.0,
    ) -> None:
        """
        Update the authoritative Relay measurement state.

        Parameters
        ----------
        current:
            Measured current.

        voltage:
            Measured voltage magnitude.

        impedance:
            Measured apparent impedance.

        Notes
        -----
        The actual measurement storage remains in
        core/model/relay.py.
        """

        self.relay.measure(
            current=current,
            voltage=voltage,
            impedance=impedance,
        )

    # =============================================================
    # RELAY SETTINGS
    # =============================================================

    @property
    def pickup(self) -> float:
        """
        Return the authoritative relay pickup setting.
        """

        return self.relay.pickup

    @pickup.setter
    def pickup(self, value: float) -> None:
        """
        Update the authoritative relay pickup setting.
        """

        self.relay.set_pickup(value)

    @property
    def time_delay(self) -> float:
        """
        Return the authoritative relay time delay.
        """

        return self.relay.time_delay

    @time_delay.setter
    def time_delay(self, value: float) -> None:
        """
        Update the authoritative relay time delay.
        """

        self.relay.set_time_delay(value)

    # =============================================================
    # SERVICE STATE
    # =============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the relay is in service.
        """

        return self.relay.in_service

    # =============================================================
    # TRIP STATE
    # =============================================================

    @property
    def tripped(self) -> bool:
        """
        Return the authoritative relay trip state.
        """

        return self.relay.trip

    def trip(self) -> bool:
        """
        Issue a relay trip decision.

        Returns
        -------
        bool
            True when the relay is now tripped.

        Notes
        -----
        This changes the Relay model's trip state.

        It does NOT operate a circuit breaker.

        Breaker operation belongs to ProtectionSystem /
        BreakerManager.
        """

        if not self.relay.in_service:
            self.relay.set_trip(False)
            return False

        self.relay.set_trip(True)

        return self.relay.trip

    # =============================================================
    # RESET
    # =============================================================

    def reset(self) -> None:
        """
        Reset the authoritative relay model.
        """

        self.relay.reset()

    # =============================================================
    # PICKUP LOGIC
    # =============================================================

    @abstractmethod
    def check_pickup(self) -> bool:
        """
        Evaluate the protection-specific pickup condition.

        Returns
        -------
        bool
            True when the protection element should pick up.

        Notes
        -----
        Derived classes implement the actual protection algorithm.

        The method must use the authoritative Relay measurements
        and settings rather than maintaining duplicate copies.
        """

        raise NotImplementedError

    # =============================================================
    # EVALUATION
    # =============================================================

    def evaluate(self) -> bool:
        """
        Evaluate the protection element.

        Returns
        -------
        bool
            True when the protection element picks up.

        Notes
        -----
        Pickup logic belongs to the protection subclass.

        The model Relay's generic evaluate() method is deliberately
        not called here because detailed protection algorithms
        belong in core/protection.
        """

        if not self.relay.in_service:
            self.relay.set_trip(False)
            return False

        picked_up = bool(
            self.check_pickup()
        )

        if picked_up:
            self.trip()
        else:
            self.relay.set_trip(False)

        return picked_up

    # =============================================================
    # STATUS
    # =============================================================

    def status(self) -> Dict[str, Any]:
        """
        Return protection status using the authoritative Relay model.
        """

        return {
            "id": self.relay.id,
            "name": self.relay.name,
            "type": self.relay.type,
            "pickup": self.relay.pickup,
            "time_delay": self.relay.time_delay,
            "current": self.relay.current,
            "voltage": self.relay.voltage,
            "impedance": self.relay.impedance,
            "in_service": self.relay.in_service,
            "trip": self.relay.trip,
        }


__all__ = [
    "RelayBase",
]
```
