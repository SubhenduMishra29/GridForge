# ============================================================
# File: core/model/line.py
# GridForge V2 — Transmission Line Model
# Author: Subhendu Mishra
# ============================================================

"""Authoritative two-terminal transmission-line engineering model."""

from __future__ import annotations

import math
from typing import Any

from .branch import Branch


class Line(Branch):
    """Two-terminal transmission line with explicit engineering electrical quantities.

    The authoritative Line electrical contract is:

        resistance_ohm
        reactance_ohm
        shunt_susceptance_siemens

    These are engineering quantities. Engineering-to-per-unit conversion is
    owned by PowerFlowPreparation, not by this model and not by YBusBuilder.

    Branch terminals remain the sole authoritative endpoint state.
    """

    __slots__ = ()

    def __init__(
        self,
        *,
        id: str,
        endpoint_from: Any | None = None,
        endpoint_to: Any | None = None,
        resistance_ohm: float = 0.0,
        reactance_ohm: float = 0.0,
        shunt_susceptance_siemens: float = 0.0,
        name: str | None = None,
        rate_mva: float | None = None,
        in_service: bool = True,
    ) -> None:
        """Construct a Line from explicit engineering electrical quantities."""
        super().__init__(
            id=id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=resistance_ohm,
            x=reactance_ohm,
            b=shunt_susceptance_siemens,
            name=name,
            rate_mva=rate_mva,
            in_service=in_service,
        )

    @property
    def resistance_ohm(self) -> float:
        """Series resistance in ohms."""
        return self.r

    @resistance_ohm.setter
    def resistance_ohm(self, value: float) -> None:
        self.r = value

    @property
    def reactance_ohm(self) -> float:
        """Series reactance in ohms."""
        return self.x

    @reactance_ohm.setter
    def reactance_ohm(self, value: float) -> None:
        self.x = value

    @property
    def shunt_susceptance_siemens(self) -> float:
        """Total line shunt susceptance in siemens."""
        return self.b

    @shunt_susceptance_siemens.setter
    def shunt_susceptance_siemens(self, value: float) -> None:
        self.b = value

    @property
    def series_impedance(self) -> complex:
        """Return Z = R + jX using the engineering Line quantities."""
        return complex(self.resistance_ohm, self.reactance_ohm)

    @property
    def series_admittance(self) -> complex:
        """Return the local series admittance 1/Z."""
        return self.admittance

    @property
    def total_shunt_admittance(self) -> complex:
        """Return the total shunt admittance jB."""
        return complex(0.0, self.shunt_susceptance_siemens)

    @property
    def half_shunt_admittance(self) -> complex:
        """Return half of the total nominal-pi shunt admittance."""
        return self.total_shunt_admittance / 2.0

    def pi_parameters(self) -> dict[str, complex]:
        """Return local nominal-pi parameters without creating a global Y-bus."""
        return {
            "series_impedance": self.series_impedance,
            "series_admittance": self.series_admittance,
            "shunt_admittance": self.total_shunt_admittance,
            "half_shunt_admittance": self.half_shunt_admittance,
        }

    def validate_parameters(self) -> bool:
        """Validate Branch invariants and Line engineering quantities."""
        Branch.validate_parameters(self)

        for value, name in (
            (self.resistance_ohm, "resistance_ohm"),
            (self.reactance_ohm, "reactance_ohm"),
            (self.shunt_susceptance_siemens, "shunt_susceptance_siemens"),
        ):
            if not math.isfinite(value):
                raise ValueError(f"Line {name} must be finite.")

        if self.series_impedance == 0.0 + 0.0j:
            raise ValueError("Line series impedance cannot be zero.")

        return True


__all__ = ["Line"]
