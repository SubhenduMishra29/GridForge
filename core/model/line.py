# core/model/line.py

"""
GridForge Transmission Line Model
==================================

GridForge Model Layer V2

Defines the physical two-terminal transmission-line model.

Architecture
------------

A Line is a physical impedance-bearing electrical branch:

    Bus ── Terminal ── Line ── Terminal ── Bus

The authoritative physical connection points are:

    from_terminal
    to_terminal

The connected endpoints are stored by the terminals. Bus access is
derived through ``Terminal.bus`` for compatibility with existing
GridForge network interfaces.

Electrical Model
----------------

The Line uses the standard transmission-line π-equivalent:

    Z_series = R + jX

    Y_shunt,total = jB

The ``b`` parameter represents TOTAL line shunt susceptance.

The network/Y-bus layer is responsible for applying:

    jB / 2

at each terminal during numerical network assembly.

The Line model does not perform Y-bus stamping.

Responsibilities
----------------

The Line model provides:

- Physical two-terminal connectivity.
- Series resistance.
- Series reactance.
- Total shunt susceptance.
- Thermal/equipment rating.
- In-service state.
- Local parameter validation.
- Diagnostic information.

The Line does NOT:

- Build Y-bus.
- Stamp admittance matrices.
- Calculate power flow.
- Calculate losses.
- Perform load flow.
- Perform short-circuit calculations.
- Perform contingency analysis.
- Perform protection calculations.
- Perform dynamic simulation.
- Manage global network topology.
- Manage GUI state.

Those responsibilities belong to the appropriate GridForge layers.

Units
-----

    r       : per-unit
    x       : per-unit
    b       : per-unit
    rate_mva: MVA

GridForge V2 Status
-------------------

This module is part of the GridForge Model Layer V2 baseline.

The physical connection contract is Terminal-based.

The Line remains in ``core/model`` because it represents fundamental
physical electrical equipment. Numerical interpretation belongs to
the network/solver/analysis layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .branch import Branch
from .terminal import Terminal


# =====================================================================
# TRANSMISSION LINE
# =====================================================================

class Line(Branch):
    """
    GridForge physical transmission-line model.

    Parameters
    ----------
    id : str
        Unique GridForge line identifier.

    endpoint_from :
        Initial from-side electrical endpoint.

        May be a Bus-like object or a Terminal.

    endpoint_to :
        Initial to-side electrical endpoint.

        May be a Bus-like object or a Terminal.

    r : float
        Series resistance in per-unit.

    x : float
        Series reactance in per-unit.

    b : float, optional
        Total line shunt susceptance in per-unit.

    name : str, optional
        Human-readable line name.

    rate_mva : float, optional
        Thermal/equipment rating in MVA.

    Notes
    -----
    ``from_terminal`` and ``to_terminal`` are the authoritative local
    physical connection points.

    The connected endpoint is therefore always obtained from:

        line.from_terminal.endpoint
        line.to_terminal.endpoint

    Bus access is derived through ``Terminal.bus``.

    The Line has no transformer tap or phase-shift parameter. Those
    remain at the common Branch level and are fixed to:

        tap   = 1.0
        shift = 0.0
    """

    def __init__(
        self,
        id: str,
        endpoint_from,
        endpoint_to,
        r: float,
        x: float,
        b: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
    ) -> None:

        # =============================================================
        # Initialize common branch data
        # =============================================================

        #
        # Branch V2 still provides the common electrical branch
        # representation. We deliberately pass only valid compatibility
        # endpoint objects here.
        #
        # The authoritative physical terminals are replaced below by
        # the Line-owned Terminal objects.
        #

        branch_from = (
            endpoint_from
            if not isinstance(endpoint_from, Terminal)
            else endpoint_from.endpoint
        )

        branch_to = (
            endpoint_to
            if not isinstance(endpoint_to, Terminal)
            else endpoint_to.endpoint
        )

        if branch_from is None:
            raise ValueError(
                f"Line '{id}' requires a valid from-side endpoint."
            )

        if branch_to is None:
            raise ValueError(
                f"Line '{id}' requires a valid to-side endpoint."
            )

        super().__init__(
            id=id,
            bus_from=branch_from,
            bus_to=branch_to,
            r=r,
            x=x,
            b=b,
            name=name,
            rate_mva=rate_mva,
            tap=1.0,
            shift=0.0,
        )

        # =============================================================
        # AUTHORITATIVE PHYSICAL TERMINALS
        # =============================================================

        #
        # Branch created temporary/common terminals during
        # initialization. For the V2 Line model, the Line's physical
        # terminals are authoritative and must own the Line.
        #

        self.from_terminal = (
            endpoint_from
            if isinstance(endpoint_from, Terminal)
            else Terminal(
                endpoint=endpoint_from,
                owner=self,
            )
        )

        self.to_terminal = (
            endpoint_to
            if isinstance(endpoint_to, Terminal)
            else Terminal(
                endpoint=endpoint_to,
                owner=self,
            )
        )

        # =============================================================
        # TERMINAL OWNERSHIP VALIDATION
        # =============================================================

        if self.from_terminal is self.to_terminal:
            raise ValueError(
                f"Line '{self.id}' cannot use the same Terminal "
                "for both sides."
            )

        if (
            self.from_terminal.owner is not None
            and self.from_terminal.owner is not self
        ):
            raise ValueError(
                f"Line '{self.id}' from_terminal already belongs "
                "to another equipment object."
            )

        if (
            self.to_terminal.owner is not None
            and self.to_terminal.owner is not self
        ):
            raise ValueError(
                f"Line '{self.id}' to_terminal already belongs "
                "to another equipment object."
            )

        self.from_terminal.owner = self
        self.to_terminal.owner = self

        # =============================================================
        # LINE-SPECIFIC VALIDATION
        # =============================================================

        self._validate_line_parameters()

    # =================================================================
    # TERMINALS
    # =================================================================

    @property
    def terminals(self) -> tuple[Terminal, Terminal]:
        """
        Return the Line's two physical terminals.

        Returns
        -------
        tuple
            ``(from_terminal, to_terminal)``
        """

        return (
            self.from_terminal,
            self.to_terminal,
        )

    # =================================================================
    # ENDPOINT ACCESS
    # =================================================================

    @property
    def from_endpoint(self):
        """
        Return the authoritative from-side endpoint.

        This is equivalent to:

            self.from_terminal.endpoint
        """

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self):
        """
        Return the authoritative to-side endpoint.

        This is equivalent to:

            self.to_terminal.endpoint
        """

        return self.to_terminal.endpoint

    def endpoints(self) -> tuple:
        """
        Return the authoritative physical endpoint pair.

        Returns
        -------
        tuple
            ``(from_endpoint, to_endpoint)``
        """

        return (
            self.from_endpoint,
            self.to_endpoint,
        )

    # =================================================================
    # BUS COMPATIBILITY
    # =================================================================

    @property
    def from_bus(self):
        """
        Return the Bus-like object associated with the from terminal.

        This is a compatibility accessor only.

        The authoritative physical connection remains:

            self.from_terminal.endpoint
        """

        return self.from_terminal.bus

    @property
    def to_bus(self):
        """
        Return the Bus-like object associated with the to terminal.

        This is a compatibility accessor only.

        The authoritative physical connection remains:

            self.to_terminal.endpoint
        """

        return self.to_terminal.bus

    def buses(self) -> tuple:
        """
        Return the derived endpoint buses.

        Returns
        -------
        tuple
            ``(from_bus, to_bus)``

        Notes
        -----
        This method is provided for compatibility with the common
        Branch interface.

        It does not perform global topology resolution.
        """

        return (
            self.from_bus,
            self.to_bus,
        )

    # =================================================================
    # CONNECTION STATE
    # =================================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both physical terminals have endpoints.
        """

        return (
            self.from_terminal.is_connected
            and self.to_terminal.is_connected
        )

    # =================================================================
    # ELECTRICAL PARAMETERS
    # =================================================================

    @property
    def r_pu(self) -> float:
        """
        Return series resistance in per-unit.
        """

        return self.r

    @property
    def x_pu(self) -> float:
        """
        Return series reactance in per-unit.
        """

        return self.x

    @property
    def b_pu(self) -> float:
        """
        Return total line shunt susceptance in per-unit.

        The network/Y-bus layer is responsible for applying B/2 at
        each terminal.
        """

        return self.b

    @property
    def is_pi_model(self) -> bool:
        """
        Return True because the Line uses the standard π-equivalent.
        """

        return True

    # =================================================================
    # CONNECTION CONTROL
    # =================================================================

    def connect_from(self, endpoint) -> None:
        """
        Connect the from-side terminal locally.

        Global topology remains the responsibility of core/network.
        """

        self.from_terminal.connect(endpoint)

    def connect_to(self, endpoint) -> None:
        """
        Connect the to-side terminal locally.

        Global topology remains the responsibility of core/network.
        """

        self.to_terminal.connect(endpoint)

    def disconnect_from(self) -> None:
        """
        Disconnect the from-side terminal locally.
        """

        self.from_terminal.disconnect()

    def disconnect_to(self) -> None:
        """
        Disconnect the to-side terminal locally.
        """

        self.to_terminal.disconnect()

    # =================================================================
    # LOCAL VALIDATION
    # =================================================================

    def _validate_line_parameters(self) -> None:
        """
        Validate local transmission-line parameters.

        Network-level electrical compatibility and topology rules
        belong to the network/validation layers.
        """

        # -------------------------------------------------------------
        # Series resistance
        # -------------------------------------------------------------

        if not isfinite(self.r):
            raise ValueError(
                f"Line '{self.id}' resistance must be finite."
            )

        if self.r < 0.0:
            raise ValueError(
                f"Line '{self.id}' resistance cannot be negative."
            )

        # -------------------------------------------------------------
        # Series reactance
        # -------------------------------------------------------------

        if not isfinite(self.x):
            raise ValueError(
                f"Line '{self.id}' reactance must be finite."
            )

        if self.x == 0.0:
            raise ValueError(
                f"Line '{self.id}' reactance cannot be zero."
            )

        # -------------------------------------------------------------
        # Total shunt susceptance
        # -------------------------------------------------------------

        if not isfinite(self.b):
            raise ValueError(
                f"Line '{self.id}' shunt susceptance must be finite."
            )

        # -------------------------------------------------------------
        # Thermal rating
        # -------------------------------------------------------------

        if not isfinite(self.rate_mva):
            raise ValueError(
                f"Line '{self.id}' MVA rating must be finite."
            )

        if self.rate_mva <= 0.0:
            raise ValueError(
                f"Line '{self.id}' MVA rating must be greater than zero."
            )

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured transmission-line information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "Line",

            "from_terminal": self.from_terminal.summary(),
            "to_terminal": self.to_terminal.summary(),

            "from_endpoint": (
                self.from_endpoint.id
                if self.from_endpoint is not None
                else None
            ),

            "to_endpoint": (
                self.to_endpoint.id
                if self.to_endpoint is not None
                else None
            ),

            "from_bus": (
                self.from_bus.id
                if self.from_bus is not None
                else None
            ),

            "to_bus": (
                self.to_bus.id
                if self.to_bus is not None
                else None
            ),

            "connected": self.is_connected,

            "r_pu": self.r,
            "x_pu": self.x,
            "b_pu": self.b,

            "model": "pi",
            "rate_mva": self.rate_mva,

            # Fixed for a physical transmission line.
            "tap": 1.0,
            "shift": 0.0,

            "in_service": self.in_service,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        from_id = (
            self.from_endpoint.id
            if self.from_endpoint is not None
            else None
        )

        to_id = (
            self.to_endpoint.id
            if self.to_endpoint is not None
            else None
        )

        return (
            f"<Line "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"r={self.r:.6f}, "
            f"x={self.x:.6f}, "
            f"b={self.b:.6f}, "
            f"rate={self.rate_mva:.2f} MVA, "
            f"in_service={self.in_service}>"
        )
