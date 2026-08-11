```python
# core/model/injection.py

"""
GridForge Power Injection Interface
===================================

GridForge Model Layer V2

Defines the common interface for electrical power injections
connected to a GridForge Bus.

The interface is implemented by model objects such as:

- Load
- Generator
- Distributed-energy resources
- Energy-storage systems
- Grid-forming sources
- Grid-following sources
- Future electrical injection devices

Network Injection Convention
----------------------------
GridForge uses the network-injection sign convention:

    +P, +Q
        Power injected into the electrical network.

    -P, -Q
        Power consumed from the electrical network.

Therefore, typical implementations are:

    Generator -> (+P, +Q)
    Load      -> (-P, -Q)

The interface does not prescribe how an individual device stores
its internal engineering quantities.

For example, Load may store positive consumption internally and
return the corresponding negative network injection through
``get_power()``.

Responsibilities
----------------
This interface:

- Defines the common power-injection contract.
- Defines access to the connected Bus.
- Allows numerical layers to process different injection types
  polymorphically.
- Provides a stable boundary between model objects and numerical
  network/solver layers.

This interface does NOT:

- Calculate bus power balance.
- Modify Bus state.
- Perform load-flow calculations.
- Build Y-bus.
- Enforce generator reactive-power limits.
- Perform contingency analysis.
- Perform dynamic simulation.
- Perform protection calculations.
- Manage network registration.
- Manage GUI objects.

Those responsibilities belong to the appropriate
network/solver/analysis/simulation/UI layers.

Design Principle
----------------
``Injection`` intentionally contains only the minimum common
contract required by numerical consumers.

It does not require:

- a specific concrete Bus class,
- a Terminal implementation,
- an ElectricalObject base class,
- an identifier,
- a name,
- a particular device technology.

Concrete model classes may provide these features independently.

This keeps the interface suitable for future DER, storage,
converter-based sources, and other injection models.

GridForge V2 Status
-------------------
This module is part of the frozen GridForge Model Layer V2 baseline.

Changes require evidence of a genuinely fundamental model-interface
requirement that cannot be satisfied by a concrete injection model
or a higher-level network/solver interface.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


# =====================================================================
# POWER INJECTION INTERFACE
# =====================================================================

class Injection(ABC):
    """
    Abstract interface for a GridForge power-injecting model object.

    Implementations must provide:

        get_power()
        bus

    ``get_power()`` returns electrical power using the GridForge
    network-injection sign convention.
    """

    # =================================================================
    # POWER INTERFACE
    # =================================================================

    @abstractmethod
    def get_power(self) -> tuple[float, float]:
        """
        Return the object's electrical power injection.

        Returns
        -------
        tuple[float, float]
            ``(P, Q)`` using the GridForge network-injection
            sign convention.

        Sign Convention
        ----------------
        +P
            Active power injected into the network.

        -P
            Active power consumed from the network.

        +Q
            Reactive power injected into the network.

        -Q
            Reactive power consumed from the network.

        Notes
        -----
        The returned values are electrical model quantities.
        Numerical consumers such as power-flow solvers may transform
        or aggregate them as required.

        The interface itself performs no calculations.
        """

        raise NotImplementedError

    # =================================================================
    # CONNECTION INTERFACE
    # =================================================================

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
        The interface intentionally does not import the concrete
        ``Bus`` class.

        This avoids coupling the abstract injection interface to
        concrete model implementations and prevents unnecessary
        circular dependencies.

        Concrete implementations may obtain the Bus directly or
        through a Terminal abstraction.
        """

        raise NotImplementedError
```
