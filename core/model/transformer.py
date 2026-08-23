# core/model/transformer.py
"""
GridForge V2 Transformer Model
==============================

Author:
    Subhendu Mishra

Static two-terminal transformer electrical model.

Architecture
------------

    ElectricalObject
          |
        Branch
          |
      Transformer
       /        \
    Terminal  Terminal

Branch owns:

    - two authoritative terminals
    - endpoint access
    - connectivity
    - operational state
    - generic branch rating
    - generic r/x/b storage

Transformer owns:

    - transformer-specific r/x/b interpretation
    - static tap ratio
    - static phase shift
    - transformer-specific validation
    - transformer diagnostics

This model does NOT own:

    - global network topology
    - bus collections
    - Y-bus construction
    - load-flow solving
    - short-circuit solving
    - OLTC control
    - protection logic
    - dynamic simulation
    - SLD geometry
    - GUI state

Tap ratio and phase shift are static electrical parameters.
Changing them is a model mutation; automatic tap-control logic belongs
to a separate application/domain service.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .branch import Branch


class Transformer(Branch):
    """
    Static two-terminal transformer model.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint_from:
        Optional initial from-side endpoint.

    endpoint_to:
        Optional initial to-side endpoint.

    r:
        Equivalent series resistance in per-unit.

    x:
        Equivalent series reactance in per-unit.

    b:
        Equivalent total shunt susceptance in per-unit.

    tap:
        Static magnitude tap ratio.

    shift:
        Static phase shift in radians.

    name:
        Human-readable transformer name.

    rate_mva:
        Optional transformer rating in MVA.

    in_service:
        Initial operational state.
    """

    TYPE = "TRANSFORMER"

    def __init__(
        self,
        id: str,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        *,
        r: float,
        x: float,
        b: float = 0.0,
        tap: float = 1.0,
        shift: float = 0.0,
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
            tap=tap,
            shift=shift,
            in_service=in_service,
        )

        self.validate_parameters()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # =================================================================
    # STATIC TRANSFORMER PARAMETERS
    # =================================================================

    @property
    def turns_ratio(self) -> float:
        """
        Return the configured static magnitude ratio.

        In this simplified per-unit model, the ratio is represented
        by the static tap parameter.
        """

        return self.tap

    @property
    def tap_ratio(self) -> float:
        """Return the static tap ratio."""

        return self.tap

    @property
    def phase_shift_rad(self) -> float:
        """Return static phase shift in radians."""

        return self.shift

    @property
    def phase_shift_deg(self) -> float:
        """Return static phase shift in degrees."""

        return math.degrees(self.shift)

    # =================================================================
    # TAP
    # =================================================================

    def set_tap(
        self,
        tap: float,
    ) -> None:
        """
        Set the static tap ratio.

        This does not implement automatic voltage regulation or OLTC
        control.
        """

        self.tap = self._validate_positive(
            tap,
            "tap",
        )

    # =================================================================
    # PHASE SHIFT
    # =================================================================

    def set_phase_shift(
        self,
        shift: float,
    ) -> None:
        """
        Set static phase shift in radians.
        """

        self.shift = self._validate_finite(
            shift,
            "shift",
        )

    def set_phase_shift_degrees(
        self,
        degrees: float,
    ) -> None:
        """
        Set static phase shift in degrees.
        """

        degrees = self._validate_finite(
            degrees,
            "degrees",
        )

        self.shift = math.radians(
            degrees
        )

    # =================================================================
    # RATING
    # =================================================================

    @property
    def has_rating(self) -> bool:
        """Return whether a transformer rating is defined."""

        return self.rate_mva is not None

    def set_rating(
        self,
        rate_mva: float | None,
    ) -> None:
        """Set or clear the transformer rating."""

        if rate_mva is None:
            self.rate_mva = None
            return

        self.rate_mva = self._validate_positive(
            rate_mva,
            "rate_mva",
        )

    # =================================================================
    # ELECTRICAL MODEL
    # =================================================================

    @property
    def series_impedance(self) -> complex:
        """
        Return transformer equivalent series impedance.

            Z = R + jX
        """

        if self.r is None or self.x is None:
            raise ValueError(
                f"Transformer '{self.id}' requires "
                "both r and x."
            )

        return complex(
            self.r,
            self.x,
        )

    @property
    def series_admittance(self) -> complex:
        """
        Return transformer equivalent series admittance.

            Y = 1 / Z
        """

        z = self.series_impedance

        if abs(z) <= 1e-15:
            raise ZeroDivisionError(
                f"Transformer '{self.id}' has zero "
                "series impedance."
            )

        return 1.0 / z

    @property
    def shunt_admittance(self) -> complex:
        """
        Return equivalent total shunt admittance.

            Ysh = jB
        """

        return complex(
            0.0,
            self.b if self.b is not None else 0.0,
        )

    # =================================================================
    # PER-UNIT ACCESSORS
    # =================================================================

    @property
    def r_pu(self) -> float:
        """Return transformer resistance in per-unit."""

        if self.r is None:
            raise ValueError(
                f"Transformer '{self.id}' does not define r."
            )

        return self.r

    @property
    def x_pu(self) -> float:
        """Return transformer reactance in per-unit."""

        if self.x is None:
            raise ValueError(
                f"Transformer '{self.id}' does not define x."
            )

        return self.x

    @property
    def b_pu(self) -> float:
        """Return transformer shunt susceptance in per-unit."""

        return self.b if self.b is not None else 0.0

    # =================================================================
    # ELECTRICAL PARAMETERS
    # =================================================================

    def get_electrical_parameters(
        self,
    ) -> dict[str, float | None]:
        """
        Return static transformer parameters.

        The numerical layer decides how these parameters are stamped
        into a particular network formulation.
        """

        return {
            "r_pu": self.r_pu,
            "x_pu": self.x_pu,
            "b_pu": self.b_pu,
            "tap": self.tap,
            "shift_rad": self.shift,
            "rate_mva": self.rate_mva,
        }

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate transformer-local parameters.

        Branch validation is intentionally used as the common
        foundation, while Transformer applies its own requirements.
        """

        super().validate_parameters()

        if self.r is None:
            raise ValueError(
                f"Transformer '{self.id}' requires resistance r."
            )

        if self.x is None:
            raise ValueError(
                f"Transformer '{self.id}' requires reactance x."
            )

        self.r = self._validate_finite(
            self.r,
            "r",
        )

        self.x = self._validate_finite(
            self.x,
            "x",
        )

        self.b = self._validate_finite(
            self.b if self.b is not None else 0.0,
            "b",
        )

        if self.r < 0.0:
            raise ValueError(
                f"Transformer '{self.id}' resistance "
                "cannot be negative."
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
                f"Transformer '{self.id}' cannot have "
                "zero series impedance."
            )

        self.tap = self._validate_positive(
            self.tap,
            "tap",
        )

        self.shift = self._validate_finite(
            self.shift,
            "shift",
        )

        if self.rate_mva is not None:
            self.rate_mva = self._validate_positive(
                self.rate_mva,
                "rate_mva",
            )

        return True

    def validate(self) -> bool:
        """
        Public Transformer validation entry point.

        Network topology and study-specific validity are outside this
        model.
        """

        return self.validate_parameters()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return structured transformer diagnostics."""

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

            "r_pu": self.r_pu,
            "x_pu": self.x_pu,
            "b_pu": self.b_pu,

            "series_impedance":
                self.series_impedance,

            "series_admittance":
                self.series_admittance,

            "shunt_admittance":
                self.shunt_admittance,

            "tap_ratio":
                self.tap_ratio,

            "phase_shift_rad":
                self.phase_shift_rad,

            "phase_shift_deg":
                self.phase_shift_deg,

            "rate_mva":
                self.rate_mva,
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
            f"<Transformer "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"r={self.r_pu:.6f}, "
            f"x={self.x_pu:.6f}, "
            f"b={self.b_pu:.6f}, "
            f"tap={self.tap_ratio:.6f}, "
            f"shift={self.phase_shift_rad:.6f}, "
            f"rate={self.rate_mva}, "
            f"in_service={self.in_service}>"
        )

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Validate and return a finite floating-point value."""

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

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
        """Validate and return a finite positive value."""

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value


__all__ = [
    "Transformer",
]
