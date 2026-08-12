"""
GridForge Transient-Stability Events
====================================

Event scheduling and dispatch for dynamic simulations.

Responsibilities
----------------
- Register simulation events.
- Maintain deterministic event ordering.
- Detect events occurring within a simulation interval.
- Dispatch each event exactly once.
- Support event cancellation and reset.
- Keep event handling independent of network and machine models.

Non-responsibilities
--------------------
This module does NOT:

- modify network topology directly;
- solve the electrical network;
- implement breakers;
- implement faults;
- implement machine dynamics;
- perform numerical integration.

An event is represented by a time, an action, and optional metadata.

Examples
--------

Fault application:

    events.add(
        time=1.0,
        action=apply_fault,
        event_type="fault_apply",
    )

Fault clearing:

    events.add(
        time=1.1,
        action=clear_fault,
        event_type="fault_clear",
    )

The event manager determines WHEN the action is dispatched.

The action determines WHAT happens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


# ======================================================================
# TYPES
# ======================================================================

EventAction = Callable[[], Any]


# ======================================================================
# ERRORS
# ======================================================================


class EventError(
    RuntimeError
):
    """Base exception for simulation-event errors."""


class DuplicateEventError(
    EventError
):
    """Raised when an event ID is duplicated."""


class UnknownEventError(
    EventError
):
    """Raised when an unknown event is referenced."""


# ======================================================================
# EVENT
# ======================================================================


@dataclass
class SimulationEvent:
    """
    Scheduled simulation event.

    Parameters
    ----------
    time:
        Event time [s].

    action:
        Callable executed when the event is dispatched.

    event_id:
        Unique event identifier.

    event_type:
        Optional semantic event type.

    description:
        Human-readable description.

    priority:
        Ordering priority for events occurring at the same time.

        Lower values execute first.

    enabled:
        Whether the event is active.

    triggered:
        Whether the event has already been dispatched.

    metadata:
        Optional event-specific metadata.

    Notes
    -----
    The event manager owns scheduling state, not engineering behavior.

    A fault, breaker operation, generator trip, load switching operation,
    or topology change is implemented elsewhere and supplied as an
    action.
    """

    time: float

    action: EventAction

    event_id: str

    event_type: str = "generic"

    description: str = ""

    priority: int = 0

    enabled: bool = True

    triggered: bool = False

    metadata: dict[
        str,
        Any,
    ] = field(
        default_factory=dict
    )

    def __post_init__(
        self,
    ) -> None:

        try:

            self.time = float(
                self.time
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise EventError(
                "Event time must be "
                "numeric."
            ) from exc

        if self.time < 0.0:

            raise EventError(
                "Event time cannot "
                "be negative."
            )

        if not str(
            self.event_id
        ).strip():

            raise EventError(
                "event_id cannot "
                "be empty."
            )

        if not callable(
            self.action
        ):

            raise EventError(
                f"Action for event "
                f"'{self.event_id}' "
                "must be callable."
            )

        self.event_id = str(
            self.event_id
        )

        self.event_type = str(
            self.event_type
        )

        self.description = str(
            self.description
        )

        self.priority = int(
            self.priority
        )

    def reset(
        self,
    ) -> None:
        """Return the event to an untriggered state."""

        self.triggered = False


# ======================================================================
# EVENT RESULT
# ======================================================================


@dataclass(frozen=True)
class EventExecution:
    """
    Result of a dispatched event.
    """

    event_id: str

    event_type: str

    time: float

    result: Any = None


# ======================================================================
# EVENT MANAGER
# ======================================================================


class EventManager:
    """
    Deterministic transient-stability event scheduler.

    Parameters
    ----------
    tolerance:
        Time tolerance used when determining whether an event lies
        inside a simulation interval.

    Notes
    -----
    Events are processed by interval rather than exact floating-point
    time equality.

    For example, if the solver moves from:

        t = 0.99

    to:

        t = 1.01

    an event scheduled at:

        t = 1.00

    is still detected.

    This is essential for numerical transient-stability simulation.
    """

    def __init__(
        self,
        tolerance: float = 1e-9,
    ) -> None:

        if tolerance < 0.0:

            raise EventError(
                "Event tolerance "
                "cannot be negative."
            )

        self._tolerance = float(
            tolerance
        )

        self._events: dict[
            str,
            SimulationEvent,
        ] = {}

        self._execution_order = 0

        self._history: list[
            EventExecution
        ] = []

    # ==================================================================
    # PROPERTIES
    # ==================================================================

    @property
    def tolerance(
        self,
    ) -> float:
        """Event-time tolerance."""

        return self._tolerance

    @property
    def events(
        self,
    ) -> tuple[
        SimulationEvent,
        ...,
    ]:
        """
        Return events in deterministic execution order.
        """

        return tuple(
            sorted(
                self._events.values(),
                key=self._sort_key,
            )
        )

    @property
    def history(
        self,
    ) -> tuple[
        EventExecution,
        ...,
    ]:
        """Return immutable execution history."""

        return tuple(
            self._history
        )

    @property
    def pending_events(
        self,
    ) -> tuple[
        SimulationEvent,
        ...,
    ]:
        """Return enabled events that have not executed."""

        return tuple(
            event
            for event in self.events
            if (
                event.enabled
                and not event.triggered
            )
        )

    # ==================================================================
    # REGISTRATION
    # ==================================================================

    def add(
        self,
        time: float,
        action: EventAction,
        *,
        event_id: str,
        event_type: str = "generic",
        description: str = "",
        priority: int = 0,
        metadata: dict[
            str,
            Any,
        ] | None = None,
    ) -> SimulationEvent:
        """
        Register a simulation event.

        Event IDs must be unique.
        """

        event_id = str(
            event_id
        )

        if event_id in self._events:

            raise DuplicateEventError(
                f"Event '{event_id}' "
                "already exists."
            )

        event = SimulationEvent(
            time=time,
            action=action,
            event_id=event_id,
            event_type=event_type,
            description=description,
            priority=priority,
            metadata=(
                {}
                if metadata is None
                else dict(metadata)
            ),
        )

        self._events[
            event_id
        ] = event

        return event

    # ==================================================================
    # BACKWARD-COMPATIBLE REGISTRATION
    # ==================================================================

    def add_event(
        self,
        time: float,
        action: EventAction,
        *,
        event_id: str | None = None,
        event_type: str = "generic",
        description: str = "",
        priority: int = 0,
        metadata: dict[
            str,
            Any,
        ] | None = None,
    ) -> SimulationEvent:
        """
        Register an event using the legacy method name.

        ``event_id`` is generated when omitted.
        """

        if event_id is None:

            event_id = (
                f"event_{len(self._events):06d}"
            )

        return self.add(
            time=time,
            action=action,
            event_id=event_id,
            event_type=event_type,
            description=description,
            priority=priority,
            metadata=metadata,
        )

    # ==================================================================
    # ENABLE / DISABLE
    # ==================================================================

    def enable(
        self,
        event_id: str,
    ) -> None:
        """Enable a scheduled event."""

        event = self._get_event(
            event_id
        )

        event.enabled = True

    def disable(
        self,
        event_id: str,
    ) -> None:
        """Disable a scheduled event."""

        event = self._get_event(
            event_id
        )

        event.enabled = False

    def cancel(
        self,
        event_id: str,
    ) -> None:
        """
        Disable and remove an event.

        A cancelled event is removed permanently from the scheduler.
        """

        if event_id not in self._events:

            raise UnknownEventError(
                f"Unknown event "
                f"'{event_id}'."
            )

        del self._events[
            event_id
        ]

    # ==================================================================
    # PROCESSING
    # ==================================================================

    def process(
        self,
        t: float,
    ) -> tuple[
        EventExecution,
        ...,
    ]:
        """
        Process all events scheduled at or before ``t``.

        This method is retained for compatibility with a simulation loop
        that advances to exact event times.

        Events are dispatched once.
        """

        current_time = self._validate_time(
            t
        )

        executions: list[
            EventExecution
        ] = []

        for event in self.events:

            if not event.enabled:
                continue

            if event.triggered:
                continue

            if (
                event.time
                <= current_time
                + self._tolerance
            ):

                execution = (
                    self._execute_event(
                        event
                    )
                )

                executions.append(
                    execution
                )

        return tuple(
            executions
        )

    def process_interval(
        self,
        t_start: float,
        t_end: float,
    ) -> tuple[
        EventExecution,
        ...,
    ]:
        """
        Process all events lying inside a simulation interval.

        Parameters
        ----------
        t_start:
            Beginning of numerical integration interval.

        t_end:
            End of numerical integration interval.

        Returns
        -------
        tuple
            Events executed in deterministic order.

        Notes
        -----
        Events satisfy:

            t_start < event_time <= t_end

        subject to the configured tolerance.

        An event exactly at the beginning of the interval is normally
        considered already handled by the previous step.
        """

        start = self._validate_time(
            t_start
        )

        end = self._validate_time(
            t_end
        )

        if end < start:

            raise EventError(
                "t_end cannot be earlier "
                "than t_start."
            )

        executions: list[
            EventExecution
        ] = []

        candidates = [
            event
            for event in self.events
            if (
                event.enabled
                and not event.triggered
                and event.time
                > start
                - self._tolerance
                and event.time
                <= end
                + self._tolerance
            )
        ]

        for event in candidates:

            execution = (
                self._execute_event(
                    event
                )
            )

            executions.append(
                execution
            )

        return tuple(
            executions
        )

    # ==================================================================
    # RESET
    # ==================================================================

    def reset(
        self,
    ) -> None:
        """
        Reset all event-trigger state and execution history.

        This permits a new simulation run using the same event schedule.
        """

        for event in (
            self._events.values()
        ):

            event.reset()

        self._history.clear()

    # ==================================================================
    # QUERY
    # ==================================================================

    def next_event_time(
        self,
        current_time: float,
    ) -> float | None:
        """
        Return the next pending event time after ``current_time``.
        """

        current_time = (
            self._validate_time(
                current_time
            )
        )

        pending = [
            event
            for event in self.events
            if (
                event.enabled
                and not event.triggered
                and event.time
                > current_time
                + self._tolerance
            )
        ]

        if not pending:

            return None

        return min(
            event.time
            for event in pending
        )

    def has_pending_events(
        self,
    ) -> bool:
        """Return True if at least one event remains pending."""

        return any(
            event.enabled
            and not event.triggered
            for event in self._events.values()
        )

    # ==================================================================
    # INTERNAL EXECUTION
    # ==================================================================

    def _execute_event(
        self,
        event: SimulationEvent,
    ) -> EventExecution:
        """
        Execute one event and record the result.
        """

        try:

            result = event.action()

        except Exception as exc:

            raise EventError(
                f"Event '{event.event_id}' "
                f"failed during execution."
            ) from exc

        event.triggered = True

        execution = EventExecution(
            event_id=event.event_id,
            event_type=event.event_type,
            time=event.time,
            result=result,
        )

        self._history.append(
            execution
        )

        return execution

    def _get_event(
        self,
        event_id: str,
    ) -> SimulationEvent:
        """Return an event by ID."""

        try:

            return self._events[
                str(event_id)
            ]

        except KeyError as exc:

            raise UnknownEventError(
                f"Unknown event "
                f"'{event_id}'."
            ) from exc

    @staticmethod
    def _sort_key(
        event: SimulationEvent,
    ) -> tuple[
        float,
        int,
        str,
    ]:
        """
        Deterministic event ordering.

        Ordering:

            1. event time
            2. priority
            3. event ID
        """

        return (
            event.time,
            event.priority,
            event.event_id,
        )

    @staticmethod
    def _validate_time(
        time: float,
    ) -> float:
        """Validate a simulation time."""

        try:

            value = float(
                time
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise EventError(
                "Simulation time must "
                "be numeric."
            ) from exc

        if value < 0.0:

            raise EventError(
                "Simulation time cannot "
                "be negative."
            )

        return value


# ======================================================================
# COMMON EVENT FACTORY
# ======================================================================


def create_event(
    time: float,
    action: EventAction,
    *,
    event_id: str,
    event_type: str = "generic",
    description: str = "",
    priority: int = 0,
    metadata: dict[
        str,
        Any,
    ] | None = None,
) -> SimulationEvent:
    """
    Convenience factory for creating a SimulationEvent.
    """

    return SimulationEvent(
        time=time,
        action=action,
        event_id=event_id,
        event_type=event_type,
        description=description,
        priority=priority,
        metadata=(
            {}
            if metadata is None
            else dict(metadata)
        ),
    )


__all__ = [
    "EventAction",
    "SimulationEvent",
    "EventExecution",
    "EventError",
    "DuplicateEventError",
    "UnknownEventError",
    "EventManager",
    "create_event",
]
```
