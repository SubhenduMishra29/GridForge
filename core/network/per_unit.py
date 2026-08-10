import math


class PerUnitSystem:
    """
    Industrial-grade per-unit system for multi-voltage networks.

    Assumptions:
    - Voltage in kV
    - Power in MVA
    - Impedance returned in ohms
    """

    def __init__(self, base_mva: float):
        if base_mva <= 0:
            raise ValueError("Base MVA must be positive")

        self.base_mva = base_mva
        self.voltage_bases = {}  # {bus_id: kV}

    # ---------------------------------------------------------
    # BASE DEFINITIONS
    # ---------------------------------------------------------

    def set_voltage_base(self, bus_id: str, kv: float):
        if kv <= 0:
            raise ValueError("Voltage base must be positive")

        if kv > 1000:
            raise ValueError("Voltage must be in kV, not volts")

        self.voltage_bases[bus_id] = kv

    def get_voltage_base(self, bus_id: str) -> float:
        if bus_id not in self.voltage_bases:
            raise KeyError(f"Voltage base not set for bus {bus_id}")
        return self.voltage_bases[bus_id]

    # ---------------------------------------------------------
    # BASE CALCULATIONS
    # ---------------------------------------------------------

    def base_impedance(self, kv: float) -> float:
        return (kv ** 2) / self.base_mva

    def base_current(self, kv: float) -> float:
        return self.base_mva / (math.sqrt(3) * kv)

    # ---------------------------------------------------------
    # IMPEDANCE CONVERSIONS
    # ---------------------------------------------------------

    def ohm_to_pu(self, z_ohm: complex, bus_id: str) -> complex:
        kv = self.get_voltage_base(bus_id)
        z_base = self.base_impedance(kv)
        return z_ohm / z_base

    def pu_to_ohm(self, z_pu: complex, bus_id: str) -> complex:
        kv = self.get_voltage_base(bus_id)
        z_base = self.base_impedance(kv)
        return z_pu * z_base

    def change_base(
        self,
        z_pu: complex,
        old_mva: float,
        old_kv: float,
        new_kv: float
    ) -> complex:

        if old_mva <= 0 or old_kv <= 0 or new_kv <= 0:
            raise ValueError("Invalid base values")

        return z_pu * (self.base_mva / old_mva) * ((old_kv / new_kv) ** 2)

    # ---------------------------------------------------------
    # POWER CONVERSIONS
    # ---------------------------------------------------------

    def mw_to_pu(self, mw: float) -> float:
        return mw / self.base_mva

    def pu_to_mw(self, pu: float) -> float:
        return pu * self.base_mva

    def mvar_to_pu(self, mvar: float) -> float:
        return mvar / self.base_mva

    def pu_to_mvar(self, pu: float) -> float:
        return pu * self.base_mva

    # ---------------------------------------------------------
    # CURRENT CONVERSIONS
    # ---------------------------------------------------------

    def amp_to_pu(self, amps: float, bus_id: str) -> float:
        kv = self.get_voltage_base(bus_id)
        return amps / self.base_current(kv)

    def pu_to_amp(self, pu: float, bus_id: str) -> float:
        kv = self.get_voltage_base(bus_id)
        return pu * self.base_current(kv)

    # ---------------------------------------------------------
    # ADMITTANCE
    # ---------------------------------------------------------

    def ohm_to_pu_admittance(self, z_ohm: complex, bus_id: str) -> complex:
        z_pu = self.ohm_to_pu(z_ohm, bus_id)
        if abs(z_pu) < 1e-12:
            raise ZeroDivisionError("Zero impedance")
        return 1 / z_pu

    def siemens_to_pu(self, y_siemens: complex, bus_id: str) -> complex:
        kv = self.get_voltage_base(bus_id)
        z_base = self.base_impedance(kv)
        return y_siemens * z_base

    # ---------------------------------------------------------
    # DEBUG
    # ---------------------------------------------------------

    def summary(self):
        return {
            "base_mva": self.base_mva,
            "voltage_bases": self.voltage_bases
        }
