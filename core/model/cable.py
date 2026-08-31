# ============================================================
# File: core/model/cable.py
# GridForge V2 — Cable Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Cable Model
==========================

Concrete two-terminal physical cable model.

Architecture
------------

    ElectricalObject
          |
          v
        Branch
          |
          v
        Cable
       /     \
      v       v
 FROM       TO
Terminal   Terminal
      |       |
      v       v
 endpoint  endpoint

Cable inherits the authoritative terminal and endpoint contract
from Branch.

Endpoint ownership
------------------

Cable does NOT maintain independent endpoint state.

The authoritative endpoint references are:

    Cable.from_terminal.endpoint
    Cable.to_terminal.endpoint

Network interprets those endpoints into topology.

Electrical parameter ownership
------------------------------

Branch owns the canonical positive-sequence branch parameters:

    r
    x
    b

Cable exposes engineering aliases:

    r1
    x1
    b1

These aliases do NOT create duplicate state.

Therefore:

    r1 <-> Branch.r
    x1 <-> Branch.x
    b1 <-> Branch.b

Cable additionally owns zero-sequence parameters:

    r0
    x0
    b0

and physical/rating parameters:

    length_km
    rated_voltage_kv
    rated_current_a

Responsibility boundaries
-------------------------

Cable does NOT:

    - own Bus objects;
    - resolve endpoints into Bus objects;
    - mutate Network topology;
    - maintain Network collections;
    - construct global Y-bus matrices;
    - assign solver indices;
    - maintain solved numerical state;
    - perform power-flow calculations;
    - perform short-circuit calculations;
    - execute protection logic;
    - execute control logic;
    - maintain UI/SLD state;
    - perform persistence.

Study-specific use of sequence parameters belongs to the
Analysis/Numerical layers.

Validation
----------

Validation follows:

    ElectricalObject.validate()
            |
            v
    Cable.validate_parameters()
            |
            v
    Branch.validate_parameters()
            |
            v
    ElectricalObject.validate_parameters()

Construction deliberately does not call validate() because the
complete concrete object must first be initialized.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .branch import Branch


