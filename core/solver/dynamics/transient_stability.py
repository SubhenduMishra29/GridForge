```python
"""
GridForge Transient Stability Solver
====================================

Solver-level engine for time-domain transient-stability simulation.

Purpose
-------
Coordinates a transient-stability study using the GridForge dynamic
simulation stack.

Architecture
------------

    TransientStabilitySolver
              |
              v
          DAESolver
          /       \
         v         v
 MultiMachine   Network Solver
    System
         |
         v
 Dynamic Machine Models

Responsibilities
----------------
This module:

- configures a transient-stability simulation;
- initializes the dynamic solver;
- advances simulation time;
- respects scheduled event boundaries;
- collects time-domain results;
- provides a solver-level result object.

This module does NOT:

- implement swing equations;
- implement machine models;
- implement AVR/Governor/PSS equations;
- implement numerical integration;
- solve Y-bus directly;
- implement network topology;
- provide the public study API.

The public study facade belongs in the GridForge analysis layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np

from .dae_solver import (
    DAESolver,
    DAEStepResult,
)


# ======================================================================
# ERRORS
# ======================================================================


class TransientStabilityError(
    RuntimeError
):
    """Raised when a transient-stability simulation fails."""


# ======================================================================
# TIME-DOMAIN RESULT
# ======================================================================


@dataclass
class TransientStabilityResult:
    """
    Time-domain results from a transient-stability simulation.

    Attributes
    ----------
    time:
        Simulation time samples [s].

    states:
        Dynamic state vector at every recorded sample.

    terminal_voltages:
        Bus terminal voltages for every recorded sample.

    electrical_powers:
        Machine electrical powers for every recorded sample.

    events:
        Events processed during the simulation.
    """

    time: np.ndarray

    states: np.ndarray

    terminal_voltages: list[
        dict[str, complex]
    ] = field(
        default_factory=list
    )

    electrical_powers: list[
        dict[
            str,
            tuple[float, float],
        ]
    ] = field(
        default_factory=list
    )

    events: list[Any] = field(
        default_factory=list
    )

    @property
    def final_time(
        self,
    ) -> float:
        """Return the final simulated time."""

        if self.time.size == 0:
            return 0.0

        return float(
            self.time[-1]
        )

    @property
    def final_state(
        self,
    ) -> np.ndarray:
        """Return the final dynamic state."""

        if self.states.size == 0:
            return np.empty(
                0,
                dtype=float,
            )

        return self.states[-1].copy()

    @property
    def number_of_steps(
        self,
    ) -> int:
        """Return the number of recorded time intervals."""

        return max(
            0,
            self.time.size - 1,
        )

    @property
    def number_of_events(
        self,
    ) -> int:
        """Return the number of processed events."""

        return len(
            self.events
        )


# ======================================================================
# SOLVER
# ======================================================================


class TransientStabilitySolver:
    """
    Solver-level transient-stability simulation engine.

    Parameters
    ----------
    dae_solver:
        Configured GridForge DAESolver.

    start_time:
        Simulation start time [s].

    end_time:
        Simulation end time [s].

    dt:
        Default simulation step [s].

    Notes
    -----
    The DAE solver must already contain the configured dynamic machine
    system, algebraic network solver, integrator, and event manager.
    """

    def __init__(
        self,
        dae_solver: DAESolver,
        *,
        start_time: float = 0.0,
        end_time: float = 10.0,
        dt: float | None = None,
    ) -> None:

        if not isinstance(
            dae_solver,
            DAESolver,
        ):
            raise TypeError(
                "dae_solver must be a "
                "DAESolver instance."
            )

        if start_time < 0.0:
            raise ValueError(
                "start_time cannot be negative."
            )

        if end_time <= start_time:
            raise ValueError(
                "end_time must be greater "
                "than start_time."
            )

        if dt is not None and dt <= 0.0:
            raise ValueError(
                "dt must be greater "
                "than zero."
            )

        self.dae_solver = dae_solver

        self.start_time = float(
            start_time
        )

        self.end_time = float(
            end_time
        )

        self.dt = (
            dae_solver.dt
            if dt is None
            else float(dt)
        )

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
    ) -> np.ndarray:
        """
        Initialize the transient-stability simulation.

        Returns
        -------
        numpy.ndarray
            Initial dynamic state vector.
        """

        return self.dae_solver.initialize(
            terminal_voltages=(
                terminal_voltages
            ),
            electrical_powers=(
                electrical_powers
            ),
            mechanical_powers=(
                mechanical_powers
            ),
            time=self.start_time,
        )

    # ==================================================================
    # RUN
    # ==================================================================

    def run(
        self,
        *,
        record_initial: bool = True,
    ) -> TransientStabilityResult:
        """
        Run the transient-stability simulation.

        Parameters
        ----------
        record_initial:
            If True, record the initial state at the beginning of the
            result.

        Returns
        -------
        TransientStabilityResult
            Complete time-domain simulation result.

        Raises
        ------
        TransientStabilityError
            If the solver has not been initialized or simulation
            progress becomes invalid.
        """

        if not self.dae_solver._initialized:
            raise TransientStabilityError(
                "DAESolver must be initialized "
                "before running the transient-"
                "stability simulation."
            )

        # --------------------------------------------------------------
        # Ensure the solver starts at the requested time.
        # --------------------------------------------------------------

        if abs(
            self.dae_solver.time
            - self.start_time
        ) > 1e-9:

            raise TransientStabilityError(
                "DAESolver time does not match "
                "the configured simulation "
                "start_time."
            )

        times: list[float] = []

        states: list[
            np.ndarray
        ] = []

        voltages: list[
            dict[str, complex]
        ] = []

        powers: list[
            dict[
                str,
                tuple[float, float],
            ]
        ] = []

        events: list[Any] = []

        # --------------------------------------------------------------
        # Initial sample
        # --------------------------------------------------------------

        if record_initial:

            self._record_sample(
                times=times,
                states=states,
                voltages=voltages,
                powers=powers,
            )

        # --------------------------------------------------------------
        # Time-domain simulation
        # --------------------------------------------------------------

        while (
            self.dae_solver.time
            < self.end_time
            - self.dae_solver.event_manager
            .time_tolerance
        ):

            remaining = (
                self.end_time
                - self.dae_solver.time
            )

            step_dt = min(
                self.dt,
                remaining,
            )

            if step_dt <= 0.0:
                break

            previous_time = (
                self.dae_solver.time
            )

            try:

                result = (
                    self.dae_solver.step(
                        dt=step_dt
                    )
                )

            except Exception as exc:

                raise TransientStabilityError(
                    "Transient-stability "
                    f"simulation failed at "
                    f"t={previous_time:.9g} s."
                ) from exc

            if (
                result.time
                <= previous_time
            ):
                raise TransientStabilityError(
                    "Simulation time failed "
                    "to advance."
                )

            if (
                result.time
                > self.end_time
                + self.dae_solver
                .event_manager
                .time_tolerance
            ):
                raise TransientStabilityError(
                    "Simulation advanced "
                    "beyond end_time."
                )

            # ----------------------------------------------------------
            # Record sample
            # ----------------------------------------------------------

            self._record_result(
                result=result,
                times=times,
                states=states,
                voltages=voltages,
                powers=powers,
                events=events,
            )

        # --------------------------------------------------------------
        # Assemble result
        # --------------------------------------------------------------

        return self._build_result(
            times=times,
            states=states,
            voltages=voltages,
            powers=powers,
            events=events,
        )

    # ==================================================================
    # SINGLE STEP
    # ==================================================================

    def step(
        self,
        dt: float | None = None,
    ) -> DAEStepResult:
        """
        Execute one solver step.

        This method is useful for interactive simulation, debugging,
        and future real-time/co-simulation workflows.
        """

        step_dt = (
            self.dt
            if dt is None
            else float(dt)
        )

        if step_dt <= 0.0:
            raise ValueError(
                "dt must be greater "
                "than zero."
            )

        if (
            self.dae_solver.time
            >= self.end_time
            - self.dae_solver
            .event_manager
            .time_tolerance
        ):
            raise TransientStabilityError(
                "Simulation has reached "
                "end_time."
            )

        remaining = (
            self.end_time
            - self.dae_solver.time
        )

        return self.dae_solver.step(
            dt=min(
                step_dt,
                remaining,
            )
        )

    # ==================================================================
    # RESET
    # ==================================================================

    def reset(
        self,
    ) -> None:
        """
        Reset the event manager and simulation time.

        A complete physical-state reinitialization should be performed
        through ``initialize()``.
        """

        self.dae_solver.time = (
            self.start_time
        )

        self.dae_solver.event_manager.reset()

    # ==================================================================
    # RECORDING
    # ==================================================================

    @staticmethod
    def _record_sample(
        *,
        times: list[float],
        states: list[np.ndarray],
        voltages: list[
            dict[str, complex]
        ],
        powers: list[
            dict[
                str,
                tuple[float, float],
            ]
        ],
    ) -> None:
        """
        Record the current DAE solver state.
        """

        times.append(
            float(
                # The caller's DAE solver time is supplied indirectly
                # through the current state records below.
                0.0
            )
        )

    def _record_result(
        self,
        *,
        result: DAEStepResult,
        times: list[float],
        states: list[np.ndarray],
        voltages: list[
            dict[str, complex]
        ],
        powers: list[
            dict[
                str,
                tuple[float, float],
            ]
        ],
        events: list[Any],
    ) -> None:
        """
        Record one DAE step result.
        """

        times.append(
            float(result.time)
        )

        states.append(
            result.state.copy()
        )

        voltages.append(
            dict(
                result.terminal_voltages
            )
        )

        powers.append(
            dict(
                result.electrical_powers
            )
        )

        events.extend(
            result.processed_events
        )

    # ==================================================================
    # RESULT ASSEMBLY
    # ==================================================================

    @staticmethod
    def _build_result(
        *,
        times: Sequence[float],
        states: Sequence[np.ndarray],
        voltages: Sequence[
            dict[str, complex]
        ],
        powers: Sequence[
            dict[
                str,
                tuple[float, float],
            ]
        ],
        events: Sequence[Any],
    ) -> TransientStabilityResult:
        """
        Construct the final result object.
        """

        time_array = np.asarray(
            times,
            dtype=float,
        )

        if states:

            state_array = np.vstack(
                states
            )

        else:

            state_array = np.empty(
                (0, 0),
                dtype=float,
            )

        return TransientStabilityResult(
            time=time_array,
            states=state_array,
            terminal_voltages=[
                dict(item)
                for item in voltages
            ],
            electrical_powers=[
                dict(item)
                for item in powers
            ],
            events=list(events),
        )


__all__ = [
    "TransientStabilityError",
    "TransientStabilityResult",
    "TransientStabilitySolver",
]
```
