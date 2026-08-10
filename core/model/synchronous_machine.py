```python
"""
GridForge Synchronous Machine Model
===================================

File:
    core/model/synchronous_machine.py

Defines the GridForge synchronous-machine dynamic model.

Purpose
-------
The SynchronousMachine represents the electromechanical dynamics of
a synchronous generator.

Current model
-------------
Classical second-order synchronous-machine model.

Dynamic states:

    delta
        Rotor electrical angle in radians.

    omega
        Rotor speed deviation in per-unit.

The machine equations are:

    d(delta)/dt = omega_base * omega

    d(omega)/dt =
        [Pm - Pe - D * omega] / (2H)

Where:

    delta
        Rotor electrical angle.

    omega
        Rotor speed deviation from synchronous speed.

    Pm
        Mechanical input power.

    Pe
        Electrical air-gap/output power.

    H
        Inertia constant in seconds.

    D
        Damping coefficient.

    omega_base
        Electrical synchronous angular frequency in rad/s.

Architecture
------------
The SynchronousMachine does NOT perform numerical integration.

The dynamic / DAE solver owns:

    - Dynamic state vector
    - State integration
    - Time stepping
    - Initial conditions
    - Differential-algebraic solution

The SynchronousMachine provides:

    - Differential equations
    - Electrical power input interface
    - Mechanical power input interface
    - Initial-state calculation
    - Parameter management
    - Basic machine limits
    - Machine diagnostics

The machine model does NOT:

    - Build Ybus.
    - Solve load flow.
    - Solve network algebraic equations.
    - Perform Newton-Raphson iterations.
    - Perform short-circuit calculations.
    - Perform transient-stability integration.
    - Control the AVR.
    - Control the governor.
    - Perform protection calculations.

Those responsibilities belong to the appropriate solver,
analysis, control, or protection layers.

Control-system relationship
---------------------------

Typical dynamic chain:

    Rotor speed
        |
        v
    Governor
        |
        v
       Pm
        |
        v
    +----------------------+
    | Synchronous Machine  |
    +----------------------+
        |
        +---- delta
        |
        +---- omega
        |
        v
       Pe
        |
        v
      Network

Excitation path:

    Vt
     |
     v
    AVR <---- PSS
     |
     v
    Efd
     |
     v
    Synchronous Machine

Future extensions
-----------------
The model can later be extended to support:

    - 3rd-order models
    - 4th-order transient models
    - 5th/6th-order subtransient models
    - xd / xq
    - xd' / xq'
    - xd'' / xq''
    - Td0'
    - Tq0'
    - Td0''
    - Tq0''
    - E'q / E'd states
    - E''q / E''d states
    - Saturation
    - Damper windings
    - Saliency
    - Field-current limits
    - Machine-specific electrical equations

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math


class SynchronousMachine:
    """
    Classical second-order synchronous-machine model.

    The model contains machine parameters only. Dynamic states are
    supplied by the dynamic solver.

    Parameters
    ----------
    id:
        Unique machine identifier.

    name:
        Human-readable machine name.

    rated_mva:
        Machine MVA base/rating.

    H:
        Inertia constant in seconds.

    D:
        Mechanical damping coefficient.

    omega_base:
        Electrical synchronous angular frequency in rad/s.

    Pm_min:
        Minimum mechanical input power.

    Pm_max:
        Maximum mechanical input power.

    Pe_min:
        Minimum electrical power.

    Pe_max:
        Maximum electrical power.

    Efd_min:
        Minimum excitation voltage.

    Efd_max:
        Maximum excitation voltage.

    Notes
    -----
    ``omega`` is represented as a per-unit speed deviation:

        omega = (w - w_s) / w_s

    Therefore:

        d(delta)/dt = omega_base * omega
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        id: str,
        name: str = "",
        rated_mva: float = 100.0,
        H: float = 3.5,
        D: float = 0.0,
        omega_base: float = 2.0 * math.pi * 50.0,
        Pm_min: float = 0.0,
        Pm_max: float = 1.2,
        Pe_min: float = -1.2,
        Pe_max: float = 1.2,
        Efd_min: float = 0.0,
        Efd_max: float = 5.0,
    ):
        """
        Initialize a synchronous-machine model.

        Parameters
        ----------
        id:
            Unique machine identifier.

        name:
            Human-readable machine name.

        rated_mva:
            Machine MVA rating.

        H:
            Inertia constant in seconds.

        D:
            Damping coefficient.

        omega_base:
            Synchronous electrical angular frequency in rad/s.

        Pm_min:
            Minimum mechanical input power.

        Pm_max:
            Maximum mechanical input power.

        Pe_min:
            Minimum electrical power.

        Pe_max:
            Maximum electrical power.

        Efd_min:
            Minimum excitation voltage.

        Efd_max:
            Maximum excitation voltage.
        """

        self.id = str(id)
        self.name = str(name)

        # ---------------------------------------------------------
        # Machine base
        # ---------------------------------------------------------

        self.rated_mva = float(rated_mva)

        # ---------------------------------------------------------
        # Dynamic parameters
        # ---------------------------------------------------------

        self.H = float(H)
        self.D = float(D)
        self.omega_base = float(omega_base)

        # ---------------------------------------------------------
        # Mechanical power limits
        # ---------------------------------------------------------

        self.Pm_min = float(Pm_min)
        self.Pm_max = float(Pm_max)

        # ---------------------------------------------------------
        # Electrical power limits
        # ---------------------------------------------------------

        self.Pe_min = float(Pe_min)
        self.Pe_max = float(Pe_max)

        # ---------------------------------------------------------
        # Excitation limits
        #
        # These are stored here as machine capability limits.
        # AVR dynamics remain responsible for regulating Efd.
        # ---------------------------------------------------------

        self.Efd_min = float(Efd_min)
        self.Efd_max = float(Efd_max)

        self._validate()

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate(self) -> None:
        """
        Validate synchronous-machine parameters.
        """

        if not self.id:
            raise ValueError(
                "Synchronous machine id cannot be empty."
            )

        if self.rated_mva <= 0.0:
            raise ValueError(
                "Machine rated MVA must be greater than zero."
            )

        if not math.isfinite(self.rated_mva):
            raise ValueError(
                "Machine rated MVA must be finite."
            )

        if self.H <= 0.0:
            raise ValueError(
                "Machine inertia constant H must be greater than zero."
            )

        if not math.isfinite(self.H):
            raise ValueError(
                "Machine inertia constant H must be finite."
            )

        if self.D < 0.0:
            raise ValueError(
                "Machine damping coefficient D must be >= 0."
            )

        if self.omega_base <= 0.0:
            raise ValueError(
                "Machine omega_base must be greater than zero."
            )

        if self.Pm_min > self.Pm_max:
            raise ValueError(
                "Pm_min must not be greater than Pm_max."
            )

        if self.Pe_min > self.Pe_max:
            raise ValueError(
                "Pe_min must not be greater than Pe_max."
            )

        if self.Efd_min > self.Efd_max:
            raise ValueError(
                "Efd_min must not be greater than Efd_max."
            )

    # =============================================================
    # ROTOR ANGLE EQUATION
    # =============================================================

    def angle_derivative(
        self,
        omega: float,
    ) -> float:
        """
        Calculate rotor-angle derivative.

        Equation:

            d(delta)/dt = omega_base * omega

        Parameters
        ----------
        omega:
            Rotor speed deviation in per-unit.

        Returns
        -------
        float
            Rotor electrical-angle derivative in rad/s.
        """

        omega = float(omega)

        return self.omega_base * omega

    # =============================================================
    # SPEED EQUATION
    # =============================================================

    def speed_derivative(
        self,
        Pm: float,
        Pe: float,
        omega: float,
    ) -> float:
        """
        Calculate rotor-speed derivative.

        Swing equation:

            d(omega)/dt =
                [Pm - Pe - D * omega] / (2H)

        Parameters
        ----------
        Pm:
            Mechanical input power in per-unit.

        Pe:
            Electrical output power in per-unit.

        omega:
            Rotor speed deviation in per-unit.

        Returns
        -------
        float
            Rotor speed-deviation derivative.
        """

        Pm = float(Pm)
        Pe = float(Pe)
        omega = float(omega)

        return (
            Pm
            - Pe
            - self.D * omega
        ) / (
            2.0 * self.H
        )

    # =============================================================
    # COMBINED STATE EQUATION
    # =============================================================

    def derivative(
        self,
        delta: float,
        omega: float,
        Pm: float,
        Pe: float,
    ) -> tuple[float, float]:
        """
        Calculate both machine state derivatives.

        Parameters
        ----------
        delta:
            Rotor electrical angle in radians.

        omega:
            Rotor speed deviation in per-unit.

        Pm:
            Mechanical input power in per-unit.

        Pe:
            Electrical output power in per-unit.

        Returns
        -------
        tuple
            (d_delta_dt, d_omega_dt)

        Notes
        -----
        ``delta`` is currently accepted as part of the standard
        dynamic-state interface even though the classical swing
        equations do not require its value directly.
        """

        # Validate that delta is numerically usable.
        delta = float(delta)

        if not math.isfinite(delta):
            raise ValueError(
                "Rotor angle delta must be finite."
            )

        d_delta_dt = self.angle_derivative(
            omega=omega
        )

        d_omega_dt = self.speed_derivative(
            Pm=Pm,
            Pe=Pe,
            omega=omega,
        )

        return (
            d_delta_dt,
            d_omega_dt,
        )

    # =============================================================
    # MECHANICAL POWER
    # =============================================================

    def limit_mechanical_power(
        self,
        Pm: float,
    ) -> float:
        """
        Apply mechanical-power limits.
        """

        return max(
            self.Pm_min,
            min(
                float(Pm),
                self.Pm_max,
            ),
        )

    # =============================================================
    # ELECTRICAL POWER
    # =============================================================

    def limit_electrical_power(
        self,
        Pe: float,
    ) -> float:
        """
        Apply electrical-power capability limits.
        """

        return max(
            self.Pe_min,
            min(
                float(Pe),
                self.Pe_max,
            ),
        )

    # =============================================================
    # EXCITATION
    # =============================================================

    def limit_excitation(
        self,
        Efd: float,
    ) -> float:
        """
        Apply machine excitation capability limits.

        The AVR remains responsible for excitation control.
        """

        return max(
            self.Efd_min,
            min(
                float(Efd),
                self.Efd_max,
            ),
        )

    # =============================================================
    # INITIAL STATE
    # =============================================================

    def initial_state(
        self,
        delta: float = 0.0,
        omega: float = 0.0,
    ) -> tuple[float, float]:
        """
        Return the initial machine dynamic state.

        Parameters
        ----------
        delta:
            Initial rotor electrical angle.

        omega:
            Initial rotor speed deviation.

        Returns
        -------
        tuple
            (delta, omega)

        Notes
        -----
        For a machine initialized at synchronous speed:

            omega = 0

        The rotor angle is supplied by the initialization/load-flow
        layer or defaults to zero.
        """

        delta = float(delta)
        omega = float(omega)

        if not math.isfinite(delta):
            raise ValueError(
                "Initial rotor angle delta must be finite."
            )

        if not math.isfinite(omega):
            raise ValueError(
                "Initial rotor speed deviation must be finite."
            )

        return (
            delta,
            omega,
        )

    # =============================================================
    # RESET
    # =============================================================

    def reset(
        self,
        delta: float = 0.0,
        omega: float = 0.0,
    ) -> tuple[float, float]:
        """
        Return the default/reset machine state.

        The dynamic solver should use this value when resetting
        the simulation.
        """

        return self.initial_state(
            delta=delta,
            omega=omega,
        )

    # =============================================================
    # PARAMETER MANAGEMENT
    # =============================================================

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
                "Machine inertia constant H must be greater than zero."
            )

        self.H = H

    def set_damping(
        self,
        D: float,
    ) -> None:
        """
        Update mechanical damping coefficient.
        """

        D = float(D)

        if D < 0.0:
            raise ValueError(
                "Machine damping coefficient D must be >= 0."
            )

        self.D = D

    def set_base_frequency(
        self,
        frequency_hz: float,
    ) -> None:
        """
        Set synchronous electrical frequency.

        Parameters
        ----------
        frequency_hz:
            System frequency in Hz.

        Notes
        -----
        The internal ``omega_base`` value is stored in rad/s.
        """

        frequency_hz = float(frequency_hz)

        if frequency_hz <= 0.0:
            raise ValueError(
                "System frequency must be greater than zero."
            )

        self.omega_base = (
            2.0
            * math.pi
            * frequency_hz
        )

    def set_power_limits(
        self,
        Pm_min: float,
        Pm_max: float,
        Pe_min: float | None = None,
        Pe_max: float | None = None,
    ) -> None:
        """
        Update mechanical and optional electrical power limits.
        """

        Pm_min = float(Pm_min)
        Pm_max = float(Pm_max)

        if Pm_min > Pm_max:
            raise ValueError(
                "Pm_min must not be greater than Pm_max."
            )

        self.Pm_min = Pm_min
        self.Pm_max = Pm_max

        if Pe_min is not None:
            Pe_min = float(Pe_min)

        if Pe_max is not None:
            Pe_max = float(Pe_max)

        new_pe_min = (
            self.Pe_min
            if Pe_min is None
            else Pe_min
        )

        new_pe_max = (
            self.Pe_max
            if Pe_max is None
            else Pe_max
        )

        if new_pe_min > new_pe_max:
            raise ValueError(
                "Pe_min must not be greater than Pe_max."
            )

        self.Pe_min = new_pe_min
        self.Pe_max = new_pe_max

    def set_excitation_limits(
        self,
        Efd_min: float,
        Efd_max: float,
    ) -> None:
        """
        Update machine excitation limits.
        """

        Efd_min = float(Efd_min)
        Efd_max = float(Efd_max)

        if Efd_min > Efd_max:
            raise ValueError(
                "Efd_min must not be greater than Efd_max."
            )

        self.Efd_min = Efd_min
        self.Efd_max = Efd_max

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict:
        """
        Return synchronous-machine configuration information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "model": "CLASSICAL_2ND_ORDER",
            "rated_mva": self.rated_mva,
            "H": self.H,
            "D": self.D,
            "omega_base": self.omega_base,
            "Pm_min": self.Pm_min,
            "Pm_max": self.Pm_max,
            "Pe_min": self.Pe_min,
            "Pe_max": self.Pe_max,
            "Efd_min": self.Efd_min,
            "Efd_max": self.Efd_max,
        }

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<SynchronousMachine "
            f"id={self.id}, "
            f"model=CLASSICAL_2ND_ORDER, "
            f"H={self.H:.4f}, "
            f"D={self.D:.4f}, "
            f"omega_base={self.omega_base:.4f}>"
        )
```
