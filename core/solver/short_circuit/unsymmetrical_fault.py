```python
"""
GridForge Unsymmetrical Fault Analysis
======================================

File:
    core/solver/short_circuit/unsymmetrical_fault.py

GridForge Short-Circuit Solver V2

Purpose
-------
Calculate unsymmetrical short-circuit faults using positive,
negative, and zero-sequence network impedances.

Supported faults
----------------
    LG   - Single line-to-ground
    LL   - Line-to-line
    LLG  - Double line-to-ground

Sequence networks
-----------------
    Positive sequence : Z1
    Negative sequence : Z2
    Zero sequence     : Z0

The sequence impedances are supplied by:

    core.solver.short_circuit.sequence_network.SequenceNetwork

Responsibilities
----------------
- Validate fault inputs.
- Obtain sequence equivalent impedances.
- Calculate sequence currents.
- Calculate physical fault-current quantities.
- Support fault impedance.
- Return deterministic fault-analysis results.

This module does NOT:
- Build Ybus.
- Build Zbus.
- Perform network inversion.
- Modify the Network.
- Build sequence networks.
- Perform relay/protection decisions.
- Perform relay coordination.
- Perform contingency analysis.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import cmath
import math
from typing import Any, Iterable

import numpy as np

from .fault_types import FaultType


class UnsymmetricalFault:
    """
    Unsymmetrical short-circuit calculation engine.

    Parameters
    ----------
    sequence_network:
        GridForge SequenceNetwork instance.

    Notes
    -----
    The SequenceNetwork owns sequence impedance data.

    This class performs the fault-specific sequence-network
    algebra only.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        sequence_network: Any,
    ) -> None:

        if sequence_network is None:
            raise ValueError(
                "Sequence network cannot be None."
            )

        required_methods = (
            "total_impedance",
        )

        for method_name in required_methods:

            method = getattr(
                sequence_network,
                method_name,
                None,
            )

            if not callable(method):
                raise ValueError(
                    "Sequence network must provide "
                    f"'{method_name}()'."
                )

        self.sequence_network = sequence_network

    # =========================================================
    # VALIDATION HELPERS
    # =========================================================

    @staticmethod
    def _validate_elements(
        elements: Iterable[Any],
    ) -> list:
        """
        Validate and normalize the sequence-network element
        collection.
        """

        if elements is None:
            raise ValueError(
                "elements cannot be None."
            )

        try:
            result = list(
                elements
            )

        except TypeError as exc:

            raise TypeError(
                "elements must be an iterable."
            ) from exc

        if len(result) == 0:
            raise ValueError(
                "At least one sequence-network element "
                "is required."
            )

        return result

    @staticmethod
    def _validate_complex(
        value: Any,
        name: str,
    ) -> complex:
        """
        Validate a finite real or complex number.
        """

        try:
            value = complex(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise TypeError(
                f"{name} must be a real or complex number."
            ) from exc

        if not (
            math.isfinite(value.real)
            and math.isfinite(value.imag)
        ):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @staticmethod
    def _validate_fault_impedance(
        Zf: Any,
    ) -> complex:
        """
        Validate fault impedance.
        """

        Zf = UnsymmetricalFault._validate_complex(
            Zf,
            "Zf",
        )

        if Zf.real < 0.0:
            raise ValueError(
                "Fault impedance real part cannot be negative."
            )

        return Zf

    @staticmethod
    def _validate_total_impedance(
        Z: complex,
        name: str,
    ) -> complex:
        """
        Validate an equivalent sequence impedance and reject
        an effectively zero denominator.
        """

        Z = UnsymmetricalFault._validate_complex(
            Z,
            name,
        )

        if abs(Z) <= np.finfo(float).eps:

            raise ValueError(
                f"{name} is zero; fault current is undefined."
            )

        return Z

    # =========================================================
    # SEQUENCE IMPEDANCES
    # =========================================================

    def _get_sequence_impedances(
        self,
        elements: Iterable[Any],
    ) -> tuple[complex, complex, complex]:
        """
        Obtain positive, negative, and zero sequence equivalent
        impedances.
        """

        elements = self._validate_elements(
            elements
        )

        try:

            Z1 = self.sequence_network.total_impedance(
                elements,
                "positive",
            )

            Z2 = self.sequence_network.total_impedance(
                elements,
                "negative",
            )

            Z0 = self.sequence_network.total_impedance(
                elements,
                "zero",
            )

        except Exception as exc:

            raise RuntimeError(
                "Failed to obtain sequence impedances: "
                f"{exc}"
            ) from exc

        Z1 = self._validate_complex(
            Z1,
            "Z1",
        )

        Z2 = self._validate_complex(
            Z2,
            "Z2",
        )

        Z0 = self._validate_complex(
            Z0,
            "Z0",
        )

        return Z1, Z2, Z0

    # =========================================================
    # SEQUENCE RESULT HELPERS
    # =========================================================

    @staticmethod
    def _polar(
        value: complex,
    ) -> tuple[float, float]:
        """
        Return magnitude and angle in degrees.
        """

        return (
            float(abs(value)),
            float(
                math.degrees(
                    cmath.phase(value)
                )
            ),
        )

    @staticmethod
    def _result_sequence_quantities(
        I1: complex,
        I2: complex,
        I0: complex,
    ) -> dict:
        """
        Build deterministic sequence-current diagnostics.
        """

        I1_mag, I1_ang = UnsymmetricalFault._polar(I1)
        I2_mag, I2_ang = UnsymmetricalFault._polar(I2)
        I0_mag, I0_ang = UnsymmetricalFault._polar(I0)

        return {
            "sequence_currents": {
                "I1": I1,
                "I2": I2,
                "I0": I0,
            },
            "sequence_current_magnitudes": {
                "I1": I1_mag,
                "I2": I2_mag,
                "I0": I0_mag,
            },
            "sequence_current_angles_deg": {
                "I1": I1_ang,
                "I2": I2_ang,
                "I0": I0_ang,
            },
        }

    # =========================================================
    # LG FAULT
    # =========================================================

    def calculate_lg_fault(
        self,
        elements: Iterable[Any],
        Vprefault: Any = 1.0 + 0.0j,
        Zf: Any = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate a single line-to-ground fault.

        Sequence-network equation:

            I1 = I2 = I0

            I1 =
                Vprefault
                -----------------------
                Z1 + Z2 + Z0 + 3 Zf

        Ground/fault current:

            If = Ia = 3 I0

        Parameters
        ----------
        elements:
            Sequence-network elements forming the fault path.

        Vprefault:
            Prefault positive-sequence voltage in per-unit.

        Zf:
            Fault impedance in per-unit.

        Returns
        -------
        dict
            Fault result including sequence and physical
            fault-current quantities.
        """

        Vprefault = self._validate_complex(
            Vprefault,
            "Vprefault",
        )

        Zf = self._validate_fault_impedance(
            Zf
        )

        Z1, Z2, Z0 = self._get_sequence_impedances(
            elements
        )

        Z_total = self._validate_total_impedance(
            Z1 + Z2 + Z0 + 3.0 * Zf,
            "LG total sequence impedance",
        )

        I1 = (
            Vprefault
            /
            Z_total
        )

        I2 = I1
        I0 = I1

        If = 3.0 * I0

        If_mag, If_ang = self._polar(
            If
        )

        result = {
            "fault_type": FaultType.SINGLE_LINE_GROUND.value,
            "Vprefault": Vprefault,
            "Z1": Z1,
            "Z2": Z2,
            "Z0": Z0,
            "Zf": Zf,
            "Z_total": Z_total,
            "fault_current": If,
            "fault_current_magnitude": If_mag,
            "fault_current_angle_deg": If_ang,
            "ground_current": If,
            "ground_current_magnitude": If_mag,
        }

        result.update(
            self._result_sequence_quantities(
                I1,
                I2,
                I0,
            )
        )

        return result

    # =========================================================
    # LL FAULT
    # =========================================================

    def calculate_ll_fault(
        self,
        elements: Iterable[Any],
        Vprefault: Any = 1.0 + 0.0j,
        Zf: Any = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate a line-to-line fault.

        For a line-to-line fault:

            I0 = 0

            I1 =
                Vprefault
                ----------------
                Z1 + Z2 + Zf

            I2 = -I1

        The magnitude of the physical line current is:

            |If| = sqrt(3) |I1|

        Parameters
        ----------
        elements:
            Sequence-network elements forming the fault path.

        Vprefault:
            Prefault positive-sequence voltage in per-unit.

        Zf:
            Fault impedance in per-unit.

        Returns
        -------
        dict
            LL fault result.
        """

        Vprefault = self._validate_complex(
            Vprefault,
            "Vprefault",
        )

        Zf = self._validate_fault_impedance(
            Zf
        )

        Z1, Z2, Z0 = self._get_sequence_impedances(
            elements
        )

        Z_total = self._validate_total_impedance(
            Z1 + Z2 + Zf,
            "LL total sequence impedance",
        )

        I1 = (
            Vprefault
            /
            Z_total
        )

        I2 = -I1
        I0 = 0.0 + 0.0j

        # -----------------------------------------------------
        # Phase currents using symmetrical components:
        #
        # Ia = I0 + I1 + I2 = 0
        #
        # Ib = I0 + a^2 I1 + a I2
        #
        # Ic = I0 + a I1 + a^2 I2
        # -----------------------------------------------------

        a = cmath.exp(
            1j * 2.0 * math.pi / 3.0
        )

        Ia = (
            I0
            + I1
            + I2
        )

        Ib = (
            I0
            + (a ** 2) * I1
            + a * I2
        )

        Ic = (
            I0
            + a * I1
            + (a ** 2) * I2
        )

        If = Ib

        If_mag, If_ang = self._polar(
            If
        )

        result = {
            "fault_type": FaultType.LINE_LINE.value,
            "Vprefault": Vprefault,
            "Z1": Z1,
            "Z2": Z2,
            "Z0": Z0,
            "Zf": Zf,
            "Z_total": Z_total,
            "fault_current": If,
            "fault_current_magnitude": If_mag,
            "fault_current_angle_deg": If_ang,
            "phase_currents": {
                "Ia": Ia,
                "Ib": Ib,
                "Ic": Ic,
            },
            "phase_current_magnitudes": {
                "Ia": float(abs(Ia)),
                "Ib": float(abs(Ib)),
                "Ic": float(abs(Ic)),
            },
        }

        result.update(
            self._result_sequence_quantities(
                I1,
                I2,
                I0,
            )
        )

        return result

    # =========================================================
    # LLG FAULT
    # =========================================================

    def calculate_llg_fault(
        self,
        elements: Iterable[Any],
        Vprefault: Any = 1.0 + 0.0j,
        Zf: Any = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate a double line-to-ground fault.

        Sequence-network relationship:

            Zg = Z0 + 3 Zf

            Zparallel =
                Z2 * Zg
                -----------
                Z2 + Zg

            I1 =
                Vprefault
                -----------------
                Z1 + Zparallel

        The remaining sequence currents are:

            I0 = -I1 * Z2 / (Z2 + Zg)

            I2 = -I1 * Zg / (Z2 + Zg)

        The physical phase currents are then obtained from
        symmetrical-component transformation.

        Parameters
        ----------
        elements:
            Sequence-network elements forming the fault path.

        Vprefault:
            Prefault positive-sequence voltage in per-unit.

        Zf:
            Fault impedance in per-unit.

        Returns
        -------
        dict
            LLG fault result.
        """

        Vprefault = self._validate_complex(
            Vprefault,
            "Vprefault",
        )

        Zf = self._validate_fault_impedance(
            Zf
        )

        Z1, Z2, Z0 = self._get_sequence_impedances(
            elements
        )

        Zg = (
            Z0
            +
            3.0 * Zf
        )

        denominator = (
            Z2
            +
            Zg
        )

        denominator = self._validate_total_impedance(
            denominator,
            "LLG negative/zero-sequence coupling impedance",
        )

        Zparallel = (
            Z2
            *
            Zg
            /
            denominator
        )

        Z_total = self._validate_total_impedance(
            Z1 + Zparallel,
            "LLG total sequence impedance",
        )

        I1 = (
            Vprefault
            /
            Z_total
        )

        I2 = (
            -I1
            *
            Zg
            /
            denominator
        )

        I0 = (
            -I1
            *
            Z2
            /
            denominator
        )

        # -----------------------------------------------------
        # Symmetrical-component transformation.
        # -----------------------------------------------------

        a = cmath.exp(
            1j * 2.0 * math.pi / 3.0
        )

        Ia = (
            I0
            + I1
            + I2
        )

        Ib = (
            I0
            + (a ** 2) * I1
            + a * I2
        )

        Ic = (
            I0
            + a * I1
            + (a ** 2) * I2
        )

        # -----------------------------------------------------
        # Ground current.
        #
        # Ig = Ia + Ib + Ic = 3 I0
        # -----------------------------------------------------

        Ig = (
            Ia
            + Ib
            + Ic
        )

        If_mag, If_ang = self._polar(
            Ia
        )

        result = {
            "fault_type": FaultType.DOUBLE_LINE_GROUND.value,
            "Vprefault": Vprefault,
            "Z1": Z1,
            "Z2": Z2,
            "Z0": Z0,
            "Zf": Zf,
            "Zg": Zg,
            "Zparallel": Zparallel,
            "Z_total": Z_total,
            "fault_current": Ia,
            "fault_current_magnitude": If_mag,
            "fault_current_angle_deg": If_ang,
            "phase_currents": {
                "Ia": Ia,
                "Ib": Ib,
                "Ic": Ic,
            },
            "phase_current_magnitudes": {
                "Ia": float(abs(Ia)),
                "Ib": float(abs(Ib)),
                "Ic": float(abs(Ic)),
            },
            "ground_current": Ig,
            "ground_current_magnitude": float(
                abs(Ig)
            ),
        }

        result.update(
            self._result_sequence_quantities(
                I1,
                I2,
                I0,
            )
        )

        return result

    # =========================================================
    # GENERIC DISPATCH
    # =========================================================

    def calculate(
        self,
        fault_type: FaultType | str,
        elements: Iterable[Any],
        Vprefault: Any = 1.0 + 0.0j,
        Zf: Any = 0.0 + 0.0j,
    ) -> dict:
        """
        Dispatch an unsymmetrical fault calculation.

        Parameters
        ----------
        fault_type:
            FaultType member or its string value.

        elements:
            Sequence-network elements.

        Vprefault:
            Prefault positive-sequence voltage.

        Zf:
            Fault impedance.

        Returns
        -------
        dict
            Fault-specific result.
        """

        if isinstance(
            fault_type,
            FaultType,
        ):

            fault_value = fault_type.value

        elif isinstance(
            fault_type,
            str,
        ):

            fault_value = fault_type.upper()

        else:

            raise TypeError(
                "fault_type must be a FaultType or string."
            )

        if fault_value == FaultType.SINGLE_LINE_GROUND.value:

            return self.calculate_lg_fault(
                elements,
                Vprefault,
                Zf,
            )

        if fault_value == FaultType.LINE_LINE.value:

            return self.calculate_ll_fault(
                elements,
                Vprefault,
                Zf,
            )

        if fault_value == FaultType.DOUBLE_LINE_GROUND.value:

            return self.calculate_llg_fault(
                elements,
                Vprefault,
                Zf,
            )

        raise ValueError(
            "Unsupported unsymmetrical fault type: "
            f"{fault_type}"
        )

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return calculator diagnostics.
        """

        return {
            "calculator": "UnsymmetricalFault",
            "version": "2.0",
            "supported_faults": [
                FaultType.SINGLE_LINE_GROUND.value,
                FaultType.LINE_LINE.value,
                FaultType.DOUBLE_LINE_GROUND.value,
            ],
            "sequence_networks": [
                "positive",
                "negative",
                "zero",
            ],
            "returns_sequence_currents": True,
            "returns_phase_currents": True,
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            "UnsymmetricalFault("
            "sequence_network="
            f"{type(self.sequence_network).__name__}"
            ")"
        )


__all__ = [
    "UnsymmetricalFault",
]
```
