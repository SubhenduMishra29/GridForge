"""
GridForge Differential-Algebraic Equation Solver
=================================================

Time-domain coupling engine for GridForge dynamic simulation.

The dynamic system is represented by:

    dx/dt = f(x, z, u, t)

and the electrical network by:

    0 = g(x, z, u, t)

where:

    x
        Differential states.

    z
        Algebraic network variables.

    u
        External inputs / simulation conditions.

Responsibilities
----------------
- Coordinate dynamic machine models.
- Coordinate the algebraic network solver.
- Evaluate dynamic derivatives using the current algebraic solution.
- Advance differential states using the configured integrator.
- Provide a clean time-stepping interface.

This module does NOT:
- implement generator equations
- implement AVR/GOV/PSS equations
- implement network equations
- implement Y-bus construction
- manage protection logic
- own persistent network topology
- define individual simulation events

Event scheduling is handled by ``events.py`` and the higher-level
transient-stability study controller.

Important
---------
The algebraic network solver is injected into this class.

This avoids coupling the dynamic solver to a particular network
implementation and allows GridForge's existing network/solver layers
to remain authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

import numpy as np

from .integrator import (
    BaseIntegrator,
    Integrator,
)
from .machine_models import (
    MachineInputs,
)
from .multimachine import (
    MultiMachineSystem,
)
from .state_vector import (
    DynamicStateVector,
)


class AlgebraicSolverProtocol(Protocol):
    """
    Protocol required from the electrical-network algebraic solver.

    The concrete network solver may expose additional functionality,
    but it must provide a solve method compatible with this protocol.
    """

    def solve(
        self,
        injections: Mapping[str, complex],
        **kwargs: Any,
    ) -> Mapping[str, complex]:
        """
        Solve the algebraic network and return bus voltages.

        Returns
        -------
        Mapping[str, complex]
            Bus ID -> complex bus voltage [pu].
        """
        ...


class DAESolverError(RuntimeError):
    """Raised when DAE coupling or solution fails."""


@dataclass(frozen=True)
class AlgebraicSolution:
    """
    Result of one algebraic network solution.

    Parameters
    ----------
    voltages:
        Bus ID -> complex bus voltage [pu].

    currents:
        Bus ID -> complex dynamic-machine current injection [pu].

    electrical_powers:
        Machine ID -> electrical active power [pu].
    """

    voltages: Mapping[str, complex]

    currents: Mapping[str, complex]

    electrical_powers: Mapping[str, float]


class DAESolver:
    """
    Differential-algebraic coupling solver.

    Parameters
    ----------
    machine_system:
        Multi-machine dynamic system.

    algebraic_solver:
        Electrical-network algebraic solver.

    integrator:
        Numerical differential-state integrator.

    dt:
        Default simulation time step [s].
    """

    def __init__(
        self,
        machine_system: MultiMachineSystem,
        algebraic_solver: AlgebraicSolverProtocol,
        integrator: BaseIntegrator | Integrator | None = None,
        dt: float = 0.01,
    ) -> None:

        if dt <= 0.0:
            raise ValueError(
                "Time step dt must be greater than zero."
            )

        if not np.isfinite(dt):
            raise ValueError(
                "Time step dt must be finite."
            )

        self.machine_system = (
            machine_system
        )

        self.algebraic_solver = (
            algebraic_solver
        )

        self.integrator = (
            integrator
            if integrator is not None
            else Integrator("RK4")
        )

        self.dt = float(dt)

        self.time = 0.0

        self.state = (
            machine_system.create_state_vector()
        )

        self._last_algebraic_solution: (
            AlgebraicSolution | None
        ) = None

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def initialize(
        self,
        inputs: Mapping[
            str,
            MachineInputs,
        ],
    ) -> DynamicStateVector:
        """
        Initialize the dynamic state from the supplied operating point.

        Parameters
        ----------
        inputs:
            Initial machine electrical/mechanical inputs.

        Returns
        -------
        DynamicStateVector
            Initialized global dynamic state.
        """

        self.machine_system.initialize(
            self.state,
            inputs,
        )

        self.time = 0.0

        # Establish an initial algebraic solution.
        self._solve_algebraic(
            self.state.pack(),
            inputs,
            self.time,
        )

        return self.state

    # =========================================================
    # ALGEBRAIC NETWORK SOLUTION
    # =========================================================

    def solve_algebraic(
        self,
        inputs: Mapping[
            str,
            MachineInputs,
        ],
        time: float | None = None,
    ) -> AlgebraicSolution:
        """
        Solve the electrical network for the current dynamic state.
        """

        if time is None:
            time = self.time

        return self._solve_algebraic(
            self.state.pack(),
            inputs,
            time,
        )

    def _solve_algebraic(
        self,
        state: np.ndarray,
        inputs: Mapping[
            str,
            MachineInputs,
        ],
        time: float,
    ) -> AlgebraicSolution:

        del time

        injections = (
            self.machine_system.electrical_injections(
                state,
                inputs,
            )
        )

        try:
            voltages = (
                self.algebraic_solver.solve(
                    injections
                )
            )
        except Exception as exc:
            raise DAESolverError(
                "Algebraic network solution failed."
            ) from exc

        voltages = {
            bus_id: complex(
                voltage
            )
            for bus_id, voltage
            in voltages.items()
        }

        for bus_id, voltage in voltages.items():

            if not (
                np.isfinite(
                    voltage.real
                )
                and np.isfinite(
                    voltage.imag
                )
            ):
                raise DAESolverError(
                    "Algebraic solver returned "
                    f"a non-finite voltage for "
                    f"bus '{bus_id}'."
                )

        machine_inputs = (
            self._update_machine_inputs(
                inputs,
                voltages,
            )
        )

        electrical_powers = {
            machine_id:
                machine_input.electrical_power
            for machine_id, machine_input
            in machine_inputs.items()
        }

        solution = AlgebraicSolution(
            voltages=voltages,
            currents=injections,
            electrical_powers=electrical_powers,
        )

        self._last_algebraic_solution = (
            solution
        )

        return solution

    # =========================================================
    # DYNAMIC DERIVATIVE
    # =========================================================

    def derivatives(
        self,
        state: np.ndarray,
        inputs: Mapping[
            str,
            MachineInputs,
        ],
        time: float,
    ) -> np.ndarray:
        """
        Evaluate dx/dt for the complete dynamic system.

        The algebraic network is solved first, then machine inputs are
        updated from the resulting terminal voltages.
        """

        state = self._validate_state(
            state
        )

        algebraic = (
            self._solve_algebraic(
                state,
                inputs,
                time,
            )
        )

        machine_inputs = (
            self._update_machine_inputs(
                inputs,
                algebraic.voltages,
            )
        )

        return self.machine_system.derivatives(
            state=state,
            inputs=machine_inputs,
            time=time,
        )

    # =========================================================
    # TIME STEP
    # =========================================================

    def step(
        self,
        inputs: Mapping[
            str,
            MachineInputs,
        ],
        dt: float | None = None,
    ) -> DynamicStateVector:
        """
        Advance the dynamic system by one time step.

        Parameters
        ----------
        inputs:
            Current external/mechanical inputs.

        dt:
            Optional step size. If omitted, ``self.dt`` is used.

        Returns
        -------
        DynamicStateVector
            Updated global dynamic state.
        """

        step_size = (
            self.dt
            if dt is None
            else float(dt)
        )

        if step_size <= 0.0:
            raise ValueError(
                "Integration step must be greater than zero."
            )

        if not np.isfinite(
            step_size
        ):
            raise ValueError(
                "Integration step must be finite."
            )

        x = self.state.pack()

        # Capture the current time explicitly. This is important for
        # time-dependent models and event-aware simulation.
        current_time = self.time

        def derivative(
            state: np.ndarray,
            evaluation_time: float,
        ) -> np.ndarray:

            return self.derivatives(
                state=state,
                inputs=inputs,
                time=evaluation_time,
            )

        try:
            x_new = self.integrator.step(
                x=x,
                derivative=derivative,
                t=current_time,
                dt=step_size,
            )
        except Exception as exc:
            raise DAESolverError(
                "Dynamic integration failed."
            ) from exc

        self._validate_state(
            x_new
        )

        self.state.unpack(
            x_new
        )

        self.time = (
            current_time
            + step_size
        )

        # Solve once at the accepted state so that the solver retains
        # a consistent algebraic operating point.
        self._solve_algebraic(
            self.state.pack(),
            inputs,
            self.time,
        )

        return self.state

    # =========================================================
    # STATE / RESULTS
    # =========================================================

    @property
    def algebraic_solution(
        self,
    ) -> AlgebraicSolution | None:
        """
        Return the latest algebraic solution.
        """

        return self._last_algebraic_solution

    def reset(
        self,
    ) -> None:
        """
        Reset the solver time and dynamic state to initial values.
        """

        self.state = (
            self.machine_system.create_state_vector()
        )

        self.time = 0.0

        self._last_algebraic_solution = (
            None
        )

    # =========================================================
    # MACHINE INPUT COUPLING
    # =========================================================

    def _update_machine_inputs(
        self,
        inputs: Mapping[
            str,
            MachineInputs,
        ],
        voltages: Mapping[str, complex],
    ) -> dict[
        str,
        MachineInputs,
    ]:
        """
        Update terminal-voltage-dependent machine inputs.

        The supplied Mapping is not modified.
        """

        updated: dict[
            str,
            MachineInputs,
        ] = {}

        for model in (
            self.machine_system.models.models
        ):

            machine_id = (
                model.machine_id
            )

            if machine_id not in inputs:
                raise DAESolverError(
                    "Missing machine input for "
                    f"'{machine_id}'."
                )

            if model.bus_id not in voltages:
                raise DAESolverError(
                    "Algebraic solution does not "
                    f"contain machine bus "
                    f"'{model.bus_id}'."
                )

            old = inputs[
                machine_id
            ]

            terminal_voltage = complex(
                voltages[
                    model.bus_id
                ]
            )

            electrical_power = (
                old.electrical_power
            )

            if old.terminal_current is not None:

                electrical_power = (
                    terminal_voltage
                    * np.conj(
                        old.terminal_current
                    )
                ).real

            updated[
                machine_id
            ] = MachineInputs(
                terminal_voltage=terminal_voltage,
                electrical_power=float(
                    electrical_power
                ),
                mechanical_power=(
                    old.mechanical_power
                ),
                terminal_current=(
                    old.terminal_current
                ),
                electrical_reactive_power=(
                    old.electrical_reactive_power
                ),
            )

        return updated

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_state(
        self,
        state: np.ndarray,
    ) -> np.ndarray:

        state = np.asarray(
            state,
            dtype=float,
        )

        if state.ndim != 1:
            raise DAESolverError(
                "Dynamic state must be "
                "one-dimensional."
            )

        if state.size != (
            self.machine_system.size
        ):
            raise DAESolverError(
                "Dynamic state size mismatch: "
                f"expected "
                f"{self.machine_system.size}, "
                f"received {state.size}."
            )

        if not np.all(
            np.isfinite(state)
        ):
            raise DAESolverError(
                "Dynamic state contains "
                "non-finite values."
            )

        return state
