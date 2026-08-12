# core/model/shunt.py

"""
GridForge Shunt Model
=====================

GridForge Model Layer V2

Defines the GridForge passive shunt-admittance model.

Architecture
------------
A Shunt is a single-terminal passive electrical element.

    Shunt
      |
    Terminal
      |
      +---- network topology ---- Bus

The Shunt owns its physical Terminal.

The Terminal represents the Shunt's physical connection point.
The network layer is responsible for incorporating that connection
into the assembled network representation.

A Shunt is NOT a two-terminal branch and therefore does not create
connectivity between two electrical nodes.

Electrical Model
----------------
The Shunt represents a general passive admittance:

    Y = G + jB

where:

    G : conductance in per-unit
    B : susceptance in per-unit

Sign convention:

    B > 0
        Capacitive shunt.

    B < 0
        Inductive shunt.

The numerical network/Y-bus layer is responsible for incorporating
the admittance into the network admittance matrix.

Responsibilities
----------------
The Shunt model:

- Stores authoritative shunt electrical parameters.
- Owns one physical Terminal.
- Stores operational service state.
- Provides the shunt admittance.
- Provides capacitive/inductive identification.
- Provides local parameter validation.
- Provides diagnostic information.

The Shunt model does NOT:

- Build Y-bus.
- Stamp admittance matrices.
- Calculate bus power.
- Perform load flow.
- Perform short-circuit calculations.
- Perform voltage-control calculations.
- Perform protection calculations.
- Perform contingency analysis.
- Perform dynamic simulation.
- Determine global electrical topology.
- Store study results.
- Store GUI geometry.

Those responsibilities belong to the appropriate
network/solver/analysis/protection/simulation layers.

Topology Semantics
------------------
A Shunt is a node-attached electrical element.

It does not connect two buses.

Therefore:

    in_service = True
        -> Shunt contributes its admittance to the electrical model.

    in_service = False
        -> Shunt contributes no admittance.

Opening/tripping a Shunt must NOT by itself create an electrical
island because the Shunt is not a connectivity branch.

Terminal Architecture
----------------------
The authoritative local physical connection is:

    self.terminal

The ``bus`` property is retained as a compatibility/convenience
interface derived from the Terminal.

The network layer remains responsible for global topology.

Units
-----
    g : per-unit
    b : per-unit

GridForge V2 Status
-------------------
This module is part of the GridForge Model Layer V2 baseline.

Changes require evidence of a genuinely fundamental shunt-model
requirement that cannot be satisfied through the Terminal,
existing electrical model interfaces, or higher-level layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# SHUNT MODEL
# =====================================================================

class Shunt(ElectricalObject):
    """
    GridForge passive shunt-admittance model.

    Parameters
    ----------
    id : str
        Unique GridForge shunt identifier.

    bus :
        Initial electrical connection endpoint.

        Normally this is a Bus. The Terminal architecture permits the
        network layer to establish the global physical/electrical
        connection representation.

    g : float, optional
        Conductance in per-unit.

    b : float, optional
        Susceptance in per-unit.

        Positive values represent capacitive susceptance.
        Negative values represent inductive susceptance.

    name : str, optional
        Human-readable shunt name.

    Notes
    -----
    The Shunt owns its physical Terminal.

    The complete shunt admittance is:

        Y = G + jB

    The Shunt does not perform any numerical network calculation.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        id: str,
        bus,
        g: float = 0.0,
        b: float = 0.0,
        name: str = "",
    ) -> None:
        """
        Initialize a GridForge shunt.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # -------------------------------------------------------------
        # Physical connection
        #
        # The Shunt owns its Terminal.
        # -------------------------------------------------------------

        if bus is None:
            raise ValueError(
                f"Shunt '{id}' bus/endpoint cannot be None."
            )

        self.terminal = Terminal(
            endpoint=bus,
            owner=self,
        )

        # -------------------------------------------------------------
        # Electrical parameters
        # -------------------------------------------------------------

        self.g = float(g)
        self.b = float(b)

        # -------------------------------------------------------------
        # Operational state
        # -------------------------------------------------------------

        self.in_service = True

        # -------------------------------------------------------------
        # Local validation
        # -------------------------------------------------------------

        self._validate_parameters()

    # =================================================================
    # CONNECTION
    # =================================================================

    @property
    def bus(self):
        """
        Return the Bus associated with the Shunt Terminal.

        This is a compatibility/convenience property.

        The authoritative local physical connection is:

            self.terminal
        """

        return self.terminal.bus

    # =================================================================
    # ELECTRICAL PARAMETERS
    # =================================================================

    @property
    def g_pu(self) -> float:
        """
        Return conductance in per-unit.

        Compatibility alias for ``g``.
        """

        return self.g

    @property
    def b_pu(self) -> float:
        """
        Return susceptance in per-unit.

        Compatibility alias for ``b``.
        """

        return self.b

    @property
    def y_pu(self) -> complex:
        """
        Return the complete shunt admittance.

            Y = G + jB
        """

        return complex(
            self.g,
            self.b,
        )

    @property
    def admittance(self) -> complex:
        """
        Return the complete shunt admittance.

        Alias for ``y_pu``.
        """

        return self.y_pu

    # =================================================================
    # TYPE IDENTIFICATION
    # =================================================================

    @property
    def is_capacitive(self) -> bool:
        """
        Return True when the shunt susceptance is positive.
        """

        return self.b > 0.0

    @property
    def is_inductive(self) -> bool:
        """
        Return True when the shunt susceptance is negative.
        """

        return self.b < 0.0

    # =================================================================
    # PARAMETER UPDATE
    # =================================================================

    def set_admittance(
        self,
        g: float | None = None,
        b: float | None = None,
    ) -> None:
        """
        Update the shunt admittance.

        Parameters
        ----------
        g : float, optional
            New conductance in per-unit.

        b : float, optional
            New susceptance in per-unit.

        Notes
        -----
        Only supplied values are changed.

        The candidate state is validated before it is committed.
        """

        new_g = (
            self.g
            if g is None
            else float(g)
        )

        new_b = (
            self.b
            if b is None
            else float(b)
        )

        self._validate_admittance(
            new_g,
            new_b,
        )

        self.g = new_g
        self.b = new_b

    # =================================================================
    # SERVICE STATE
    # =================================================================

    def trip(self) -> None:
        """
        Remove the Shunt from service.

        This changes only the authoritative local service state.

        The network/Y-bus layer is responsible for deriving the
        resulting electrical representation.
        """

        self.in_service = False

    def close(self) -> None:
        """
        Return the Shunt to service.

        This changes only the authoritative local service state.
        """

        self.in_service = True

    # =================================================================
    # STATUS
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """
        Return True when the Shunt is in service.
        """

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return True when the Shunt is out of service.
        """

        return not self.in_service

    # =================================================================
    # VALIDATION
    # =================================================================

    @staticmethod
    def _validate_admittance(
        g: float,
        b: float,
    ) -> None:
        """
        Validate a candidate shunt admittance.

        Both G and B must be finite.

        A zero admittance is not a meaningful Shunt model and is
        therefore rejected.
        """

        if not isfinite(g):
            raise ValueError(
                "Shunt conductance must be finite."
            )

        if not isfinite(b):
            raise ValueError(
                "Shunt susceptance must be finite."
            )

        if g == 0.0 and b == 0.0:
            raise ValueError(
                "Shunt must have non-zero admittance."
            )

    def _validate_parameters(self) -> None:
        """
        Validate the complete local Shunt state.
        """

        self._validate_admittance(
            self.g,
            self.b,
        )

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured Shunt diagnostic information.

        The summary contains authoritative model state only and does
        not contain calculated study results.
        """

        bus = self.bus

        return {
            "id": self.id,
            "name": self.name,
            "type": "shunt",
            "bus": (
                bus.id
                if bus is not None
                else None
            ),
            "terminal": self.terminal.summary(),
            "g_pu": self.g,
            "b_pu": self.b,
            "y_pu": self.y_pu,
            "in_service": self.in_service,
            "is_capacitive": self.is_capacitive,
            "is_inductive": self.is_inductive,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        bus_id = (
            self.bus.id
            if self.bus is not None
            else None
        )

        return (
            f"<Shunt "
            f"id={self.id}, "
            f"bus={bus_id}, "
            f"Y={self.g:.6f}"
            f"+j{self.b:.6f}, "
            f"in_service={self.in_service}>"
        )
