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

This module does NOT create a second authoritative relay state.

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
    - measurement access
    - relay setting access
    - protection pickup interface
    - trip-state interface
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
from typing import Any


class RelayBase(ABC):
    """
    Abstract base class for GridForge protection algorithms.

    Parameters
    ----------
    relay:
        Authoritative Relay object from core.model.relay.

    Notes
    -----
    The supplied Relay object is the single source of truth
    for relay state, measurements, and settings.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        relay: Any,
    ) -> None:

        if relay is None:
            raise ValueError(
                "relay cannot be None."
            )

        self.relay = relay

    # =========================================================
    # RELAY IDENTITY
    # =========================================================

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

    # =========================================================
    # MEASUREMENTS
    # =========================================================

    @property
    def current(self) -> float:
        """
        Return the authoritative current measurement.
        """

        return self.relay.current

    @property
    def voltage(self) -> float:
        """
        Return the authoritative voltage measurement.
        """

        return self.relay.voltage

    @property
    def impedance(self) -> complex:
        """
        Return the authoritative impedance measurement.
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

        Storage remains exclusively in core/model/relay.py.
        """

        self.relay.measure(
            current=current,
            voltage=voltage,
            impedance=impedance,
        )

    # =========================================================
    # RELAY SETTINGS
    # =========================================================

    @property
    def pickup(self) -> float:
        """
        Return the authoritative pickup setting.
        """

        return self.relay.pickup

    @pickup.setter
    def pickup(
        self,
        value: float,
    ) -> None:
        """
        Update the authoritative pickup setting.
        """

        self.relay.set_pickup(
            value
        )

    @property
    def time_delay(self) -> float:
        """
        Return the authoritative relay time delay.
        """

        return self.relay.time_delay

    @time_delay.setter
    def time_delay(
        self,
        value: float,
    ) -> None:
        """
        Update the authoritative relay time delay.
        """

        self.relay.set_time_delay(
            value
        )

    # =========================================================
    # SERVICE STATE
    # =========================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the relay is in service.
        """

        return self.relay.in_service

    # =========================================================
    # TRIP STATE
    # =========================================================

    @property
    def tripped(self) -> bool:
        """
        Return the authoritative relay trip state.
        """

        return self.relay.trip

    def trip(self) -> bool:
        """
        Set the authoritative relay trip state.

        This method does NOT operate a circuit breaker.

        Breaker operation belongs to:

            ProtectionSystem
                |
                v
            BreakerManager
        """

        if not self.relay.in_service:
            self.relay.set_trip(
                False
            )

            return False

        self.relay.set_trip(
            True
        )

        return self.relay.trip

    # =========================================================
    # RESET
    # =========================================================

    def reset(self) -> None:
        """
        Reset the authoritative Relay model.

        Protection-specific transient state must also be reset
        by subclasses when required.
        """

        self.relay.reset()

    # =========================================================
    # PICKUP LOGIC
    # =========================================================

    @abstractmethod
    def check_pickup(self) -> bool:
        """
        Evaluate the protection-specific pickup condition.

        Returns
        -------
        bool
            True when the protection element picks up.

        Notes
        -----
        Implementations must use the authoritative Relay model
        rather than maintaining duplicate measurement or state
        variables.
        """

        raise NotImplementedError

    # =========================================================
    # GENERIC EVALUATION
    # =========================================================

    def evaluate(self) -> bool:
        """
        Evaluate the protection pickup condition.

        Returns
        -------
        bool
            True when the protection element operates.

        Notes
        -----
        This base implementation represents an instantaneous
        protection decision.

        Time grading, TCC behaviour, breaker operating time,
        and event scheduling belong to the appropriate higher
        protection/simulation layers.

        Protection subclasses may override this method when
        their operating criterion requires additional inputs,
        such as directional phase angles or distance zones.
        """

        if not self.relay.in_service:
            self.relay.set_trip(
                False
            )

            return False

        operates = bool(
            self.check_pickup()
        )

        if operates:
            self.trip()
        else:
            self.relay.set_trip(
                False
            )

        return operates

    # =========================================================
    # STATUS
    # =========================================================

    def status(self) -> dict[str, Any]:
        """
        Return protection status using the authoritative
        Relay model.
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
