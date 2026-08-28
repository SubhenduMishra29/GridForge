# ============================================================
# File: core/model/cable.py
#
# GridForge V2 — Cable Model
#
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Cable Model
========================

A Cable is a specialized two-terminal Branch representing a
physical power cable.

Architecture
------------

    ElectricalObject
          |
          v
        Branch
          |
          v
        Cable

Cable owns only cable-specific physical configuration.

Cable does NOT own:

    - Bus objects;
    - Network topology;
    - Network collections;
    - endpoint-to-Bus resolution;
    - study formulation;
    - solved numerical state;
    - Y-bus matrices;
    - solver indices;
    - GUI/SLD state;
    - persistence;
    - protection logic;
    - control logic.

Terminal Boundary
-----------------

Cable inherits the authoritative two-terminal interface from
Branch:

    from_terminal
    to_terminal

Cable does not accept externally supplied Terminal objects and
does not share Terminal instances.

Endpoint interpretation and authoritative topology remain
Network responsibilities.

Validation Boundary
-------------------

Validation follows the frozen model hierarchy:

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

Cable therefore validates:

    1. Base identity/name constraints;
    2. Branch-local constraints;
    3. Cable-specific physical parameters.

Construction Boundary
---------------------

Cable does not call validate() or validate_parameters() from
its constructor.

All Cable state is initialized before validation is requested
through the public validate() entry point.

Electrical Boundary
-------------------

Cable-specific quantities are physical equipment parameters.

Positive-sequence and zero-sequence parameters remain Cable
model properties. Their use in a particular power-system study
belongs to the Analysis/Numerical layers.

No study-specific bus type, solved state, Y-bus state, or solver
state is stored here.

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

    Cable extends Branch with cable-specific physical parameters.

    Positive-sequence parameters:

        r1
        x1
        b1

    Zero-sequence parameters:

        r0
        x0
        b0

    Additional physical/rating parameters:

        length_km
        rated_voltage_kv
        rated_current_a

    The Cable owns no Network topology.
    """

    TYPE = "CABLE"

    def __init__(
        self,
        id: str,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        *,
        length_km: float | None = None,
        r1: float | None = None,
        x1: float | None = None,
        b1: float | None = None,
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
            Optional endpoint reference for the from terminal.

        endpoint_to:
            Optional endpoint reference for the to terminal.

        length_km:
            Physical cable length in kilometres.

        r1:
            Positive-sequence series resistance.

        x1:
            Positive-sequence series reactance.

        b1:
            Positive-sequence shunt susceptance.

        r0:
            Zero-sequence series resistance.

        x0:
            Zero-sequence series reactance.

        b0:
            Zero-sequence shunt susceptance.

        rated_voltage_kv:
            Cable rated voltage in kV.

        rated_current_a:
            Cable rated current in amperes.

        name:
            Human-readable cable name.

        rate_mva:
            Optional apparent-power branch rating in MVA.

        in_service:
            Operational state.

        Notes
        -----
        Construction deliberately does not invoke validation.

        The complete object must be initialized before the
        inherited ElectricalObject.validate() entry point is used.
        """

        super().__init__(
            id=id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            name=name,
            rate_mva=rate_mva,
            in_service=in_service,
        )

        self._length_km = self._validate_optional_positive(
            length_km,
            "length_km",
        )

        self._r1 = self._validate_optional_finite(
            r1,
            "r1",
        )

        self._x1 = self._validate_optional_finite(
            x1,
            "x1",
        )

        self._b1 = self._validate_optional_finite(
            b1,
            "b1",
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

        # ---------------------------------------------------------
        # IMPORTANT
        # ---------------------------------------------------------
        #
        # Do NOT call self.validate() or
        # self.validate_parameters() here.
        #
        # Validation is intentionally deferred until the complete
        # concrete Cable object has been constructed.
        #

    # ================================================================
    # TYPE
    # ================================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge model type.
        """

        return self.TYPE

    # ================================================================
    # CABLE LENGTH
    # ================================================================

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

    # ================================================================
    # POSITIVE-SEQUENCE PARAMETERS
    # ================================================================

    @property
    def r1(self) -> float | None:
        """
        Return positive-sequence resistance.
        """

        return self._r1

    @r1.setter
    def r1(
        self,
        value: float | None,
    ) -> None:
        self._r1 = self._validate_optional_finite(
            value,
            "r1",
        )

    @property
    def x1(self) -> float | None:
        """
        Return positive-sequence reactance.
        """

        return self._x1

    @x1.setter
    def x1(
        self,
        value: float | None,
    ) -> None:
        self._x1 = self._validate_optional_finite(
            value,
            "x1",
        )

    @property
    def b1(self) -> float | None:
        """
        Return positive-sequence shunt susceptance.
        """

        return self._b1

    @b1.setter
    def b1(
        self,
        value: float | None,
    ) -> None:
        self._b1 = self._validate_optional_finite(
            value,
            "b1",
        )

    # ================================================================
    # ZERO-SEQUENCE PARAMETERS
    # ================================================================

    @property
    def r0(self) -> float | None:
        """
        Return zero-sequence resistance.
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
        Return zero-sequence reactance.
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

    # ================================================================
    # RATED VOLTAGE
    # ================================================================

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

    # ================================================================
    # RATED CURRENT
    # ================================================================

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

    # ================================================================
    # VALIDATION
    # ================================================================

    def validate_parameters(self) -> bool:
        """
        Validate the complete Cable parameter hierarchy.

        Validation chain:

            Cable
              |
              v
            Branch
              |
              v
            ElectricalObject

        Cable-specific validation is performed after the inherited
        Branch/Base validation succeeds.
        """

        Branch.validate_parameters(
            self
        )

        self._length_km = (
            self._validate_optional_positive(
                self._length_km,
                "length_km",
            )
        )

        self._r1 = self._validate_optional_finite(
            self._r1,
            "r1",
        )

        self._x1 = self._validate_optional_finite(
            self._x1,
            "x1",
        )

        self._b1 = self._validate_optional_finite(
            self._b1,
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

    # ================================================================
    # DIAGNOSTICS
    # ================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return Cable-local diagnostics.

        No Network topology or study/numerical state is included.
        """

        summary = super().summary()

        summary.update(
            {
                "type": self.TYPE,
                "length_km": self._length_km,
                "r1": self._r1,
                "x1": self._x1,
                "b1": self._b1,
                "r0": self._r0,
                "x0": self._x0,
                "b0": self._b0,
                "rated_voltage_kv": (
                    self._rated_voltage_kv
                ),
                "rated_current_a": (
                    self._rated_current_a
                ),
            }
        )

        return summary

    # ================================================================
    # REPRESENTATION
    # ================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<Cable "
            f"id={self.id}, "
            f"length_km={self._length_km}, "
            f"rated_voltage_kv="
            f"{self._rated_voltage_kv}, "
            f"rated_current_a="
            f"{self._rated_current_a}, "
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
