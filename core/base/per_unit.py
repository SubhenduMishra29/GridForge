# core/base/per_unit.py

"""
GridForge Per-Unit System
=========================

GridForge Base Layer v1.0

Provides the fundamental per-unit conversions used throughout GridForge.

Design principles:
- Global system MVA base
- Explicit voltage-base inputs
- No hidden conversions
- Scalar and vectorized utilities
- Compatible with network, Y-bus, solver, and analysis layers

Unit conventions:
- Power: MW / MVAr / MVA
- Voltage: kV
- Current: kA
- Impedance: ohms
- Admittance: Siemens
- Per-unit quantities are dimensionless
"""

import numpy as np


class PerUnitSystem:
    """
    Handles per-unit conversions for a multi-voltage power system.

    The system uses a common global MVA base while allowing the caller
    to specify the appropriate voltage base for each voltage level.
    """

    def __init__(self, base_mva: float):
        if base_mva <= 0:
            raise ValueError("Base MVA must be positive")

        self.base_mva = base_mva

    # ------------------------------------------------------------------
    # Base Calculations
    # ------------------------------------------------------------------

    def z_base(self, kv: float) -> float:
        """
        Calculate base impedance.

        Z_base = kV² / MVA

        Parameters
        ----------
        kv:
            Base line-to-line voltage in kV.

        Returns
        -------
        float
            Base impedance in ohms.
        """
        return (kv ** 2) / self.base_mva

    def y_base(self, kv: float) -> float:
        """
        Calculate base admittance.

        Y_base = 1 / Z_base

        Parameters
        ----------
        kv:
            Base line-to-line voltage in kV.

        Returns
        -------
        float
            Base admittance in Siemens.
        """
        return 1.0 / self.z_base(kv)

    def i_base(self, kv: float) -> float:
        """
        Calculate base current.

        I_base = MVA / (sqrt(3) × kV)

        Parameters
        ----------
        kv:
            Base line-to-line voltage in kV.

        Returns
        -------
        float
            Base current in kA.
        """
        return self.base_mva / (np.sqrt(3.0) * kv)

    # ------------------------------------------------------------------
    # Impedance Conversions
    # ------------------------------------------------------------------

    def to_pu_impedance(
        self,
        z_ohm: complex,
        kv: float,
    ) -> complex:
        """
        Convert impedance from ohms to per unit.
        """
        return z_ohm / self.z_base(kv)

    def from_pu_impedance(
        self,
        z_pu: complex,
        kv: float,
    ) -> complex:
        """
        Convert impedance from per unit to ohms.
        """
        return z_pu * self.z_base(kv)

    # ------------------------------------------------------------------
    # Admittance Conversions
    # ------------------------------------------------------------------

    def to_pu_admittance(
        self,
        y_siemens: complex,
        kv: float,
    ) -> complex:
        """
        Convert admittance from Siemens to per unit.
        """
        return y_siemens / self.y_base(kv)

    def from_pu_admittance(
        self,
        y_pu: complex,
        kv: float,
    ) -> complex:
        """
        Convert admittance from per unit to Siemens.
        """
        return y_pu * self.y_base(kv)

    # ------------------------------------------------------------------
    # Power Conversions
    # ------------------------------------------------------------------

    def to_pu_power(
        self,
        p_mw: float,
        q_mvar: float = 0.0,
    ) -> complex:
        """
        Convert MW + jMVAr to per-unit complex power.
        """
        return complex(p_mw, q_mvar) / self.base_mva

    def from_pu_power(
        self,
        s_pu: complex,
    ) -> tuple[float, float]:
        """
        Convert per-unit complex power to MW and MVAr.

        Returns
        -------
        tuple[float, float]
            (MW, MVAr)
        """
        s = s_pu * self.base_mva
        return s.real, s.imag

    # ------------------------------------------------------------------
    # Voltage Conversions
    # ------------------------------------------------------------------

    def to_pu_voltage(
        self,
        kv_actual: float,
        kv_base: float,
    ) -> float:
        """
        Convert actual voltage in kV to per unit.
        """
        return kv_actual / kv_base

    def from_pu_voltage(
        self,
        v_pu: float,
        kv_base: float,
    ) -> float:
        """
        Convert per-unit voltage to kV.
        """
        return v_pu * kv_base

    # ------------------------------------------------------------------
    # Current Conversions
    # ------------------------------------------------------------------

    def to_pu_current(
        self,
        i_ka: float,
        kv: float,
    ) -> float:
        """
        Convert current in kA to per unit.
        """
        return i_ka / self.i_base(kv)

    def from_pu_current(
        self,
        i_pu: float,
        kv: float,
    ) -> float:
        """
        Convert per-unit current to kA.
        """
        return i_pu * self.i_base(kv)

    # ------------------------------------------------------------------
    # Transformer / Impedance Base Conversion
    # ------------------------------------------------------------------

    def convert_impedance_base(
        self,
        z_pu: float,
        old_mva: float,
        old_kv: float,
        new_kv: float,
    ) -> float:
        """
        Convert per-unit impedance from an old base to the
        GridForge system MVA base and specified new voltage base.

        Zpu_new =
            Zpu_old
            × (MVA_new / MVA_old)
            × (kV_old / kV_new)²

        Parameters
        ----------
        z_pu:
            Impedance in per unit on the old base.

        old_mva:
            MVA base on which z_pu was originally specified.

        old_kv:
            Voltage base associated with the original impedance.

        new_kv:
            New voltage base.

        Returns
        -------
        float
            Impedance in per unit on the GridForge system base.
        """
        return (
            z_pu
            * (self.base_mva / old_mva)
            * (old_kv / new_kv) ** 2
        )

    # ------------------------------------------------------------------
    # Vectorized Utilities
    # ------------------------------------------------------------------

    def z_base_vector(
        self,
        kv_array: np.ndarray,
    ) -> np.ndarray:
        """
        Vectorized base impedance calculation.
        """
        return (kv_array ** 2) / self.base_mva

    def to_pu_impedance_vector(
        self,
        z_array: np.ndarray,
        kv_array: np.ndarray,
    ) -> np.ndarray:
        """
        Vectorized impedance conversion from ohms to per unit.
        """
        return z_array / self.z_base_vector(kv_array)

    def to_pu_power_vector(
        self,
        s_array: np.ndarray,
    ) -> np.ndarray:
        """
        Vectorized complex-power conversion to per unit.
        """
        return s_array / self.base_mva
