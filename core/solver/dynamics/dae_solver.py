```python
"""
GridForge Dynamic Algebraic Equation Solver
===========================================

Coordinates the differential and algebraic parts of GridForge
time-domain simulation.

Mathematical structure
----------------------

Differential equations:

    dx/dt = f(x, z, u, t)

Algebraic equations:

    0 = g(x, z, u, t)

where:

    x
        Dynamic state vector.

    z
        Algebraic network variables.

    u
        External inputs / controls.

The DAE solver coordinates:

    DynamicMachineSystem
            ↓
    machine electrical injections
            ↓
    AlgebraicNetworkSolver
            ↓
    terminal voltages
            ↓
    machine electrical outputs
            ↓
    dynamic derivatives
            ↓
    Integrator
            ↓
    updated dynamic state

Architectural responsibilities
-------------------------------
This module:

- owns the simulation dynamic state;
- couples dynamic machines to the algebraic network;
- evaluates machine derivatives;
- invokes the numerical integrator;
- provides one simulation time-step operation;
- optionally processes scheduled events.

This module does NOT:

- implement machine physics;
- implement AVR equations;
- implement governor equations;
- implement PSS equations;
- construct Y-bus;
- implement topology;
- directly manipulate GUI state;
- replace the GridForge network layer.

Dependency injection
--------------------
The algebraic network solver is supplied to this class. This keeps
the dynamics layer independent from a particular network-solver
implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

import numpy as np

from .events import EventManager
from .integrator import Integrator
from .multimachine import MultiMachineSystem


# ======================================================================
# NETWORK SOLVER CONTRACT
# ======================================================================


class AlgebraicNetworkSolverProtocol(
    Protocol
):
    """
    Protocol for the algebraic network solver used by DAESolver.

    The actual GridForge implementation may provide additional
    functionality, but it must provide a method capable of solving
    the algebraic network equations from machine injections.
    """

    def solve(
        self,
        current_injections: Mapping[
            str,
            complex,
        ],
        *,
        previous_voltages: Mapping[
            str,
            complex,
        ]
        | None = None,
        time: float = 0.0,
    ) -> Mapping[
        str,
        complex,
    ]:
        """
        Solve the algebraic network and return bus voltages.
        """
        ...


# ======================================================================
# SIMULATION RESULT
# ======================================================================


@dataclass(frozen=True)
class DAEStepResult:
    """
    Result returned by one DAE simulation step.
    """

    time: float

    state: np.ndarray

    terminal_voltages: dict[
        str,
        complex,
    ]

    electrical_powers: dict[
        str,
        tuple[float, float],
    ]

    processed_events: tuple[Any, ...]


# ======================================================================
# DAE ERROR
# ======================================================================


class DAEError(RuntimeError):
    """Raised when the DAE simulation cannot proceed."""


# ======================================================================
# DAE SOLVER
# ======================================================================


class DAESolver:
    """
    Differential-algebraic simulation coordinator.

    Parameters
    ----------
    machines:
        MultiMachineSystem containing the dynamic machine models.

    network_solver:
        Algebraic network solver implementing
        AlgebraicNetworkSolverProtocol.

    integrator:
        GridForge Integrator instance.

    dt:
        Default simulation time step [s].

    event_manager:
        Optional event manager.

    Notes
    -----
    The DAE solver owns the global dynamic state and simulation time,
    but does not own the physical definitions of generators,
    networks, faults, breakers, or controllers.
    """

    def __init__(
        self,
        machines: MultiMachineSystem,
        network_solver:
            AlgebraicNetworkSolverProtocol,
        integrator: Integrator | None = None,
        dt: float = 0.01,
        event_manager:
            EventManager | None = None,
    ) -> None:

        if not isinstance(
            machines,
            MultiMachineSystem,
        ):
            raise TypeError(
                "machines must be a "
                "MultiMachineSystem."
            )

        if dt <= 0.0:
            raise ValueError(
                "dt must be greater "
                "than zero."
            )

        self.machines = machines

        self.network_solver = (
            network_solver
        )

        self.integrator = (
            integrator
            if integrator is not None
            else Integrator(
                method="RK4"
            )
        )

        self.dt = float(dt)

        self.event_manager = (
            event_manager
            if event_manager is not None
            else EventManager()
        )

        self.time = 0.0

        self.state = (
            self.machines.state_vector.values.copy()
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
        terminal_voltages: Mapping[
            str,
            complex,
        ],
        electrical_powers: Mapping[
            str,
            float,
        ],
        mechanical_powers: Mapping[
            str,
            float,
        ],
        *,
        time: float = 0.0,
    ) -> np.ndarray:
        """
        Initialize the dynamic simulation.

        Parameters
        ----------
        terminal_voltages:
            Initial machine-terminal bus voltages.

        electrical_powers:
            Initial machine electrical active powers.

        mechanical_powers:
            Initial machine mechanical powers.

        time:
            Initial simulation time.

        Returns
        -------
        numpy.ndarray
            Initialized dynamic state vector.
        """

        if time < 0.0:
            raise ValueError(
                "Initial time cannot "
                "be negative."
            )

        self.state = (
            self.machines.initialize(
                terminal_voltages=(
                    terminal_voltages
                ),
                electrical_powers=(
                    electrical_powers
                ),
                mechanical_powers=(
                    mechanical_powers
                ),
            )
        )

        self.time = float(
            time
        )

        self.terminal_voltages = {
            bus_id: complex(voltage)
            for bus_id, voltage
            in terminal_voltages.items()
        }

        self.electrical_powers = (
            self.machines.electrical_powers(
                self.state,
                self.terminal_voltages,
            )
        )

        self._initialized = True

        return self.state.copy()

    # ==================================================================
    # STATE ACCESS
    # ==================================================================

    def get_state(
        self,
    ) -> np.ndarray:
        """
        Return a copy of the current dynamic state.
        """

        return self.state.copy()

    def set_state(
        self,
        state: np.ndarray,
    ) -> None:
        """
        Replace the current dynamic state.

        Intended for controlled solver operations such as
        predictor/corrector workflows and restart handling.
        """

        state_array = (
            np.asarray(
                state,
                dtype=float,
            )
        )

        if state_array.ndim != 1:
            raise DAEError(
                "Dynamic state must be "
                "one-dimensional."
            )

        if state_array.size != (
            self.machines.size
        ):
            raise DAEError(
                "Dynamic state size mismatch: "
                f"expected "
                f"{self.machines.size}, "
                f"received "
                f"{state_array.size}."
            )

        if not np.all(
            np.isfinite(
                state_array
            )
        ):
            raise DAEError(
                "Dynamic state contains "
                "non-finite values."
            )

        self.state = (
            state_array.copy()
        )

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
        Solve the algebraic network for a dynamic state.

        Parameters
        ----------
        state:
            Dynamic state to evaluate. If omitted, current state is
            used.

        time:
            Evaluation time. If omitted, current simulation time is
            used.

        Returns
        -------
        dict
            bus_id -> terminal voltage.
        """

        if not self._initialized:
            raise DAEError(
                "DAESolver must be initialized "
                "before solving the algebraic "
                "network."
            )

        x = (
            self.state
            if state is None
            else np.asarray(
                state,
                dtype=float,
            )
        )

        evaluation_time = (
            self.time
            if time is None
            else float(time)
        )

        voltages = (
            self.terminal_voltages
        )

        injections = (
            self.machines.current_injections(
                x,
                voltages,
            )
        )

        try:

            solved_voltages = (
                self.network_solver.solve(
                    injections,
                    previous_voltages=(
                        voltages
                    ),
                    time=evaluation_time,
                )
            )

        except TypeError:

            # Compatibility with simpler network-solver interfaces.
            solved_voltages = (
                self.network_solver.solve(
                    injections
                )
            )

        result = {
            bus_id: complex(voltage)
            for bus_id, voltage
            in solved_voltages.items()
        }

        if not result:
            raise DAEError(
                "Algebraic network solver "
                "returned no bus voltages."
            )

        if not all(
            np.isfinite(
                voltage.real
            )
            and np.isfinite(
                voltage.imag
            )
            for voltage
            in result.values()
        ):
            raise DAEError(
                "Algebraic network solver "
                "returned non-finite "
                "voltages."
            )

        return result

    # ==================================================================
    # DERIVATIVE EVALUATION
    # ==================================================================

    def derivatives(
        self,
        state: np.ndarray,
        time: float,
    ) -> np.ndarray:
        """
        Evaluate dx/dt for a dynamic state.

        The algebraic network is solved first, followed by machine
        electrical-output evaluation and dynamic-equation evaluation.
        """

        if not self._initialized:
            raise DAEError(
                "DAESolver must be initialized "
                "before evaluating derivatives."
            )

        x = np.asarray(
            state,
            dtype=float,
        )

        if x.ndim != 1:
            raise DAEError(
                "Dynamic state must be "
                "one-dimensional."
            )

        if x.size != (
            self.machines.size
        ):
            raise DAEError(
                "Dynamic state size mismatch."
            )

        # --------------------------------------------------------------
        # 1. Algebraic network
        # --------------------------------------------------------------

        voltages = (
            self.solve_algebraic(
                x,
                time=time,
            )
        )

        # --------------------------------------------------------------
        # 2. Machine electrical outputs
        # --------------------------------------------------------------

        outputs = (
            self.machines.electrical_outputs(
                x,
                voltages,
            )
        )

        # --------------------------------------------------------------
        # 3. Construct machine inputs
        # --------------------------------------------------------------

        machine_inputs = {}

        for model in self.machines:

            machine_id = (
                model.machine_id
            )

            output = outputs[
                machine_id
            ]

            machine_inputs[
                machine_id
            ] = model.build_inputs(
                terminal_voltage=(
                    voltages[
                        model.bus_id
                    ]
                ),
                electrical_output=output,
                time=time,
            )

        # --------------------------------------------------------------
        # 4. Dynamic equations
        # --------------------------------------------------------------

        dx = (
            self.machines.derivatives(
                x,
                machine_inputs,
                time,
            )
        )

        if not np.all(
            np.isfinite(dx)
        ):
            raise DAEError(
                "Dynamic derivative vector "
                "contains non-finite values."
            )

        return dx

    # ==================================================================
    # STEP
    # ==================================================================

    def step(
        self,
        dt: float | None = None,
    ) -> DAEStepResult:
        """
        Advance the DAE simulation by one time step.

        Event boundaries are respected. If an event occurs before the
        requested end time, the integration step is shortened to reach
        that event exactly.

        Parameters
        ----------
        dt:
            Optional step size. Defaults to the solver's configured dt.

        Returns
        -------
        DAEStepResult
            State and algebraic results after the step.
        """

        if not self._initialized:
            raise DAEError(
                "DAESolver must be initialized "
                "before stepping."
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

        target_time = (
            self.time
            + requested_dt
        )

        # --------------------------------------------------------------
        # Respect the next event boundary.
        # --------------------------------------------------------------

        next_event_time = (
            self.event_manager.next_event_time(
                self.time
            )
        )

        if (
            next_event_time is not None
            and next_event_time
            > self.time
            and next_event_time
            < target_time
        ):

            target_time = (
                next_event_time
            )

        actual_dt = (
            target_time
            - self.time
        )

        processed_events: tuple[
            Any,
            ...
        ] = ()

        # --------------------------------------------------------------
        # Process events exactly at current time.
        # --------------------------------------------------------------

        due_now = (
            self.event_manager.due_events(
                self.time
            )
        )

        if due_now:

            processed_events = (
                self.event_manager.process(
                    self.time
                )
            )

            # Topology/control changes may have altered the algebraic
            # system, so discard the previous terminal-voltage cache.
            self.terminal_voltages = {}

            if actual_dt <= (
                self.event_manager.time_tolerance
            ):

                return self._result(
                    processed_events
                )

        # --------------------------------------------------------------
        # Integrate dynamic state.
        # --------------------------------------------------------------

        def derivative(
            x: np.ndarray,
            t: float,
        ) -> np.ndarray:

            return self.derivatives(
                x,
                t,
            )

        self.state = (
            self.integrator.step(
                x=self.state,
                derivative=derivative,
                t=self.time,
                dt=actual_dt,
            )
        )

        self.time = (
            self.time
            + actual_dt
        )

        # --------------------------------------------------------------
        # Solve final algebraic state.
        # --------------------------------------------------------------

        self.terminal_voltages = (
            self.solve_algebraic(
                self.state,
                time=self.time,
            )
        )

        self.electrical_powers = (
            self.machines.electrical_powers(
                self.state,
                self.terminal_voltages,
            )
        )

        # --------------------------------------------------------------
        # Process events exactly at new time.
        # --------------------------------------------------------------

        end_events = (
            self.event_manager.due_events(
                self.time
            )
        )

        if end_events:

            newly_processed = (
                self.event_manager.process(
                    self.time
                )
            )

            processed_events = (
                processed_events
                + newly_processed
            )

        return self._result(
            processed_events
        )

    # ==================================================================
    # INTERNAL RESULT
    # ==================================================================

    def _result(
        self,
        processed_events: tuple[
            Any,
            ...
        ],
    ) -> DAEStepResult:

        return DAEStepResult(
            time=float(
                self.time
            ),
            state=self.state.copy(),
            terminal_voltages=dict(
                self.terminal_voltages
            ),
            electrical_powers=dict(
                self.electrical_powers
            ),
            processed_events=(
                processed_events
            ),
        )


__all__ = [
    "AlgebraicNetworkSolverProtocol",
    "DAEStepResult",
    "DAEError",
    "DAESolver",
]
```
