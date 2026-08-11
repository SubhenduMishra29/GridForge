```python
"""
GridForge Synchronous Machine Model
===================================

File:
    core/model/synchronous_machine.py

Defines the synchronous-machine dynamic model used by the
GridForge transient-stability / dynamic simulation framework.

Purpose
-------
The SynchronousMachine represents the electrical and mechanical
dynamics of a synchronous generator.

The present implementation uses a fourth-order transient
synchronous-machine model with the following dynamic states:

    delta
        Rotor electrical angle.

    omega
        Rotor speed deviation.

    Eq_prime
        q-axis transient internal EMF.

    Ed_prime
        d-axis transient internal EMF.

The model is intended to interface with:

    - Generator
    - Governor
    - AVR
    - PSS
    - Network algebraic equations
    - Dynamic / DAE solver

Architecture
------------
The SynchronousMachine does NOT perform numerical integration.

The dynamic / DAE solver owns:

    - Dynamic state vector
    - State integration
    - Time stepping
    - Initial conditions
    - Algebraic network solution
    - Differential-algebraic solution

The machine model provides:

    - Differential equations
    - Electrical power calculations
    - Electrical torque calculations
    - Internal EMF calculations
    - Initial-state calculation
    - Parameter validation
    - Diagnostic information

Electrical Sign Convention
---------------------------
Generator-side electrical power is positive when power is
delivered from the synchronous machine into the electrical
network.

Mechanical input power is positive when supplied by the turbine
or prime mover to the synchronous machine.

The swing equation is represented as:

    d(delta)/dt = omega_b * omega

    d(omega)/dt =
        (Pm - Pe - D * omega) / (2H)

where:

    H
        Inertia constant in seconds.

    D
        Damping coefficient.

    omega_b
        Electrical base angular frequency.

    Pm
        Mechanical input power.

    Pe
        Electrical air-gap/electrical output power.

Rotor Electrical Equations
---------------------------
The transient EMF equations are represented as:

    dEq'/dt =
        [Efd - Eq' - (Xd - Xd') * Id] / Tdo'

    dEd'/dt =
        [-Ed' + (Xq - Xq') * Iq] / Tqo'

The exact current and sign convention must remain consistent
between this model and the network/interface transformation used
by the dynamic solver.

Power-angle transformation
--------------------------
The stator currents are represented in the rotor reference frame.

For a network terminal voltage represented by:

    V = Vd + jVq

the dq components are obtained using the rotor angle.

The machine terminal power is calculated from the dq quantities.

This class does NOT solve the terminal algebraic equations.
The dynamic solver/network solver supplies the terminal voltage
and obtains the corresponding machine current.

Future Extensions
-----------------
The model can later support:

    - Classical second-order machine
    - Fifth / sixth-order models
    - Subtransient EMF states
    - Salient-pole machines
    - Round-rotor machines
    - Saturation
    - Damper windings
    - Frequency-dependent parameters
    - Negative-sequence models
    - Zero-sequence models
    - Detailed stator algebraic equations
    - IEEE machine models

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math


class SynchronousMachine:
    """
    Fourth-order transient synchronous-machine model.

    The machine does not integrate its dynamic states.

    The dynamic solver supplies the current state and network
    quantities and integrates the derivatives returned by this
    model.

    Parameters
    ----------
    id:
        Unique machine identifier.

    rated_mva:
        Machine rated apparent power in MVA.

    H:
        Inertia constant in seconds.

    D:
        Damping coefficient.

    xd:
        d-axis synchronous reactance.

    xq:
        q-axis synchronous reactance.

    xd_prime:
        d-axis transient reactance.

    xq_prime:
        q-axis transient reactance.

    Tdo_prime:
        d-axis open-circuit transient time constant.

    Tqo_prime:
        q-axis open-circuit transient time constant.

    frequency_hz:
        Electrical system base frequency.

    name:
        Human-readable machine name.

    Notes
    -----
    All electrical quantities are represented in per-unit unless
    explicitly stated otherwise.

    The dynamic state is intentionally NOT stored as an
    authoritative state inside this model.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        id: str,
        rated_mva: float = 100.0,
        H: float = 3.5,
        D: float = 0.0,
        xd: float = 1.80,
        xq: float = 1.70,
        xd_prime: float = 0.30,
        xq_prime: float = 0.55,
        Tdo_prime: float = 8.0,
        Tqo_prime: float = 0.4,
        frequency_hz: float = 50.0,
        name: str = "",
    ) -> None:
        """
        Initialize the synchronous-machine model.
        """

        self.id = str(id)

        self.name = str(name)

        # -----------------------------------------------------
        # Machine rating
        # -----------------------------------------------------

        self.rated_mva = float(rated_mva)

        # -----------------------------------------------------
        # Mechanical parameters
        # -----------------------------------------------------

        self.H = float(H)

        self.D = float(D)

        # -----------------------------------------------------
        # Synchronous reactances
        # -----------------------------------------------------

        self.xd = float(xd)

        self.xq = float(xq)

        # -----------------------------------------------------
        # Transient reactances
        # -----------------------------------------------------

        self.xd_prime = float(xd_prime)

        self.xq_prime = float(xq_prime)

        # -----------------------------------------------------
        # Transient time constants
        # -----------------------------------------------------

        self.Tdo_prime = float(Tdo_prime)

        self.Tqo_prime = float(Tqo_prime)

        # -----------------------------------------------------
        # System frequency
        # -----------------------------------------------------

        self.frequency_hz = float(frequency_hz)

        # -----------------------------------------------------
        # Operational state
        # -----------------------------------------------------

        self.in_service = True

        self._validate()

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate(self) -> None:
        """
        Validate synchronous-machine parameters.
        """

        if self.rated_mva <= 0.0:
            raise ValueError(
                "Machine rated MVA must be greater than zero."
            )

        if self.H <= 0.0:
            raise ValueError(
                "Machine inertia constant H "
                "must be greater than zero."
            )

        if self.D < 0.0:
            raise ValueError(
                "Machine damping coefficient D "
                "must be greater than or equal to zero."
            )

        if self.xd <= 0.0:
            raise ValueError(
                "d-axis synchronous reactance xd "
                "must be greater than zero."
            )

        if self.xq <= 0.0:
            raise ValueError(
                "q-axis synchronous reactance xq "
                "must be greater than zero."
            )

        if self.xd_prime <= 0.0:
            raise ValueError(
                "d-axis transient reactance xd_prime "
                "must be greater than zero."
            )

        if self.xq_prime <= 0.0:
            raise ValueError(
                "q-axis transient reactance xq_prime "
                "must be greater than zero."
            )

        if self.xd_prime > self.xd:
            raise ValueError(
                "xd_prime cannot exceed xd."
            )

        if self.xq_prime > self.xq:
            raise ValueError(
                "xq_prime cannot exceed xq."
            )

        if self.Tdo_prime <= 0.0:
            raise ValueError(
                "Tdo_prime must be greater than zero."
            )

        if self.Tqo_prime <= 0.0:
            raise ValueError(
                "Tqo_prime must be greater than zero."
            )

        if self.frequency_hz <= 0.0:
            raise ValueError(
                "frequency_hz must be greater than zero."
            )

    # =========================================================
    # BASE FREQUENCY
    # =========================================================

    @property
    def omega_base(self) -> float:
        """
        Return electrical base angular frequency.

        omega_b = 2 * pi * f
        """

        return (
            2.0
            * math.pi
            * self.frequency_hz
        )

    # =========================================================
    # ROTOR REFERENCE TRANSFORMATION
    # =========================================================

    @staticmethod
    def terminal_voltage_dq(
        Vt: float,
        angle: float,
    ) -> tuple[float, float]:
        """
        Convert terminal-voltage magnitude and rotor angle
        into rotor-frame d/q components.

        Parameters
        ----------
        Vt:
            Terminal-voltage magnitude in per-unit.

        angle:
            Rotor electrical angle in radians.

        Returns
        -------
        tuple
            (Vd, Vq)

        Notes
        -----
        The convention used here is:

            Vd = Vt * sin(delta)

            Vq = Vt * cos(delta)

        The dynamic solver must use the same convention when
        transforming currents between network and rotor frames.
        """

        Vt = float(Vt)
        angle = float(angle)

        Vd = (
            Vt
            * math.sin(angle)
        )

        Vq = (
            Vt
            * math.cos(angle)
        )

        return Vd, Vq

    # =========================================================
    # CURRENT FROM TRANSIENT EMF
    # =========================================================

    def currents_from_terminal_voltage(
        self,
        Eq_prime: float,
        Ed_prime: float,
        Vd: float,
        Vq: float,
    ) -> tuple[float, float]:
        """
        Calculate d/q stator currents from transient internal EMF
        and terminal voltage.

        The transient voltage relations are represented as:

            Vd = Ed' + Xq' * Iq

            Vq = Eq' - Xd' * Id

        Therefore:

            Id = (Eq' - Vq) / Xd'

            Iq = (Vd - Ed') / Xq'

        Returns
        -------
        tuple
            (Id, Iq)
        """

        Eq_prime = float(Eq_prime)
        Ed_prime = float(Ed_prime)
        Vd = float(Vd)
        Vq = float(Vq)

        Id = (
            Eq_prime
            - Vq
        ) / self.xd_prime

        Iq = (
            Vd
            - Ed_prime
        ) / self.xq_prime

        return Id, Iq

    # =========================================================
    # ELECTRICAL POWER
    # =========================================================

    @staticmethod
    def electrical_power(
        Vd: float,
        Vq: float,
        Id: float,
        Iq: float,
    ) -> float:
        """
        Calculate three-phase electrical power in per-unit.

        Equation:

            Pe = Vd * Id + Vq * Iq

        Returns
        -------
        float
            Electrical active-power output in per-unit.
        """

        return (
            float(Vd) * float(Id)
            +
            float(Vq) * float(Iq)
        )

    # =========================================================
    # REACTIVE POWER
    # =========================================================

    @staticmethod
    def reactive_power(
        Vd: float,
        Vq: float,
        Id: float,
        Iq: float,
    ) -> float:
        """
        Calculate reactive power in per-unit.

        Equation:

            Q = Vq * Id - Vd * Iq

        The sign convention follows the dq convention used by
        this machine model.
        """

        return (
            float(Vq) * float(Id)
            -
            float(Vd) * float(Iq)
        )

    # =========================================================
    # ELECTRICAL TORQUE
    # =========================================================

    @staticmethod
    def electrical_torque(
        Pe: float,
        omega: float = 0.0,
    ) -> float:
        """
        Return electrical torque approximation.

        For the normalized per-unit dynamic representation,
        electrical torque is normally represented by electrical
        power divided by per-unit rotor speed.

        At nominal speed (omega = 0), the per-unit rotor speed is
        one.

        Therefore:

            Te = Pe / (1 + omega)

        Parameters
        ----------
        Pe:
            Electrical power in per-unit.

        omega:
            Rotor speed deviation in per-unit.
        """

        rotor_speed = 1.0 + float(omega)

        if rotor_speed <= 0.0:
            raise ValueError(
                "Rotor speed must remain greater than zero."
            )

        return (
            float(Pe)
            / rotor_speed
        )

    # =========================================================
    # SWING EQUATION
    # =========================================================

    def rotor_derivative(
        self,
        omega: float,
        Pm: float,
        Pe: float,
    ) -> tuple[float, float]:
        """
        Calculate rotor-angle and rotor-speed derivatives.

        Equations:

            d(delta)/dt = omega_b * omega

            d(omega)/dt =
                (Pm - Pe - D*omega) / (2H)

        Parameters
        ----------
        omega:
            Rotor speed deviation in per-unit.

        Pm:
            Mechanical input power in per-unit.

        Pe:
            Electrical power output in per-unit.

        Returns
        -------
        tuple
            (d_delta_dt, d_omega_dt)
        """

        omega = float(omega)
        Pm = float(Pm)
        Pe = float(Pe)

        d_delta_dt = (
            self.omega_base
            * omega
        )

        d_omega_dt = (
            Pm
            - Pe
            - self.D * omega
        ) / (
            2.0 * self.H
        )

        return (
            d_delta_dt,
            d_omega_dt,
        )

    # =========================================================
    # TRANSIENT EMF EQUATIONS
    # =========================================================

    def emf_derivative(
        self,
        Eq_prime: float,
        Ed_prime: float,
        Id: float,
        Iq: float,
        Efd: float,
    ) -> tuple[float, float]:
        """
        Calculate transient EMF derivatives.

        Equations:

            dEq'/dt =
                [Efd - Eq' - (xd - xd') * Id] / Tdo'

            dEd'/dt =
                [-Ed' + (xq - xq') * Iq] / Tqo'

        Parameters
        ----------
        Eq_prime:
            q-axis transient EMF.

        Ed_prime:
            d-axis transient EMF.

        Id:
            d-axis stator current.

        Iq:
            q-axis stator current.

        Efd:
            Field excitation voltage supplied by the AVR.

        Returns
        -------
        tuple
            (dEq_prime_dt, dEd_prime_dt)
        """

        Eq_prime = float(Eq_prime)
        Ed_prime = float(Ed_prime)
        Id = float(Id)
        Iq = float(Iq)
        Efd = float(Efd)

        dEq_prime_dt = (
            Efd
            - Eq_prime
            - (
                self.xd
                - self.xd_prime
            ) * Id
        ) / self.Tdo_prime

        dEd_prime_dt = (
            -Ed_prime
            + (
                self.xq
                - self.xq_prime
            ) * Iq
        ) / self.Tqo_prime

        return (
            dEq_prime_dt,
            dEd_prime_dt,
        )

    # =========================================================
    # COMPLETE DYNAMIC EVALUATION
    # =========================================================

    def evaluate(
        self,
        delta: float,
        omega: float,
        Eq_prime: float,
        Ed_prime: float,
        Vt: float,
        Pm: float,
        Efd: float,
    ) -> dict:
        """
        Evaluate the complete fourth-order machine equations.

        Parameters
        ----------
        delta:
            Rotor electrical angle in radians.

        omega:
            Rotor speed deviation in per-unit.

        Eq_prime:
            q-axis transient EMF.

        Ed_prime:
            d-axis transient EMF.

        Vt:
            Terminal-voltage magnitude in per-unit.

        Pm:
            Mechanical input power in per-unit.

        Efd:
            Field excitation voltage.

        Returns
        -------
        dict
            Machine derivatives and calculated electrical
            quantities.

        Notes
        -----
        No numerical integration is performed.
        """

        Vd, Vq = self.terminal_voltage_dq(
            Vt=Vt,
            angle=delta,
        )

        Id, Iq = self.currents_from_terminal_voltage(
            Eq_prime=Eq_prime,
            Ed_prime=Ed_prime,
            Vd=Vd,
            Vq=Vq,
        )

        Pe = self.electrical_power(
            Vd=Vd,
            Vq=Vq,
            Id=Id,
            Iq=Iq,
        )

        Qe = self.reactive_power(
            Vd=Vd,
            Vq=Vq,
            Id=Id,
            Iq=Iq,
        )

        d_delta_dt, d_omega_dt = self.rotor_derivative(
            omega=omega,
            Pm=Pm,
            Pe=Pe,
        )

        dEq_prime_dt, dEd_prime_dt = self.emf_derivative(
            Eq_prime=Eq_prime,
            Ed_prime=Ed_prime,
            Id=Id,
            Iq=Iq,
            Efd=Efd,
        )

        return {
            "d_delta_dt": d_delta_dt,
            "d_omega_dt": d_omega_dt,
            "dEq_prime_dt": dEq_prime_dt,
            "dEd_prime_dt": dEd_prime_dt,
            "Vd": Vd,
            "Vq": Vq,
            "Id": Id,
            "Iq": Iq,
            "Pe": Pe,
            "Qe": Qe,
        }

    # =========================================================
    # INITIAL STATE
    # =========================================================

    def initial_state(
        self,
        delta: float = 0.0,
        omega: float = 0.0,
        Pm: float = 1.0,
        Vt: float = 1.0,
        Efd: float = 1.0,
    ) -> tuple[float, float, float, float]:
        """
        Estimate an initial fourth-order machine state.

        The initial rotor angle and speed deviation are supplied
        directly.

        The transient EMFs are estimated from the specified
        mechanical power, terminal voltage, and excitation.

        This method provides a practical initialization state for
        the dynamic solver. It does not solve a complete nonlinear
        machine/network initialization problem.

        Returns
        -------
        tuple
            (delta, omega, Eq_prime, Ed_prime)
        """

        delta = float(delta)
        omega = float(omega)
        Pm = float(Pm)
        Vt = float(Vt)
        Efd = float(Efd)

        if Vt <= 0.0:
            raise ValueError(
                "Initial terminal voltage Vt "
                "must be greater than zero."
            )

        Vd, Vq = self.terminal_voltage_dq(
            Vt=Vt,
            angle=delta,
        )

        # -----------------------------------------------------
        # Approximate initial current.
        #
        # For initialization, assume electrical power is equal
        # to mechanical input and reactive power is initially
        # zero.
        # -----------------------------------------------------

        Pe = Pm

        S = complex(
            Pe,
            0.0,
        )

        V = complex(
            Vq,
            Vd,
        )

        if abs(V) <= 0.0:
            raise ValueError(
                "Initial terminal voltage cannot be zero."
            )

        I_complex = (
            S.conjugate()
            / V.conjugate()
        )

        Id = I_complex.imag

        Iq = I_complex.real

        # -----------------------------------------------------
        # Estimate transient EMFs from terminal voltage/current.
        # -----------------------------------------------------

        Eq_prime = (
            Vq
            + self.xd_prime * Id
        )

        Ed_prime = (
            Vd
            - self.xq_prime * Iq
        )

        # If excitation is explicitly supplied, retain it as
        # an input to the dynamic model rather than modifying
        # the state here.

        return (
            delta,
            omega,
            Eq_prime,
            Ed_prime,
        )

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
        delta: float = 0.0,
        omega: float = 0.0,
        Pm: float = 1.0,
        Vt: float = 1.0,
        Efd: float = 1.0,
    ) -> tuple[float, float, float, float]:
        """
        Return an initial machine state for solver reset.
        """

        return self.initial_state(
            delta=delta,
            omega=omega,
            Pm=Pm,
            Vt=Vt,
            Efd=Efd,
        )

    # =========================================================
    # OPERATIONAL STATE
    # =========================================================

    def trip(self) -> None:
        """
        Remove the machine from service.

        The dynamic/network solver is responsible for deciding
        how an out-of-service machine is represented electrically.
        """

        self.in_service = False

    def close(self) -> None:
        """
        Return the machine to service.
        """

        self.in_service = True

    @property
    def is_in_service(self) -> bool:
        """
        Return True when the machine is in service.
        """

        return self.in_service

    # =========================================================
    # PARAMETER MANAGEMENT
    # =========================================================

    def set_inertia(
        self,
        H: float,
    ) -> None:
        """
        Update inertia constant.
        """

        H = float(H)

        if H <= 0.0:
            raise ValueError(
                "Machine inertia constant H "
                "must be greater than zero."
            )

        self.H = H

    def set_damping(
        self,
        D: float,
    ) -> None:
        """
        Update machine damping coefficient.
        """

        D = float(D)

        if D < 0.0:
            raise ValueError(
                "Machine damping coefficient D "
                "must be greater than or equal to zero."
            )

        self.D = D

    def set_frequency(
        self,
        frequency_hz: float,
    ) -> None:
        """
        Update system frequency.
        """

        frequency_hz = float(frequency_hz)

        if frequency_hz <= 0.0:
            raise ValueError(
                "frequency_hz must be greater than zero."
            )

        self.frequency_hz = frequency_hz

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return synchronous-machine configuration information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "rated_mva": self.rated_mva,
            "H": self.H,
            "D": self.D,
            "xd": self.xd,
            "xq": self.xq,
            "xd_prime": self.xd_prime,
            "xq_prime": self.xq_prime,
            "Tdo_prime": self.Tdo_prime,
            "Tqo_prime": self.Tqo_prime,
            "frequency_hz": self.frequency_hz,
            "omega_base": self.omega_base,
            "in_service": self.in_service,
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        state = (
            "IN_SERVICE"
            if self.in_service
            else "OUT_OF_SERVICE"
        )

        return (
            f"<SynchronousMachine "
            f"id={self.id}, "
            f"rated_mva={self.rated_mva:.2f}, "
            f"H={self.H:.4f}, "
            f"xd={self.xd:.4f}, "
            f"xq={self.xq:.4f}, "
            f"state={state}>"
        )
```
