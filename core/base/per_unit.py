"""
GridForge Per-Unit System
=========================

GridForge Base Layer V1.0

Provides the fundamental per-unit conversions used throughout
GridForge.

Architecture
------------

    core/base/
        Fundamental reusable engineering utilities

    core/model/
        Canonical electrical entities

    core/network/
        Assembled network and topology services

    core/solver/
        Numerical algorithms

    core/analysis/
        Engineering study orchestration

The per-unit system belongs to the Base Layer because it is a
fundamental engineering utility shared by multiple layers.

Design Principles
-----------------

- One explicit global system MVA base.
- Explicit voltage-base inputs.
- No hidden voltage-base assumptions.
- No network/model ownership.
- No topology knowledge.
- No solver dependency.
- Scalar conversion utilities.
- Vectorized utilities where useful.
- Suitable for multi-voltage electrical networks.

Unit Conventions
----------------

Physical quantities:

    Power       : MW / MVAr / MVA
    Voltage     : kV
    Current     : kA
    Impedance   : ohms
    Admittance  : Siemens

Per-unit quantities are dimensionless.

Base Equations
--------------

For a three-phase system using line-to-line voltage:

    Z_base = kV_base² / MVA_base

    Y_base = 1 / Z_base

    I_base = MVA_base / (sqrt(3) × kV_base)

Power:

    S_pu = S_actual / MVA_base

Voltage:

    V_pu = V_actual / V_base

Impedance:

    Z_pu = Z_actual / Z_base

Admittance:

    Y_pu = Y_actual / Y_base

Base Conversion
---------------

For an impedance specified on an original base:

    Zpu_new =
        Zpu_old
        × (MVA_new / MVA_old)
        × (kV_old / kV_new)²

The GridForge global system MVA base is used as MVA_new.

Responsibilities
----------------

This module:

- Stores the system MVA base.
- Calculates electrical base quantities.
- Converts scalar physical quantities to per-unit.
- Converts scalar per-unit quantities to physical units.
- Provides selected vectorized conversions.
- Supports impedance-base conversion.

This module does NOT:

- Store network state.
- Know buses or branches.
- Build Y-bus.
- Perform topology analysis.
- Perform load-flow calculations.
- Perform short-circuit calculations.
- Perform engineering validation of equipment.
- Modify model objects.
- Manage GUI state.

GridForge V2 Status
-------------------

This module is the canonical per-unit utility for GridForge.

Network-layer code must import ``PerUnitSystem`` from:

    core.base.per_unit

The former ``core.network.per_unit`` implementation is therefore
not part of the active architecture.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np


# =====================================================================
# PER-UNIT SYSTEM
# =====================================================================

class PerUnitSystem:
    """
    Fundamental per-unit conversion service for GridForge.

    Parameters
    ----------
    base_mva : float
        Global system apparent-power base in MVA.

    Notes
    -----
    Voltage bases are supplied explicitly to conversion methods.
    This is intentional: GridForge supports multi-voltage networks
    and therefore must not infer a single system-wide voltage base.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(self, base_mva: float) -> None:
        """
        Initialize the per-unit system.
        """

        base_mva = float(base_mva)

        if not math.isfinite(base_mva):
            raise ValueError(
                "Base MVA must be finite."
            )

        if base_mva <= 0.0:
            raise ValueError(
                "Base MVA must be positive."
            )

        self.base_mva = base_mva

    # =================================================================
    # INTERNAL VALIDATION
    # =================================================================

    @staticmethod
    def _validate_voltage_base(kv: float) -> float:
        """
        Validate and normalize a voltage-base value.
        """

        kv = float(kv)

        if not math.isfinite(kv):
            raise ValueError(
                "Voltage base must be finite."
            )

        if kv <= 0.0:
            raise ValueError(
                "Voltage base must be positive."
            )

        return kv

    @staticmethod
    def _validate_mva_base(mva: float, name: str = "MVA base") -> float:
        """
        Validate and normalize an MVA base.
        """

        mva = float(mva)

        if not math.isfinite(mva):
            raise ValueError(
                f"{name} must be finite."
            )

        if mva <= 0.0:
            raise ValueError(
                f"{name} must be positive."
            )

        return mva

    # =================================================================
    # BASE CALCULATIONS
    # =================================================================

    def z_base(self, kv: float) -> float:
        """
        Calculate base impedance.

        Formula
        -------
        Z_base = kV_base² / MVA_base

        Parameters
        ----------
        kv : float
            Base line-to-line voltage in kV.

        Returns
        -------
        float
            Base impedance in ohms.
        """

        kv = self._validate_voltage_base(kv)

        return (kv ** 2) / self.base_mva

    # -----------------------------------------------------------------

    def y_base(self, kv: float) -> float:
        """
        Calculate base admittance.

        Formula
        -------
        Y_base = 1 / Z_base

        Parameters
        ----------
        kv : float
            Base line-to-line voltage in kV.

        Returns
        -------
        float
            Base admittance in Siemens.
        """

        return 1.0 / self.z_base(kv)

    # -----------------------------------------------------------------

    def i_base(self, kv: float) -> float:
        """
        Calculate three-phase base current.

        Formula
        -------
        I_base = MVA_base / (sqrt(3) × kV_base)

        Parameters
        ----------
        kv : float
            Base line-to-line voltage in kV.

        Returns
        -------
        float
            Base current in kA.
        """

        kv = self._validate_voltage_base(kv)

        return self.base_mva / (
            math.sqrt(3.0) * kv
        )

    # =================================================================
    # IMPEDANCE CONVERSIONS
    # =================================================================

    def to_pu_impedance(
        self,
        z_ohm: complex,
        kv: float,
    ) -> complex:
        """
        Convert impedance from ohms to per unit.

        Parameters
        ----------
        z_ohm : complex
            Physical impedance in ohms.

        kv : float
            Voltage base in kV.

        Returns
        -------
        complex
            Per-unit impedance.
        """

        return z_ohm / self.z_base(kv)

    # -----------------------------------------------------------------

    def from_pu_impedance(
        self,
        z_pu: complex,
        kv: float,
    ) -> complex:
        """
        Convert impedance from per unit to ohms.

        Parameters
        ----------
        z_pu : complex
            Per-unit impedance.

        kv : float
            Voltage base in kV.

        Returns
        -------
        complex
            Physical impedance in ohms.
        """

        return z_pu * self.z_base(kv)

    # =================================================================
    # ADMITTANCE CONVERSIONS
    # =================================================================

    def to_pu_admittance(
        self,
        y_siemens: complex,
        kv: float,
    ) -> complex:
        """
        Convert admittance from Siemens to per unit.

        Parameters
        ----------
        y_siemens : complex
            Physical admittance in Siemens.

        kv : float
            Voltage base in kV.

        Returns
        -------
        complex
            Per-unit admittance.
        """

        return y_siemens / self.y_base(kv)

    # -----------------------------------------------------------------

    def from_pu_admittance(
        self,
        y_pu: complex,
        kv: float,
    ) -> complex:
        """
        Convert admittance from per unit to Siemens.

        Parameters
        ----------
        y_pu : complex
            Per-unit admittance.

        kv : float
            Voltage base in kV.

        Returns
        -------
        complex
            Physical admittance in Siemens.
        """

        return y_pu * self.y_base(kv)

    # =================================================================
    # POWER CONVERSIONS
    # =================================================================

    def to_pu_power(
        self,
        p_mw: float,
        q_mvar: float = 0.0,
    ) -> complex:
        """
        Convert MW + jMVAr to per-unit complex power.

        Parameters
        ----------
        p_mw : float
            Active power in MW.

        q_mvar : float, optional
            Reactive power in MVAr.

        Returns
        -------
        complex
            Complex power in per unit.
        """

        return complex(
            float(p_mw),
            float(q_mvar),
        ) / self.base_mva

    # -----------------------------------------------------------------

    def from_pu_power(
        self,
        s_pu: complex,
    ) -> Tuple[float, float]:
        """
        Convert per-unit complex power to MW and MVAr.

        Parameters
        ----------
        s_pu : complex
            Complex power in per unit.

        Returns
        -------
        tuple[float, float]
            ``(MW, MVAr)``.
        """

        s = s_pu * self.base_mva

        return (
            float(s.real),
            float(s.imag),
        )

    # =================================================================
    # VOLTAGE CONVERSIONS
    # =================================================================

    def to_pu_voltage(
        self,
        kv_actual: float,
        kv_base: float,
    ) -> float:
        """
        Convert actual voltage in kV to per unit.

        Parameters
        ----------
        kv_actual : float
            Actual line-to-line voltage in kV.

        kv_base : float
            Voltage base in kV.

        Returns
        -------
        float
            Voltage in per unit.
        """

        kv_base = self._validate_voltage_base(kv_base)

        return float(kv_actual) / kv_base

    # -----------------------------------------------------------------

    def from_pu_voltage(
        self,
        v_pu: float,
        kv_base: float,
    ) -> float:
        """
        Convert per-unit voltage to kV.

        Parameters
        ----------
        v_pu : float
            Voltage magnitude in per unit.

        kv_base : float
            Voltage base in kV.

        Returns
        -------
        float
            Actual voltage in kV.
        """

        kv_base = self._validate_voltage_base(kv_base)

        return float(v_pu) * kv_base

    # =================================================================
    # CURRENT CONVERSIONS
    # =================================================================

    def to_pu_current(
        self,
        i_ka: float,
        kv: float,
    ) -> float:
        """
        Convert current in kA to per unit.

        Parameters
        ----------
        i_ka : float
            Physical current in kA.

        kv : float
            Voltage base in kV.

        Returns
        -------
        float
            Current in per unit.
        """

        return float(i_ka) / self.i_base(kv)

    # -----------------------------------------------------------------

    def from_pu_current(
        self,
        i_pu: float,
        kv: float,
    ) -> float:
        """
        Convert per-unit current to kA.

        Parameters
        ----------
        i_pu : float
            Current in per unit.

        kv : float
            Voltage base in kV.

        Returns
        -------
        float
            Physical current in kA.
        """

        return float(i_pu) * self.i_base(kv)

    # =================================================================
    # IMPEDANCE BASE CONVERSION
    # =================================================================

    def convert_impedance_base(
        self,
        z_pu: complex,
        old_mva: float,
        old_kv: float,
        new_kv: float,
    ) -> complex:
        """
        Convert per-unit impedance from an old base to the
        GridForge system MVA base and a specified new voltage base.

        Formula
        -------
        Zpu_new =
            Zpu_old
            × (MVA_new / MVA_old)
            × (kV_old / kV_new)²

        Parameters
        ----------
        z_pu : complex
            Impedance in per unit on the original base.

        old_mva : float
            Original MVA base.

        old_kv : float
            Original voltage base in kV.

        new_kv : float
            New voltage base in kV.

        Returns
        -------
        complex
            Impedance in per unit on the GridForge system base.

        Notes
        -----
        The method changes the reference base only. It does not
        alter the physical impedance represented by the quantity.
        """

        old_mva = self._validate_mva_base(
            old_mva,
            "Old MVA base",
        )

        old_kv = self._validate_voltage_base(old_kv)
        new_kv = self._validate_voltage_base(new_kv)

        return (
            z_pu
            * (self.base_mva / old_mva)
            * (old_kv / new_kv) ** 2
        )

    # =================================================================
    # VECTORIZED BASE CALCULATIONS
    # =================================================================

    def z_base_vector(
        self,
        kv_array: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate base impedance for an array of voltage bases.

        Parameters
        ----------
        kv_array : numpy.ndarray
            Voltage-base values in kV.

        Returns
        -------
        numpy.ndarray
            Base impedances in ohms.
        """

        kv_array = np.asarray(
            kv_array,
            dtype=float,
        )

        if np.any(~np.isfinite(kv_array)):
            raise ValueError(
                "Voltage-base array contains non-finite values."
            )

        if np.any(kv_array <= 0.0):
            raise ValueError(
                "Voltage-base array must contain only "
                "positive values."
            )

        return (
            kv_array ** 2
        ) / self.base_mva

    # -----------------------------------------------------------------

    def to_pu_impedance_vector(
        self,
        z_array: np.ndarray,
        kv_array: np.ndarray,
    ) -> np.ndarray:
        """
        Vectorized conversion of impedance from ohms to per unit.

        Parameters
        ----------
        z_array : numpy.ndarray
            Physical impedances in ohms.

        kv_array : numpy.ndarray
            Corresponding voltage bases in kV.

        Returns
        -------
        numpy.ndarray
            Per-unit impedances.
        """

        z_array = np.asarray(
            z_array,
            dtype=complex,
        )

        kv_array = np.asarray(
            kv_array,
            dtype=float,
        )

        if z_array.shape != kv_array.shape:
            raise ValueError(
                "z_array and kv_array must have identical shapes."
            )

        return (
            z_array
            / self.z_base_vector(kv_array)
        )

    # -----------------------------------------------------------------

    def to_pu_power_vector(
        self,
        s_array: np.ndarray,
    ) -> np.ndarray:
        """
        Vectorized conversion of complex power to per unit.

        Parameters
        ----------
        s_array : numpy.ndarray
            Complex powers in MVA, represented as
            ``MW + jMVAr``.

        Returns
        -------
        numpy.ndarray
            Complex powers in per unit.
        """

        s_array = np.asarray(
            s_array,
            dtype=complex,
        )

        return s_array / self.base_mva

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<PerUnitSystem "
            f"base_mva={self.base_mva:.6f}>"
        )
