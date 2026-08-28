# ============================================================
# File: core/model/transformer.py
#
# GridForge V2 — Transformer Model
#
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Transformer Model
==============================

A Transformer is a specialized two-terminal Branch representing
a static physical transformer.

Architecture
------------

    ElectricalObject
          |
          v
        Branch
          |
          v
      Transformer
        /      \
    Terminal  Terminal

Ownership
---------

Branch owns:

    - the two authoritative terminals;
    - endpoint references;
    - local connectivity;
    - operational state;
    - generic branch rating.

Transformer owns:

    - transformer-specific electrical parameters;
    - static tap ratio;
    - static phase shift;
    - transformer-specific validation;
    - transformer diagnostics.

Transformer does NOT own:

    - Bus objects;
    - Network topology;
    - Network collections;
    - endpoint resolution;
    - Y-bus construction;
    - solver indices;
    - load-flow calculations;
    - short-circuit calculations;
    - OLTC control;
    - protection logic;
    - dynamic simulation;
    - SLD geometry;
    - GUI state;
    - persistence.

Topology Boundary
-----------------

Transformer is terminal-centric.

Its connectivity is represented through the inherited:

    from_terminal
    to_terminal

and their endpoint references.

Transformer never owns or adopts Bus objects.

Network is responsible for authoritative topology and for
interpreting endpoint relationships.

Electrical Boundary
-------------------

The Transformer stores static physical/electrical parameters.

The numerical/analysis layer decides how those parameters are
converted into a particular network formulation.

Tap ratio and phase shift are static model parameters.

Automatic tap control, voltage regulation, and OLTC behavior
belong outside this model.

Validation Boundary
-------------------

The public validation entry point is inherited from
ElectricalObject.

The concrete validation chain is:

    ElectricalObject.validate()
            |
            v
    Transformer.validate_parameters()
            |
            v
    Branch.validate_parameters()
            |
            v
    ElectricalObject.validate_parameters()

