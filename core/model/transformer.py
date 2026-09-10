# ============================================================
# File: core/model/transformer.py
# GridForge V2 — Transformer Model
# Author: Subhendu Mishra
# ============================================================

"""Authoritative two-terminal transformer model.

Transformer ``r/x/b`` values require an explicit impedance basis.
For engineering values the reference voltage is explicit. For PU
values the original MVA base is explicit (or, for compatibility,
derived from the transformer rated MVA supplied as ``rate_mva``).
No unit or base inference is performed by numerical builders.
"""

from __future__ import annotations

import math
from typing import Any

from .branch import Branch


class Transformer(Branch):
    """Static two-terminal transformer with an explicit impedance basis.

    ``r``, ``x`` and ``b`` retain the established API. Their meaning is
    determined by ``impedance_basis``:

    * ``pu``: values are per-unit on ``impedance_base_mva`` and
      ``impedance_base_voltage_kv``.
    * ``engineering``: values are physical ohms/siemens referred to the
      declared ``impedance_base_voltage_kv`` side.

    ``rate_mva`` remains the existing transformer rating field and is
    exposed as ``rated_mva`` for engineering clarity.
    """

    TYPE = "TRANSFORMER"
    VALID_IMPEDANCE_BASES = frozenset({"pu", "engineering"})

    __slots__ = (
        "_tap",
        "_shift",
        "_impedance_basis",
        "_impedance_base_mva",
        "_impedance_base_voltage_kv",
    )

    def __init__(
        self,
        id: str,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        *,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        impedance_basis: str,
        impedance_base_mva: float | None = None,
        impedance_base_voltage_kv: float | None = None,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str = "",
        rate_mva: float | None = None,
        in_service: bool = True,
    ) -> None:
        if impedance_basis is None:
            raise ValueError(
                "Transformer impedance_basis is required; ambiguous r/x/b data is not accepted."
            )
        impedance_basis = str(impedance_basis).strip().lower()
        if impedance_basis not in self.VALID_IMPEDANCE_BASES:
            raise ValueError(
                "Transformer impedance_basis must be 'pu' or 'engineering'."
            )

        # The existing Branch ``rate_mva`` is the transformer nameplate
        # rating. It is a valid original MVA basis only when explicitly
        # supplied; no default base is invented.
        effective_base_mva = (
            impedance_base_mva if impedance_base_mva is not None else rate_mva
        )

        if effective_base_mva is None:
            raise ValueError(
                "Transformer impedance base MVA must be declared through "
                "impedance_base_mva or rate_mva."
            )

        effective_base_mva = self._validate_positive(
            effective_base_mva,
            "impedance_base_mva",
        )

        if impedance_base_voltage_kv is None:
            raise ValueError(
                "Transformer impedance_base_voltage_kv is required; "
                "the physical/reference voltage side must not be inferred."
            )
        impedance_base_voltage_kv = self._validate_positive(
            impedance_base_voltage_kv,
            "impedance_base_voltage_kv",
        )

        super().__init__(
            id=id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r,
            x=x,
            b=b,
            name=name,
            rate_mva=rate_mva,
            in_service=in_service,
        )

        self._impedance_basis = impedance_basis
        self._impedance_base_mva = effective_base_mva
        self._impedance_base_voltage_kv = impedance_base_voltage_kv
        self._tap = self._validate_positive(tap, "tap")
        self._shift = self._validate_finite(shift, "shift")

    @property
    def element_type(self) -> str:
        return self.TYPE

    @property
    def impedance_basis(self) -> str:
        """Return the declared basis of ``r/x/b``."""
        return self._impedance_basis

    @property
    def impedance_base_mva(self) -> float:
        """Return the declared original MVA basis of ``r/x/b``."""
        return self._impedance_base_mva

    @property
    def impedance_base_voltage_kv(self) -> float:
        """Return the declared voltage-side basis of ``r/x/b``."""
        return self._impedance_base_voltage_kv

    @property
    def rated_mva(self) -> float | None:
        """Return the transformer nameplate MVA rating."""
        return self.rate_mva

    @property
    def tap(self) -> float:
        return self._tap

    @tap.setter
    def tap(self, value: float) -> None:
        self._tap = self._validate_positive(value, "tap")

    @property
    def tap_ratio(self) -> float:
        return self._tap

    @tap_ratio.setter
    def tap_ratio(self, value: float) -> None:
        self._tap = self._validate_positive(value, "tap_ratio")

    @property
    def turns_ratio(self) -> float:
        return self._tap

    def set_tap(self, tap: float) -> None:
        self.tap = tap

    @property
    def shift(self) -> float:
        return self._shift

    @shift.setter
    def shift(self, value: float) -> None:
        self._shift = self._validate_finite(value, "shift")

    @property
    def phase_shift_rad(self) -> float:
        return self._shift

    @phase_shift_rad.setter
    def phase_shift_rad(self, value: float) -> None:
        self._shift = self._validate_finite(value, "phase_shift_rad")

    @property
    def phase_shift_deg(self) -> float:
        return math.degrees(self._shift)

    @phase_shift_deg.setter
    def phase_shift_deg(self, value: float) -> None:
        self._shift = math.radians(
            self._validate_finite(value, "phase_shift_deg")
        )

    def set_phase_shift(self, shift: float) -> None:
        self.shift = shift

    def set_phase_shift_degrees(self, degrees: float) -> None:
        self.phase_shift_deg = degrees

    def validate_parameters(self) -> bool:
        Branch.validate_parameters(self)
        if self._impedance_basis not in self.VALID_IMPEDANCE_BASES:
            raise ValueError("Transformer impedance_basis is invalid.")
        self._impedance_base_mva = self._validate_positive(
            self._impedance_base_mva,
            "impedance_base_mva",
        )
        self._impedance_base_voltage_kv = self._validate_positive(
            self._impedance_base_voltage_kv,
            "impedance_base_voltage_kv",
        )
        self._tap = self._validate_positive(self._tap, "tap")
        self._shift = self._validate_finite(self._shift, "shift")
        return True

    def summary(self) -> dict[str, Any]:
        summary = super().summary()
        summary.update(
            {
                "type": self.TYPE,
                "impedance_basis": self._impedance_basis,
                "impedance_base_mva": self._impedance_base_mva,
                "impedance_base_voltage_kv": self._impedance_base_voltage_kv,
                "rated_mva": self.rate_mva,
                "tap": self._tap,
                "tap_ratio": self._tap,
                "shift_rad": self._shift,
                "shift_deg": self.phase_shift_deg,
            }
        )
        return summary

    def __repr__(self) -> str:
        from_endpoint = self.from_endpoint
        to_endpoint = self.to_endpoint
        from_id = getattr(from_endpoint, "id", None) if from_endpoint is not None else None
        to_id = getattr(to_endpoint, "id", None) if to_endpoint is not None else None
        return (
            f"<Transformer id={self.id}, {from_id} -> {to_id}, "
            f"basis={self._impedance_basis}, "
            f"base={self._impedance_base_mva:.6f} MVA/{self._impedance_base_voltage_kv:.6f} kV, "
            f"tap={self._tap:.6f}, shift={self._shift:.6f} rad>"
        )

    @staticmethod
    def _validate_finite(value: float, name: str) -> float:
        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be numeric.") from exc
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")
        return value

    @staticmethod
    def _validate_positive(value: float, name: str) -> float:
        value = Transformer._validate_finite(value, name)
        if value <= 0.0:
            raise ValueError(f"{name} must be greater than zero.")
        return value


__all__ = ["Transformer"]
