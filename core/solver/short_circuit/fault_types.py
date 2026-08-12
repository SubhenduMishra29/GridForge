"""
GridForge Short-Circuit Fault Types
===================================

File:
    core/solver/short_circuit/fault_types.py

GridForge Short-Circuit Fault Classification V1.0
--------------------------------------------------

Defines the fundamental electrical fault classifications
supported by the GridForge short-circuit numerical engine.

Supported fault classes
-----------------------
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
- Provide deterministic fault-type classification utilities.
- Validate fault-type values.

This module does NOT:
- Calculate fault currents.
- Build impedance matrices.
- Build sequence networks.
- Calculate Zbus.
- Calculate Ybus.
- Perform symmetrical-component transformations.
- Calculate fault voltages.
- Calculate fault currents.
- Perform short-circuit iterations.
- Perform protection calculations.
- Perform breaker-duty calculations.
- Modify network state.

Calculation logic belongs to:

    core.solver.short_circuit.fault_calculator
    core.solver.short_circuit.symmetrical_fault
    core.solver.short_circuit.unsymmetrical_fault

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from enum import Enum


class FaultType(Enum):
    """
    Canonical GridForge electrical fault classifications.

    The enum intentionally represents fault topology only.
    Fault impedance, fault location, grounding conditions,
    prefault state, and sequence-network parameters belong
    to the corresponding short-circuit calculation layers.
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

    @classmethod
    def is_balanced(
        cls,
        fault_type: "FaultType",
    ) -> bool:
        """
        Return whether a fault type is balanced.

        Parameters
        ----------
        fault_type:
            FaultType value to classify.

        Returns
        -------
        bool
            True only for a three-phase fault.

        Raises
        ------
        TypeError
            If fault_type is not a FaultType instance.
        """

        cls.validate(
            fault_type
        )

        return fault_type is cls.THREE_PHASE

    @classmethod
    def is_unbalanced(
        cls,
        fault_type: "FaultType",
    ) -> bool:
        """
        Return whether a fault type is unbalanced.

        Parameters
        ----------
        fault_type:
            FaultType value to classify.

        Returns
        -------
        bool
            True for LG, LL, and LLG faults.

        Raises
        ------
        TypeError
            If fault_type is not a FaultType instance.
        """

        cls.validate(
            fault_type
        )

        return fault_type in (
            cls.SINGLE_LINE_GROUND,
            cls.LINE_LINE,
            cls.DOUBLE_LINE_GROUND,
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    @classmethod
    def validate(
        cls,
        fault_type: "FaultType",
    ) -> None:
        """
        Validate a fault-type value.

        Parameters
        ----------
        fault_type:
            Value to validate.

        Raises
        ------
        TypeError
            If the supplied value is not a FaultType.

        Notes
        -----
        Validation is intentionally strict.

        The numerical solver should receive canonical
        FaultType values rather than silently accepting
        arbitrary strings.
        """

        if not isinstance(
            fault_type,
            cls,
        ):
            raise TypeError(
                "fault_type must be an instance of "
                "FaultType."
            )

    # =========================================================
    # VALUE CONVERSION
    # =========================================================

    @classmethod
    def from_value(
        cls,
        value: str | "FaultType",
    ) -> "FaultType":
        """
        Convert a canonical fault value to FaultType.

        Parameters
        ----------
        value:
            Either an existing FaultType or one of the
            canonical values:

                "3PH"
                "LG"
                "LL"
                "LLG"

        Returns
        -------
        FaultType
            Canonical fault classification.

        Raises
        ------
        TypeError
            If value is neither a FaultType nor a string.

        ValueError
            If the string does not represent a supported
            fault type.
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
            raise TypeError(
                "Fault type value must be a string or "
                "FaultType instance."
            )

        try:

            return cls(
                value
            )

        except ValueError as exc:

            raise ValueError(
                f"Unsupported fault type: {value!r}. "
                "Supported values are: "
                "'3PH', 'LG', 'LL', 'LLG'."
            ) from exc

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __str__(
        self,
    ) -> str:
        """
        Return the canonical electrical fault code.
        """

        return self.value


__all__ = [
    "FaultType",
]