class Cable(Branch):
    """
    Two-terminal physical cable model.

    Positive-sequence parameters are inherited canonically from
    Branch:

        r
        x
        b

    Engineering aliases are provided as:

        r1
        x1
        b1

    Zero-sequence parameters remain Cable-specific:

        r0
        x0
        b0
    """

    TYPE = "CABLE"

    __slots__ = (
        "_length_km",
        "_r0",
        "_x0",
        "_b0",
        "_rated_voltage_kv",
        "_rated_current_a",
    )

    def __init__(
        self,
        id: str,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        *,
        length_km: float | None = None,
        r1: float = 0.0,
        x1: float = 0.0,
        b1: float = 0.0,
        r0: float | None = None,
        x0: float | None = None,
        b0: float | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        name: str = "",
        rate_mva: float | None = None,
        in_service: bool = True,
    ) -> None:
        """
        Construct a Cable.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint_from:
            Optional endpoint reference for the FROM terminal.

        endpoint_to:
            Optional endpoint reference for the TO terminal.

        length_km:
            Physical cable length in kilometres.

        r1:
            Positive-sequence series resistance.

            Stored canonically as Branch.r.

        x1:
            Positive-sequence series reactance.

            Stored canonically as Branch.x.

        b1:
            Positive-sequence total shunt susceptance.

            Stored canonically as Branch.b.

        r0:
            Zero-sequence series resistance.

        x0:
            Zero-sequence series reactance.

        b0:
            Zero-sequence total shunt susceptance.

        rated_voltage_kv:
            Cable rated voltage in kV.

        rated_current_a:
            Cable rated current in amperes.

        name:
            Human-readable cable name.

        rate_mva:
            Optional continuous apparent-power rating in MVA.

        in_service:
            Operational service state.

        Notes
        -----
        No validation is performed during construction.

        The complete object is validated through the inherited
        ElectricalObject.validate() entry point after construction.
        """

        super().__init__(
            id=id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            r=r1,
            x=x1,
            b=b1,
            name=name,
            rate_mva=rate_mva,
            in_service=in_service,
        )

        self._length_km = self._validate_optional_positive(
            length_km,
            "length_km",
        )

        self._r0 = self._validate_optional_finite(
            r0,
            "r0",
        )

        self._x0 = self._validate_optional_finite(
            x0,
            "x0",
        )

        self._b0 = self._validate_optional_finite(
            b0,
            "b0",
        )

        self._rated_voltage_kv = (
            self._validate_optional_positive(
                rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self._rated_current_a = (
            self._validate_optional_positive(
                rated_current_a,
                "rated_current_a",
            )
        )

    # ============================================================
    # TYPE
    # ============================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge model type.
        """
        return self.TYPE

    # ============================================================
    # POSITIVE-SEQUENCE PARAMETERS
    # ============================================================

    @property
    def r1(self) -> float:
        """
        Return positive-sequence resistance.

        Canonical storage is Branch.r.
        """
        return self.r

    @r1.setter
    def r1(self, value: float) -> None:
        """
        Set positive-sequence resistance.

        Canonical storage is Branch.r.
        """
        self.r = value

    @property
    def x1(self) -> float:
        """
        Return positive-sequence reactance.

        Canonical storage is Branch.x.
        """
        return self.x

    @x1.setter
    def x1(self, value: float) -> None:
        """
        Set positive-sequence reactance.

        Canonical storage is Branch.x.
        """
        self.x = value

    @property
    def b1(self) -> float:
        """
        Return positive-sequence shunt susceptance.

        Canonical storage is Branch.b.
        """
        return self.b

    @b1.setter
    def b1(self, value: float) -> None:
        """
        Set positive-sequence shunt susceptance.

        Canonical storage is Branch.b.
        """
        self.b = value

    # ============================================================
    # CABLE LENGTH
    # ============================================================

    @property
    def length_km(self) -> float | None:
        """
        Return physical cable length in kilometres.
        """
        return self._length_km

    @length_km.setter
    def length_km(
        self,
        value: float | None,
    ) -> None:
        self._length_km = self._validate_optional_positive(
            value,
            "length_km",
        )

    # ============================================================
    # ZERO-SEQUENCE PARAMETERS
    # ============================================================

    @property
    def r0(self) -> float | None:
        """
        Return zero-sequence series resistance.
        """
        return self._r0

    @r0.setter
    def r0(
        self,
        value: float | None,
    ) -> None:
        self._r0 = self._validate_optional_finite(
            value,
            "r0",
        )

    @property
    def x0(self) -> float | None:
        """
        Return zero-sequence series reactance.
        """
        return self._x0

    @x0.setter
    def x0(
        self,
        value: float | None,
    ) -> None:
        self._x0 = self._validate_optional_finite(
            value,
            "x0",
        )

    @property
    def b0(self) -> float | None:
        """
        Return zero-sequence shunt susceptance.
        """
        return self._b0

    @b0.setter
    def b0(
        self,
        value: float | None,
    ) -> None:
        self._b0 = self._validate_optional_finite(
            value,
            "b0",
        )

    # ============================================================
    # RATED VOLTAGE
    # ============================================================

    @property
    def rated_voltage_kv(self) -> float | None:
        """
        Return cable rated voltage in kV.
        """
        return self._rated_voltage_kv

    @rated_voltage_kv.setter
    def rated_voltage_kv(
        self,
        value: float | None,
    ) -> None:
        self._rated_voltage_kv = (
            self._validate_optional_positive(
                value,
                "rated_voltage_kv",
            )
        )

    # ============================================================
    # RATED CURRENT
    # ============================================================

    @property
    def rated_current_a(self) -> float | None:
        """
        Return cable rated current in amperes.
        """
        return self._rated_current_a

    @rated_current_a.setter
    def rated_current_a(
        self,
        value: float | None,
    ) -> None:
        self._rated_current_a = (
            self._validate_optional_positive(
                value,
                "rated_current_a",
            )
        )

    # ============================================================
    # SEQUENCE PARAMETERS
    # ============================================================

    def positive_sequence_parameters(
        self,
    ) -> dict[str, float]:
        """
        Return canonical positive-sequence parameters.

        The returned values are aliases of Branch-owned state.
        """
        return {
            "r": self.r,
            "x": self.x,
            "b": self.b,
        }

    def zero_sequence_parameters(
        self,
    ) -> dict[str, float | None]:
        """
        Return Cable zero-sequence parameters.

        Zero-sequence state is Cable-specific.
        """
        return {
            "r0": self.r0,
            "x0": self.x0,
            "b0": self.b0,
        }

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate the complete Cable parameter hierarchy.

        Order:

            Cable
              |
              v
            Branch
              |
              v
            ElectricalObject
        """

        Branch.validate_parameters(self)

        self._validate_finite(
            self.r,
            "r1",
        )

        self._validate_finite(
            self.x,
            "x1",
        )

        self._validate_finite(
            self.b,
            "b1",
        )

        self._r0 = self._validate_optional_finite(
            self._r0,
            "r0",
        )

        self._x0 = self._validate_optional_finite(
            self._x0,
            "x0",
        )

        self._b0 = self._validate_optional_finite(
            self._b0,
            "b0",
        )

        self._length_km = (
            self._validate_optional_positive(
                self._length_km,
                "length_km",
            )
        )

        self._rated_voltage_kv = (
            self._validate_optional_positive(
                self._rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self._rated_current_a = (
            self._validate_optional_positive(
                self._rated_current_a,
                "rated_current_a",
            )
        )

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return Cable-local diagnostics.

        No Network topology or solved numerical state is included.
        """

        summary = super().summary()

        summary.update(
            {
                "type": self.TYPE,
                "length_km": self.length_km,
                "r1": self.r1,
                "x1": self.x1,
                "b1": self.b1,
                "r0": self.r0,
                "x0": self.x0,
                "b0": self.b0,
                "rated_voltage_kv": self.rated_voltage_kv,
                "rated_current_a": self.rated_current_a,
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

        return (
            f"<Cable "
            f"id={self.id}, "
            f"length_km={self.length_km}, "
            f"r1={self.r1}, "
            f"x1={self.x1}, "
            f"b1={self.b1}, "
            f"rated_voltage_kv={self.rated_voltage_kv}, "
            f"rated_current_a={self.rated_current_a}, "
            f"in_service={self.in_service}>"
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
        Validate and return a finite numeric value.
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

    @classmethod
    def _validate_optional_positive(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """
        Validate an optional finite positive numeric value.
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


__all__ = [
    "Cable",
]
