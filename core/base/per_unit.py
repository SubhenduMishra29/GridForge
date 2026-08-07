# core/base/per_unit.py

"""
GridForge Per-Unit System (Industrial Grade)

Design Principles:
- Global base MVA
- Bus-level voltage bases
- Explicit conversions (no hidden magic)
- Vectorization-ready
- Compatible with Y-bus and solver layers
"""

import numpy as np


class PerUnitSystem:
    """
    Handles per-unit conversions for a multi-voltage power system.
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
        Z_base = (kV^2) / MVA
        Returns in ohms
        """
        return (kv ** 2) / self.base_mva

    def y_base(self, kv: float) -> float:
        """
        Y_base = 1 / Z_base
        """
        return 1.0 / self.z_base(kv)

    def i_base(self, kv: float) -> float:
        """
        I_base = MVA / (sqrt(3) * kV)
        Returns in kA
        """
        return self.base_mva / (np.sqrt(3) * kv)

    # ------------------------------------------------------------------
    # Impedance Conversions
    # ------------------------------------------------------------------

    def to_pu_impedance(self, z_ohm: complex, kv: float) -> complex:
        """
        Convert impedance in ohms → per unit
        """
        return z_ohm / self.z_base(kv)

    def from_pu_impedance(self, z_pu: complex, kv: float) -> complex:
        """
        Convert impedance per unit → ohms
        """
        return z_pu * self.z_base(kv)

    # ------------------------------------------------------------------
    # Admittance Conversions
    # ------------------------------------------------------------------

    def to_pu_admittance(self, y_siemens: complex, kv: float) -> complex:
        """
        Convert admittance in Siemens → per unit
        """
        return y_siemens / self.y_base(kv)

    def from_pu_admittance(self, y_pu: complex, kv: float) -> complex:
        """
        Convert per unit → Siemens
        """
        return y_pu * self.y_base(kv)

    # ------------------------------------------------------------------
    # Power Conversions
    # ------------------------------------------------------------------

    def to_pu_power(self, p_mw: float, q_mvar: float = 0.0) -> complex:
        """
        Convert MW + jMVAr → per unit complex power
        """
        return complex(p_mw, q_mvar) / self.base_mva

    def from_pu_power(self, s_pu: complex) -> tuple:
        """
        Convert per unit complex power → (MW, MVAr)
        """
        s = s_pu * self.base_mva
        return s.real, s.imag

    # ------------------------------------------------------------------
    # Voltage Conversions
    # ------------------------------------------------------------------

    def to_pu_voltage(self, kv_actual: float, kv_base: float) -> float:
        """
        Convert kV → per unit voltage
        """
        return kv_actual / kv_base

    def from_pu_voltage(self, v_pu: float, kv_base: float) -> float:
        """
        Convert per unit → kV
        """
        return v_pu * kv_base

    # ------------------------------------------------------------------
    # Current Conversions
    # ------------------------------------------------------------------

    def to_pu_current(self, i_ka: float, kv: float) -> float:
        """
        Convert kA → per unit current
        """
        return i_ka / self.i_base(kv)

    def from_pu_current(self, i_pu: float, kv: float) -> float:
        """
        Convert per unit → kA
        """
        return i_pu * self.i_base(kv)

    # ------------------------------------------------------------------
    # Transformer Base Conversion
    # ------------------------------------------------------------------

    def convert_impedance_base(
        self,
        z_pu: float,
        old_mva: float,
        old_kv: float,
        new_kv: float,
    ) -> float:
        """
        Convert impedance from one base to another.

        Zpu_new = Zpu_old * (MVA_new / MVA_old) * (KV_old / KV_new)^2
        """
        return z_pu * (self.base_mva / old_mva) * (old_kv / new_kv) ** 2

    # ------------------------------------------------------------------
    # Vectorized Utilities (for solver)
    # ------------------------------------------------------------------

    def z_base_vector(self, kv_array: np.ndarray) -> np.ndarray:
        return (kv_array ** 2) / self.base_mva

    def to_pu_impedance_vector(
        self, z_array: np.ndarray, kv_array: np.ndarray
    ) -> np.ndarray:
        return z_array / self.z_base_vector(kv_array)

    def to_pu_power_vector(self, s_array: np.ndarray) -> np.ndarray:
        return s_array / self.base_mva
