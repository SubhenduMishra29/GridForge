# ============================================================
# File: core/model/line.py
#
# GridForge V2 — Line Model
#
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Line Model
=======================

A Line is a two-terminal electrical branch representing an
overhead or generic transmission/distribution line.

Architecture
------------

    ElectricalObject
          |
          v
        Branch
          |
          v
         Line
       /      \
from_terminal  to_terminal

Line owns line-specific physical parameters.

Line does NOT own:

    - Network topology
    - Bus objects
    - endpoint resolution
    - Network collections
    - Y-bus matrices
    - solver indices
    - solved numerical state
    - study-specific classifications
    - GUI/SLD state
    - persistence

Endpoint Boundary
-----------------

Line inherits the terminal-centric endpoint contract from Branch.

The Line model exposes:

    from_terminal
    to_terminal
    from_endpoint
    to_endpoint

It deliberately does NOT expose:

    from_bus
    to_bus

Bus resolution is a Network-layer responsibility.

Validation Boundary
-------------------

Validation enters through:

    ElectricalObject.validate()

which dispatches to:

    self.validate_parameters()

Because Line overrides validate_parameters(), Branch validation
is explicitly invoked through the inheritance chain.

Construction therefore follows:

    Branch initialization
            |
            v
    Line initialization
            |
            v
    Line.validate()
            |
            v
    ElectricalObject.validate()
            |
            v
    Line.validate_parameters()
            |
            v
    Branch.validate_parameters()
            |
            v
    ElectricalObject.validate_parameters()

No overridable validation method is called by Branch.__init__().

Electrical Model
----------------

The generic Line model supports:

    - series resistance r
    - series reactance x
    - total shunt susceptance b
    - optional MVA rating
    - operational state

The standard nominal π representation is:

        Yseries = 1 / (R + jX)

        Yshunt = jB

with B representing total line shunt susceptance.

The Line model does not assemble a global Y-bus.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

from .branch import Branch


