"""
GridForge Transient Stability Study
===================================

Public study/facade for time-domain transient-stability simulation.

The transient-stability study coordinates:

    - dynamic machine models
    - DAE solver
    - discrete simulation events
    - simulation time
    - result collection

Architectural role
------------------
This module is a study-level orchestration layer.

It does NOT:
    - implement the swing equation
    - implement machine differential equations
    - implement AVR/GOV/PSS equations
    - implement numerical integration
    - solve the electrical network directly
    - construct Y-bus matrices
    - implement protection algorithms

Those responsibilities belong to the appropriate lower layers.

Simulation sequence
-------------------

    initialize
        |
        v
    solve initial algebraic state
        |
        v
    identify next event
        |
        v
    integrate dynamic states
        |
        v
    process event
        |
        v
    solve algebraic state
        |
        v
    record results
        |
        +----> repeat
        |
        v
    StudyResult


The class is deliberately designed so that the public study API can
remain stable while the underlying numerical DAE implementation
evolves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from .dae_solver import (
    DAESolver,
    DAESolverError,
)
from .events import (
    EventManager,
    SimulationEvent,
)
from .machine_models import (
    MachineInputs,
)


class TransientStabilityError(RuntimeError):
    """Raised when a transient-stability study cannot be completed."""


@dataclass(frozen=True)
class SimulationSnapshot:
    """
    One recorded transient-stability simulation point.

    Parameters
    ----------
    time:
        Simulation time [s].

    state:
        Complete dynamic-state vector.

    voltages:
        Algebraic bus-voltage solution.

    electrical_powers:
        Electrical active power of each dynamic machine.

    event_ids:
        Events processed at this simulation point.
    """

    time: float
    state: np.ndarray
    voltages: Mapping[str, complex]
    electrical_powers: Mapping[str, float]
    event_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "state",
            np.asarray(
                self.state,
                dtype=float,
            ).copy(),
        )

    def copy(self) -> "SimulationSnapshot":
        """Return an independent copy of the snapshot."""

        return SimulationSnapshot(
            time=self.time,
            state=self.state.copy(),
            voltages=dict(
                self.voltages
            ),
            electrical_powers=dict(
                self.electrical_powers
            ),
            event_ids=tuple(
                self.event_ids
            ),
        )


@dataclass
class TransientStabilityResult:
    """
    Results returned by a transient-stability study.

    The result is intentionally study-oriented rather than tied to a
    particular numerical integration implementation.
    """

    snapshots: list[
        SimulationSnapshot
    ] = field(
        default_factory=list
    )

    converged: bool = False

    final_time: float = 0.0

    failure_reason: str | None = None

    @property
    def times(self) -> np.ndarray:
        """Return recorded simulation times."""

        return np.asarray(
            [
                snapshot.time
                for snapshot in self.snapshots
            ],
            dtype=float,
        )

    @property
    def states(self) -> np.ndarray:
        """
        Return all recorded dynamic states.

        Shape:

            (number_of_snapshots, number_of_states)
        """

        if not self.snapshots:
            return np.empty(
                (0, 0),
                dtype=float,
            )

        return np.vstack(
            [
                snapshot.state
                for snapshot in self.snapshots
            ]
        )

    def snapshot_at(
        self,
        index: int,
    ) -> SimulationSnapshot:
        """Return one recorded snapshot."""

        return self.snapshots[index]


@dataclass(frozen=True)
class TransientStabilityConfig:
    """
    Configuration for a transient-stability study.

    Parameters
    ----------
    start_time:
        Simulation start time [s].

    end_time:
        Simulation end time [s].

    time_step:
        Default integration time step [s].

    record_interval:
        Requested result-recording interval [s].

        ``None`` means record every accepted integration step.

    max_steps:
        Safety limit on the total number of simulation steps.

    event_tolerance:
        Time tolerance used when aligning integration steps with events.
    """

    start_time: float = 0.0

    end_time: float = 10.0

    time_step: float = 0.01

    record_interval: float | None = None

    max_steps: int = 1_000_000

    event_tolerance: float = 1.0e-9

    def __post_init__(self) -> None:

        if not np.isfinite(
            self.start_time
        ):
            raise ValueError(
                "start_time must be finite."
            )

        if not np.isfinite(
            self.end_time
        ):
            raise ValueError(
                "end_time must be finite."
            )

        if self.end_time <= self.start_time:
            raise ValueError(
                "end_time must be greater than start_time."
            )

        if (
            not np.isfinite(
                self.time_step
            )
            or self.time_step <= 0.0
        ):
            raise ValueError(
                "time_step must be greater than zero."
            )

        if self.record_interval is not None:
            if (
                not np.isfinite(
                    self.record_interval
                )
                or self.record_interval <= 0.0
            ):
                raise ValueError(
                    "record_interval must be greater than zero."
                )

        if self.max_steps < 1:
            raise ValueError(
                "max_steps must be at least 1."
            )

        if (
            not np.isfinite(
                self.event_tolerance
            )
            or self.event_tolerance <= 0.0
        ):
            raise ValueError(
                "event_tolerance must be greater than zero."
            )


class TransientStabilityStudy:
    """
    Public transient-stability study interface.

    Parameters
    ----------
    dae_solver:
        Configured GridForge DAE solver.

    event_manager:
        Optional event scheduler.

    config:
        Study configuration.

    The study owns simulation orchestration but does not own the
    underlying dynamic or network models.
    """

    def __init__(
        self,
        dae_solver: DAESolver,
        event_manager: EventManager | None = None,
        config: TransientStabilityConfig | None = None,
    ) -> None:

        self.dae_solver = dae_solver

        self.event_manager = (
            event_manager
            if event_manager is not None
            else EventManager()
        )

        self.config = (
            config
            if config is not None
            else TransientStabilityConfig()
        )

    # =========================================================
    # PUBLIC STUDY API
    # =========================================================

    def run(
        self,
        initial_inputs: Mapping[
            str,
            MachineInputs,
        ],
    ) -> TransientStabilityResult:
        """
        Execute the complete transient-stability study.

        Parameters
        ----------
        initial_inputs:
            Initial dynamic-machine operating-point inputs.

        Returns
        -------
        TransientStabilityResult
            Complete time-domain study result.
        """

        result = TransientStabilityResult()

        try:
            self._prepare_solver()

            self.dae_solver.initialize(
                initial_inputs
            )

            self._record_snapshot(
                result=result,
                event_ids=(),
            )

            current_time = (
                self.config.start_time
            )

            if abs(
                current_time
                - self.dae_solver.time
            ) > self.config.event_tolerance:

                self.dae_solver.time = (
                    current_time
                )

            next_record_time = self._next_record_time(
                current_time
            )

            step_count = 0

            while current_time < (
                self.config.end_time
                - self.config.event_tolerance
            ):

                if step_count >= (
                    self.config.max_steps
                ):
                    raise TransientStabilityError(
                        "Maximum simulation-step limit "
                        "was exceeded."
                    )

                # -------------------------------------------------
                # Determine next integration boundary.
                #
                # The step must never cross an event time.
                # -------------------------------------------------

                step = min(
                    self.config.time_step,
                    self.config.end_time
                    - current_time,
                )

                next_event_time = (
                    self.event_manager.next_event_time(
                        current_time
                    )
                )

                if next_event_time is not None:

                    time_to_event = (
                        next_event_time
                        - current_time
                    )

                    if (
                        time_to_event
                        > self.config.event_tolerance
                    ):
                        step = min(
                            step,
                            time_to_event,
                        )

                # -------------------------------------------------
                # Also respect requested recording interval.
                # -------------------------------------------------

                if next_record_time is not None:

                    time_to_record = (
                        next_record_time
                        - current_time
                    )

                    if (
                        time_to_record
                        > self.config.event_tolerance
                    ):
                        step = min(
                            step,
                            time_to_record,
                        )

                if step <= (
                    self.config.event_tolerance
                ):
                    # We are effectively at a boundary. Process
                    # events before attempting another integration
                    # step.
                    event_ids = (
                        self._process_events(
                            current_time
                        )
                    )

                    if event_ids:
                        self._record_snapshot(
                            result=result,
                            event_ids=event_ids,
                        )

                    next_record_time = (
                        self._advance_record_time(
                            next_record_time,
                            current_time,
                        )
                    )

                    # Prevent an infinite loop caused by a numerical
                    # boundary that cannot advance time.
                    if (
                        next_event_time is None
                        and next_record_time is None
                    ):
                        break

                    if (
                        next_event_time is not None
                        and abs(
                            next_event_time
                            - current_time
                        )
                        <= self.config.event_tolerance
                    ):
                        continue

                # -------------------------------------------------
                # Dynamic integration.
                # -------------------------------------------------

                self.dae_solver.step(
                    inputs=initial_inputs,
                    dt=step,
                )

                current_time = (
                    self.dae_solver.time
                )

                step_count += 1

                # -------------------------------------------------
                # Process events exactly at the accepted boundary.
                # -------------------------------------------------

                event_ids = (
                    self._process_events(
                        current_time
                    )
                )

                # -------------------------------------------------
                # Record result.
                # -------------------------------------------------

                should_record = (
                    self._should_record(
                        current_time,
                        next_record_time,
                        event_ids,
                    )
                )

                if should_record:

                    self._record_snapshot(
                        result=result,
                        event_ids=event_ids,
                    )

                    next_record_time = (
                        self._advance_record_time(
                            next_record_time,
                            current_time,
                        )
                    )

            # Ensure final state is represented.
            if not result.snapshots or abs(
                result.snapshots[-1].time
                - self.dae_solver.time
            ) > self.config.event_tolerance:

                self._record_snapshot(
                    result=result,
                    event_ids=(),
                )

            result.converged = True

            result.final_time = (
                self.dae_solver.time
            )

            return result

        except (
            DAESolverError,
            TransientStabilityError,
            ValueError,
        ) as exc:

            result.converged = False

            result.final_time = (
                self.dae_solver.time
            )

            result.failure_reason = str(
                exc
            )

            return result

    # =========================================================
    # EVENT MANAGEMENT
    # =========================================================

    def add_event(
        self,
        event: SimulationEvent,
    ) -> None:
        """
        Register a simulation event.
        """

        self.event_manager.add(
            event
        )

    def add_event_at(
        self,
        time: float,
        action,
        *,
        event_id: str,
        event_type: str = "generic",
        target: str | None = None,
        parameters: dict | None = None,
        priority: int = 100,
        one_shot: bool = True,
    ) -> SimulationEvent:
        """
        Convenience method for registering a simulation event.
        """

        return self.event_manager.add_event(
            time=time,
            action=action,
            event_id=event_id,
            event_type=event_type,
            target=target,
            parameters=parameters,
            priority=priority,
            one_shot=one_shot,
        )

    # =========================================================
    # INTERNAL INITIALIZATION
    # =========================================================

    def _prepare_solver(self) -> None:
        """
        Prepare the DAE solver for a new study run.
        """

        self.dae_solver.reset()

        self.dae_solver.dt = (
            self.config.time_step
        )

    # =========================================================
    # EVENT PROCESSING
    # =========================================================

    def _process_events(
        self,
        time: float,
    ) -> tuple[str, ...]:

        executed = (
            self.event_manager.process(
                time
            )
        )

        return tuple(
            event.event_id
            for event in executed
        )

    # =========================================================
    # RESULT RECORDING
    # =========================================================

    def _record_snapshot(
        self,
        result: TransientStabilityResult,
        event_ids: Sequence[str],
    ) -> None:

        algebraic = (
            self.dae_solver.algebraic_solution
        )

        if algebraic is None:
            raise TransientStabilityError(
                "Cannot record simulation result "
                "without an algebraic solution."
            )

        snapshot = SimulationSnapshot(
            time=self.dae_solver.time,
            state=self.dae_solver.state.pack(),
            voltages=dict(
                algebraic.voltages
            ),
            electrical_powers=dict(
                algebraic.electrical_powers
            ),
            event_ids=tuple(
                event_ids
            ),
        )

        result.snapshots.append(
            snapshot
        )

    # =========================================================
    # RECORDING CONTROL
    # =========================================================

    def _next_record_time(
        self,
        current_time: float,
    ) -> float | None:

        interval = (
            self.config.record_interval
        )

        if interval is None:
            return None

        return (
            current_time
            + interval
        )

    def _advance_record_time(
        self,
        next_record_time: float | None,
        current_time: float,
    ) -> float | None:

        if next_record_time is None:
            return None

        interval = (
            self.config.record_interval
        )

        if interval is None:
            return None

        next_time = next_record_time

        while next_time <= (
            current_time
            + self.config.event_tolerance
        ):
            next_time += interval

        return next_time

    def _should_record(
        self,
        current_time: float,
        next_record_time: float | None,
        event_ids: Sequence[str],
    ) -> bool:

        # Always record event boundaries.
        if event_ids:
            return True

        # Without a recording interval, record every accepted step.
        if next_record_time is None:
            return True

        return (
            current_time
            >= next_record_time
            - self.config.event_tolerance
        )
