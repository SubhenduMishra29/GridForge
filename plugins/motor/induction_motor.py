```python
"""
GridForge Induction Motor Plugin
================================

Detailed induction-motor engineering model for GridForge.

Location
--------
    plugins/motor/induction_motor.py

Architecture
------------
This module is deliberately outside ``core/model``.

The plugin represents detailed induction-motor behavior associated
with a GridForge motor/electrical equipment object.

It does NOT:

    - own GridForge network topology
    - create or modify Terminals
    - register itself with a Network
    - build Y-bus
    - perform Newton-Raphson load flow
    - perform short-circuit studies
    - perform contingency analysis
    - perform global motor aggregation
    - manage GUI state
    - own a dynamic simulation state vector
    - perform time integration

Those responsibilities belong to the appropriate GridForge layers.

Engineering Scope
-----------------
The plugin provides a standard three-phase induction-motor
equivalent-circuit representation suitable for:

    - steady-state motor calculations
    - slip-dependent impedance
    - current calculation
    - power calculation
    - torque calculation
    - power factor calculation
    - starting-current estimation
    - torque-speed evaluation

The numerical solver may use these methods as part of a larger
network solution.

Per-unit convention
-------------------
Electrical quantities are represented in per-unit unless explicitly
specified otherwise.

Equivalent circuit
-------------------
The plugin uses the standard approximate per-phase induction-motor
equivalent circuit:

                    R1       X1
             ─────/\\/\\/─────jX1─────┐
                                     │
                                     ├────
                                     │
                         R2/s   jX2  │
                         ─/\\/\\/──jX2─┘
                                     │
                                     │
                                   neutral

The rotor branch is represented as:

    Z2(s) = R2 / s + j X2

where:

    s = slip

The approximate series equivalent is:

    Z_motor(s) =
        R1 + jX1 + R2/s + jX2

The plugin intentionally keeps the model explicit and transparent.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math


# =====================================================================
# INDUCTION MOTOR
# =====================================================================

class InductionMotor:
    """
    GridForge induction-motor engineering plugin.

    This class contains motor-specific engineering behavior only.

    Parameters
    ----------
    id : str
        Unique plugin/model identifier.

    rated_power_mva : float
        Motor apparent-power base in MVA.

    rated_voltage_kv : float
        Rated line-to-line voltage in kV.

    frequency_hz : float
        Electrical supply frequency in Hz.

    poles : int
        Number of motor poles.

    r1 : float
        Stator resistance in per-unit.

    x1 : float
        Stator leakage reactance in per-unit.

    r2 : float
        Rotor resistance referred to stator in per-unit.

    x2 : float
        Rotor leakage reactance referred to stator in per-unit.

    xm : float
        Magnetizing reactance in per-unit.

    core_loss_g : float, optional
        Core-loss conductance in per-unit.

    Notes
    -----
    This plugin does not contain a GridForge Terminal.

    The physical electrical connection belongs to the owning core
    equipment/model object and the network layer.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        id: str,
        rated_power_mva: float,
        rated_voltage_kv: float,
        frequency_hz: float,
        poles: int,
        r1: float,
        x1: float,
        r2: float,
        x2: float,
        xm: float,
        core_loss_g: float = 0.0,
    ) -> None:

        self.id = id

        self.rated_power_mva = float(rated_power_mva)
        self.rated_voltage_kv = float(rated_voltage_kv)
        self.frequency_hz = float(frequency_hz)

        self.poles = int(poles)

        self.r1 = float(r1)
        self.x1 = float(x1)

        self.r2 = float(r2)
        self.x2 = float(x2)

        self.xm = float(xm)
        self.core_loss_g = float(core_loss_g)

        self._validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate(self) -> None:
        """Validate induction-motor parameters."""

        finite_values = {
            "rated_power_mva": self.rated_power_mva,
            "rated_voltage_kv": self.rated_voltage_kv,
            "frequency_hz": self.frequency_hz,
            "r1": self.r1,
            "x1": self.x1,
            "r2": self.r2,
            "x2": self.x2,
            "xm": self.xm,
            "core_loss_g": self.core_loss_g,
        }

        for name, value in finite_values.items():
            if not math.isfinite(value):
                raise ValueError(
                    f"InductionMotor '{self.id}': "
                    f"{name} must be finite."
                )

        if self.rated_power_mva <= 0.0:
            raise ValueError(
                "Induction motor rated power must be greater than zero."
            )

        if self.rated_voltage_kv <= 0.0:
            raise ValueError(
                "Induction motor rated voltage must be greater than zero."
            )

        if self.frequency_hz <= 0.0:
            raise ValueError(
                "Induction motor frequency must be greater than zero."
            )

        if self.poles <= 0:
            raise ValueError(
                "Induction motor pole count must be greater than zero."
            )

        if self.poles % 2 != 0:
            raise ValueError(
                "Induction motor pole count must be even."
            )

        if self.r1 < 0.0:
            raise ValueError("Induction motor R1 cannot be negative.")

        if self.x1 < 0.0:
            raise ValueError("Induction motor X1 cannot be negative.")

        if self.r2 < 0.0:
            raise ValueError("Induction motor R2 cannot be negative.")

        if self.x2 < 0.0:
            raise ValueError("Induction motor X2 cannot be negative.")

        if self.xm <= 0.0:
            raise ValueError(
                "Induction motor magnetizing reactance "
                "must be greater than zero."
            )

        if self.core_loss_g < 0.0:
            raise ValueError(
                "Induction motor core-loss conductance "
                "cannot be negative."
            )

    # =================================================================
    # SYNCHRONOUS SPEED
    # =================================================================

    @property
    def synchronous_speed_rpm(self) -> float:
        """
        Return synchronous speed in revolutions per minute.

        Formula:

            Ns = 120 f / poles
        """

        return (
            120.0
            * self.frequency_hz
            / self.poles
        )

    @property
    def synchronous_speed_rad_s(self) -> float:
        """
        Return synchronous mechanical angular speed in rad/s.
        """

        return (
            2.0
            * math.pi
            * self.synchronous_speed_rpm
            / 60.0
        )

    # =================================================================
    # SLIP
    # =================================================================

    def slip_from_speed(
        self,
        speed_rpm: float,
    ) -> float:
        """
        Calculate slip from rotor speed.

        Formula:

            s = (Ns - N) / Ns

        Parameters
        ----------
        speed_rpm:
            Rotor speed in rpm.
        """

        speed_rpm = float(speed_rpm)

        if not math.isfinite(speed_rpm):
            raise ValueError(
                "Motor speed must be finite."
            )

        return (
            self.synchronous_speed_rpm - speed_rpm
        ) / self.synchronous_speed_rpm

    def speed_from_slip(
        self,
        slip: float,
    ) -> float:
        """
        Calculate rotor speed from slip.

        Formula:

            N = Ns (1 - s)
        """

        slip = self._validate_slip(slip)

        return (
            self.synchronous_speed_rpm
            * (1.0 - slip)
        )

    # =================================================================
    # SLIP VALIDATION
    # =================================================================

    @staticmethod
    def _validate_slip(slip: float) -> float:
        """
        Validate slip for normal induction-motor operation.

        Slip must satisfy:

            0 < s <= 1

        ``s = 1`` represents standstill/start.

        ``s <= 0`` would represent synchronous or generating
        operation and is outside this basic motor plugin model.
        """

        slip = float(slip)

        if not math.isfinite(slip):
            raise ValueError(
                "Motor slip must be finite."
            )

        if slip <= 0.0 or slip > 1.0:
            raise ValueError(
                "Motor slip must satisfy 0 < s <= 1."
            )

        return slip

    # =================================================================
    # EQUIVALENT CIRCUIT
    # =================================================================

    def rotor_impedance(
        self,
        slip: float,
    ) -> complex:
        """
        Return the slip-dependent rotor impedance.

        Formula:

            Z2 = R2/s + jX2
        """

        slip = self._validate_slip(slip)

        return complex(
            self.r2 / slip,
            self.x2,
        )

    def series_impedance(
        self,
        slip: float,
    ) -> complex:
        """
        Return the approximate motor series impedance.

        Formula:

            Zmotor =
                R1 + jX1 + R2/s + jX2
        """

        slip = self._validate_slip(slip)

        return complex(
            self.r1 + self.r2 / slip,
            self.x1 + self.x2,
        )

    def input_admittance(
        self,
        slip: float,
    ) -> complex:
        """
        Return approximate motor input admittance.

        This uses the series equivalent model.

            Y = 1 / Zmotor
        """

        z = self.series_impedance(slip)

        if abs(z) == 0.0:
            raise ZeroDivisionError(
                "Motor equivalent impedance is zero."
            )

        return 1.0 / z

    # =================================================================
    # CURRENT
    # =================================================================

    def current_pu(
        self,
        voltage_pu: float,
        slip: float,
    ) -> complex:
        """
        Calculate approximate motor current in per-unit.

        Parameters
        ----------
        voltage_pu:
            Applied positive-sequence voltage magnitude in per-unit.

        slip:
            Motor slip.
        """

        voltage_pu = float(voltage_pu)

        if not math.isfinite(voltage_pu):
            raise ValueError(
                "Motor voltage must be finite."
            )

        if voltage_pu < 0.0:
            raise ValueError(
                "Motor voltage cannot be negative."
            )

        return (
            complex(voltage_pu, 0.0)
            * self.input_admittance(slip)
        )

    # =================================================================
    # POWER
    # =================================================================

    def power_pu(
        self,
        voltage_pu: float,
        slip: float,
    ) -> tuple[float, float]:
        """
        Calculate approximate motor input power.

        Returns
        -------
        tuple
            ``(P, Q)`` in per-unit.

        P and Q are positive for motor consumption.
        """

        current = self.current_pu(
            voltage_pu,
            slip,
        )

        voltage = complex(
            float(voltage_pu),
            0.0,
        )

        apparent = (
            voltage
            * current.conjugate()
        )

        return (
            apparent.real,
            apparent.imag,
        )

    # =================================================================
    # POWER FACTOR
    # =================================================================

    def power_factor(
        self,
        voltage_pu: float,
        slip: float,
    ) -> float:
        """
        Return motor input power factor.

        Positive value indicates normal motor consumption.
        """

        p, q = self.power_pu(
            voltage_pu,
            slip,
        )

        s = math.hypot(p, q)

        if s == 0.0:
            return 1.0

        return abs(p) / s

    # =================================================================
    # TORQUE
    # =================================================================

    def torque_pu(
        self,
        voltage_pu: float,
        slip: float,
    ) -> float:
        """
        Calculate approximate electromagnetic torque in per-unit.

        The torque is derived from the air-gap power approximation:

            Pgap = I² R2/s

        and:

            Tpu = Pgap / (1 - s)

        relative to synchronous-speed power normalization.

        This method is intended for engineering evaluation and
        comparison, not as a replacement for a validated transient
        machine model.
        """

        slip = self._validate_slip(slip)

        current = self.current_pu(
            voltage_pu,
            slip,
        )

        current_squared = abs(current) ** 2

        air_gap_power = (
            current_squared
            * self.r2
            / slip
        )

        return air_gap_power / (
            1.0 - slip
        ) if slip < 1.0 else float("inf")

    # =================================================================
    # STARTING CONDITION
    # =================================================================

    def starting_current_pu(
        self,
        voltage_pu: float = 1.0,
    ) -> float:
        """
        Return approximate starting-current magnitude.

        Starting condition:

            s = 1
        """

        return abs(
            self.current_pu(
                voltage_pu,
                1.0,
            )
        )

    def starting_torque_pu(
        self,
        voltage_pu: float = 1.0,
    ) -> float:
        """
        Return approximate starting torque.

        Starting condition:

            s = 1

        A finite torque expression is used directly from the
        air-gap-power relationship.
        """

        current = self.current_pu(
            voltage_pu,
            1.0,
        )

        return (
            abs(current) ** 2
            * self.r2
        )

    # =================================================================
    # TORQUE-SPEED DATA
    # =================================================================

    def torque_speed_point(
        self,
        speed_rpm: float,
        voltage_pu: float = 1.0,
    ) -> dict:
        """
        Evaluate one point on the motor torque-speed curve.
        """

        slip = self.slip_from_speed(
            speed_rpm
        )

        if slip <= 0.0 or slip > 1.0:
            raise ValueError(
                "Speed must correspond to "
                "0 < slip <= 1."
            )

        current = self.current_pu(
            voltage_pu,
            slip,
        )

        p, q = self.power_pu(
            voltage_pu,
            slip,
        )

        torque = self.torque_pu(
            voltage_pu,
            slip,
        )

        return {
            "speed_rpm": speed_rpm,
            "slip": slip,
            "current_pu": abs(current),
            "P_pu": p,
            "Q_pu": q,
            "power_factor": self.power_factor(
                voltage_pu,
                slip,
            ),
            "torque_pu": torque,
        }

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured motor-plugin information.
        """

        return {
            "id": self.id,
            "type": "induction_motor",
            "rated_power_mva": self.rated_power_mva,
            "rated_voltage_kv": self.rated_voltage_kv,
            "frequency_hz": self.frequency_hz,
            "poles": self.poles,
            "synchronous_speed_rpm": (
                self.synchronous_speed_rpm
            ),
            "r1_pu": self.r1,
            "x1_pu": self.x1,
            "r2_pu": self.r2,
            "x2_pu": self.x2,
            "xm_pu": self.xm,
            "core_loss_g_pu": self.core_loss_g,
            "model": "approximate_series_equivalent",
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        return (
            f"<InductionMotor "
            f"id={self.id}, "
            f"rating={self.rated_power_mva:.3f} MVA, "
            f"voltage={self.rated_voltage_kv:.3f} kV, "
            f"poles={self.poles}, "
            f"frequency={self.frequency_hz:.2f} Hz>"
        )
```

