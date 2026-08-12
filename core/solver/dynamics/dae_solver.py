```python
"""
GridForge Dynamic Algebraic Equation Solver
===========================================

Coordinates differential and algebraic equations for GridForge
dynamic simulation.

Mathematical structure
----------------------

    dx/dt = f(x, V, u, t)

    0 = g(x, V, u, t)

where:

    x
        Dynamic state vector.

    V
        Algebraic network variables, primarily bus voltages.

    u
        External/control inputs.

The DAE solver does not implement the physical equations itself.
It coordinates:

    Dynamic state
          |
          v
    MultiMachineSystem
          |
          v
    Current injections
          |
          v
    Algebraic network solver
          |
          v
    Bus voltages
          |
          v
    Machine electrical outputs
          |
          v
    Dynamic derivatives
          |
          v
    Numerical integrator
          |
          v
    Updated dynamic state

Responsibilities
----------------
- own simulation time;
- own the dynamic state vector;
- coordinate the multi-machine system;
- solve algebraic network equations;
- evaluate dynamic derivatives;
- invoke the configured numerical integrator;
- process simulation events;
- retain the latest algebraic solution;
- return a complete time-step result.

This module does NOT:
- construct Y-bus;
- modify network topology;
- implement machine equations;
- implement AVR/governor/PSS physics;
- implement breaker physics;
- implement protection logic;
- provide the public transient-stability analysis API.

The public study facade belongs in ``core/analysis``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

import numpy as np

from .events import EventManager
from .integrator import (
    DerivativeFunction,
    Integrator,
    JacobianFunction,
)
from .multimachine import MultiMachineSystem


# ======================================================================
# TYPES
# ======================================================================

ComplexVoltageMap = Mapping[
    str,
    complex,
]

PowerMap = Mapping[
    str,
    float,
]


# ======================================================================
# ALGEBRAIC SOLVER CONTRACT
# ======================================================================


class AlgebraicNetworkSolver(
    Protocol
):
    """
    Protocol for the algebraic network solver.

    The DAE solver depends only on this contract. The concrete
    implementation belongs to the appropriate GridForge network/solver
    layer.

    The algebraic solver receives machine current injections and returns
    the corresponding bus-voltage solution.
    """

    def solve(
        self,
        current_injections: ComplexVoltageMap,
        *,
        previous_voltages: ComplexVoltageMap | None = None,
        time: float = 0.0,
    ) -> ComplexVoltageMap:
        """
        Solve the algebraic network equations.
        """
        ...


# ======================================================================
# STEP RESULT
# ======================================================================


@dataclass(frozen=True)
class DAEStepResult:
    """
    Result of one DAE integration step.

    Attributes
    ----------
    time:
        Time at the end of the step [s].

    state:
        Dynamic state vector at the end of the step.

    derivative:
        Derivative evaluated at the final state.

    terminal_voltages:
        Latest algebraic network solution.

    electrical_powers:
        Machine electrical outputs.

    processed_events:
        Events executed during this step.
    """

    time: float

    state: np.ndarray

    derivative: np.ndarray

    terminal_voltages: dict[
        str,
        complex,
    ]

    electrical_powers: dict[
        str,
        tuple[float, float],
    ]

    processed_events: tuple[
        Any,
        ...,
    ] = field(
        default_factory=tuple
    )

    def __post_init__(
        self,
    ) -> None:

        object.__setattr__(
            self,
            "state",
            np.asarray(
                self.state,
                dtype=float,
            ).copy(),
        )

        object.__setattr__(
            self,
            "derivative",
            np.asarray(
                self.derivative,
                dtype=float,
            ).copy(),
        )

        object.__setattr__(
            self,
            "terminal_voltages",
            dict(
                self.terminal_voltages
            ),
        )

        object.__setattr__(
            self,
            "electrical_powers",
            dict(
                self.electrical_powers
            ),
        )

        object.__setattr__(
            self,
            "processed_events",
            tuple(
                self.processed_events
            ),
        )


# ======================================================================
# ERRORS
# ======================================================================


class DAESolverError(
    RuntimeError
):
    """Base exception for DAE solver failures."""


class DAEInitializationError(
    DAESolverError
):
    """Raised when DAE initialization fails."""


class DAEAlgebraicError(
    DAESolverError
):
    """Raised when the algebraic network solution fails."""


# ======================================================================
# DAE SOLVER
# ======================================================================


class DAESolver:
    """
    GridForge differential-algebraic equation solver.

    Parameters
    ----------
    machine_system:
        Configured ``MultiMachineSystem``.

    algebraic_solver:
        Network algebraic-equation solver implementing the
        ``AlgebraicNetworkSolver`` protocol.

    dt:
        Default integration step [s].

    integration_method:
        Numerical integration method.

        Supported:

        - ``"RK4"``
        - ``"TRAPEZOIDAL"``

    event_manager:
        Optional event manager. If omitted, a new one is created.

    Notes
    -----
    The solver accepts a machine-system object rather than a raw list of
    generators. This prevents the DAE layer from becoming coupled to
    individual machine implementations.
    """

    def __init__(
        self,
        machine_system: MultiMachineSystem,
        algebraic_solver: AlgebraicNetworkSolver,
        *,
        dt: float = 0.01,
        integration_method: str = "RK4",
        event_manager: EventManager | None = None,
    ) -> None:

        if not isinstance(
            machine_system,
            MultiMachineSystem,
        ):

            raise TypeError(
                "machine_system must be "
                "a MultiMachineSystem."
            )

        if algebraic_solver is None:

            raise ValueError(
                "algebraic_solver cannot "
                "be None."
            )

        if dt <= 0.0:

            raise ValueError(
                "dt must be greater "
                "than zero."
            )

        self.machine_system = (
            machine_system
        )

        self.algebraic_solver = (
            algebraic_solver
        )

        self.dt = float(dt)

        self.integrator = Integrator(
            method=integration_method
        )

        self.event_manager = (
            event_manager
            if event_manager is not None
            else EventManager()
        )

        self.time = 0.0

        self.state = np.empty(
            0,
            dtype=float,
        )

        self.terminal_voltages: dict[
            str,
            complex,
        ] = {}

        self.electrical_powers: dict[
            str,
            tuple[float, float],
        ] = {}

        self._initialized = False

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def initialize(
        self,
        terminal_voltages: ComplexVoltageMap,
        electrical_powers: PowerMap,
        mechanical_powers: PowerMap,
        *,
        time: float = 0.0,
    ) -> np.ndarray:
        """
        Initialize the complete dynamic state.

        Parameters
        ----------
        terminal_voltages:
            Initial machine terminal voltages.

        electrical_powers:
            Initial machine electrical active powers.

        mechanical_powers:
            Initial machine mechanical powers.

        time:
            Initial simulation time [s].

        Returns
        -------
        numpy.ndarray
            Initial global dynamic state vector.
        """

        if time < 0.0:

            raise ValueError(
                "Initial time cannot "
                "be negative."
            )

        try:

            state = (
                self.machine_system.initialize(
                    terminal_voltages=(
                        terminal_voltages
                    ),
                    electrical_powers=(
                        electrical_powers
                    ),
                    mechanical_powers=(
                        mechanical_powers
                    ),
                    time=time,
                )
            )

        except Exception as exc:

            raise DAEInitializationError(
                "Failed to initialize "
                "dynamic machine state."
            ) from exc

        state = np.asarray(
            state,
            dtype=float,
        )

        if state.ndim != 1:

            raise DAEInitializationError(
                "Machine system returned "
                "a non-vector state."
            )

        if state.size == 0:

            raise DAEInitializationError(
                "Machine system returned "
                "an empty state."
            )

        if not np.all(
            np.isfinite(state)
        ):

            raise DAEInitializationError(
                "Initial dynamic state "
                "contains non-finite "
                "values."
            )

        self.state = state.copy()

        self.time = float(time)

        self.terminal_voltages = (
            dict(
                terminal_voltages
            )
        )

        self.electrical_powers = (
            self._normalize_power_map(
                electrical_powers
            )
        )

        self._initialized = True

        return self.state.copy()

    # ==================================================================
    # DIFFERENTIAL EQUATION
    # ==================================================================

    def derivatives(
        self,
        state: np.ndarray,
        time: float,
    ) -> np.ndarray:
        """
        Evaluate the complete differential equation:

            dx/dt = f(x, V, t)

        The algebraic network is solved for the supplied dynamic state
        before machine derivatives are evaluated.

        This method is intentionally compatible with the finalized
        ``Integrator`` contract:

            derivative(x, t)
        """

        state = np.asarray(
            state,
            dtype=float,
        )

        if state.shape != (
            self.state.shape
        ):

            raise DAESolverError(
                "Derivative state shape "
                "does not match the "
                "solver state."
            )

        # --------------------------------------------------------------
        # 1. Obtain machine current injections.
        # --------------------------------------------------------------

        try:

            current_injections = (
                self.machine_system
                .current_injections(
                    state=state,
                    time=time,
                    terminal_voltages=(
                        self.terminal_voltages
                    ),
                )
            )

        except Exception as exc:

            raise DAESolverError(
                "Failed to calculate "
                "machine current "
                "injections."
            ) from exc

        # --------------------------------------------------------------
        # 2. Solve algebraic network.
        # --------------------------------------------------------------

        try:

            voltages = (
                self.algebraic_solver.solve(
                    current_injections,
                    previous_voltages=(
                        self.terminal_voltages
                    ),
                    time=time,
                )
            )

        except Exception as exc:

            raise DAEAlgebraicError(
                "Algebraic network "
                f"solution failed at "
                f"t={time:.12g} s."
            ) from exc

        voltages = dict(
            voltages
        )

        # --------------------------------------------------------------
        # 3. Calculate machine electrical
        #    outputs.
        # --------------------------------------------------------------

        try:

            electrical_outputs = (
                self.machine_system
                .electrical_outputs(
                    state=state,
                    terminal_voltages=(
                        voltages
                    ),
                    time=time,
                )
            )

        except Exception as exc:

            raise DAESolverError(
                "Failed to calculate "
                "machine electrical "
                "outputs."
            ) from exc

        # --------------------------------------------------------------
        # 4. Calculate dynamic derivatives.
        # --------------------------------------------------------------

        try:

            dx = (
                self.machine_system
                .derivatives(
                    state=state,
                    terminal_voltages=(
                        voltages
                    ),
                    electrical_outputs=(
                        electrical_outputs
                    ),
                    time=time,
                )
            )

        except Exception as exc:

            raise DAESolverError(
                "Failed to calculate "
                "dynamic derivatives."
            ) from exc

        dx = np.asarray(
            dx,
            dtype=float,
        )

        if dx.shape != (
            state.shape
        ):

            raise DAESolverError(
                "Machine-system derivative "
                "shape does not match "
                "dynamic state shape."
            )

        if not np.all(
            np.isfinite(dx)
        ):

            raise DAESolverError(
                "Dynamic derivative "
                "contains non-finite "
                "values."
            )

        return dx

    # ==================================================================
    # ALGEBRAIC SOLUTION
    # ==================================================================

    def solve_algebraic(
        self,
        state: np.ndarray | None = None,
        *,
        time: float | None = None,
    ) -> dict[
        str,
        complex,
    ]:
        """
        Solve the algebraic network equations for the supplied state.

        This method updates the solver's cached terminal voltages and
        electrical powers.
        """

        if not self._initialized:

            raise DAESolverError(
                "DAESolver must be "
                "initialized before "
                "solving the algebraic "
                "network."
            )

        if state is None:

            state = self.state

        state = np.asarray(
            state,
            dtype=float,
        )

        evaluation_time = (
            self.time
            if time is None
            else float(time)
        )

        try:

            currents = (
                self.machine_system
                .current_injections(
                    state=state,
                    time=evaluation_time,
                    terminal_voltages=(
                        self.terminal_voltages
                    ),
                )
            )

            voltages = (
                self.algebraic_solver.solve(
                    currents,
                    previous_voltages=(
                        self.terminal_voltages
                    ),
                    time=evaluation_time,
                )
            )

            voltages = dict(
                voltages
            )

            outputs = (
                self.machine_system
                .electrical_outputs(
                    state=state,
                    terminal_voltages=(
                        voltages
                    ),
                    time=evaluation_time,
                )
            )

        except Exception as exc:

            raise DAEAlgebraicError(
                "Failed to solve the "
                "algebraic network."
            ) from exc

        self.terminal_voltages = (
            voltages
        )

        self.electrical_powers = (
            self._electrical_power_map(
                outputs
            )
        )

        return dict(
            self.terminal_voltages
        )

    # ==================================================================
    # ONE TIME STEP
    # ==================================================================

    def step(
        self,
        dt: float | None = None,
    ) -> DAEStepResult:
        """
        Advance the DAE system by one time step.

        The step is event-aware. If an event occurs inside the requested
        integration interval, the step is shortened so that the event
        occurs exactly at the event boundary.
        """

        if not self._initialized:

            raise DAESolverError(
                "DAESolver must be "
                "initialized before "
                "stepping."
            )

        requested_dt = (
            self.dt
            if dt is None
            else float(dt)
        )

        if requested_dt <= 0.0:

            raise ValueError(
                "dt must be greater "
                "than zero."
            )

        start_time = (
            self.time
        )

        # --------------------------------------------------------------
        # Determine the next event boundary.
        # --------------------------------------------------------------

        step_dt = (
            self.event_manager
            .limit_step(
                start_time,
                requested_dt,
            )
        )

        if step_dt <= 0.0:

            step_dt = requested_dt

        target_time = (
            start_time
            + step_dt
        )

        # --------------------------------------------------------------
        # Cache the starting algebraic solution.
        #
        # RK4 may subsequently evaluate several intermediate states.
        # Each derivative evaluation performs its own algebraic solve.
        # --------------------------------------------------------------

        self.solve_algebraic(
            self.state,
            time=start_time,
        )

        # --------------------------------------------------------------
        # Dynamic derivative callback.
        # --------------------------------------------------------------

        derivative: DerivativeFunction = (
            self.derivatives
        )

        # --------------------------------------------------------------
        # Optional Jacobian.
        #
        # At present we deliberately do not fabricate a DAE Jacobian.
        # The trapezoidal integrator will use its finite-difference
        # fallback unless a future machine/network implementation
        # supplies one.
        # --------------------------------------------------------------

        jacobian: JacobianFunction | None = (
            None
        )

        # --------------------------------------------------------------
        # Numerical integration.
        # --------------------------------------------------------------

        try:

            new_state = (
                self.integrator.step(
                    x=self.state,
                    derivative=derivative,
                    t=start_time,
                    dt=step_dt,
                    jacobian=jacobian,
                )
            )

        except Exception as exc:

            raise DAESolverError(
                "Dynamic integration "
                f"failed at "
                f"t={start_time:.12g} s."
            ) from exc

        # --------------------------------------------------------------
        # Update state and time.
        # --------------------------------------------------------------

        self.state = np.asarray(
            new_state,
            dtype=float,
        )

        self.time = (
            target_time
        )

        # --------------------------------------------------------------
        # Solve algebraic equations at
        # the final state.
        # --------------------------------------------------------------

        self.solve_algebraic(
            self.state,
            time=self.time,
        )

        # --------------------------------------------------------------
        # Evaluate final derivative.
        # --------------------------------------------------------------

        final_derivative = (
            self.derivatives(
                self.state,
                self.time,
            )
        )

        # --------------------------------------------------------------
        # Process events exactly at the
        # completed step boundary.
        # --------------------------------------------------------------

        processed_events = (
            self.event_manager.process(
                self.time
            )
        )

        return DAEStepResult(
            time=self.time,
            state=self.state,
            derivative=final_derivative,
            terminal_voltages=(
                self.terminal_voltages
            ),
            electrical_powers=(
                self.electrical_powers
            ),
            processed_events=(
                tuple(
                    processed_events
                )
            ),
        )

    # ==================================================================
    # RESET
    # ==================================================================

    def reset(
        self,
        *,
        time: float = 0.0,
    ) -> None:
        """
        Reset solver execution state.

        Physical machine state must subsequently be initialized through
        ``initialize()``.
        """

        if time < 0.0:

            raise ValueError(
                "time cannot be negative."
            )

        self.time = float(
            time
        )

        self.state = np.empty(
            0,
            dtype=float,
        )

        self.terminal_voltages = {}

        self.electrical_powers = {}

        self._initialized = False

        self.event_manager.reset()

    # ==================================================================
    # HELPERS
    # ==================================================================

    @staticmethod
    def _normalize_power_map(
        values: PowerMap,
    ) -> dict[
        str,
        tuple[float, float],
    ]:
        """
        Normalize active-power initialization data.

        The internal result format stores:

            (P, Q)

        with Q initialized to zero when only active power is supplied.
        """

        return {
            str(machine_id): (
                float(power),
                0.0,
            )
            for machine_id, power
            in values.items()
        }

    @staticmethod
    def _electrical_power_map(
        outputs: Mapping[
            str,
            Any,
        ],
    ) -> dict[
        str,
        tuple[float, float],
    ]:
        """
        Convert machine electrical outputs into a stable result format.
        """

        result: dict[
            str,
            tuple[float, float],
        ] = {}

        for machine_id, output in (
            outputs.items()
        ):

            if hasattr(
                output,
                "active_power",
            ):

                p = float(
                    output.active_power
                )

                q = float(
                    output.reactive_power
                )

            elif isinstance(
                output,
                Mapping,
            ):

                p = float(
                    output["active_power"]
                )

                q = float(
                    output.get(
                        "reactive_power",
                        0.0,
                    )
                )

            else:

                p = float(
                    output
                )

                q = 0.0

            result[
                str(machine_id)
            ] = (
                p,
                q,
            )

        return result


__all__ = [
    "AlgebraicNetworkSolver",
    "DAEStepResult",
    "DAESolverError",
    "DAEInitializationError",
    "DAEAlgebraicError",
    "DAESolver",
]
```
