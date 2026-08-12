```python
"""
GridForge Dynamic Machine Models
================================

Dynamic machine models used by the GridForge transient-stability
solver.

Architecture
------------

The machine model is responsible for:

- machine identity;
- electrical connection information;
- machine dynamic-state definition;
- initialization of dynamic states;
- internal-emf/current calculation;
- electrical power calculation;
- differential equations.

The machine model is NOT responsible for:

- numerical integration;
- network solution;
- Y-bus construction;
- event processing;
- protection;
- simulation orchestration.

Controller models such as AVR, governor, and PSS are deliberately not
embedded in the classical machine model. They may be connected through
the dynamic-control architecture in a higher-level composition layer.

Classical machine model
-----------------------

The baseline model is the classical synchronous-machine model:

    E' = Efd ∠ δ

    I = (E' - V) / (j Xd')

    S = V I*

Rotor equations:

    dδ/dt = ω

    dω/dt =
        (Pm - Pe - Dω) / (2H)

where:

    δ
        Rotor angle [rad].

    ω
        Speed deviation [pu].

    Efd
        Internal excitation magnitude [pu].

    Pm
        Mechanical input power [pu].

    Pe
        Electrical active power [pu].

    H
        Inertia constant [s].

    D
        Damping coefficient [pu torque / pu speed].

The exact machine state vector is:

    [δ, ω]

for the classical second-order model.

More detailed machine models can expose additional states without
requiring changes to MultiMachineSystem or DAESolver.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


# ======================================================================
# ERRORS
# ======================================================================


class MachineModelError(
    RuntimeError
):
    """Base exception for dynamic-machine errors."""


class MachineParameterError(
    MachineModelError
):
    """Raised when machine parameters are invalid."""


class MachineStateError(
    MachineModelError
):
    """Raised when machine state is invalid."""


# ======================================================================
# ELECTRICAL OUTPUT
# ======================================================================


@dataclass(frozen=True)
class MachineElectricalOutput:
    """
    Electrical output of a dynamic machine.

    Parameters
    ----------
    active_power:
        Active electrical power Pe [pu].

    reactive_power:
        Reactive electrical power Qe [pu].

    current:
        Complex terminal current injection [pu].

    terminal_voltage:
        Complex terminal voltage [pu].

    internal_emf:
        Complex internal emf [pu].
    """

    active_power: float
    reactive_power: float
    current: complex
    terminal_voltage: complex
    internal_emf: complex

    @property
    def apparent_power(
        self,
    ) -> complex:
        """Return complex electrical power S = P + jQ."""

        return complex(
            self.active_power,
            self.reactive_power,
        )


# ======================================================================
# MACHINE PARAMETERS
# ======================================================================


@dataclass(frozen=True)
class ClassicalMachineParameters:
    """
    Parameters for the classical synchronous-machine model.

    Parameters
    ----------
    H:
        Inertia constant [s].

    Xd_prime:
        Direct-axis transient reactance Xd' [pu].

    D:
        Damping coefficient.

    Efd:
        Internal emf magnitude [pu].

    initial_delta:
        Initial rotor angle [rad].

    initial_omega:
        Initial speed deviation [pu].

    Notes
    -----
    The synchronous-machine model uses Xd' rather than the synchronous
    reactance Xd because the classical transient-stability model
    represents the internal emf behind transient reactance.
    """

    H: float

    Xd_prime: float

    D: float = 0.0

    Efd: float = 1.0

    initial_delta: float = 0.0

    initial_omega: float = 0.0

    def __post_init__(
        self,
    ) -> None:

        if self.H <= 0.0:

            raise MachineParameterError(
                "H must be greater "
                "than zero."
            )

        if self.Xd_prime <= 0.0:

            raise MachineParameterError(
                "Xd_prime must be "
                "greater than zero."
            )

        if self.D < 0.0:

            raise MachineParameterError(
                "D cannot be negative."
            )

        if self.Efd < 0.0:

            raise MachineParameterError(
                "Efd cannot be negative."
            )

        for name, value in (
            (
                "initial_delta",
                self.initial_delta,
            ),
            (
                "initial_omega",
                self.initial_omega,
            ),
        ):

            if not np.isfinite(
                value
            ):

                raise MachineParameterError(
                    f"{name} must be finite."
                )


# ======================================================================
# CLASSICAL SYNCHRONOUS MACHINE
# ======================================================================


class ClassicalSynchronousMachine:
    """
    Classical second-order synchronous-machine model.

    Dynamic states
    --------------

        state[0] = delta
        state[1] = omega

    The machine does not own a numerical integrator. Its ``derivatives``
    method returns dx/dt for the global numerical integration layer.

    Parameters
    ----------
    machine_id:
        Unique machine identifier.

    bus_id:
        Electrical bus identifier.

    H:
        Inertia constant [s].

    Xd_prime:
        Direct-axis transient reactance [pu].

    D:
        Damping coefficient.

    Efd:
        Internal emf magnitude [pu].

    initial_delta:
        Initial rotor angle [rad].

    initial_omega:
        Initial speed deviation [pu].
    """

    STATE_SIZE = 2

    def __init__(
        self,
        machine_id: str,
        bus_id: str,
        H: float,
        Xd_prime: float,
        *,
        D: float = 0.0,
        Efd: float = 1.0,
        initial_delta: float = 0.0,
        initial_omega: float = 0.0,
    ) -> None:

        if not str(
            machine_id
        ).strip():

            raise ValueError(
                "machine_id cannot "
                "be empty."
            )

        if not str(
            bus_id
        ).strip():

            raise ValueError(
                "bus_id cannot "
                "be empty."
            )

        self._machine_id = (
            str(machine_id)
        )

        self._bus_id = (
            str(bus_id)
        )

        self.parameters = (
            ClassicalMachineParameters(
                H=H,
                Xd_prime=Xd_prime,
                D=D,
                Efd=Efd,
                initial_delta=(
                    initial_delta
                ),
                initial_omega=(
                    initial_omega
                ),
            )
        )

    # ==================================================================
    # IDENTITY
    # ==================================================================

    @property
    def machine_id(
        self,
    ) -> str:
        """Unique machine identifier."""

        return self._machine_id

    @property
    def bus_id(
        self,
    ) -> str:
        """Electrical bus identifier."""

        return self._bus_id

    # ==================================================================
    # STATE
    # ==================================================================

    @property
    def state_size(
        self,
    ) -> int:
        """Number of dynamic states."""

        return self.STATE_SIZE

    @property
    def H(
        self,
    ) -> float:
        """Inertia constant."""

        return self.parameters.H

    @property
    def Xd_prime(
        self,
    ) -> float:
        """Transient reactance."""

        return self.parameters.Xd_prime

    @property
    def D(
        self,
    ) -> float:
        """Damping coefficient."""

        return self.parameters.D

    @property
    def Efd(
        self,
    ) -> float:
        """Internal emf magnitude."""

        return self.parameters.Efd

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def initial_state(
        self,
        terminal_voltage: complex,
        electrical_power: Any,
        mechanical_power: float,
        *,
        time: float = 0.0,
    ) -> np.ndarray:
        """
        Construct the initial dynamic state.

        The classical model initializes rotor angle from the initial
        electrical power and terminal voltage when sufficient phasor
        information is available.

        If a meaningful angle cannot be inferred, the configured
        ``initial_delta`` is retained.

        ``mechanical_power`` is validated here because it is part of the
        machine operating point, although the classical second-order
        state vector does not contain Pm as a dynamic state.
        """

        del time

        voltage = complex(
            terminal_voltage
        )

        if not (
            np.isfinite(
                voltage.real
            )
            and np.isfinite(
                voltage.imag
            )
        ):

            raise MachineStateError(
                "Terminal voltage "
                "must be finite."
            )

        if not np.isfinite(
            mechanical_power
        ):

            raise MachineStateError(
                "Mechanical power "
                "must be finite."
            )

        delta = (
            self.parameters.initial_delta
        )

        omega = (
            self.parameters.initial_omega
        )

        # --------------------------------------------------------------
        # If complex electrical power is
        # supplied, infer the internal
        # emf angle from:
        #
        #     E' = V + j Xd' I
        #
        # where:
        #
        #     I = conj(S / V)
        #
        # This gives a more physically
        # meaningful initial rotor angle.
        # --------------------------------------------------------------

        apparent_power = (
            self._complex_power(
                electrical_power
            )
        )

        if (
            apparent_power is not None
            and abs(voltage) > 1e-12
        ):

            current = (
                np.conj(
                    apparent_power
                    / voltage
                )
            )

            internal_emf = (
                voltage
                + 1j
                * self.Xd_prime
                * current
            )

            if abs(
                internal_emf
            ) > 1e-12:

                delta = float(
                    np.angle(
                        internal_emf
                    )
                )

                # Preserve the configured
                # emf magnitude when the
                # operating point is not
                # intended to modify Efd.
                #
                # The classical model uses
                # the configured Efd as its
                # internal-emf magnitude.
                #

        state = np.array(
            [
                delta,
                omega,
            ],
            dtype=float,
        )

        self._validate_state(
            state
        )

        return state

    # ==================================================================
    # INTERNAL EMF
    # ==================================================================

    def internal_emf(
        self,
        state: np.ndarray,
    ) -> complex:
        """
        Return internal emf E' behind Xd'.

            E' = Efd * exp(jδ)
        """

        state = self._validate_state(
            state
        )

        delta = state[0]

        return (
            self.Efd
            * np.exp(
                1j * delta
            )
        )

    # ==================================================================
    # CURRENT INJECTION
    # ==================================================================

    def current_injection(
        self,
        state: np.ndarray,
        terminal_voltage: complex,
        *,
        time: float = 0.0,
    ) -> complex:
        """
        Calculate terminal current injection.

            I = (E' - V) / (j Xd')

        Positive current represents current injected by the machine
        into the network.
        """

        del time

        state = self._validate_state(
            state
        )

        voltage = complex(
            terminal_voltage
        )

        if abs(
            self.Xd_prime
        ) <= 1e-15:

            raise MachineModelError(
                "Xd_prime is too small "
                "for current calculation."
            )

        emf = (
            self.internal_emf(
                state
            )
        )

        return (
            emf - voltage
        ) / (
            1j * self.Xd_prime
        )

    # ==================================================================
    # ELECTRICAL OUTPUT
    # ==================================================================

    def electrical_output(
        self,
        state: np.ndarray,
        terminal_voltage: complex,
        *,
        time: float = 0.0,
    ) -> MachineElectricalOutput:
        """
        Calculate terminal electrical power.

            S = V I*

        Returns active and reactive power together with the underlying
        electrical phasors.
        """

        del time

        voltage = complex(
            terminal_voltage
        )

        current = (
            self.current_injection(
                state=state,
                terminal_voltage=voltage,
            )
        )

        apparent_power = (
            voltage
            * np.conj(
                current
            )
        )

        emf = (
            self.internal_emf(
                state
            )
        )

        return MachineElectricalOutput(
            active_power=float(
                apparent_power.real
            ),
            reactive_power=float(
                apparent_power.imag
            ),
            current=current,
            terminal_voltage=voltage,
            internal_emf=emf,
        )

    # ==================================================================
    # DIFFERENTIAL EQUATIONS
    # ==================================================================

    def derivatives(
        self,
        state: np.ndarray,
        terminal_voltage: complex,
        electrical_output: Any,
        *,
        time: float = 0.0,
    ) -> np.ndarray:
        """
        Return the classical rotor differential equations.

            dδ/dt = ω

            dω/dt =
                (Pm - Pe - Dω) / (2H)

        ``mechanical_power`` is supplied through the operating-point /
        dynamic-control composition and is therefore obtained from the
        electrical-output context where supported.

        For the pure classical machine, a mechanical-power value must be
        supplied in ``electrical_output`` or through ``set_mechanical_power``.
        """

        del terminal_voltage
        del time

        state = self._validate_state(
            state
        )

        Pe = (
            self._extract_active_power(
                electrical_output
            )
        )

        Pm = (
            self.mechanical_power
        )

        delta = state[0]
        omega = state[1]

        del delta

        ddelta_dt = (
            omega
        )

        domega_dt = (
            Pm
            - Pe
            - self.D * omega
        ) / (
            2.0 * self.H
        )

        derivative = np.array(
            [
                ddelta_dt,
                domega_dt,
            ],
            dtype=float,
        )

        self._validate_state(
            derivative,
            name="derivative",
        )

        return derivative

    # ==================================================================
    # MECHANICAL POWER
    # ==================================================================

    @property
    def mechanical_power(
        self,
    ) -> float:
        """
        Current mechanical input power.

        The classical machine keeps this as an operating-point input,
        not as an independently integrated state.

        A future turbine/governor model can replace/update this value
        through the dynamic-control composition layer.
        """

        return getattr(
            self,
            "_mechanical_power",
            1.0,
        )

    def set_mechanical_power(
        self,
        mechanical_power: float,
    ) -> None:
        """
        Set the current mechanical input power.

        This method is intended for operating-point initialization and
        external dynamic-control composition.
        """

        value = float(
            mechanical_power
        )

        if not np.isfinite(
            value
        ):

            raise ValueError(
                "mechanical_power must "
                "be finite."
            )

        self._mechanical_power = value

    # ==================================================================
    # HELPERS
    # ==================================================================

    @staticmethod
    def _complex_power(
        electrical_power: Any,
    ) -> complex | None:
        """
        Extract a complex power from common GridForge power formats.
        """

        if electrical_power is None:

            return None

        if isinstance(
            electrical_power,
            complex,
        ):

            return electrical_power

        if hasattr(
            electrical_power,
            "apparent_power",
        ):

            return complex(
                electrical_power.apparent_power
            )

        if hasattr(
            electrical_power,
            "active_power",
        ):

            p = float(
                electrical_power.active_power
            )

            q = float(
                getattr(
                    electrical_power,
                    "reactive_power",
                    0.0,
                )
            )

            return complex(
                p,
                q,
            )

        if isinstance(
            electrical_power,
            dict,
        ):

            if "active_power" in (
                electrical_power
            ):

                return complex(
                    float(
                        electrical_power[
                            "active_power"
                        ]
                    ),
                    float(
                        electrical_power.get(
                            "reactive_power",
                            0.0,
                        )
                    ),
                )

            if "P" in electrical_power:

                return complex(
                    float(
                        electrical_power["P"]
                    ),
                    float(
                        electrical_power.get(
                            "Q",
                            0.0,
                        )
                    ),
                )

        if np.isscalar(
            electrical_power
        ):

            value = float(
                electrical_power
            )

            if np.isfinite(
                value
            ):

                return complex(
                    value,
                    0.0,
                )

        return None

    @staticmethod
    def _extract_active_power(
        electrical_output: Any,
    ) -> float:
        """
        Extract Pe from a machine electrical-output object.
        """

        if electrical_output is None:

            raise MachineModelError(
                "Electrical output "
                "cannot be None."
            )

        if hasattr(
            electrical_output,
            "active_power",
        ):

            value = float(
                electrical_output.active_power
            )

        elif isinstance(
            electrical_output,
            dict,
        ):

            if "active_power" in (
                electrical_output
            ):

                value = float(
                    electrical_output[
                        "active_power"
                    ]
                )

            elif "P" in electrical_output:

                value = float(
                    electrical_output["P"]
                )

            else:

                raise MachineModelError(
                    "Electrical output "
                    "does not contain "
                    "active power."
                )

        elif np.isscalar(
            electrical_output
        ):

            value = float(
                electrical_output
            )

        else:

            raise MachineModelError(
                "Unsupported electrical "
                "output format."
            )

        if not np.isfinite(
            value
        ):

            raise MachineModelError(
                "Electrical active power "
                "must be finite."
            )

        return value

    def _validate_state(
        self,
        state: np.ndarray,
        *,
        name: str = "state",
    ) -> np.ndarray:
        """
        Validate the classical machine state.
        """

        values = np.asarray(
            state,
            dtype=float,
        )

        if values.ndim != 1:

            raise MachineStateError(
                f"{name} must be "
                "one-dimensional."
            )

        if values.size != (
            self.STATE_SIZE
        ):

            raise MachineStateError(
                f"{name} must contain "
                f"{self.STATE_SIZE} "
                "values."
            )

        if not np.all(
            np.isfinite(values)
        ):

            raise MachineStateError(
                f"{name} contains "
                "non-finite values."
            )

        return values


# ======================================================================
# BACKWARD-COMPATIBILITY ALIAS
# ======================================================================

DynamicGenerator = (
    ClassicalSynchronousMachine
)


__all__ = [
    "MachineModelError",
    "MachineParameterError",
    "MachineStateError",
    "MachineElectricalOutput",
    "ClassicalMachineParameters",
    "ClassicalSynchronousMachine",
    "DynamicGenerator",
]
```
