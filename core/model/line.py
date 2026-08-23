# core/model/line.py
"""
GridForge V2 Transmission Line Model
=====================================

Author:
    Subhendu Mishra

A Line is a physical two-terminal electrical conductor-system model.

Architecture
------------

    endpoint_from
         │
      Terminal
         │
       Line
         │
      Terminal
         │
    endpoint_to

The Line is a specialized Branch.

The authoritative local connectivity is held by:

    from_terminal
    to_terminal

The connected endpoints are obtained from those terminals.

The Line does NOT:

    - own global network topology
    - maintain bus collections
    - add itself to a Grid
    - build Y-bus matrices
    - stamp numerical matrices
    - solve power flow
    - solve short circuit
    - perform protection calculations
    - perform dynamic simulation
    - manage SLD geometry
    - manage GUI state

Electrical model
----------------

The Line uses the standard transmission-line pi equivalent:

    Z = R + jX

    Y_shunt,total = jB

where B is the TOTAL line shunt susceptance.

The numerical/network layer is responsible for applying:

    jB / 2

at each terminal during network assembly.

Units
-----

    r        : per-unit
    x        : per-unit
    b        : per-unit
    rate_mva : MVA

A Line has no transformer tap or phase-shift parameter.

    tap   = 1.0
    shift = 0.0

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .branch import Branch
from .terminal import Terminal


class Line(Branch):
    """
    Physical two-terminal transmission/distribution line.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint_from:
        Initial from-side electrical endpoint.

        May be None, a Bus-like object, or a Terminal.

    endpoint_to:
        Initial to-side electrical endpoint.

        May be None, a Bus-like object, or a Terminal.

    r:
        Series resistance in per-unit.

    x:
        Series reactance in per-unit.

    b:
        Total line shunt susceptance in per-unit.

    name:
        Human-readable line name.

    rate_mva:
        Optional thermal/equipment rating in MVA.
    """

    TYPE = "LINE"

    def __init__(
        self,
        id: str,
        endpoint_from=None,
        endpoint_to=None,
        *,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        name: str = "",
        rate_mva: float | None = None,
    ) -> None:

        # ---------------------------------------------------------
        # Initialize Branch once.
        #
        # Branch creates the authoritative two terminals.
        # We do not replace them afterwards.
        # ---------------------------------------------------------

        super().__init__(
            id=id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            b=b,
            name=name,
            rate_mva=rate_mva,
            tap=1.0,
            shift=0.0,
        )

        self.validate_parameters()

    # =============================================================
    # IDENTITY
    # =============================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # =============================================================
    # LINE MODEL
    # =============================================================

    @property
    def is_pi_model(self) -> bool:
        """
        Return True because the Line uses the standard pi-equivalent.
        """

        return True

    @property
    def total_shunt_susceptance(self) -> float:
        """
        Return total line shunt susceptance B in per-unit.

        The numerical/network layer decides how B is distributed
        between the two terminals.
        """

        return self.b

    @property
    def half_shunt_susceptance(self) -> float:
        """
        Return B/2 for one terminal of the standard pi model.
        """

        return self.b / 2.0

    @property
    def shunt_admittance_total(self) -> complex:
        """
        Return total line shunt admittance.

            Ysh,total = jB
        """

        return complex(
            0.0,
            self.b,
        )

    @property
    def shunt_admittance_per_end(self) -> complex:
        """
        Return the shunt admittance assigned to one end.

            Ysh,end = jB/2
        """

        return complex(
            0.0,
            self.b / 2.0,
        )

    # =============================================================
    # SERIES MODEL
    # =============================================================

    @property
    def series_impedance(self) -> complex:
        """
        Return:

            Z = R + jX
        """

        return complex(
            self.r,
            self.x,
        )

    @property
    def series_admittance(self) -> complex:
        """
        Return:

            Y = 1 / Z

        Numerical matrix construction remains outside Line.
        """

        z = self.series_impedance

        if abs(z) <= 1e-15:
            raise ZeroDivisionError(
                f"Line '{self.id}' has zero series impedance."
            )

        return 1.0 / z

    # =============================================================
    # ELECTRICAL PARAMETERS
    # =============================================================

    @property
    def r_pu(self) -> float:
        """Return series resistance in per-unit."""

        return self.r

    @property
    def x_pu(self) -> float:
        """Return series reactance in per-unit."""

        return self.x

    @property
    def b_pu(self) -> float:
        """Return total shunt susceptance in per-unit."""

        return self.b

    # =============================================================
    # TERMINALS
    # =============================================================

    @property
    def terminals(self) -> tuple[Terminal, Terminal]:
        """
        Return the two authoritative Line terminals.
        """

        return (
            self.from_terminal,
            self.to_terminal,
        )

    @property
    def from_endpoint(self):
        """Return the authoritative from-side endpoint."""

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self):
        """Return the authoritative to-side endpoint."""

        return self.to_terminal.endpoint

    def endpoints(self) -> tuple:
        """
        Return:

            (from_endpoint, to_endpoint)
        """

        return (
            self.from_endpoint,
            self.to_endpoint,
        )

    # =============================================================
    # BUS COMPATIBILITY
    # =============================================================

    @property
    def from_bus(self):
        """
        Return the bus derived from the from terminal.

        This is a compatibility accessor only.
        """

        return self.from_terminal.bus

    @property
    def to_bus(self):
        """
        Return the bus derived from the to terminal.

        This is a compatibility accessor only.
        """

        return self.to_terminal.bus

    def buses(self) -> tuple:
        """
        Return derived bus references.

        No global topology is resolved here.
        """

        return (
            self.from_bus,
            self.to_bus,
        )

    # =============================================================
    # CONNECTIVITY
    # =============================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both physical endpoints are assigned.
        """

        return (
            self.from_terminal.is_connected
            and self.to_terminal.is_connected
        )

    @property
    def has_from_endpoint(self) -> bool:
        """Return True if the from terminal is connected."""

        return self.from_terminal.is_connected

    @property
    def has_to_endpoint(self) -> bool:
        """Return True if the to terminal is connected."""

        return self.to_terminal.is_connected

    # =============================================================
    # TERMINAL OPERATIONS
    # =============================================================

    def connect_from(self, endpoint) -> None:
        """
        Assign the physical from-side endpoint.

        Global topology is not modified here.
        """

        self.from_terminal.connect(endpoint)

    def connect_to(self, endpoint) -> None:
        """
        Assign the physical to-side endpoint.

        Global topology is not modified here.
        """

        self.to_terminal.connect(endpoint)

    def disconnect_from(self) -> None:
        """
        Remove the from-side endpoint.
        """

        self.from_terminal.disconnect()

    def disconnect_to(self) -> None:
        """
        Remove the to-side endpoint.
        """

        self.to_terminal.disconnect()

    # =============================================================
    # SERVICE STATE
    # =============================================================

    def connect(self) -> None:
        """
        Place the Line in service.

        This does not connect either terminal.
        """

        self.in_service = True

    def disconnect(self) -> None:
        """
        Take the Line out of service.

        This does not disconnect either terminal.
        """

        self.in_service = False

    def close(self) -> None:
        """Compatibility alias for connect()."""

        self.connect()

    def trip(self) -> None:
        """Compatibility alias for disconnect()."""

        self.disconnect()

    @property
    def is_in_service(self) -> bool:
        """Return True when the Line is in service."""

        return self.in_service

    # =============================================================
    # RATING
    # =============================================================

    @property
    def has_rating(self) -> bool:
        """Return whether a thermal rating is defined."""

        return self.rate_mva is not None

    def set_rating(
        self,
        rate_mva: float | None,
    ) -> None:
        """
        Set or clear the Line thermal rating.
        """

        if rate_mva is None:
            self.rate_mva = None
            return

        rate_mva = float(rate_mva)

        if not math.isfinite(rate_mva) or rate_mva <= 0.0:
            raise ValueError(
                f"Line '{self.id}' rate_mva must be finite "
                "and greater than zero."
            )

        self.rate_mva = rate_mva

    # =============================================================
    # VALIDATION
    # =============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Line-local engineering parameters.

        This deliberately does not validate network topology.
        """

        self.r = self._validate_finite(
            self.r,
            "r",
        )

        self.x = self._validate_finite(
            self.x,
            "x",
        )

        self.b = self._validate_finite(
            self.b,
            "b",
        )

        if self.r < 0.0:
            raise ValueError(
                f"Line '{self.id}' resistance cannot be negative."
            )

        if (
            math.isclose(
                self.r,
                0.0,
                abs_tol=1e-15,
            )
            and math.isclose(
                self.x,
                0.0,
                abs_tol=1e-15,
            )
        ):
            raise ValueError(
                f"Line '{self.id}' cannot have zero "
                "series impedance."
            )

        if self.rate_mva is not None:
            self.rate_mva = self._validate_positive(
                self.rate_mva,
                "rate_mva",
            )

        # A physical transmission line never uses transformer
        # tap or phase shift.
        self.tap = 1.0
        self.shift = 0.0

        return True

    def validate(self) -> bool:
        """
        Public local validation entry point.

        Network topology is intentionally not validated here.
        """

        return self.validate_parameters()

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return a structured Line diagnostic representation.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

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

            "is_connected": self.is_connected,
            "in_service": self.in_service,

            "model": "pi",

            "r_pu": self.r,
            "x_pu": self.x,
            "b_pu": self.b,

            "series_impedance": self.series_impedance,
            "series_admittance": self.series_admittance,

            "total_shunt_admittance":
                self.shunt_admittance_total,

            "shunt_admittance_per_end":
                self.shunt_admittance_per_end,

            "rate_mva": self.rate_mva,

            # Fixed for Line.
            "tap": 1.0,
            "shift": 0.0,
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
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
            f"rate={self.rate_mva}, "
            f"in_service={self.in_service}>"
        )

    # =============================================================
    # LOCAL HELPERS
    # =============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Return a finite floating-point value."""

        value = float(value)

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @staticmethod
    def _validate_positive(
        value: float,
        name: str,
    ) -> float:
        """Return a finite positive floating-point value."""

        value = float(value)

        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(
                f"{name} must be finite and greater than zero."
            )

        return value