class Line(Branch):
    """
    Two-terminal electrical line.

    The Line inherits terminal ownership, endpoint references,
    operational state, and generic branch infrastructure from
    Branch.

    Line-specific physical parameters are:

        resistance
        reactance
        shunt_susceptance

    The canonical internal representation is per-unit.
    """

    TYPE = "LINE"

    def __init__(
        self,
        id: str,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        *,
        resistance: float | None = None,
        reactance: float | None = None,
        shunt_susceptance: float | None = None,
        name: str = "",
        rate_mva: float | None = None,
        in_service: bool = True,
    ) -> None:
        """
        Construct a Line.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint_from:
            Optional endpoint reference for the from terminal.

        endpoint_to:
            Optional endpoint reference for the to terminal.

        resistance:
            Series resistance in per-unit.

        reactance:
            Series reactance in per-unit.

        shunt_susceptance:
            Total line shunt susceptance in per-unit.

        name:
            Human-readable line name.

        rate_mva:
            Optional thermal rating in MVA.

        in_service:
            Operational state.

        Notes
        -----
        The endpoints are endpoint references only. The Network
        layer is responsible for topology interpretation.

        Validation is intentionally deferred until the complete
        Line object has been initialized.
        """

        super().__init__(
            id=id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=resistance,
            x=reactance,
            b=shunt_susceptance,
            name=name,
            rate_mva=rate_mva,
            in_service=in_service,
        )

        # Validation is intentionally not performed here.
        #
        # Branch.__init__() also does not invoke
        # validate_parameters().
        #
        # The complete Line object is validated explicitly through
        # Line.validate().

    # ================================================================
    # IDENTITY
    # ================================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge element type.
        """

        return self.TYPE

    # ================================================================
    # LINE PARAMETERS
    # ================================================================

    @property
    def resistance(self) -> float | None:
        """
        Return series resistance in per-unit.
        """

        return self.r

    @resistance.setter
    def resistance(
        self,
        value: float | None,
    ) -> None:
        self.r = self._validate_optional_finite(
            value,
            "resistance",
        )

    @property
    def reactance(self) -> float | None:
        """
        Return series reactance in per-unit.
        """

        return self.x

    @reactance.setter
    def reactance(
        self,
        value: float | None,
    ) -> None:
        self.x = self._validate_optional_finite(
            value,
            "reactance",
        )

    @property
    def shunt_susceptance(self) -> float | None:
        """
        Return total shunt susceptance in per-unit.
        """

        return self.b

    @shunt_susceptance.setter
    def shunt_susceptance(
        self,
        value: float | None,
    ) -> None:
        self.b = self._validate_optional_finite(
            value,
            "shunt_susceptance",
        )

    # ================================================================
    # π MODEL
    # ================================================================

    @property
    def series_impedance(self) -> complex:
        """
        Return the line series impedance.

            Z = R + jX
        """

        if (
            self.resistance is None
            or self.reactance is None
        ):
            raise ValueError(
                f"Line '{self.id}' does not define "
                "complete series impedance."
            )

        z = complex(
            self.resistance,
            self.reactance,
        )

        if z == 0.0 + 0.0j:
            raise ZeroDivisionError(
                f"Line '{self.id}' has zero series impedance."
            )

        return z

    @property
    def series_admittance(self) -> complex:
        """
        Return the line series admittance.

            Y = 1 / Z
        """

        return 1.0 / self.series_impedance

    @property
    def total_shunt_admittance(self) -> complex:
        """
        Return the total line shunt admittance.

            Ysh = jB
        """

        if self.shunt_susceptance is None:
            return 0.0 + 0.0j

        return complex(
            0.0,
            self.shunt_susceptance,
        )

    @property
    def half_shunt_admittance(self) -> complex:
        """
        Return the shunt admittance assigned to either end of the
        nominal π equivalent.

            Yhalf = jB / 2
        """

        return (
            self.total_shunt_admittance / 2.0
        )

    @property
    def y_series(self) -> complex:
        """
        Alias for series_admittance.
        """

        return self.series_admittance

    @property
    def y_shunt(self) -> complex:
        """
        Alias for total_shunt_admittance.
        """

        return self.total_shunt_admittance

    # ================================================================
    # NOMINAL π PARAMETERS
    # ================================================================

    def pi_parameters(self) -> dict[str, complex]:
        """
        Return the nominal π-equivalent branch parameters.

        Returns
        -------
        dict
            Keys:

                y_series
                y_shunt_from
                y_shunt_to
        """

        y_series = self.series_admittance
        y_half = self.half_shunt_admittance

        return {
            "y_series": y_series,
            "y_shunt_from": y_half,
            "y_shunt_to": y_half,
        }

    # ================================================================
    # VALIDATION
    # ================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Line-specific parameters.

        The Branch validation contract is invoked first so that
        Branch-owned invariants remain authoritative.

        Validation chain:

            Line.validate_parameters()
                    |
                    v
            Branch.validate_parameters()
                    |
                    v
            ElectricalObject.validate_parameters()
        """

        Branch.validate_parameters(
            self
        )

        self.r = self._validate_optional_finite(
            self.r,
            "resistance",
        )

        self.x = self._validate_optional_finite(
            self.x,
            "reactance",
        )

        self.b = self._validate_optional_finite(
            self.b,
            "shunt_susceptance",
        )

        if (
            self.r is not None
            and self.x is not None
            and self.r == 0.0
            and self.x == 0.0
        ):
            raise ValueError(
                f"Line '{self.id}' cannot have zero "
                "series impedance."
            )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Line.

        ElectricalObject.validate() is the authoritative public
        validation entry point.

        Dynamic dispatch invokes:

            Line.validate_parameters()
                ↓
            Branch.validate_parameters()
                ↓
            ElectricalObject.validate_parameters()
        """

        return super().validate()

    # ================================================================
    # DIAGNOSTICS
    # ================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return Line-local diagnostic information.

        No Bus resolution, Network topology, or solved numerical
        state is included.
        """

        from_endpoint = self.from_endpoint
        to_endpoint = self.to_endpoint

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "from_endpoint": (
                from_endpoint.id
                if from_endpoint is not None
                and hasattr(from_endpoint, "id")
                else from_endpoint
            ),

            "to_endpoint": (
                to_endpoint.id
                if to_endpoint is not None
                and hasattr(to_endpoint, "id")
                else to_endpoint
            ),

            "connected": self.is_connected,
            "in_service": self.in_service,

            "resistance": self.resistance,
            "reactance": self.reactance,
            "shunt_susceptance": self.shunt_susceptance,

            "rate_mva": self.rate_mva,
        }

    # ================================================================
    # REPRESENTATION
    # ================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        from_endpoint = self.from_endpoint
        to_endpoint = self.to_endpoint

        from_id = (
            from_endpoint.id
            if from_endpoint is not None
            and hasattr(from_endpoint, "id")
            else from_endpoint
        )

        to_id = (
            to_endpoint.id
            if to_endpoint is not None
            and hasattr(to_endpoint, "id")
            else to_endpoint
        )

        return (
            f"<Line "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"r={self.resistance}, "
            f"x={self.reactance}, "
            f"b={self.shunt_susceptance}, "
            f"rate_mva={self.rate_mva}, "
            f"in_service={self.in_service}>"
        )

    # ================================================================
    # VALIDATION HELPERS
    # ================================================================

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
    def _validate_optional_finite(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """
        Validate an optional finite numeric value.
        """

        if value is None:
            return None

        return cls._validate_finite(
            value,
            name,
        )


__all__ = [
    "Line",
]
