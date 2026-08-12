"""
GridForge Short-Circuit Fault Types
===================================

File:
    core/solver/short_circuit/fault_types.py

GridForge Short-Circuit Solver V1.0
-----------------------------------

Defines the supported electrical fault classifications used
by the GridForge short-circuit numerical layer.

Supported fault types
---------------------
THREE_PHASE
    Balanced three-phase fault.

SINGLE_LINE_GROUND
    Single-line-to-ground fault (LG).

LINE_LINE
    Line-to-line fault (LL).

DOUBLE_LINE_GROUND
    Double-line-to-ground fault (LLG).

Responsibilities
----------------
- Define canonical fault classifications.
- Provide deterministic fault classification utilities.
- Validate fault-type values.
- Provide stable string representations.

This module does NOT:
- Calculate fault currents.
- Build Ybus.
- Build Zbus.
- Build sequence networks.
- Modify network topology.
- Perform short-circuit calculations.
- Perform protection decisions.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class FaultType(str, Enum):
    """
    Canonical GridForge electrical fault classifications.

    The enumeration inherits from ``str`` so that fault types
    remain convenient for serialization while retaining the
    safety of an explicit enumeration.
    """

    # =========================================================
    # BALANCED FAULT
    # =========================================================

    THREE_PHASE = "3PH"

    # =========================================================
    # UNBALANCED FAULTS
    # =========================================================

    SINGLE_LINE_GROUND = "LG"

    LINE_LINE = "LL"

    DOUBLE_LINE_GROUND = "LLG"

    # =========================================================
    # CLASSIFICATION
    # =========================================================

    @property
    def is_balanced(self) -> bool:
        """
        Return whether this is a balanced fault.

        Returns
        -------
        bool
            ``True`` only for a three-phase fault.
        """

        return self is FaultType.THREE_PHASE

    @property
    def is_unbalanced(self) -> bool:
        """
        Return whether this is an unbalanced fault.

        Returns
        -------
        bool
            ``True`` for LG, LL, and LLG faults.
        """

        return self is not FaultType.THREE_PHASE

    # =========================================================
    # SEQUENCE REQUIREMENT
    # =========================================================

    @property
    def requires_positive_sequence(self) -> bool:
        """
        Return whether the fault requires positive-sequence data.

        All supported fault types require the positive-sequence
        network.
        """

        return True

    @property
    def requires_negative_sequence(self) -> bool:
        """
        Return whether the fault requires negative-sequence data.

        Negative sequence is required for LL and LLG faults.
        It is also part of the complete sequence formulation for
        an LG fault.
        """

        return self in (
            FaultType.SINGLE_LINE_GROUND,
            FaultType.LINE_LINE,
            FaultType.DOUBLE_LINE_GROUND,
        )

    @property
    def requires_zero_sequence(self) -> bool:
        """
        Return whether the fault requires zero-sequence data.

        Zero sequence is required for LG and LLG faults.
        """

        return self in (
            FaultType.SINGLE_LINE_GROUND,
            FaultType.DOUBLE_LINE_GROUND,
        )

    # =========================================================
    # CONVERSION
    # =========================================================

    @classmethod
    def from_value(
        cls,
        value: Any,
    ) -> "FaultType":
        """
        Convert a supported value into ``FaultType``.

        Accepted values include:

        - FaultType members.
        - Canonical values such as ``"3PH"``, ``"LG"``,
          ``"LL"``, and ``"LLG"``.
        - Enumeration names such as ``"THREE_PHASE"``.

        Parameters
        ----------
        value:
            Fault classification to normalize.

        Returns
        -------
        FaultType
            Canonical fault type.

        Raises
        ------
        ValueError
            If the value is not a supported fault type.
        """

        if isinstance(
            value,
            cls,
        ):
            return value

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                "Fault type must be a FaultType or string value."
            )

        normalized = value.strip().upper()

        # -----------------------------------------------------
        # Canonical serialized values.
        # -----------------------------------------------------

        for fault_type in cls:

            if normalized == fault_type.value:
                return fault_type

        # -----------------------------------------------------
        # Enumeration names.
        # -----------------------------------------------------

        try:
            return cls[
                normalized
            ]

        except KeyError as exc:
            raise ValueError(
                "Unsupported fault type: "
                f"{value!r}. Supported values are: "
                f"{', '.join(item.value for item in cls)}."
            ) from exc

    # =========================================================
    # VALIDATION
    # =========================================================

    @classmethod
    def validate(
        cls,
        value: Any,
    ) -> "FaultType":
        """
        Validate and normalize a fault type.

        This is an explicit convenience alias for
        ``FaultType.from_value()``.

        Parameters
        ----------
        value:
            Fault classification to validate.

        Returns
        -------
        FaultType
            Validated canonical fault type.
        """

        return cls.from_value(
            value
        )

    # =========================================================
    # COLLECTION UTILITIES
    # =========================================================

    @classmethod
    def balanced_types(
        cls,
    ) -> tuple["FaultType", ...]:
        """
        Return all supported balanced fault types.
        """

        return (
            cls.THREE_PHASE,
        )

    @classmethod
    def unbalanced_types(
        cls,
    ) -> tuple["FaultType", ...]:
        """
        Return all supported unbalanced fault types.
        """

        return (
            cls.SINGLE_LINE_GROUND,
            cls.LINE_LINE,
            cls.DOUBLE_LINE_GROUND,
        )

    @classmethod
    def supported_types(
        cls,
    ) -> tuple["FaultType", ...]:
        """
        Return all supported GridForge fault types.
        """

        return tuple(cls)

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __str__(
        self,
    ) -> str:
        """
        Return the canonical serialized fault code.
        """

        return self.value


__all__ = [
    "FaultType",
]