The Transformer constructor does not invoke validation.

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

    Transformer-specific parameters are maintained locally while
    terminal ownership and endpoint connectivity remain inherited
    from Branch.
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
        """
        Construct a static two-terminal Transformer.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint_from:
            Optional initial endpoint reference for the from
            terminal.

        endpoint_to:
            Optional initial endpoint reference for the to
            terminal.

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

        Notes
        -----
        Transformer-specific state is initialized after the
        Branch state.

        Validation is intentionally deferred. The constructor
        does not call validate() or validate_parameters().
        """

        super().__init__(
            id=id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            name=name,
            rate_mva=rate_mva,
            in_service=in_service,
        )

        self._r = self._validate_finite(
            r,
            "r",
        )

        self._x = self._validate_finite(
            x,
            "x",
        )

        self._b = self._validate_finite(
            b,
            "b",
        )

        self._tap = self._validate_positive(
            tap,
            "tap",
        )

        self._shift = self._validate_finite(
            shift,
            "shift",
        )

        self._rate_mva = self._validate_optional_positive(
            rate_mva,
            "rate_mva",
        )

        self._in_service = self._validate_bool(
            in_service,
            "in_service",
        )

    # ============================================================
    # IDENTITY
    # ============================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge element type.
        """

        return self.TYPE

    # ============================================================
    # ELECTRICAL PARAMETERS
    # ============================================================

    @property
    def r(self) -> float:
        """
        Return equivalent series resistance in per-unit.
        """

        return self._r

    @r.setter
    def r(self, value: float) -> None:
        self._r = self._validate_finite(
            value,
            "r",
        )

    @property
    def x(self) -> float:
        """
        Return equivalent series reactance in per-unit.
        """

        return self._x

    @x.setter
    def x(self, value: float) -> None:
        self._x = self._validate_finite(
            value,
            "x",
        )

    @property
    def b(self) -> float:
        """
        Return equivalent total shunt susceptance in per-unit.
        """

        return self._b

    @b.setter
    def b(self, value: float) -> None:
        self._b = self._validate_finite(
            value,
            "b",
        )

    # ============================================================
    # TAP RATIO
    # ============================================================

    @property
    def tap(self) -> float:
        """
        Return the static magnitude tap ratio.
        """

        return self._tap

    @tap.setter
    def tap(self, value: float) -> None:
        self._tap = self._validate_positive(
            value,
            "tap",
        )

    @property
    def tap_ratio(self) -> float:
        """
        Return the static magnitude tap ratio.
        """

        return self._tap

    @tap_ratio.setter
    def tap_ratio(self, value: float) -> None:
        self._tap = self._validate_positive(
            value,
            "tap_ratio",
        )

    @property
    def turns_ratio(self) -> float:
        """
        Return the configured static magnitude ratio.

        In this model the static transformer ratio is represented
        by the tap parameter.
        """

        return self._tap

    # ============================================================
    # PHASE SHIFT
    # ============================================================

    @property
    def shift(self) -> float:
        """
        Return static phase shift in radians.
        """

        return self._shift

    @shift.setter
    def shift(self, value: float) -> None:
        self._shift = self._validate_finite(
            value,
            "shift",
        )

    @property
    def phase_shift_rad(self) -> float:
        """
        Return static phase shift in radians.
        """

        return self._shift

    @phase_shift_rad.setter
    def phase_shift_rad(self, value: float) -> None:
        self._shift = self._validate_finite(
            value,
            "phase_shift_rad",
        )

    @property
    def phase_shift_deg(self) -> float:
        """
        Return static phase shift in degrees.
        """

        return math.degrees(
            self._shift
        )

    @phase_shift_deg.setter
    def phase_shift_deg(self, value: float) -> None:
        value = self._validate_finite(
            value,
            "phase_shift_deg",
        )

        self._shift = math.radians(
            value
        )

    # ============================================================
    # RATING
    # ============================================================

    @property
    def rate_mva(self) -> float | None:
        """
        Return transformer rating in MVA.
        """

        return self._rate_mva

    @rate_mva.setter
    def rate_mva(
        self,
        value: float | None,
    ) -> None:
        self._rate_mva = (
            self._validate_optional_positive(
                value,
                "rate_mva",
            )
        )

    @property
    def has_rating(self) -> bool:
        """
        Return whether a transformer rating is defined.
        """

        return self._rate_mva is not None

    def set_rating(
        self,
        rate_mva: float | None,
    ) -> None:
        """
        Set or clear the transformer rating.
        """

        self.rate_mva = rate_mva

    # ============================================================
    # STATIC TAP / SHIFT MUTATION
    # ============================================================

    def set_tap(
        self,
        tap: float,
    ) -> None:
        """
        Set the static transformer tap ratio.

        This method does not implement automatic voltage
        regulation or OLTC control.
        """

        self.tap = tap

    def set_phase_shift(
        self,
        shift: float,
    ) -> None:
        """
        Set static phase shift in radians.
        """

        self.shift = shift

    def set_phase_shift_degrees(
        self,
        degrees: float,
    ) -> None:
        """
        Set static phase shift in degrees.
        """

        self.phase_shift_deg = degrees

    # ============================================================
    # ELECTRICAL DERIVED VALUES
    # ============================================================

    @property
    def series_impedance(self) -> complex:
        """
        Return equivalent series impedance.

            Z = R + jX
        """

        return complex(
            self._r,
            self._x,
        )

    @property
    def series_admittance(self) -> complex:
        """
        Return equivalent series admittance.

            Y = 1 / Z

        A zero series impedance is invalid for this operation.
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
            self._b,
        )

    @property
    def r_pu(self) -> float:
        """
        Return resistance in per-unit.
        """

        return self._r

    @property
    def x_pu(self) -> float:
        """
        Return reactance in per-unit.
        """

        return self._x

    @property
    def b_pu(self) -> float:
        """
        Return shunt susceptance in per-unit.
        """

        return self._b

    def get_electrical_parameters(
        self,
    ) -> dict[str, float | None]:
        """
        Return static transformer electrical parameters.

        The numerical layer determines how these values are
        used in a particular network formulation.
        """

        return {
            "r_pu": self._r,
            "x_pu": self._x,
            "b_pu": self._b,
            "tap": self._tap,
            "shift_rad": self._shift,
            "rate_mva": self._rate_mva,
        }

    # ============================================================
    # OPERATIONAL STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the transformer is in service.
        """

        return self._in_service

    @in_service.setter
    def in_service(
        self,
        value: bool,
    ) -> None:
        self._in_service = self._validate_bool(
            value,
            "in_service",
        )

    @property
    def is_in_service(self) -> bool:
        """
        Compatibility/read-only alias for in_service.
        """

        return self._in_service

    @property
    def is_out_of_service(self) -> bool:
        """
        Return True when the transformer is out of service.
        """

        return not self._in_service

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """
        Set transformer operational state.
        """

        self.in_service = value

    def close(self) -> None:
        """
        Place the transformer in service.
        """

        self._in_service = True

    def trip(self) -> None:
        """
        Remove the transformer from service.
        """

        self._in_service = False

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate the complete Transformer parameter hierarchy.

        Validation order:

            Transformer
                ↓
            Branch
                ↓
            ElectricalObject
        """

        Branch.validate_parameters(
            self
        )

        self._r = self._validate_finite(
            self._r,
            "r",
        )

        self._x = self._validate_finite(
            self._x,
            "x",
        )

        self._b = self._validate_finite(
            self._b,
            "b",
        )

        self._tap = self._validate_positive(
            self._tap,
            "tap",
        )

        self._shift = self._validate_finite(
            self._shift,
            "shift",
        )

        self._rate_mva = (
            self._validate_optional_positive(
                self._rate_mva,
                "rate_mva",
            )
        )

        self._in_service = self._validate_bool(
            self._in_service,
            "in_service",
        )

        if self._r < 0.0:
            raise ValueError(
                f"Transformer '{self.id}' resistance "
                "cannot be negative."
            )

        if (
            math.isclose(
                self._r,
                0.0,
                abs_tol=1e-15,
            )
            and math.isclose(
                self._x,
                0.0,
                abs_tol=1e-15,
            )
        ):
            raise ValueError(
                f"Transformer '{self.id}' cannot have "
                "zero series impedance."
            )

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return Transformer-local diagnostics.

        Topology is represented through endpoint references only.

        No from_bus / to_bus attributes are used.
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

            "connected": self.is_connected,
            "in_service": self._in_service,

            "r_pu": self._r,
            "x_pu": self._x,
            "b_pu": self._b,

            "series_impedance":
                self.series_impedance,

            "series_admittance":
                self.series_admittance,

            "shunt_admittance":
                self.shunt_admittance,

            "tap_ratio":
                self._tap,

            "phase_shift_rad":
                self._shift,

            "phase_shift_deg":
                self.phase_shift_deg,

            "rate_mva":
                self._rate_mva,
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

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
            f"<Transformer "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"r={self._r:.6f}, "
            f"x={self._x:.6f}, "
            f"b={self._b:.6f}, "
            f"tap={self._tap:.6f}, "
            f"shift={self._shift:.6f}, "
            f"rate_mva={self._rate_mva}, "
            f"in_service={self._in_service}>"
        )

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """
        Validate a finite numeric value.
        """

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @classmethod
    def _validate_optional_positive(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """
        Validate an optional positive numeric value.
        """

        if value is None:
            return None

        value = cls._validate_finite(
            value,
            name,
        )

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value

    @staticmethod
    def _validate_positive(
        value: float,
        name: str,
    ) -> float:
        """
        Validate a finite positive numeric value.
        """

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
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

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> bool:
        """
        Validate a strict boolean.
        """

        if not isinstance(value, bool):
            raise ValueError(
                f"{name} must be boolean."
            )

        return value


__all__ = [
    "Transformer",
]
