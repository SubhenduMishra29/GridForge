# ============================================================
# File: core/model/line.py
# GridForge V2 — Transmission Line Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Transmission Line Model
=======================================

Concrete two-terminal transmission-line model.

Architecture
------------

    ElectricalObject
          │
          ▼
        Branch
          │
          ▼
         Line
       /      \
      ▼        ▼
 FROM Terminal  TO Terminal
      │              │
      ▼              ▼
 endpoint         endpoint

Line inherits the complete terminal and endpoint contract from
Branch.

Authoritative endpoint state is owned exclusively by:

    Branch.from_terminal
    Branch.to_terminal

Line does not maintain a second endpoint representation.

Electrical responsibility
-------------------------

Line owns line-specific electrical parameters and provides the
local π-model representation:

    Z = R + jX

    Yseries = 1 / Z

    Yshunt = jB

    Yhalf = jB / 2

Line does NOT:

    - resolve endpoints into buses;
    - mutate Network topology;
    - construct a global Y-bus;
    - assign numerical indices;
    - perform power-flow calculations;
    - perform short-circuit calculations;
    - perform protection calculations;
    - maintain UI/SLD state.

Validation
----------

Public validation is inherited from ElectricalObject.

Line-specific validation is implemented through:

    validate_parameters()

which delegates first to:

    Branch.validate_parameters()

and then validates Line-specific electrical invariants.

Parameter contract
------------------

The frozen Branch contract requires:

    r : float
    x : float
    b : float

Line therefore exposes its engineering-facing names as
properties delegating to those canonical Branch values:

    resistance
    reactance
    shunt_susceptance

These values are always numeric.

A physically invalid zero series impedance is rejected by
Line.validate_parameters().

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .branch import Branch


class Line(Branch):
    """
    Two-terminal transmission-line model.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint_from:
        Optional endpoint for the FROM terminal.

    endpoint_to:
        Optional endpoint for the TO terminal.

    resistance:
        Series resistance R.

    reactance:
        Series reactance X.

    shunt_susceptance:
        Total line shunt susceptance B.

    name:
        Human-readable line name.

    rate_mva:
        Optional continuous apparent-power rating.

    in_service:
        Whether the line is in service.

    Notes
    -----
    ``resistance``, ``reactance`` and ``shunt_susceptance`` are
    engineering-facing aliases over the canonical Branch
    parameters ``r``, ``x`` and ``b``.

    The endpoints are owned by the inherited Terminal objects.
    """

    __slots__ = ()

    def __init__(
        self,
        *,
        id: str,
        endpoint_from: Any | None = None,
        endpoint_to: Any | None = None,
        resistance: float = 0.0,
        reactance: float = 0.0,
        shunt_susceptance: float = 0.0,
        name: str | None = None,
        rate_mva: float | None = None,
        in_service: bool = True,
    ) -> None:
        """
        Construct a transmission line.

        Endpoint references are passed to Branch, which attaches
        them through the authoritative Terminal objects.
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

    # ============================================================
    # ENGINEERING PARAMETER ALIASES
    # ============================================================

    @property
    def resistance(self) -> float:
        """
        Return series resistance R.

        Canonical storage is Branch.r.
        """
        return self.r

    @resistance.setter
    def resistance(self, value: float) -> None:
        self.r = value

    @property
    def reactance(self) -> float:
        """
        Return series reactance X.

        Canonical storage is Branch.x.
        """
        return self.x

    @reactance.setter
    def reactance(self, value: float) -> None:
        self.x = value

    @property
    def shunt_susceptance(self) -> float:
        """
        Return total shunt susceptance B.

        Canonical storage is Branch.b.
        """
        return self.b

    @shunt_susceptance.setter
    def shunt_susceptance(self, value: float) -> None:
        self.b = value

    # ============================================================
    # π-MODEL ELECTRICAL PROPERTIES
    # ============================================================

    @property
    def series_impedance(self) -> complex:
        """
        Return the series impedance:

            Z = R + jX
        """
        return self.impedance

    @property
    def series_admittance(self) -> complex:
        """
        Return the series admittance:

            Yseries = 1 / Z
        """
        return self.admittance

    @property
    def total_shunt_admittance(self) -> complex:
        """
        Return the total shunt admittance:

            Ysh = jB
        """
        return self.shunt_admittance

    @property
    def half_shunt_admittance(self) -> complex:
        """
        Return the shunt admittance assigned to either end of
        the nominal π model:

            Yhalf = jB / 2
        """
        return self.shunt_admittance / 2.0

    # ============================================================
    # π-MODEL REPRESENTATION
    # ============================================================

    def pi_parameters(self) -> dict[str, complex]:
        """
        Return the local nominal π-model parameters.

        Returns
        -------
        dict
            Keys:

                series_impedance
                series_admittance
                shunt_admittance
                half_shunt_admittance

        This method returns local electrical parameters only.
        It does not construct or mutate a global Network matrix.
        """
        return {
            "series_impedance": self.series_impedance,
            "series_admittance": self.series_admittance,
            "shunt_admittance": self.total_shunt_admittance,
            "half_shunt_admittance": self.half_shunt_admittance,
        }

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Branch and Line invariants.

        Validation hierarchy:

            Line.validate_parameters()
                ↓
            Branch.validate_parameters()
                ↓
            ElectricalObject.validate_parameters()
        """

        Branch.validate_parameters(self)

        if not math.isfinite(self.r):
            raise ValueError(
                "Line resistance must be finite."
            )

        if not math.isfinite(self.x):
            raise ValueError(
                "Line reactance must be finite."
            )

        if not math.isfinite(self.b):
            raise ValueError(
                "Line shunt susceptance must be finite."
            )

        if self.impedance == 0.0 + 0.0j:
            raise ValueError(
                "Line series impedance cannot be zero."
            )

        return True


__all__ = [
    "Line",
]
