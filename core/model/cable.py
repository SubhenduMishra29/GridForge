# ============================================================
# File: core/model/cable.py
# GridForge V2 — Cable Model
# Author: Subhendu Mishra
# ============================================================

"""Authoritative two-terminal cable engineering model.

Cable stores engineering quantities only. Numerical per-unit values
are created by the power-flow preparation boundary, never here.
"""

from __future__ import annotations

import math
from typing import Any

from .branch import Branch


class Cable(Branch):
    """Two-terminal cable with engineering sequence parameters.

    Canonical electrical representation:

    * ``r1_ohm_per_km``, ``x1_ohm_per_km``, ``b1_us_per_km``
    * ``r0_ohm_per_km``, ``x0_ohm_per_km``, ``b0_us_per_km``
    * ``length_km``

    ``b*_us_per_km`` is charging susceptance in micro-siemens/km.
    The model deliberately does not accept ambiguous ``r/x/b`` inputs.
    """

    TYPE = "CABLE"

    def __init__(
        self,
        id: str,
        *,
        endpoint_from: Any | None = None,
        endpoint_to: Any | None = None,
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
        thermal_limit_mva: float | None = None,
        conductor_count: int = 1,
        in_service: bool = True,
    ) -> None:
        if r0_ohm_per_km is None:
            r0_ohm_per_km = r1_ohm_per_km
        if x0_ohm_per_km is None:
            x0_ohm_per_km = x1_ohm_per_km
        if b0_us_per_km is None:
            b0_us_per_km = b1_us_per_km

        # Branch owns connectivity. Its generic electrical fields are
        # intentionally neutral for Cable; preparation reads Cable's
        # engineering fields explicitly.
        super().__init__(
            id=id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=0.0,
            x=0.0,
            b=0.0,
            name=name,
            rate_mva=thermal_limit_mva,
            in_service=in_service,
        )

        self.length_km = self._validate_non_negative(length_km, "length_km")
        self.rated_voltage_kv = self._validate_optional_non_negative(
            rated_voltage_kv, "rated_voltage_kv"
        )
        self.rated_current_a = self._validate_optional_non_negative(
            rated_current_a, "rated_current_a"
        )
        self.r1_ohm_per_km = self._validate_non_negative(
            r1_ohm_per_km, "r1_ohm_per_km"
        )
        self.x1_ohm_per_km = self._validate_non_negative(
            x1_ohm_per_km, "x1_ohm_per_km"
        )
        self.b1_us_per_km = self._validate_finite(
            b1_us_per_km, "b1_us_per_km"
        )
        self.r0_ohm_per_km = self._validate_non_negative(
            r0_ohm_per_km, "r0_ohm_per_km"
        )
        self.x0_ohm_per_km = self._validate_non_negative(
            x0_ohm_per_km, "x0_ohm_per_km"
        )
        self.b0_us_per_km = self._validate_finite(
            b0_us_per_km, "b0_us_per_km"
        )

        if thermal_limit_mva is None:
            self.thermal_limit_mva = 0.0
        else:
            self.thermal_limit_mva = self._validate_non_negative(
                thermal_limit_mva, "thermal_limit_mva"
            )

        if not isinstance(conductor_count, int):
            raise TypeError("conductor_count must be an integer.")
        if conductor_count < 1:
            raise ValueError("conductor_count must be at least 1.")
        self.conductor_count = conductor_count
        self.validate()

    @property
    def element_type(self) -> str:
        return self.TYPE

    # ------------------------------------------------------------
    # Engineering totals used by preparation
    # ------------------------------------------------------------

    @property
    def resistance_ohm(self) -> float:
        return self.r1_ohm_per_km * self.length_km

    @property
    def reactance_ohm(self) -> float:
        return self.x1_ohm_per_km * self.length_km

    @property
    def shunt_susceptance_siemens(self) -> float:
        return self.b1_us_per_km * self.length_km * 1.0e-6

    @property
    def zero_sequence_resistance_ohm(self) -> float:
        return self.r0_ohm_per_km * self.length_km

    @property
    def zero_sequence_reactance_ohm(self) -> float:
        return self.x0_ohm_per_km * self.length_km

    @property
    def zero_sequence_shunt_susceptance_siemens(self) -> float:
        return self.b0_us_per_km * self.length_km * 1.0e-6

    # ------------------------------------------------------------
    # Engineering convenience accessors
    # ------------------------------------------------------------

    @property
    def length_m(self) -> float:
        return self.length_km * 1000.0

    @length_m.setter
    def length_m(self, value: float) -> None:
        self.length_km = self._validate_non_negative(value, "length_m") / 1000.0

    @property
    def rated_apparent_power_mva(self) -> float:
        if self.thermal_limit_mva > 0.0:
            return self.thermal_limit_mva
        if self.rated_voltage_kv and self.rated_current_a:
            return math.sqrt(3.0) * self.rated_voltage_kv * self.rated_current_a / 1000.0
        return 0.0

    @property
    def ampacity_a(self) -> float:
        return self.rated_current_a or 0.0

    # ------------------------------------------------------------
    # Service state
    # ------------------------------------------------------------

    @property
    def is_in_service(self) -> bool:
        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        return not self.in_service

    def put_in_service(self) -> None:
        self.set_in_service(True)

    def take_out_of_service(self) -> None:
        self.set_in_service(False)

    # ------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------

    def validate_parameters(self) -> bool:
        super().validate_parameters()
        self.length_km = self._validate_non_negative(self.length_km, "length_km")
        self.r1_ohm_per_km = self._validate_non_negative(
            self.r1_ohm_per_km, "r1_ohm_per_km"
        )
        self.x1_ohm_per_km = self._validate_non_negative(
            self.x1_ohm_per_km, "x1_ohm_per_km"
        )
        self.b1_us_per_km = self._validate_finite(self.b1_us_per_km, "b1_us_per_km")
        self.r0_ohm_per_km = self._validate_non_negative(
            self.r0_ohm_per_km, "r0_ohm_per_km"
        )
        self.x0_ohm_per_km = self._validate_non_negative(
            self.x0_ohm_per_km, "x0_ohm_per_km"
        )
        self.b0_us_per_km = self._validate_finite(self.b0_us_per_km, "b0_us_per_km")
        self.rated_voltage_kv = self._validate_optional_non_negative(
            self.rated_voltage_kv, "rated_voltage_kv"
        )
        self.rated_current_a = self._validate_optional_non_negative(
            self.rated_current_a, "rated_current_a"
        )
        self.thermal_limit_mva = self._validate_non_negative(
            self.thermal_limit_mva, "thermal_limit_mva"
        )
        if self.resistance_ohm == 0.0 and self.reactance_ohm == 0.0:
            raise ValueError(
                f"Cable '{self.id}' must have non-zero positive-sequence series impedance."
            )
        if self.zero_sequence_resistance_ohm == 0.0 and self.zero_sequence_reactance_ohm == 0.0:
            raise ValueError(
                f"Cable '{self.id}' must have non-zero zero-sequence series impedance."
            )
        return True

    def validate(self) -> bool:
        self.validate_parameters()
        return super().validate()

    # ------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "from_endpoint": getattr(self.from_endpoint, "id", None),
            "to_endpoint": getattr(self.to_endpoint, "id", None),
            "from_connected": self.from_terminal.is_connected,
            "to_connected": self.to_terminal.is_connected,
            "r1_ohm_per_km": self.r1_ohm_per_km,
            "x1_ohm_per_km": self.x1_ohm_per_km,
            "b1_us_per_km": self.b1_us_per_km,
            "r0_ohm_per_km": self.r0_ohm_per_km,
            "x0_ohm_per_km": self.x0_ohm_per_km,
            "b0_us_per_km": self.b0_us_per_km,
            "length_km": self.length_km,
            "rated_voltage_kv": self.rated_voltage_kv,
            "rated_current_a": self.rated_current_a,
            "thermal_limit_mva": self.thermal_limit_mva,
            "conductor_count": self.conductor_count,
            "in_service": self.in_service,
        }

    def __repr__(self) -> str:
        return (
            f"<Cable id={self.id}, R1={self.resistance_ohm!r} ohm, "
            f"X1={self.reactance_ohm!r} ohm, length={self.length_km:.6f} km, "
            f"in_service={self.in_service}>"
        )

    @staticmethod
    def _validate_finite(value: float, name: str) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be numeric.") from exc
        if not math.isfinite(numeric):
            raise ValueError(f"{name} must be finite.")
        return numeric

    @classmethod
    def _validate_non_negative(cls, value: float, name: str) -> float:
        numeric = cls._validate_finite(value, name)
        if numeric < 0.0:
            raise ValueError(f"{name} cannot be negative.")
        return numeric

    @classmethod
    def _validate_optional_non_negative(
        cls, value: float | None, name: str
    ) -> float | None:
        if value is None:
            return None
        return cls._validate_non_negative(value, name)


__all__ = ["Cable"]
