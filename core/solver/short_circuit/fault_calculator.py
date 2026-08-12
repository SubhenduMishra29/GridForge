"""
GridForge Fault Calculator V2
=============================

File:
    core/solver/short_circuit/fault_calculator.py

Purpose
-------
Common numerical utilities for GridForge short-circuit studies.

Responsibilities
----------------
- Extract prefault bus voltage.
- Validate fault impedance.
- Calculate fault current from voltage and equivalent impedance.
- Calculate three-phase fault level.
- Provide common numerical validation.
- Construct standardized fault-result dictionaries.

This module does NOT:
- Build Ybus.
- Build Zbus.
- Build sequence networks.
- Determine fault type.
- Assemble sequence networks.
- Perform symmetrical-component transformations.
- Decide protection operation.
- Modify network topology.

Architecture
------------

                    Short-Circuit Solver
                            │
                            ▼
                    FaultCalculator
                     /            \
                    ▼              ▼
             SymmetricalFault   UnsymmetricalFault
                    │              │
                    └──────┬───────┘
                           ▼
                    Common Results

Unit convention
---------------
Unless explicitly stated otherwise:

- Voltage magnitude: per-unit
- Impedance: per-unit
- Current: per-unit
- Fault level: MVA when base quantities are supplied

For a three-phase system:

    S_fault = sqrt(3) × V_kV × I_kA

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

import cmath
from typing import Any

import numpy as np


class FaultCalculator:
    """
    Common numerical utility layer for GridForge
    short-circuit calculations.

    Parameters
    ----------
    network:
        GridForge Network object.

    Notes
    -----
    This class deliberately contains no fault-type-specific
    sequence-network equations. Those equations belong to the
    specialized fault calculators.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        network,
    ) -> None:
        """
        Initialize the common fault-calculation utilities.
        """

        if network is None:
            raise ValueError(
                "Network cannot be None."
            )

        if not hasattr(
            network,
            "buses",
        ):
            raise ValueError(
                "Network must provide a 'buses' collection."
            )

        self.network = network

    # =========================================================
    # NUMERICAL VALIDATION
    # =========================================================

    @staticmethod
    def _validate_complex(
        value: Any,
        name: str,
    ) -> complex:
        """
        Validate a finite complex-valued quantity.
        """

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be a numerical value."
            )

        try:

            value = complex(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise TypeError(
                f"{name} must be a valid complex number."
            ) from exc

        if not (
            np.isfinite(
                value.real
            )
            and
            np.isfinite(
                value.imag
            )
        ):

            raise ValueError(
                f"{name} must contain finite values."
            )

        return value

    @staticmethod
    def _validate_real(
        value: Any,
        name: str,
        *,
        minimum: float | None = None,
        strictly_positive: bool = False,
    ) -> float:
        """
        Validate a finite real-valued quantity.
        """

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be a real number."
            )

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise TypeError(
                f"{name} must be a real number."
            ) from exc

        if not np.isfinite(
            value
        ):
            raise ValueError(
                f"{name} must be finite."
            )

        if strictly_positive and value <= 0.0:

            raise ValueError(
                f"{name} must be greater than zero."
            )

        if (
            minimum is not None
            and
            value < minimum
        ):

            raise ValueError(
                f"{name} must be greater than or equal "
                f"to {minimum}."
            )

        return value

    # =========================================================
    # BUS LOOKUP
    # =========================================================

    def _get_bus(
        self,
        bus_id: Any,
    ):
        """
        Locate a bus by its GridForge bus identifier.
        """

        if bus_id is None:

            raise ValueError(
                "bus_id cannot be None."
            )

        for bus in self.network.buses:

            if getattr(
                bus,
                "id",
                None,
            ) == bus_id:

                return bus

        raise ValueError(
            f"Bus {bus_id!r} not found."
        )

    # =========================================================
    # PREFAULT VOLTAGE
    # =========================================================

    def get_prefault_voltage(
        self,
        bus_id: Any,
    ) -> complex:
        """
        Return the complex prefault voltage at a bus.

        Parameters
        ----------
        bus_id:
            GridForge bus identifier.

        Returns
        -------
        complex
            Prefault voltage in per-unit:

                V = Vm * exp(j * Va)

        Notes
        -----
        The method reads the current solved voltage state from
        the unified Bus model.

        It does not perform a load-flow calculation.
        """

        bus = self._get_bus(
            bus_id
        )

        if not hasattr(
            bus,
            "V",
        ):
            raise ValueError(
                f"Bus {bus_id!r} does not provide voltage "
                "magnitude 'V'."
            )

        if not hasattr(
            bus,
            "theta",
        ):
            raise ValueError(
                f"Bus {bus_id!r} does not provide voltage "
                "angle 'theta'."
            )

        voltage_magnitude = self._validate_real(
            bus.V,
            f"Bus {bus_id!r} voltage magnitude",
            minimum=0.0,
        )

        angle = self._validate_real(
            bus.theta,
            f"Bus {bus_id!r} voltage angle",
        )

        voltage = (
            voltage_magnitude
            *
            cmath.exp(
                1j * angle
            )
        )

        return self._validate_complex(
            voltage,
            "prefault voltage",
        )

    # =========================================================
    # PREFault VOLTAGE BY INDEX
    # =========================================================

    def get_prefault_voltage_by_index(
        self,
        bus_index: int,
    ) -> complex:
        """
        Return prefault voltage using network bus index.

        This is useful for Zbus-based calculations where the
        fault location is represented by a matrix index.
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

        if not (
            0 <= bus_index < len(
                self.network.buses
            )
        ):

            raise IndexError(
                f"Bus index {bus_index} is outside the "
                f"valid range 0 to "
                f"{len(self.network.buses) - 1}."
            )

        bus = self.network.buses[
            bus_index
        ]

        if not hasattr(
            bus,
            "id",
        ):

            raise ValueError(
                f"Bus at index {bus_index} does not provide an ID."
            )

        return self.get_prefault_voltage(
            bus.id
        )

    # =========================================================
    # FAULT IMPEDANCE
    # =========================================================

    @classmethod
    def validate_fault_impedance(
        cls,
        Zf: Any,
        *,
        name: str = "Zf",
    ) -> complex:
        """
        Validate a fault impedance.

        Parameters
        ----------
        Zf:
            Fault impedance in per-unit.

        Returns
        -------
        complex
            Validated fault impedance.

        Notes
        -----
        A zero fault impedance is valid and represents a
        bolted fault.

        Therefore this method does NOT reject Zf = 0.
        """

        return cls._validate_complex(
            Zf,
            name,
        )

    # =========================================================
    # FAULT CURRENT
    # =========================================================

    @classmethod
    def calculate_current(
        cls,
        V_prefault: Any,
        Z_fault: Any,
        *,
        denominator_tolerance: float = 1.0e-14,
    ) -> complex:
        """
        Calculate fault current from prefault voltage and
        equivalent fault impedance.

        Equation
        --------
            If = Vprefault / Zfault

        Parameters
        ----------
        V_prefault:
            Complex prefault voltage in per-unit.

        Z_fault:
            Complex equivalent fault impedance in per-unit.

        denominator_tolerance:
            Numerical threshold used to detect an effectively
            zero denominator.

        Returns
        -------
        complex
            Fault current in per-unit.
        """

        V_prefault = cls._validate_complex(
            V_prefault,
            "V_prefault",
        )

        Z_fault = cls.validate_fault_impedance(
            Z_fault
        )

        denominator_tolerance = cls._validate_real(
            denominator_tolerance,
            "denominator_tolerance",
            minimum=0.0,
        )

        if abs(
            Z_fault
        ) <= denominator_tolerance:

            raise ZeroDivisionError(
                "Fault equivalent impedance is zero or "
                "numerically zero."
            )

        current = (
            V_prefault
            /
            Z_fault
        )

        return cls._validate_complex(
            current,
            "fault current",
        )

    # =========================================================
    # FAULT MVA
    # =========================================================

    @classmethod
    def fault_mva(
        cls,
        voltage_kv: Any,
        current_ka: Any,
    ) -> float:
        """
        Calculate three-phase fault level.

        Equation
        --------
            S_fault = sqrt(3) × V_kV × I_kA

        Parameters
        ----------
        voltage_kv:
            Line-to-line voltage in kV.

        current_ka:
            Fault-current magnitude in kA.

        Returns
        -------
        float
            Three-phase fault level in MVA.
        """

        voltage_kv = cls._validate_real(
            voltage_kv,
            "voltage_kv",
            strictly_positive=True,
        )

        current_ka = cls._validate_real(
            current_ka,
            "current_ka",
            minimum=0.0,
        )

        return float(
            np.sqrt(3.0)
            *
            voltage_kv
            *
            current_ka
        )

    # =========================================================
    # CURRENT MAGNITUDE
    # =========================================================

    @staticmethod
    def current_magnitude(
        current: Any,
    ) -> float:
        """
        Return the magnitude of a complex fault current.
        """

        current = FaultCalculator._validate_complex(
            current,
            "current",
        )

        return float(
            abs(current)
        )

    # =========================================================
    # STANDARD RESULT
    # =========================================================

    @classmethod
    def result(
        cls,
        *,
        bus_id: Any,
        fault_type: Any,
        current: Any,
        impedance: Any,
        prefault_voltage: Any | None = None,
        fault_mva: float | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """
        Construct a standardized GridForge fault result.

        Parameters
        ----------
        bus_id:
            Faulted bus identifier.

        fault_type:
            Fault classification.

        current:
            Complex fault current in per-unit.

        impedance:
            Equivalent fault impedance in per-unit.

        prefault_voltage:
            Optional complex prefault voltage.

        fault_mva:
            Optional three-phase fault level.

        metadata:
            Optional additional calculation metadata.

        Returns
        -------
        dict
            Standardized fault result.
        """

        if bus_id is None:

            raise ValueError(
                "bus_id cannot be None."
            )

        if fault_type is None:

            raise ValueError(
                "fault_type cannot be None."
            )

        current = cls._validate_complex(
            current,
            "current",
        )

        impedance = cls._validate_complex(
            impedance,
            "impedance",
        )

        result = {
            "bus": bus_id,
            "fault_type": (
                fault_type.value
                if hasattr(
                    fault_type,
                    "value",
                )
                else fault_type
            ),
            "fault_current": current,
            "fault_current_magnitude": float(
                abs(current)
            ),
            "fault_impedance": impedance,
        }

        if prefault_voltage is not None:

            prefault_voltage = cls._validate_complex(
                prefault_voltage,
                "prefault_voltage",
            )

            result[
                "prefault_voltage"
            ] = prefault_voltage

        if fault_mva is not None:

            fault_mva = cls._validate_real(
                fault_mva,
                "fault_mva",
                minimum=0.0,
            )

            result[
                "fault_mva"
            ] = fault_mva

        if metadata is not None:

            if not isinstance(
                metadata,
                dict,
            ):

                raise TypeError(
                    "metadata must be a dictionary."
                )

            result[
                "metadata"
            ] = dict(
                metadata
            )

        return result

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(
        self,
    ) -> dict:
        """
        Return diagnostics for the common calculator.
        """

        return {
            "component": "FaultCalculator",
            "version": "2.0",
            "buses": len(
                self.network.buses
            ),
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Developer-friendly representation.
        """

        return (
            "FaultCalculator("
            f"buses={len(self.network.buses)}"
            ")"
        )


__all__ = [
    "FaultCalculator",
]
