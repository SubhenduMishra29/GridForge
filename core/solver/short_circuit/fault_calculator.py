"""
GridForge Short-Circuit Fault Calculator
========================================

File:
    core/solver/short_circuit/fault_calculator.py

GridForge Short-Circuit Solver V2.0
-----------------------------------

Common numerical utilities shared by the short-circuit fault
calculators.

Responsibilities
----------------
- Obtain prefault bus voltage.
- Calculate fault current from voltage and impedance.
- Calculate three-phase fault level.
- Validate electrical quantities.
- Provide a consistent fault-result structure.

This module does NOT:
- Build Ybus.
- Build Zbus.
- Determine fault type.
- Perform sequence-network calculations.
- Modify network topology.
- Perform protection decisions.
- Perform relay coordination.

Architecture
------------

    Network
       │
       ├── Prefault voltage
       │
       ▼
    FaultCalculator
       │
       ├── current calculation
       ├── fault MVA
       └── result normalization

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import cmath
from typing import Any

import numpy as np


class FaultCalculator:
    """
    Common short-circuit calculation service.

    Parameters
    ----------
    network:
        GridForge Network object containing the ordered
        collection of Bus objects.

    Notes
    -----
    Voltage angles are assumed to be in radians and voltage
    magnitudes are assumed to be in per-unit.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        network: Any,
    ) -> None:

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
    # PREFault VOLTAGE
    # =========================================================

    def get_prefault_voltage(
        self,
        bus_id: Any,
    ) -> complex:
        """
        Return the solved prefault complex voltage at a bus.

        Parameters
        ----------
        bus_id:
            Public GridForge bus identifier.

        Returns
        -------
        complex
            Prefault voltage:

                V = Vm ∠ theta

        Raises
        ------
        ValueError
            If the bus cannot be found or its voltage state is
            invalid.
        """

        for bus in self.network.buses:

            if getattr(
                bus,
                "id",
                None,
            ) != bus_id:

                continue

            if not hasattr(
                bus,
                "V",
            ):
                raise ValueError(
                    f"Bus {bus_id} does not provide voltage "
                    "magnitude 'V'."
                )

            if not hasattr(
                bus,
                "theta",
            ):
                raise ValueError(
                    f"Bus {bus_id} does not provide voltage "
                    "angle 'theta'."
                )

            try:

                voltage_magnitude = float(
                    bus.V
                )

                voltage_angle = float(
                    bus.theta
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    f"Bus {bus_id} voltage state must be "
                    "numerical."
                ) from exc

            if not np.isfinite(
                voltage_magnitude
            ):

                raise ValueError(
                    f"Bus {bus_id} voltage magnitude is "
                    "not finite."
                )

            if not np.isfinite(
                voltage_angle
            ):

                raise ValueError(
                    f"Bus {bus_id} voltage angle is "
                    "not finite."
                )

            if voltage_magnitude < 0.0:

                raise ValueError(
                    f"Bus {bus_id} voltage magnitude "
                    "cannot be negative."
                )

            return (
                voltage_magnitude
                *
                cmath.exp(
                    1j
                    *
                    voltage_angle
                )
            )

        raise ValueError(
            f"Bus {bus_id} not found."
        )

    # =========================================================
    # COMPLEX VALUE VALIDATION
    # =========================================================

    @staticmethod
    def _validate_complex(
        value: Any,
        name: str,
    ) -> complex:
        """
        Convert and validate a complex electrical quantity.
        """

        try:

            result = complex(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                f"{name} must be a numerical complex value."
            ) from exc

        if not (
            np.isfinite(
                result.real
            )
            and
            np.isfinite(
                result.imag
            )
        ):

            raise ValueError(
                f"{name} must be finite."
            )

        return result

    # =========================================================
    # FAULT IMPEDANCE VALIDATION
    # =========================================================

    @staticmethod
    def _validate_fault_impedance(
        Z_fault: Any,
    ) -> complex:
        """
        Validate a fault impedance.

        A zero fault impedance is permitted by the general
        calculator because a bolted fault is a valid physical
        case.

        The caller must therefore handle zero total impedance
        explicitly when appropriate.
        """

        return FaultCalculator._validate_complex(
            Z_fault,
            "Fault impedance",
        )

    # =========================================================
    # FAULT CURRENT
    # =========================================================

    def calculate_current(
        self,
        V_prefault: Any,
        Z_fault: Any,
    ) -> complex:
        """
        Calculate fault current.

        Equation
        --------
            If = Vprefault / Zfault

        Parameters
        ----------
        V_prefault:
            Complex prefault voltage.

        Z_fault:
            Complex equivalent fault impedance.

        Returns
        -------
        complex
            Fault current.

        Raises
        ------
        ZeroDivisionError
            If the total fault impedance is zero.
        """

        V_prefault = self._validate_complex(
            V_prefault,
            "Prefault voltage",
        )

        Z_fault = self._validate_fault_impedance(
            Z_fault
        )

        if abs(
            Z_fault
        ) == 0.0:

            raise ZeroDivisionError(
                "Total fault impedance cannot be zero."
            )

        current = (
            V_prefault
            /
            Z_fault
        )

        return self._validate_complex(
            current,
            "Fault current",
        )

    # =========================================================
    # THREE-PHASE FAULT LEVEL
    # =========================================================

    @staticmethod
    def fault_mva(
        voltage_kv: Any,
        current_ka: Any,
    ) -> float:
        """
        Calculate three-phase fault level.

        Equation
        --------
            S_fault = sqrt(3) * V_kV * I_kA

        Parameters
        ----------
        voltage_kv:
            Line-to-line voltage in kV.

        current_ka:
            Three-phase fault current magnitude in kA.

        Returns
        -------
        float
            Fault level in MVA.
        """

        try:

            voltage_kv = float(
                voltage_kv
            )

            current_ka = float(
                current_ka
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "Voltage and current must be real numerical "
                "values."
            ) from exc

        if not np.isfinite(
            voltage_kv
        ):

            raise ValueError(
                "Voltage must be finite."
            )

        if not np.isfinite(
            current_ka
        ):

            raise ValueError(
                "Current must be finite."
            )

        if voltage_kv < 0.0:

            raise ValueError(
                "Voltage cannot be negative."
            )

        if current_ka < 0.0:

            raise ValueError(
                "Current cannot be negative."
            )

        return float(
            np.sqrt(3.0)
            *
            voltage_kv
            *
            current_ka
        )

    # =========================================================
    # RESULT FORMATTER
    # =========================================================

    def result(
        self,
        bus_id: Any,
        fault_type: Any,
        current: Any,
        impedance: Any,
        *,
        prefault_voltage: Any | None = None,
        fault_mva: float | None = None,
    ) -> dict:
        """
        Construct the common GridForge short-circuit result.

        Parameters
        ----------
        bus_id:
            Faulted bus identifier.

        fault_type:
            Fault classification. Normally a FaultType value or
            its canonical string representation.

        current:
            Complex fault current.

        impedance:
            Equivalent fault impedance.

        prefault_voltage:
            Optional complex prefault voltage.

        fault_mva:
            Optional fault level in MVA.

        Returns
        -------
        dict
            Standardized fault result.
        """

        current = self._validate_complex(
            current,
            "Fault current",
        )

        impedance = self._validate_complex(
            impedance,
            "Fault impedance",
        )

        result = {
            "bus": bus_id,
            "fault_type": fault_type,
            "fault_current": current,
            "fault_current_magnitude": float(
                abs(current)
            ),
            "fault_impedance": impedance,
        }

        if prefault_voltage is not None:

            prefault_voltage = self._validate_complex(
                prefault_voltage,
                "Prefault voltage",
            )

            result[
                "prefault_voltage"
            ] = prefault_voltage

        if fault_mva is not None:

            try:

                fault_mva = float(
                    fault_mva
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "fault_mva must be a real numerical value."
                ) from exc

            if not np.isfinite(
                fault_mva
            ):

                raise ValueError(
                    "fault_mva must be finite."
                )

            if fault_mva < 0.0:

                raise ValueError(
                    "fault_mva cannot be negative."
                )

            result[
                "fault_mva"
            ] = fault_mva

        return result

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(
        self,
    ) -> dict:
        """
        Return calculator diagnostics.
        """

        return {
            "component": "FaultCalculator",
            "version": "2.0",
            "status": "READY",
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
