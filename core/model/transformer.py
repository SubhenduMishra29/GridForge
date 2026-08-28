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
a physical static transformer.

Architecture
------------

    ElectricalObject
          |
          v
        Branch
          |
          v
      Transformer

Ownership
---------

ElectricalObject owns:

    - stable identity;
    - human-readable name;
    - base validation contract.

Branch owns:

    - from_terminal;
    - to_terminal;
    - endpoint references;
    - branch-local impedance parameters;
    - branch rating;
    - operational state.

Transformer owns only transformer-specific configuration:

    - tap ratio;
    - phase shift.

Transformer does NOT own:

    - Bus objects;
    - Network topology;
    - Terminal objects supplied by callers;
    - Network collections;
    - endpoint resolution;
    - study-specific state;
    - solved numerical state;
    - Y-bus matrices;
    - solver indices;
    - protection logic;
    - control logic;
    - SLD geometry;
    - GUI state;
    - persistence.

Terminal Boundary
-----------------

Transformer inherits the authoritative two-terminal interface
from Branch.

It does not accept external Terminal objects and does not share
Terminal instances.

Endpoint interpretation and authoritative topology remain
Network responsibilities.

Electrical Boundary
-------------------

The generic branch electrical parameters are owned by Branch.

Transformer adds only transformer-specific static parameters:

    tap
    shift

The analysis/numerical layers determine how these parameters
participate in a particular mathematical formulation.

Automatic tap-changing, voltage regulation, OLTC control, and
study-specific transformer behavior are outside this model.

Validation Boundary
-------------------

The public validation entry point is inherited from
ElectricalObject.

The validation chain is:

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

    Transformer-specific state is limited to tap ratio and phase
    shift. Terminal ownership, endpoint state, generic branch
    impedance, rating, and operational state remain owned by the
    inherited Branch.
    """

    TYPE = "TRANSFORMER"

    def __init__(
        self,
        id: str,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        *,
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

        tap:
            Static transformer magnitude tap ratio.

        shift:
            Static transformer phase shift in radians.

        name:
            Human-readable transformer name.

        rate_mva:
            Optional branch rating inherited from Branch.

        in_service:
            Operational state inherited from Branch.

        Notes
        -----
        Generic branch electrical parameters and operational
        properties remain owned by Branch.

        Validation is deliberately deferred until construction
        has completed.
        """

        super().__init__(
            id=id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            name=name,
            rate_mva=rate_mva,
            in_service=in_service,
        )

        self._tap = self._validate_positive(
            tap,
            "tap",
        )

        self._shift = self._validate_finite(
            shift,
            "shift",
        )

        # Intentionally no validation call here.
        #
        # The public ElectricalObject.validate() entry point is
        # used after complete construction.

    # ============================================================
    # TYPE
    # ============================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge element type.
        """

        return self.TYPE

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

        This is an alias for tap.
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
        Return the configured static transformer ratio.

        The static ratio is represented by the tap value.
        """

        return self._tap

    def set_tap(
        self,
        tap: float,
    ) -> None:
        """
        Set the static transformer tap ratio.

        This does not implement automatic tap control or OLTC
        behavior.
        """

        self.tap = tap

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
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate the complete Transformer parameter hierarchy.

        Validation order:

            Transformer
                |
                v
            Branch
                |
                v
            ElectricalObject
        """

        Branch.validate_parameters(
            self
        )

        self._tap = self._validate_positive(
            self._tap,
            "tap",
        )

        self._shift = self._validate_finite(
            self._shift,
            "shift",
        )

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return Transformer-local diagnostics.

        Generic branch state is obtained through the inherited
        Branch summary where available.

        No from_bus or to_bus attributes are used.
        """

        summary = super().summary()

        summary.update(
            {
                "type": self.TYPE,
                "tap": self._tap,
                "tap_ratio": self._tap,
                "shift_rad": self._shift,
                "shift_deg": self.phase_shift_deg,
            }
        )

        return summary

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        from_endpoint = self.from_endpoint
        to_endpoint = self.to_endpoint

        from_id = (
            from_endpoint.id
            if from_endpoint is not None
            else None
        )

        to_id = (
            to_endpoint.id
            if to_endpoint is not None
            else None
        )

        return (
            f"<Transformer "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"tap={self._tap:.6f}, "
            f"shift={self._shift:.6f} rad>"
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

    @staticmethod
    def _validate_positive(
        value: float,
        name: str,
    ) -> float:
        """
        Validate a finite positive numeric value.
        """

        value = Transformer._validate_finite(
            value,
            name,
        )

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value


__all__ = [
    "Transformer",
]
