# core/model/line.py
"""
GridForge V2 Transmission Line Model
=====================================

Author:
    Subhendu Mishra

A Line is a physical two-terminal electrical branch using the
standard transmission-line pi equivalent.

Architecture
------------

    ElectricalObject
          │
        Branch
          │
        Line
          │
       ┌──┴──┐
    from   to
   Terminal Terminal

Branch owns the common two-terminal contract.

Line owns only transmission-line-specific electrical behavior.

Line does NOT own:

    - global network topology
    - bus collections
    - network registration
    - Y-bus construction
    - numerical matrix stamping
    - power-flow solving
    - short-circuit solving
    - protection calculations
    - dynamic simulation
    - SLD geometry
    - GUI state

Electrical model
----------------

Standard pi equivalent:

    Z = R + jX

    Y_series = 1 / Z

    Y_shunt,total = jB

    Y_shunt,end = jB / 2

The numerical/network layer is responsible for using these
quantities during network assembly.

Units
-----

    r        : per-unit
    x        : per-unit
    b        : per-unit
    rate_mva : MVA

A Line does not have transformer tap or phase-shift parameters.

    tap   = 1.0
    shift = 0.0

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .branch import Branch


class Line(Branch):
    """
    Physical two-terminal transmission/distribution line.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint_from:
        Optional initial from-side endpoint.

    endpoint_to:
        Optional initial to-side endpoint.

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

    in_service:
        Initial operational state.
    """

    TYPE = "LINE"

    def __init__(
        self,
        id: str,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        *,
        r: float,
        x: float,
        b: float = 0.0,
        name: str = "",
        rate_mva: float | None = None,
        in_service: bool = True,
    ) -> None:

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
            in_service=in_service,
        )

        self.validate_parameters()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """Return the canonical GridForge element type."""

        return self.TYPE

    # =================================================================
    # MODEL
    # =================================================================

    @property
    def model_type(self) -> str:
        """Return the Line electrical model."""

        return "pi"

    @property
    def is_pi_model(self) -> bool:
        """Return True because the Line uses the pi equivalent."""

        return True

    # =================================================================
    # SERIES MODEL
    # =================================================================

    @property
    def series_impedance(self) -> complex:
        """
        Return the series impedance.

            Z = R + jX
        """

        if self.r is None or self.x is None:
            raise ValueError(
                f"Line '{self.id}' requires both r and x."
            )

        return complex(
            self.r,
            self.x,
        )

    @property
    def series_admittance(self) -> complex:
        """
        Return the series admittance.

            Y = 1 / Z
        """

        z = self.series_impedance

        if abs(z) <= 1e-15:
            raise ZeroDivisionError(
                f"Line '{self.id}' has zero series impedance."
            )

        return 1.0 / z

    # =================================================================
    # SHUNT MODEL
    # =================================================================

    @property
    def total_shunt_susceptance(self) -> float:
        """
        Return total line shunt susceptance B.

        The returned value represents the complete line, not one end.
        """

        if self.b is None:
            return 0.0

        return self.b

    @property
    def half_shunt_susceptance(self) -> float:
        """
        Return B/2 for one terminal of the pi model.
        """

        return self.total_shunt_susceptance / 2.0

    @property
    def shunt_admittance_total(self) -> complex:
        """
        Return total shunt admittance.

            Ysh,total = jB
        """

        return complex(
            0.0,
            self.total_shunt_susceptance,
        )

    @property
    def shunt_admittance_per_end(self) -> complex:
        """
        Return shunt admittance assigned to one end.

            Ysh,end = jB/2
        """

        return complex(
            0.0,
            self.half_shunt_susceptance,
        )

    # =================================================================
    # PER-UNIT ACCESSORS
    # =================================================================

    @property
    def r_pu(self) -> float:
        """Return series resistance in per-unit."""

        if self.r is None:
            raise ValueError(
                f"Line '{self.id}' does not define r."
            )

        return self.r

    @property
    def x_pu(self) -> float:
        """Return series reactance in per-unit."""

        if self.x is None:
            raise ValueError(
                f"Line '{self.id}' does not define x."
            )

        return self.x

    @property
    def b_pu(self) -> float:
        """Return total shunt susceptance in per-unit."""

        if self.b is None:
            return 0.0

        return self.b

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Line-specific electrical parameters.

        Branch permits r/x/b to be optional because specialized
        branches may use other physical parameterizations.

        Line, however, requires a valid generic per-unit r/x model.
        """

        # -------------------------------------------------------------
        # Validate common Branch parameters first.
        # -------------------------------------------------------------

        super().validate_parameters()

        # -------------------------------------------------------------
        # Line requires r and x.
        # -------------------------------------------------------------

        if self.r is None:
            raise ValueError(
                f"Line '{self.id}' requires resistance r."
            )

        if self.x is None:
            raise ValueError(
                f"Line '{self.id}' requires reactance x."
            )

        if self.b is None:
            self.b = 0.0

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

        # -------------------------------------------------------------
        # Physical resistance cannot be negative.
        # -------------------------------------------------------------

        if self.r < 0.0:
            raise ValueError(
                f"Line '{self.id}' resistance cannot be negative."
            )

        # -------------------------------------------------------------
        # A Line cannot have zero series impedance.
        # -------------------------------------------------------------

        if math.isclose(
            self.r,
            0.0,
            abs_tol=1e-15,
        ) and math.isclose(
            self.x,
            0.0,
            abs_tol=1e-15,
        ):
            raise ValueError(
                f"Line '{self.id}' cannot have zero "
                "series impedance."
            )

        # -------------------------------------------------------------
        # Lines do not use transformer parameters.
        # -------------------------------------------------------------

        self.tap = 1.0
        self.shift = 0.0

        return True

    def validate(self) -> bool:
        """
        Validate the complete Line model.

        Topology is deliberately not validated here.
        """

        return self.validate_parameters()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured Line diagnostics.

        Endpoint information comes from Branch/Terminal state.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "model": self.model_type,

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

            "r_pu": self.r_pu,
            "x_pu": self.x_pu,
            "b_pu": self.b_pu,

            "series_impedance": self.series_impedance,
            "series_admittance": self.series_admittance,

            "total_shunt_admittance":
                self.shunt_admittance_total,

            "shunt_admittance_per_end":
                self.shunt_admittance_per_end,

            "rate_mva": self.rate_mva,

            "tap": 1.0,
            "shift": 0.0,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

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
            f"r={self.r_pu:.6f}, "
            f"x={self.x_pu:.6f}, "
            f"b={self.b_pu:.6f}, "
            f"rate={self.rate_mva}, "
            f"in_service={self.in_service}>"
        )


__all__ = [
    "Line",
]
