# core/model/injection.py
"""
GridForge V2 Power Injection Interface
======================================

Author:
    Subhendu Mishra

Defines the common electrical power-injection contract used by
GridForge model objects.

Examples
--------
Typical implementations include:

    Generator
    Grid
    Solar
    Battery
    Load
    Motor
    Future converter-based sources and loads

Network Injection Convention
-----------------------------

GridForge uses the network-injection sign convention:

    +P, +Q
        Power injected into the electrical network.

    -P, -Q
        Power consumed from the electrical network.

Therefore, typical implementations are:

    Generator / Grid / Solar -> (+P, +Q)
    Battery                  -> (+P, +Q) when discharging
                                (-P, -Q) when charging
    Load / Motor             -> (-P, -Q)

The concrete model decides how its internal engineering
quantities are represented and converts them to this convention
through ``get_power()``.

Architectural Boundary
----------------------

Injection defines only the common electrical power interface.

Physical connectivity is NOT part of the abstract Injection
contract.

Connectivity is represented separately:

    Equipment
        |
        v
    Terminal
        |
        v
    Terminal.endpoint
        |
        v
    Network / topology
        |
        v
    Bus / electrical endpoint

The Injection interface therefore does NOT require:

    - a Bus property
    - a Terminal implementation
    - an ElectricalObject base class
    - an identifier
    - a name
    - network registration

Concrete equipment models may expose convenience properties such
as ``bus`` when useful, but ``bus`` is not an abstract Injection
requirement.

Responsibilities
----------------

Injection:

    - defines the common P/Q contract;
    - provides a stable polymorphic interface for numerical layers;
    - remains technology-neutral.

Injection does NOT:

    - calculate bus power balance;
    - modify Bus state;
    - build Y-bus;
    - perform load-flow calculations;
    - perform short-circuit calculations;
    - enforce generator limits;
    - perform contingency analysis;
    - perform dynamic simulation;
    - perform protection calculations;
    - manage network registration;
    - manage topology;
    - manage GUI/SLD state.

Those responsibilities belong to the appropriate Core
network, analysis, solver, simulation, protection, application,
and UI layers.

Dynamic Simulation
------------------

Dynamic behavior is deliberately outside this interface.

Static equipment models may later expose or bind to separate
dynamic-model definitions through the appropriate simulation
architecture.

For example:

    Battery
        |
        +-- static Injection model
        |
        +-- optional dynamic model
                |
                +-- simulation layer

The Injection contract itself remains unchanged.

Design Principle
----------------

Injection is intentionally minimal.

It provides the smallest common contract required by numerical
consumers without imposing assumptions about:

    - Bus implementation
    - Terminal implementation
    - equipment technology
    - generation technology
    - load technology
    - storage technology
    - converter technology
    - simulation technology

GridForge V2 Status
-------------------

This module belongs to the GridForge V2 Model Layer.

Changes to this interface should require a fundamental
cross-model requirement. Device-specific requirements must remain
in concrete model classes or higher-level services.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Injection(ABC):
    """
    Abstract electrical power-injection interface.

    Concrete model classes implement ``get_power()`` and return
    their electrical power contribution using the GridForge
    network-injection sign convention.

    The interface deliberately contains no topology or terminal
    ownership.
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
            ``(P, Q)`` using the GridForge network-injection
            sign convention.

        Sign Convention
        ----------------
        +P:
            Active power injected into the network.

        -P:
            Active power consumed from the network.

        +Q:
            Reactive power injected into the network.

        -Q:
            Reactive power consumed from the network.

        Notes
        -----
        The returned values are electrical model quantities.

        Numerical consumers such as Network and Solver may
        aggregate, transform, or normalize these values as
        required by a particular study.

        The Injection interface itself performs no study
        calculations.
        """

        raise NotImplementedError

    # =============================================================
    # OPTIONAL CONVENIENCE VALIDATION
    # =============================================================

    def validate_injection(
        self,
        power: tuple[float, float] | None = None,
    ) -> bool:
        """
        Validate an injection power tuple.

        This performs only generic interface-level validation.

        Device-specific limits belong to the concrete model.

        Parameters
        ----------
        power:
            Optional ``(P, Q)`` tuple.

            If omitted, ``get_power()`` is called.

        Returns
        -------
        bool
            ``True`` when the values are finite.
        """

        if power is None:
            power = self.get_power()

        if (
            not isinstance(power, tuple)
            or len(power) != 2
        ):
            raise ValueError(
                "Injection power must be a "
                "(P, Q) tuple."
            )

        p, q = power

        try:
            p = float(p)
            q = float(q)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Injection P and Q must be numeric."
            ) from exc

        if not _is_finite(p):
            raise ValueError(
                "Injection active power P must be finite."
            )

        if not _is_finite(q):
            raise ValueError(
                "Injection reactive power Q must be finite."
            )

        return True


def _is_finite(value: float) -> bool:
    """
    Return whether a numeric value is finite.

    Kept local to avoid introducing a dependency into this
    technology-neutral interface.
    """

    return value == value and value not in (
        float("inf"),
        float("-inf"),
    )
