"""
GridForge Dynamic Algebraic Equation Solver
===========================================

Author:
    Subhendu Mishra

File:
    core/solver/dynamics/dae_solver.py

Purpose
-------
Low-level coordinator for differential-algebraic dynamic systems.

The DAE is represented as:

    dx/dt = f(x, V, u, t)

    0 = g(x, V, u, t)

Responsibilities
----------------
- coordinate differential and algebraic portions;
- request algebraic network solutions;
- evaluate dynamic-machine derivatives;
- perform numerical integration through Integrator;
- expose a clean low-level DAE interface.

Non-responsibilities
--------------------
- machine equations
- swing equations
- AVR / governor / PSS
- protection
- event semantics
- Y-bus construction
- power-flow formulation
- complete transient-stability study
- result storage

The complete derivative contract is:

    derivative(state, time) -> dx/dt

This contract is intentionally identical to the Integrator contract.

The DAE solver therefore preserves both state and time through every
integration stage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

import numpy as np

from .integrator import Integrator
from .multimachine import MultiMachineSystem


# ======================================================================
# TYPES
# ======================================================================

NetworkSolver = Callable[
    [np.ndarray, float],
    Mapping[str, complex],
]

MechanicalPowerMap = Mapping[
    str,
    float,
]


# ======================================================================
# ERRORS
# ======================================================================


class DAESolverError(RuntimeError):
    """Base exception for DAE-solver errors."""


class DAEConfigurationError(DAESolverError):
    """Raised when the DAE solver is incorrectly configured."""


class DAEAlgebraicError(DAESolverError):
    """Raised when the algebraic network solution fails."""


class DAENumericalError(DAESolverError):
    """Raised when numerical evaluation or integration fails."""


# ======================================================================
# DAE SOLUTION
# ======================================================================


@dataclass(frozen=True)
class DAESolution:
    """
    Result of one complete DAE evaluation.

    Attributes
    ----------
    state:
        Global dynamic state.

    terminal_voltages:
        Algebraic network solution.

    derivatives:
        Dynamic-state derivative dx/dt.

    time:
        Simulation time.
    """

    state: np.ndarray

    terminal_voltages: dict[str, complex]

    derivatives: np.ndarray

    time: float

    def __post_init__(self) -> None:
        state = np.asarray(
            self.state,
            dtype=float,
        ).copy()

        derivatives = np.asarray(
            self.derivatives,
            dtype=float,
        ).copy()

        time = float(self.time)

        if not np.isfinite(time):
            raise ValueError(
                "DAESolution time must be finite."
            )

        state.setflags(write=False)
        derivatives.setflags(write=False)

        object.__setattr__(
            self,
            "state",
            state,
        )

        object.__setattr__(
            self,
            "derivatives",
            derivatives,
        )

        object.__setattr__(
            self,
            "terminal_voltages",
            dict(self.terminal_voltages),
        )

        object.__setattr__(
            self,
            "time",
            time,
        )


# ======================================================================
# DAE SOLVER
# ======================================================================


class DAESolver:
    """
    Differential-algebraic system coordinator.

    Parameters
    ----------
    machine_system:
        MultiMachineSystem containing dynamic machine models.

    network_solver:
        Algebraic network-solution callback.

        Required signature:

            network_solver(state, time)
                -> {bus_id: complex_voltage}

    mechanical_powers:
        External mechanical-power input for every machine.

    integrator:
        Numerical Integrator.

    Important
    ---------
    The DAE solver does not alter the Integrator contract.

    The Integrator owns numerical time advancement.

    The DAE solver supplies a derivative callback with the exact
    signature:

        derivative(state, time) -> dx/dt

    Consequently RK4 receives the correct intermediate times:

        t
        t + dt/2
        t + dt/2
        t + dt
    """

    def __init__(
        self,
        machine_system: MultiMachineSystem,
        network_solver: NetworkSolver,
        mechanical_powers: MechanicalPowerMap,
        *,
        integrator: Integrator,
    ) -> None:

        if not isinstance(
            machine_system,
            MultiMachineSystem,
        ):
            raise DAEConfigurationError(
                "machine_system must be "
                "a MultiMachineSystem."
            )

        if not callable(network_solver):
            raise DAEConfigurationError(
                "network_solver must be callable."
            )

        if not isinstance(
            integrator,
            Integrator,
        ):
            raise DAEConfigurationError(
                "integrator must be "
                "an Integrator instance."
            )

        self.machine_system = machine_system
        self.network_solver = network_solver
        self.mechanical_powers = dict(
            mechanical_powers
        )
        self.integrator = integrator

        self._validate_configuration()

    # ==================================================================
    # PROPERTIES
    # ==================================================================

    @property
    def state_size(self) -> int:
        """Return the total number of dynamic states."""

        return self.machine_system.state_size

    @property
    def machines(self):
        """Return registered dynamic machines."""

        return self.machine_system.machines

    # ==================================================================
    # ALGEBRAIC SOLUTION
    # ==================================================================

    def solve_algebraic(
        self,
        state: np.ndarray,
        time: float,
    ) -> dict[str, complex]:
        """
        Solve the algebraic network for a dynamic state.
        """

        state = (
            self.machine_system.validate_global_state(
                state
            )
        )

        time = self._validate_time(time)

        try:
            result = self.network_solver(
                state,
                time,
            )

        except Exception as exc:
            raise DAEAlgebraicError(
                "Algebraic network solution "
                f"failed at t={time:.12g} s."
            ) from exc

        if result is None:
            raise DAEAlgebraicError(
                "network_solver returned None."
            )

        try:
            voltages = {
                str(bus_id): complex(voltage)
                for bus_id, voltage in result.items()
            }

        except Exception as exc:
            raise DAEAlgebraicError(
                "Invalid algebraic "
                "network-solver result."
            ) from exc

        for bus_id, voltage in voltages.items():
            if not (
                np.isfinite(voltage.real)
                and np.isfinite(voltage.imag)
            ):
                raise DAEAlgebraicError(
                    "Network solver returned "
                    f"non-finite voltage for "
                    f"bus '{bus_id}'."
                )

        self._validate_required_buses(
            voltages
        )

        return voltages

    # ==================================================================
    # DIFFERENTIAL SOLUTION
    # ==================================================================

    def derivatives(
        self,
        state: np.ndarray,
        time: float,
    ) -> np.ndarray:
        """
        Evaluate:

            dx/dt = f(x, V, u, t)

        The algebraic network is solved first, then the resulting
        terminal voltages are supplied to MultiMachineSystem.
        """

        state = (
            self.machine_system.validate_global_state(
                state
            )
        )

        time = self._validate_time(time)

        voltages = self.solve_algebraic(
            state,
            time,
        )

        try:
            derivatives = (
                self.machine_system.derivatives(
                    state=state,
                    terminal_voltages=voltages,
                    mechanical_powers=(
                        self.mechanical_powers
                    ),
                    time=time,
                )
            )

        except Exception as exc:
            raise DAENumericalError(
                "Dynamic derivative evaluation "
                f"failed at t={time:.12g} s."
            ) from exc

        derivatives = np.asarray(
            derivatives,
            dtype=float,
        )

        if derivatives.shape != state.shape:
            raise DAENumericalError(
                "Dynamic derivative shape does "
                "not match the dynamic state."
            )

        if not np.all(
            np.isfinite(derivatives)
        ):
            raise DAENumericalError(
                "Dynamic derivative contains "
                "non-finite values."
            )

        return derivatives

    # ==================================================================
    # COMPLETE DAE EVALUATION
    # ==================================================================

    def evaluate(
        self,
        state: np.ndarray,
        time: float,
    ) -> DAESolution:
        """
        Evaluate both algebraic and differential portions of the DAE.
        """

        state = (
            self.machine_system.validate_global_state(
                state
            )
        )

        time = self._validate_time(time)

        voltages = self.solve_algebraic(
            state,
            time,
        )

        try:
            derivatives = (
                self.machine_system.derivatives(
                    state=state,
                    terminal_voltages=voltages,
                    mechanical_powers=(
                        self.mechanical_powers
                    ),
                    time=time,
                )
            )

        except Exception as exc:
            raise DAENumericalError(
                "Dynamic derivative evaluation "
                f"failed at t={time:.12g} s."
            ) from exc

        derivatives = np.asarray(
            derivatives,
            dtype=float,
        )

        if derivatives.shape != state.shape:
            raise DAENumericalError(
                "Derivative/state dimension "
                "mismatch."
            )

        if not np.all(
            np.isfinite(derivatives)
        ):
            raise DAENumericalError(
                "Derivative vector contains "
                "non-finite values."
            )

        return DAESolution(
            state=state,
            terminal_voltages=voltages,
            derivatives=derivatives,
            time=time,
        )

    # ==================================================================
    # ONE INTEGRATION STEP
    # ==================================================================

    def step(
        self,
        state: np.ndarray,
        time: float,
        dt: float,
    ) -> DAESolution:
        """
        Advance the complete DAE system by one integration step.

        The Integrator contract is:

            step(
                x,
                derivative,
                t,
                dt,
                jacobian=None,
            )

        The derivative callback is:

            derivative(state, time) -> dx/dt

        The time argument is deliberately NOT captured from the
        outer scope. This is essential for RK4 and other methods that
        evaluate derivatives at intermediate times.
        """

        state = (
            self.machine_system.validate_global_state(
                state
            )
        )

        time = self._validate_time(time)
        dt = self._validate_dt(dt)

        # --------------------------------------------------------------
        # Full derivative callback.
        #
        # The Integrator supplies both state and evaluation time.
        # --------------------------------------------------------------

        def derivative(
            intermediate_state: np.ndarray,
            intermediate_time: float,
        ) -> np.ndarray:
            return self.derivatives(
                intermediate_state,
                intermediate_time,
            )

        # --------------------------------------------------------------
        # Numerical integration.
        #
        # IMPORTANT:
        # Pass BOTH time and dt.
        # --------------------------------------------------------------

        try:
            new_state = self.integrator.step(
                x=state,
                derivative=derivative,
                t=time,
                dt=dt,
            )

        except Exception as exc:
            raise DAENumericalError(
                "DAE integration failed "
                f"for interval "
                f"[{time:.12g}, "
                f"{time + dt:.12g}] s."
            ) from exc

        new_state = (
            self.machine_system.validate_global_state(
                new_state
            )
        ).copy()

        new_time = time + dt

        # --------------------------------------------------------------
        # Evaluate the algebraic system at the NEW state.
        # --------------------------------------------------------------

        return self.evaluate(
            state=new_state,
            time=new_time,
        )

    # ==================================================================
    # EXTERNAL INPUT UPDATE
    # ==================================================================

    def set_mechanical_power(
        self,
        machine_id: str,
        value: float,
    ) -> None:
        """
        Update the external mechanical-power input for one machine.

        Future governor/turbine models may use this interface.
        """

        machine_id = str(machine_id)

        machine_ids = {
            str(machine.machine_id)
            for machine
            in self.machine_system.machines
        }

        if machine_id not in machine_ids:
            raise DAEConfigurationError(
                f"Unknown machine '{machine_id}'."
            )

        try:
            numeric_value = float(value)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise DAEConfigurationError(
                "Mechanical power must be numeric."
            ) from exc

        if not np.isfinite(numeric_value):
            raise DAEConfigurationError(
                "Mechanical power must be finite."
            )

        self.mechanical_powers[
            machine_id
        ] = numeric_value

    def set_mechanical_powers(
        self,
        values: MechanicalPowerMap,
    ) -> None:
        """
        Replace all external mechanical-power inputs.
        """

        new_values = {
            str(machine_id): float(value)
            for machine_id, value
            in dict(values).items()
        }

        machine_ids = {
            str(machine.machine_id)
            for machine
            in self.machine_system.machines
        }

        missing = (
            machine_ids
            - set(new_values)
        )

        if missing:
            raise DAEConfigurationError(
                "Missing mechanical power "
                f"inputs for: {sorted(missing)}"
            )

        unknown = (
            set(new_values)
            - machine_ids
        )

        if unknown:
            raise DAEConfigurationError(
                "Unknown machine IDs in "
                f"mechanical powers: "
                f"{sorted(unknown)}"
            )

        for machine_id, value in (
            new_values.items()
        ):
            if not np.isfinite(value):
                raise DAEConfigurationError(
                    "Mechanical power must "
                    "be finite."
                )

        self.mechanical_powers = new_values

    # ==================================================================
    # CONFIGURATION VALIDATION
    # ==================================================================

    def _validate_configuration(
        self,
    ) -> None:
        """Validate the complete DAE configuration."""

        machine_ids = {
            str(machine.machine_id)
            for machine
            in self.machine_system.machines
        }

        provided_ids = {
            str(machine_id)
            for machine_id
            in self.mechanical_powers
        }

        missing = (
            machine_ids
            - provided_ids
        )

        if missing:
            raise DAEConfigurationError(
                "Missing mechanical power "
                f"inputs for: {sorted(missing)}"
            )

        unknown = (
            provided_ids
            - machine_ids
        )

        if unknown:
            raise DAEConfigurationError(
                "Unknown machine IDs in "
                f"mechanical powers: "
                f"{sorted(unknown)}"
            )

        for machine_id, value in (
            self.mechanical_powers.items()
        ):
            try:
                numeric_value = float(value)

            except (
                TypeError,
                ValueError,
            ) as exc:
                raise DAEConfigurationError(
                    "Mechanical power for "
                    f"'{machine_id}' must be "
                    "numeric."
                ) from exc

            if not np.isfinite(numeric_value):
                raise DAEConfigurationError(
                    "Mechanical power for "
                    f"'{machine_id}' must be "
                    "finite."
                )

            self.mechanical_powers[
                str(machine_id)
            ] = numeric_value

    # ==================================================================
    # REQUIRED BUS VALIDATION
    # ==================================================================

    def _validate_required_buses(
        self,
        voltages: Mapping[str, complex],
    ) -> None:
        """
        Validate that every dynamic machine's bus has an algebraic
        voltage solution.
        """

        required_buses = {
            str(machine.bus_id)
            for machine
            in self.machine_system.machines
        }

        missing = (
            required_buses
            - set(voltages)
        )

        if missing:
            raise DAEAlgebraicError(
                "Network solver did not return "
                f"required machine-bus voltages: "
                f"{sorted(missing)}"
            )

    # ==================================================================
    # VALIDATION HELPERS
    # ==================================================================

    @staticmethod
    def _validate_time(
        value: float,
    ) -> float:
        """Validate simulation time."""

        try:
            value = float(value)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise DAEConfigurationError(
                "time must be numeric."
            ) from exc

        if not np.isfinite(value):
            raise DAEConfigurationError(
                "time must be finite."
            )

        return value

    @staticmethod
    def _validate_dt(
        value: float,
    ) -> float:
        """Validate a positive integration interval."""

        try:
            value = float(value)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise DAEConfigurationError(
                "dt must be numeric."
            ) from exc

        if not np.isfinite(value):
            raise DAEConfigurationError(
                "dt must be finite."
            )

        if value <= 0.0:
            raise DAEConfigurationError(
                "dt must be greater than zero."
            )

        return value


__all__ = [
    "NetworkSolver",
    "MechanicalPowerMap",
    "DAESolverError",
    "DAEConfigurationError",
    "DAEAlgebraicError",
    "DAENumericalError",
    "DAESolution",
    "DAESolver",
]
