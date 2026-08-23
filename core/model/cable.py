# core/model/cable.py
"""
GridForge V2 Cable Model
========================

Author:
    Subhendu Mishra

A Cable is a physical two-terminal electrical branch.

Architecture
------------

    Cable
      │
      └── Branch
           ├── from_terminal
           └── to_terminal

Cable owns cable-specific electrical and physical parameters.

It does NOT own:

    - global network topology
    - Bus collections
    - SLD geometry
    - GUI state
    - power-flow solving
    - short-circuit solving
    - protection calculations
    - thermal study calculations
    - dynamic simulation

The numerical/network layers convert this physical model into the
appropriate study representation.

Parameter conventions
---------------------

Length:
    km

Positive-sequence impedance:
    R1, X1 in ohm/km

Positive-sequence shunt susceptance:
    B1 in microS/km

Zero-sequence impedance:
    R0, X0 in ohm/km

Zero-sequence shunt susceptance:
    B0 in microS/km

Ratings:
    voltage in kV
    current in A

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

from .branch import Branch


class Cable(Branch):
    """
    Physical cable electrical model.

    Cable is a specialized Branch with cable-specific physical
    parameters and sequence data.
    """

    TYPE = "CABLE"

    def __init__(
        self,
        id: str,
        endpoint_from=None,
        endpoint_to=None,
        *,
        name: str = "",
        length_km: float = 0.0,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        r1_ohm_per_km: float = 0.0,
        x1_ohm_per_km: float = 0.0,
        b1_us_per_km: float = 0.0,
        r0_ohm_per_km: float | None = None,
        x0_ohm_per_km: float | None = None,
        b0_us_per_km: float | None = None,
        in_service: bool = True,
    ) -> None:

        # ---------------------------------------------------------
        # Branch initialization
        # ---------------------------------------------------------

        super().__init__(
            id=id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            name=name,
            in_service=in_service,
        )

        # ---------------------------------------------------------
        # Physical cable parameters
        # ---------------------------------------------------------

        self.length_km = self._validate_non_negative(
            length_km,
            "length_km",
        )

        self.rated_voltage_kv = (
            self._validate_optional_positive(
                rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self.rated_current_a = (
            self._validate_optional_positive(
                rated_current_a,
                "rated_current_a",
            )
        )

        # ---------------------------------------------------------
        # Positive sequence
        # ---------------------------------------------------------

        self.r1_ohm_per_km = self._validate_non_negative(
            r1_ohm_per_km,
            "r1_ohm_per_km",
        )

        self.x1_ohm_per_km = self._validate_non_negative(
            x1_ohm_per_km,
            "x1_ohm_per_km",
        )

        self.b1_us_per_km = self._validate_finite(
            b1_us_per_km,
            "b1_us_per_km",
        )

        # ---------------------------------------------------------
        # Zero sequence
        # ---------------------------------------------------------

        self.r0_ohm_per_km = (
            self._validate_optional_non_negative(
                r0_ohm_per_km,
                "r0_ohm_per_km",
            )
        )

        self.x0_ohm_per_km = (
            self._validate_optional_non_negative(
                x0_ohm_per_km,
                "x0_ohm_per_km",
            )
        )

        self.b0_us_per_km = (
            self._validate_optional_finite(
                b0_us_per_km,
                "b0_us_per_km",
            )
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
    # SEQUENCE AVAILABILITY
    # =============================================================

    @property
    def has_zero_sequence_data(self) -> bool:
        """
        Return True when complete zero-sequence impedance data
        is available.
        """

        return (
            self.r0_ohm_per_km is not None
            and self.x0_ohm_per_km is not None
        )

    @property
    def has_zero_sequence_shunt_data(self) -> bool:
        """Return True when zero-sequence shunt data is available."""

        return self.b0_us_per_km is not None

    # =============================================================
    # TOTAL PARAMETERS
    # =============================================================

    @property
    def r1_ohm(self) -> float:
        """Return total positive-sequence resistance."""

        return (
            self.r1_ohm_per_km
            * self.length_km
        )

    @property
    def x1_ohm(self) -> float:
        """Return total positive-sequence reactance."""

        return (
            self.x1_ohm_per_km
            * self.length_km
        )

    @property
    def b1_us(self) -> float:
        """Return total positive-sequence shunt susceptance."""

        return (
            self.b1_us_per_km
            * self.length_km
        )

    @property
    def r0_ohm(self) -> float | None:
        """Return total zero-sequence resistance."""

        if self.r0_ohm_per_km is None:
            return None

        return (
            self.r0_ohm_per_km
            * self.length_km
        )

    @property
    def x0_ohm(self) -> float | None:
        """Return total zero-sequence reactance."""

        if self.x0_ohm_per_km is None:
            return None

        return (
            self.x0_ohm_per_km
            * self.length_km
        )

    @property
    def b0_us(self) -> float | None:
        """Return total zero-sequence shunt susceptance."""

        if self.b0_us_per_km is None:
            return None

        return (
            self.b0_us_per_km
            * self.length_km
        )

    # =============================================================
    # PARAMETER UPDATE
    # =============================================================

    def set_length(
        self,
        length_km: float,
    ) -> None:
        """Set physical cable length in km."""

        self.length_km = self._validate_non_negative(
            length_km,
            "length_km",
        )

    def set_positive_sequence(
        self,
        *,
        r_ohm_per_km: float,
        x_ohm_per_km: float,
        b_us_per_km: float,
    ) -> None:
        """
        Set positive-sequence cable parameters.
        """

        r_ohm_per_km = self._validate_non_negative(
            r_ohm_per_km,
            "r_ohm_per_km",
        )

        x_ohm_per_km = self._validate_non_negative(
            x_ohm_per_km,
            "x_ohm_per_km",
        )

        b_us_per_km = self._validate_finite(
            b_us_per_km,
            "b_us_per_km",
        )

        self.r1_ohm_per_km = r_ohm_per_km
        self.x1_ohm_per_km = x_ohm_per_km
        self.b1_us_per_km = b_us_per_km

    def set_zero_sequence(
        self,
        *,
        r_ohm_per_km: float | None,
        x_ohm_per_km: float | None,
        b_us_per_km: float | None,
    ) -> None:
        """
        Set zero-sequence cable parameters.

        Passing None explicitly means zero-sequence data is not
        available.
        """

        self.r0_ohm_per_km = (
            self._validate_optional_non_negative(
                r_ohm_per_km,
                "r_ohm_per_km",
            )
        )

        self.x0_ohm_per_km = (
            self._validate_optional_non_negative(
                x_ohm_per_km,
                "x_ohm_per_km",
            )
        )

        self.b0_us_per_km = (
            self._validate_optional_finite(
                b_us_per_km,
                "b_us_per_km",
            )
        )

    # =============================================================
    # VALIDATION
    # =============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Cable-local engineering parameters.

        Network topology and numerical-study validity remain outside
        the Cable model.
        """

        self.length_km = self._validate_non_negative(
            self.length_km,
            "length_km",
        )

        self.rated_voltage_kv = (
            self._validate_optional_positive(
                self.rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self.rated_current_a = (
            self._validate_optional_positive(
                self.rated_current_a,
                "rated_current_a",
            )
        )

        self.r1_ohm_per_km = (
            self._validate_non_negative(
                self.r1_ohm_per_km,
                "r1_ohm_per_km",
            )
        )

        self.x1_ohm_per_km = (
            self._validate_non_negative(
                self.x1_ohm_per_km,
                "x1_ohm_per_km",
            )
        )

        self.b1_us_per_km = (
            self._validate_finite(
                self.b1_us_per_km,
                "b1_us_per_km",
            )
        )

        self.r0_ohm_per_km = (
            self._validate_optional_non_negative(
                self.r0_ohm_per_km,
                "r0_ohm_per_km",
            )
        )

        self.x0_ohm_per_km = (
            self._validate_optional_non_negative(
                self.x0_ohm_per_km,
                "x0_ohm_per_km",
            )
        )

        self.b0_us_per_km = (
            self._validate_optional_finite(
                self.b0_us_per_km,
                "b0_us_per_km",
            )
        )

        return True

    def validate(self) -> bool:
        """Public local validation entry point."""

        return self.validate_parameters()

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """Return structured Cable diagnostics."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "endpoint_from": self.endpoint_from_id,
            "endpoint_to": self.endpoint_to_id,

            "connected": self.is_connected,
            "in_service": self.in_service,

            "length_km": self.length_km,

            "rated_voltage_kv":
                self.rated_voltage_kv,

            "rated_current_a":
                self.rated_current_a,

            "r1_ohm_per_km":
                self.r1_ohm_per_km,

            "x1_ohm_per_km":
                self.x1_ohm_per_km,

            "b1_us_per_km":
                self.b1_us_per_km,

            "r0_ohm_per_km":
                self.r0_ohm_per_km,

            "x0_ohm_per_km":
                self.x0_ohm_per_km,

            "b0_us_per_km":
                self.b0_us_per_km,

            "has_zero_sequence_data":
                self.has_zero_sequence_data,
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        return (
            f"<Cable "
            f"id={self.id}, "
            f"{self.endpoint_from_id} -> "
            f"{self.endpoint_to_id}, "
            f"length={self.length_km:.6f} km, "
            f"in_service={self.in_service}>"
        )

    # =============================================================
    # VALIDATION HELPERS
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

    @classmethod
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Return a finite non-negative value."""

        value = cls._validate_finite(
            value,
            name,
        )

        if value < 0.0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return value

    @classmethod
    def _validate_positive(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Return a finite positive value."""

        value = cls._validate_finite(
            value,
            name,
        )

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value

    @classmethod
    def _validate_optional_positive(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """Validate an optional positive value."""

        if value is None:
            return None

        return cls._validate_positive(
            value,
            name,
        )

    @classmethod
    def _validate_optional_non_negative(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """Validate an optional non-negative value."""

        if value is None:
            return None

        return cls._validate_non_negative(
            value,
            name,
        )

    @classmethod
    def _validate_optional_finite(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """Validate an optional finite value."""

        if value is None:
            return None

        return cls._validate_finite(
            value,
            name,
        )
