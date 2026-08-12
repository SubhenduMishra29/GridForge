```python
"""
GridForge Symmetrical Fault Analysis
====================================

File:
    core/solver/short_circuit/symmetrical_fault.py

GridForge Short-Circuit Solver V2

Purpose
-------
Calculate balanced three-phase short-circuit faults using the
positive-sequence Thevenin impedance at the faulted bus.

Supported fault
---------------
    3PH

Reference equation
------------------
For a bolted or impedance three-phase fault:

    If = Vprefault / (Z1 + Zf)

where:

    Vprefault : complex prefault positive-sequence voltage
    Z1        : positive-sequence Thevenin impedance
    Zf        : fault impedance
    If        : positive-sequence fault current

Responsibilities
----------------
- Validate three-phase fault inputs.
- Obtain the positive-sequence Thevenin impedance from
  ImpedanceMatrix.
- Calculate complex fault current.
- Report current magnitude and angle.
- Return deterministic fault-analysis results.

This module does NOT:
- Build Ybus.
- Build Zbus.
- Perform network inversion.
- Modify the Network.
- Calculate unsymmetrical faults.
- Build sequence networks.
- Perform protection decisions.
- Perform relay coordination.
- Perform fault contribution aggregation.

Dependencies
------------
    core.solver.short_circuit.impedance_matrix

Architecture
------------
    Network
       │
       ▼
    Ybus / Zbus
       │
       ▼
    ImpedanceMatrix
       │
       ▼
    SymmetricalFault
       │
       ▼
    3PH fault result

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import cmath
import math
from typing import Any

import numpy as np

from .fault_types import FaultType


class SymmetricalFault:
    """
    Three-phase short-circuit calculation engine.

    Parameters
    ----------
    impedance_matrix:
        GridForge ImpedanceMatrix instance.

    Notes
    -----
    The impedance matrix owns Zbus construction and Thevenin
    impedance extraction. This class only performs the
    three-phase fault calculation.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        impedance_matrix: Any,
    ) -> None:
        """
        Initialize the three-phase fault calculator.
        """

        if impedance_matrix is None:
            raise ValueError(
                "Impedance matrix cannot be None."
            )

        required_methods = (
            "get_thevenin_impedance",
        )

        for method_name in required_methods:

            method = getattr(
                impedance_matrix,
                method_name,
                None,
            )

            if not callable(method):
                raise ValueError(
                    "Impedance matrix must provide "
                    f"'{method_name}()'."
                )

        self.impedance_matrix = impedance_matrix

    # =========================================================
    # VALIDATION HELPERS
    # =========================================================

    @staticmethod
    def _validate_bus_index(
        bus_index: Any,
    ) -> int:
        """
        Validate and normalize the fault-bus index.
        """

        if isinstance(
            bus_index,
            bool,
        ) or not isinstance(
            bus_index,
            (int, np.integer),
        ):
            raise TypeError(
                "bus_index must be an integer."
            )

        bus_index = int(
            bus_index
        )

        if bus_index < 0:
            raise ValueError(
                "bus_index cannot be negative."
            )

        return bus_index

    @staticmethod
    def _validate_complex(
        value: Any,
        name: str,
    ) -> complex:
        """
        Validate a finite real or complex numerical value.
        """

        try:
            value = complex(value)

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

        A negative real resistance is rejected because it does
        not represent a passive fault impedance.

        Reactive impedance may be positive or negative because
        the numerical layer should not impose an arbitrary
        inductive/capacitive restriction.
        """

        Zf = SymmetricalFault._validate_complex(
            Zf,
            "Zf",
        )

        if Zf.real < 0.0:
            raise ValueError(
                "Fault impedance real part cannot be negative."
            )

        return Zf

    # =========================================================
    # THEVENIN IMPEDANCE
    # =========================================================

    def get_thevenin_impedance(
        self,
        bus_index: int,
    ) -> complex:
        """
        Return the positive-sequence Thevenin impedance at a
        faulted bus.

        Parameters
        ----------
        bus_index:
            Zero-based network bus index.

        Returns
        -------
        complex
            Z1 Thevenin impedance.
        """

        bus_index = self._validate_bus_index(
            bus_index
        )

        try:

            Zth = self.impedance_matrix.get_thevenin_impedance(
                bus_index
            )

        except Exception as exc:

            raise RuntimeError(
                "Failed to obtain Thevenin impedance for "
                f"bus index {bus_index}: {exc}"
            ) from exc

        return self._validate_complex(
            Zth,
            "Thevenin impedance",
        )

    # =========================================================
    # THREE-PHASE FAULT
    # =========================================================

    def calculate_three_phase_fault(
        self,
        bus_index: int,
        Vprefault: Any = 1.0 + 0.0j,
        Zf: Any = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate a balanced three-phase fault.

        Parameters
        ----------
        bus_index:
            Zero-based fault-bus index.

        Vprefault:
            Complex prefault positive-sequence bus voltage in
            per-unit.

            Default:
                1.0 + j0 pu

        Zf:
            Complex fault impedance in per-unit.

            Default:
                0.0 + j0 pu

        Returns
        -------
        dict
            Deterministic three-phase fault result containing:

                fault_type
                bus_index
                Vprefault
                Z1
                Zf
                Z_total
                fault_current
                fault_current_magnitude
                fault_current_angle_deg
                balanced

        Raises
        ------
        ValueError
            For invalid inputs or a zero total impedance.

        RuntimeError
            If the Thevenin impedance cannot be obtained.
        """

        # -----------------------------------------------------
        # Validate inputs.
        # -----------------------------------------------------

        bus_index = self._validate_bus_index(
            bus_index
        )

        Vprefault = self._validate_complex(
            Vprefault,
            "Vprefault",
        )

        Zf = self._validate_fault_impedance(
            Zf
        )

        # -----------------------------------------------------
        # Obtain positive-sequence Thevenin impedance.
        # -----------------------------------------------------

        Z1 = self.get_thevenin_impedance(
            bus_index
        )

        # -----------------------------------------------------
        # Total fault impedance.
        # -----------------------------------------------------

        Z_total = Z1 + Zf

        Z_total = self._validate_complex(
            Z_total,
            "total fault impedance",
        )

        if abs(Z_total) <= np.finfo(float).eps:

            raise ValueError(
                "Total fault impedance is zero; "
                "three-phase fault current is undefined."
            )

        # -----------------------------------------------------
        # Three-phase fault current.
        #
        # Per-unit formulation:
        #
        #     If = Vprefault / (Z1 + Zf)
        # -----------------------------------------------------

        fault_current = (
            Vprefault
            /
            Z_total
        )

        fault_current = self._validate_complex(
            fault_current,
            "fault current",
        )

        # -----------------------------------------------------
        # Current polar quantities.
        # -----------------------------------------------------

        magnitude = abs(
            fault_current
        )

        angle_deg = math.degrees(
            cmath.phase(
                fault_current
            )
        )

        # -----------------------------------------------------
        # Deterministic result.
        # -----------------------------------------------------

        return {
            "fault_type": FaultType.THREE_PHASE.value,
            "bus_index": bus_index,
            "Vprefault": Vprefault,
            "Z1": Z1,
            "Zf": Zf,
            "Z_total": Z_total,
            "fault_current": fault_current,
            "fault_current_magnitude": float(
                magnitude
            ),
            "fault_current_angle_deg": float(
                angle_deg
            ),
            "balanced": True,
        }

    # =========================================================
    # CONVENIENCE ALIAS
    # =========================================================

    def calculate(
        self,
        bus_index: int,
        Vprefault: Any = 1.0 + 0.0j,
        Zf: Any = 0.0 + 0.0j,
    ) -> dict:
        """
        Generic calculation entry point for a symmetrical
        three-phase fault.

        This alias exists to provide a consistent public
        calculation interface without introducing a separate
        fault-dispatch mechanism inside this module.
        """

        return self.calculate_three_phase_fault(
            bus_index=bus_index,
            Vprefault=Vprefault,
            Zf=Zf,
        )

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return calculator diagnostics.
        """

        return {
            "calculator": "SymmetricalFault",
            "version": "2.0",
            "supported_faults": [
                FaultType.THREE_PHASE.value,
            ],
            "method": (
                "Positive-sequence Thevenin impedance"
            ),
            "returns_complex_current": True,
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            "SymmetricalFault("
            "impedance_matrix="
            f"{type(self.impedance_matrix).__name__}"
            ")"
        )


__all__ = [
    "SymmetricalFault",
]
```
