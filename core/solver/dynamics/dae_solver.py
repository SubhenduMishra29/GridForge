```python
"""
GridForge Dynamic Algebraic Equation Solver
===========================================

Low-level DAE coordinator for transient dynamic simulation.

Mathematical formulation
------------------------

The dynamic system is represented as:

    dx/dt = f(x, V, u, t)

and the electrical network as:

    0 = g(x, V, u, t)

where:

    x = dynamic machine state vector
    V = algebraic network variables represented here by bus voltages
    u = externally supplied dynamic inputs

Responsibilities
----------------
- coordinate the differential and algebraic portions of the system;
- request network/algebraic solutions;
- evaluate multi-machine derivatives;
- perform one numerical integration step;
- expose a clean low-level DAE interface.

Non-responsibilities
--------------------
This module does NOT:

- implement machine equations;
- implement the swing equation;
- implement AVR;
- implement governor;
- implement PSS;
- implement protection;
- implement event actions;
- construct Y-bus;
- perform power-flow formulation;
- own the complete transient-stability study;
- own simulation result storage.

The actual machine physics are delegated to ``MultiMachineSystem``.

The numerical method is delegated to ``Integrator``.

The algebraic network solution is injected through ``network_solver``.

Architecture
------------

    DAESolver
        │
        ├── MultiMachineSystem
        │       └── machine_models
        │               └── swing_equation
        │
        ├── network_solver
        │
        └── Integrator

This keeps the DAE solver independent of the concrete network
implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

import numpy as np

from .integrator import (
    Integrator,
)
from .multimachine import (
    MultiMachineSystem,
)


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


class DAESolverError(
    RuntimeError
):
    """Base exception for DAE-solver errors."""


class DAEConfigurationError(
    DAESolverError
):
    """Raised when the DAE solver is incorrectly configured."""


class DAEAlgebraicError(
    DAESolverError
):
    """Raised when the algebraic network solution fails."""


class DAENumericalError(
    DAESolverError
):
    """Raised when numerical integration fails."""


# ======================================================================
# DAE SOLUTION
# ======================================================================


@dataclass(frozen=True)
class DAESolution:
    """
    Result of one DAE evaluation.

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

    terminal_voltages: dict[
        str,
        complex,
    ]

    derivatives: np.ndarray

    time: float

    def __post_init__(
        self,
    ) -> None:

        state = np.asarray(
            self.state,
            dtype=float,
        ).copy()

        derivatives = np.asarray(
            self.derivatives,
            dtype=float,
        ).copy()

        state.setflags(
            write=False
        )

        derivatives.setflags(
            write=False
        )

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
            dict(
                self.terminal_voltages
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
        MultiMachineSystem containing the dynamic machine models.

    network_solver:
        Algebraic network solution callback.

        Required signature:

            network_solver(state, time)
                -> {bus_id: complex_voltage}

    mechanical_powers:
        External mechanical power input for each machine.

    integrator:
        Numerical integration interface.

    Notes
    -----
    The solver does not own the network.

    It only requests the algebraic solution required by the dynamic
    equations.

    Mechanical power is also deliberately supplied from outside the
    machine model. This leaves room for future turbine/governor/control
    plugins without changing the DAE core.
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
                "machine_system must "
                "be a MultiMachineSystem."
            )

        if not callable(
            network_solver
        ):

            raise DAEConfigurationError(
                "network_solver must "
                "be callable."
            )

        if not isinstance(
            integrator,
            Integrator,
        ):

            raise DAEConfigurationError(
                "integrator must be "
                "an Integrator instance."
            )

        self.machine_system = (
            machine_system
        )

        self.network_solver = (
            network_solver
        )

        self.mechanical_powers = dict(
            mechanical_powers
        )

        self.integrator = (
            integrator
        )

        self._validate_configuration()

    # ==================================================================
    # PROPERTIES
    # ==================================================================

    @property
    def state_size(
        self,
    ) -> int:
        """Return total number of dynamic states."""

        return (
            self.machine_system.state_size
        )

    @property
    def machines(
        self,
    ):
        """Return registered dynamic machines."""

        return (
            self.machine_system.machines
        )

    # ==================================================================
    # ALGEBRAIC SOLUTION
    # ==================================================================

    def solve_algebraic(
        self,
        state: np.ndarray,
        time: float,
    ) -> dict[
        str,
        complex,
    ]:
        """
        Solve the algebraic network for a dynamic state.

        Returns
        -------
        dict
            Bus terminal voltages.
        """

        state = (
            self.machine_system.validate_global_state(
                state
            )
        )

        time = self._validate_time(
            time
        )

        try:

            result = (
                self.network_solver(
                    state,
                    time,
                )
            )

        except Exception as exc:

            raise DAEAlgebraicError(
                "Algebraic network "
                f"solution failed at "
                f"t={time:.12g} s."
            ) from exc

        if result is None:

            raise DAEAlgebraicError(
                "network_solver returned "
                "None."
            )

        try:

            voltages = {
                str(bus_id): complex(
                    voltage
                )
                for (
                    bus_id,
                    voltage
                ) in result.items()
            }

        except Exception as exc:

            raise DAEAlgebraicError(
                "Invalid algebraic "
                "network-solver result."
            ) from exc

        for (
            bus_id,
            voltage,
        ) in voltages.items():

            if not (
                np.isfinite(
                    voltage.real
                )
                and np.isfinite(
                    voltage.imag
                )
            ):

                raise DAEAlgebraicError(
                    "Network solver "
                    f"returned non-finite "
                    f"voltage for bus "
                    f"'{bus_id}'."
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
        Evaluate dx/dt for the complete DAE system.

        The algebraic network is solved first and the resulting terminal
        voltages are supplied to the multi-machine dynamic model.
        """

        state = (
            self.machine_system.validate_global_state(
                state
            )
        )

        time = self._validate_time(
            time
        )

        voltages = (
            self.solve_algebraic(
                state,
                time,
            )
        )

        try:

            derivatives = (
                self.machine_system.derivatives(
                    state=state,
                    terminal_voltages=(
                        voltages
                    ),
                    mechanical_powers=(
                        self.mechanical_powers
                    ),
                    time=time,
                )
            )

        except Exception as exc:

            raise DAENumericalError(
                "Dynamic derivative "
                f"evaluation failed at "
                f"t={time:.12g} s."
            ) from exc

        derivatives = np.asarray(
            derivatives,
            dtype=float,
        )

        if derivatives.shape != (
            state.shape
        ):

            raise DAENumericalError(
                "Dynamic derivative "
                "shape does not match "
                "the dynamic state."
            )

        if not np.all(
            np.isfinite(
                derivatives
            )
        ):

            raise DAENumericalError(
                "Dynamic derivative "
                "contains non-finite "
                "values."
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

        This is useful when the caller requires both terminal voltages
        and derivatives from the same state.
        """

        state = (
            self.machine_system.validate_global_state(
                state
            )
        )

        time = self._validate_time(
            time
        )

        voltages = (
            self.solve_algebraic(
                state,
                time,
            )
        )

        try:

            derivatives = (
                self.machine_system.derivatives(
                    state=state,
                    terminal_voltages=(
                        voltages
                    ),
                    mechanical_powers=(
                        self.mechanical_powers
                    ),
                    time=time,
                )
            )

        except Exception as exc:

            raise DAENumericalError(
                "Dynamic derivative "
                f"evaluation failed at "
                f"t={time:.12g} s."
            ) from exc

        derivatives = np.asarray(
            derivatives,
            dtype=float,
        )

        if derivatives.shape != (
            state.shape
        ):

            raise DAENumericalError(
                "Derivative/state "
                "dimension mismatch."
            )

        if not np.all(
            np.isfinite(
                derivatives
            )
        ):

            raise DAENumericalError(
                "Derivative vector "
                "contains non-finite "
                "values."
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

        Parameters
        ----------
        state:
            Current global dynamic state.

        time:
            Current simulation time.

        dt:
            Integration interval.

        Returns
        -------
        DAESolution
            The new state together with the algebraic solution and
            derivative evaluated at the new state.

        Notes
        -----
        For RK4, the network is solved at each intermediate dynamic
        state through the derivative callback.

        The numerical integration algorithm remains entirely inside
        ``Integrator``.
        """

        state = (
            self.machine_system.validate_global_state(
                state
            )
        )

        time = self._validate_time(
            time
        )

        dt = self._validate_dt(
            dt
        )

        def derivative(
            intermediate_state: np.ndarray,
        ) -> np.ndarray:

            return self.derivatives(
                intermediate_state,
                time,
            )

        try:

            new_state = (
                self.integrator.step(
                    state,
                    derivative,
                    dt,
                )
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

        new_time = (
            time + dt
        )

        # Evaluate the algebraic system at the NEW state.
        solution = self.evaluate(
            state=new_state,
            time=new_time,
        )

        return solution

    # ==================================================================
    # INPUT UPDATE
    # ==================================================================

    def set_mechanical_power(
        self,
        machine_id: str,
        value: float,
    ) -> None:
        """
        Update the external mechanical-power input for one machine.

        This is intentionally an external input rather than a machine
        state.

        Future governor/turbine models may call this interface.
        """

        machine_id = str(
            machine_id
        )

        if machine_id not in {
            machine.machine_id
            for machine
            in self.machine_system.machines
        }:

            raise DAEConfigurationError(
                f"Unknown machine "
                f"'{machine_id}'."
            )

        try:

            numeric_value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise DAEConfigurationError(
                "Mechanical power must "
                "be numeric."
            ) from exc

        if not np.isfinite(
            numeric_value
        ):

            raise DAEConfigurationError(
                "Mechanical power must "
                "be finite."
            )

        self.mechanical_powers[
            machine_id
        ] = numeric_value

    def set_mechanical_powers(
        self,
        values: MechanicalPowerMap,
    ) -> None:
        """
        Replace the external mechanical-power inputs.
        """

        new_values = dict(
            values
        )

        machine_ids = {
            machine.machine_id
            for machine
            in self.machine_system.machines
        }

        missing = (
            machine_ids
            - set(new_values)
        )

        if missing:

            raise DAEConfigurationError(
                "Missing mechanical "
                f"power inputs for: "
                f"{sorted(missing)}"
            )

        for (
            machine_id,
            value,
        ) in new_values.items():

            try:

                numeric_value = float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise DAEConfigurationError(
                    f"Mechanical power "
                    f"for '{machine_id}' "
                    "must be numeric."
                ) from exc

            if not np.isfinite(
                numeric_value
            ):

                raise DAEConfigurationError(
                    f"Mechanical power "
                    f"for '{machine_id}' "
                    "must be finite."
                )

        self.mechanical_powers = (
            new_values
        )

    # ==================================================================
    # REQUIRED-BUS VALIDATION
    # ==================================================================

    def _validate_required_buses(
        self,
        voltages: Mapping[
            str,
            complex,
        ],
    ) -> None:
        """
        Verify that every machine bus has an algebraic voltage.
        """

        missing = []

        for machine in (
            self.machine_system.machines
        ):

            if machine.bus_id not in (
                voltages
            ):

                missing.append(
                    machine.bus_id
                )

        if missing:

            raise DAEAlgebraicError(
                "Algebraic network "
                "solution is missing "
                f"machine-bus voltages: "
                f"{sorted(set(missing))}"
            )

    # ==================================================================
    # CONFIGURATION VALIDATION
    # ==================================================================

    def _validate_configuration(
        self,
    ) -> None:
        """
        Validate the complete DAE configuration.
        """

        if (
            self.machine_system.machine_count
            == 0
        ):

            raise DAEConfigurationError(
                "At least one dynamic "
                "machine is required."
            )

        machine_ids = {
            machine.machine_id
            for machine
            in self.machine_system.machines
        }

        supplied_ids = set(
            self.mechanical_powers
        )

        missing = (
            machine_ids
            - supplied_ids
        )

        if missing:

            raise DAEConfigurationError(
                "Missing mechanical "
                f"power inputs for: "
                f"{sorted(missing)}"
            )

        for (
            machine_id,
            value,
        ) in self.mechanical_powers.items():

            try:

                numeric_value = float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise DAEConfigurationError(
                    f"Mechanical power "
                    f"for '{machine_id}' "
                    "must be numeric."
                ) from exc

            if not np.isfinite(
                numeric_value
            ):

                raise DAEConfigurationError(
                    f"Mechanical power "
                    f"for '{machine_id}' "
                    "must be finite."
                )

    # ==================================================================
    # VALIDATION HELPERS
    # ==================================================================

    @staticmethod
    def _validate_time(
        time: float,
    ) -> float:

        try:

            value = float(
                time
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise DAEConfigurationError(
                "Simulation time must "
                "be numeric."
            ) from exc

        if not np.isfinite(
            value
        ):

            raise DAEConfigurationError(
                "Simulation time must "
                "be finite."
            )

        return value

    @staticmethod
    def _validate_dt(
        dt: float,
    ) -> float:

        try:

            value = float(
                dt
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise DAEConfigurationError(
                "Integration step must "
                "be numeric."
            ) from exc

        if (
            not np.isfinite(value)
            or value <= 0.0
        ):

            raise DAEConfigurationError(
                "Integration step must "
                "be finite and greater "
                "than zero."
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
```
