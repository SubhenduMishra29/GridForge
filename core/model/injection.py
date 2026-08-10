"""
GridForge Injection Interface
=============================

File:
    core/model/injection.py

Defines the common interface for electrical power injections
connected to a GridForge Bus.

The interface is implemented by model objects such as:

    - Load
    - Generator
    - Future distributed-energy resources
    - Future storage systems
    - Future grid-forming/grid-following sources

Sign Convention
---------------

GridForge uses the network-injection convention:

    +P, +Q
        Power injected into the electrical network.

    -P, -Q
        Power consumed from the electrical network.

Therefore:

    Generator -> typically (+P, +Q)
    Load      -> typically (-P, -Q)

Responsibilities
----------------
This interface:

    - Defines the common power-injection contract.
    - Identifies the connected Bus.
    - Allows numerical layers to work with different
      injection types polymorphically.

This interface does NOT:

    - Calculate bus power balance.
    - Modify Bus state.
    - Perform load-flow calculations.
    - Build Ybus.
    - Enforce generator Q limits.
    - Perform dynamic simulation.
    - Perform protection calculations.

Those responsibilities belong to the appropriate
network/solver/analysis layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Injection(ABC):
    """
    Abstract interface for a power-injecting model object.

    Implementations must provide:

        get_power()
        bus
    """

    # =============================================================
    # POWER INTERFACE
    # =============================================================

    @abstractmethod
    def get_power(self) -> tuple[float, float]:
        """
        Return the object's electrical power injection.

        Returns
        -------
        tuple[float, float]
            ``(P, Q)`` in the GridForge network-injection
            sign convention.

        Sign Convention
        ----------------
        +P -> active power injected into the network
        -P -> active power consumed from the network

        +Q -> reactive power injected into the network
        -Q -> reactive power consumed from the network
        """

        raise NotImplementedError

    # =============================================================
    # CONNECTION INTERFACE
    # =============================================================

    @property
    @abstractmethod
    def bus(self):
        """
        Return the Bus to which this injection is connected.

        Returns
        -------
        Bus
            Connected GridForge Bus object.

        Notes
        -----
        The interface intentionally does not import ``Bus`` here.
        This avoids a circular dependency between the model
        interfaces and concrete model classes.
        """

        raise NotImplementedError
