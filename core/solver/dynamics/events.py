"""
GridForge Dynamic Simulation Events
===================================

Event definitions and deterministic event scheduling for dynamic
and transient-stability simulations.

Responsibilities
----------------
- Represent discrete simulation events.
- Schedule events at simulation times.
- Maintain deterministic event ordering.
- Dispatch events to registered callbacks.
- Prevent accidental repeated execution of one-shot events.

Typical events include
----------------------
- fault application
- fault clearing
- breaker opening/closing
- topology changes
- controller set-point changes
- protection actions
- external disturbances

This module does NOT:
- implement protection logic
- implement breaker physics
- modify the network directly
- solve differential equations
- perform numerical integration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable
import math


EventAction = Callable[["SimulationEvent"], None]


@dataclass
class SimulationEvent:
    """
    One discrete simulation event.

    Parameters
    ----------
    time:
        Simulation time at which the event occurs [s].

    action:
        Callback executed when the event is dispatched.

    event_id:
        Unique identifier for the event.

    event_type:
        Engineering classification of the event.

    target:
        Optional identifier of the object affected by the event.

    parameters:
        Optional event-specific data.

    priority:
        Ordering for simultaneous events. Lower values execute first.

    one_shot:
        If True, the event executes only once.

    enabled:
        If False, the event is ignored.
    """

    time: float
    action: EventAction

    event_id: str
    event_type: str = "generic"

    target: str | None = None

    parameters: dict[str, Any] = field(
        default_factory=dict
    )

    priority: int = 100

    one_shot: bool = True

    enabled: bool = True

    executed: bool = False

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError(
                "Event ID must not be empty."
            )

        if not self.event_type:
            raise ValueError(
                "Event type must not be empty."
            )

        if not math.isfinite(self.time):
            raise ValueError(
                "Event time must be finite."
            )

        if self.time < 0.0:
            raise ValueError(
                "Event time cannot be negative."
            )

        if not callable(self.action):
            raise TypeError(
                "Event action must be callable."
            )

    def can_execute(self) -> bool:
        """Return True if the event is currently executable."""

        if not self.enabled:
            return False

        if self.one_shot and self.executed:
            return False

        return True

    def execute(self) -> None:
        """Execute the event callback."""

        if not self.can_execute():
            return

        self.action(self)

        if self.one_shot:
            self.executed = True


class EventManager:
    """
    Deterministic event scheduler for dynamic simulation.

    Events are ordered by:

        1. event time
        2. priority
        3. insertion order

    This guarantees deterministic execution when multiple events
    occur at the same simulation time.
    """

    def __init__(
        self,
        time_tolerance: float = 1.0e-9,
    ) -> None:

        if time_tolerance <= 0.0:
            raise ValueError(
                "time_tolerance must be greater than zero."
            )

        self.time_tolerance = float(
            time_tolerance
        )

        self._events: list[
            SimulationEvent
        ] = []

        self._sequence: dict[
            str,
            int
        ] = {}

        self._next_sequence = 0

    # =========================================================
    # EVENT REGISTRATION
    # =========================================================

    def add(
        self,
        event: SimulationEvent,
    ) -> None:
        """
        Register an event.
        """

        if event.event_id in self._sequence:
            raise ValueError(
                f"Event ID already exists: "
                f"'{event.event_id}'."
            )

        self._sequence[
            event.event_id
        ] = self._next_sequence

        self._next_sequence += 1

        self._events.append(event)

        self._sort_events()

    def add_event(
        self,
        time: float,
        action: EventAction,
        *,
        event_id: str,
        event_type: str = "generic",
        target: str | None = None,
        parameters: dict[str, Any] | None = None,
        priority: int = 100,
        one_shot: bool = True,
    ) -> SimulationEvent:
        """
        Convenience method for creating and registering an event.
        """

        event = SimulationEvent(
            time=time,
            action=action,
            event_id=event_id,
            event_type=event_type,
            target=target,
            parameters=(
                {}
                if parameters is None
                else dict(parameters)
            ),
            priority=priority,
            one_shot=one_shot,
        )

        self.add(event)

        return event

    # =========================================================
    # EVENT ACCESS
    # =========================================================

    @property
    def events(self) -> tuple[
        SimulationEvent, ...
    ]:
        """Return registered events in execution order."""

        return tuple(self._events)

    def pending_events(self) -> tuple[
        SimulationEvent, ...
    ]:
        """Return events that have not yet executed."""

        return tuple(
            event
            for event in self._events
            if event.can_execute()
        )

    def next_event_time(
        self,
        current_time: float,
    ) -> float | None:
        """
        Return the next pending event time after current_time.

        Returns None when no future event exists.
        """

        for event in self._events:

            if not event.can_execute():
                continue

            if event.time >= (
                current_time
                - self.time_tolerance
            ):
                return event.time

        return None

    # =========================================================
    # EVENT PROCESSING
    # =========================================================

    def process(
        self,
        time: float,
    ) -> list[SimulationEvent]:
        """
        Execute all events occurring at ``time``.

        Returns
        -------
        list[SimulationEvent]
            Events executed during this call.
        """

        if not math.isfinite(time):
            raise ValueError(
                "Simulation time must be finite."
            )

        executed: list[
            SimulationEvent
        ] = []

        for event in self._events:

            if not event.can_execute():
                continue

            if abs(
                event.time - time
            ) > self.time_tolerance:
                continue

            event.execute()

            executed.append(event)

        return executed

    def process_until(
        self,
        time: float,
    ) -> list[SimulationEvent]:
        """
        Execute all pending events whose scheduled time is at or
        before ``time``.

        This is useful when the simulation advances directly to an
        event boundary.
        """

        if not math.isfinite(time):
            raise ValueError(
                "Simulation time must be finite."
            )

        executed: list[
            SimulationEvent
        ] = []

        for event in self._events:

            if not event.can_execute():
                continue

            if event.time > (
                time
                + self.time_tolerance
            ):
                continue

            event.execute()

            executed.append(event)

        return executed

    # =========================================================
    # MANAGEMENT
    # =========================================================

    def remove(
        self,
        event_id: str,
    ) -> None:
        """Remove an event by ID."""

        if event_id not in self._sequence:
            raise KeyError(
                f"Unknown event ID: '{event_id}'."
            )

        self._events = [
            event
            for event in self._events
            if event.event_id != event_id
        ]

        del self._sequence[
            event_id
        ]

    def clear(self) -> None:
        """Remove all registered events."""

        self._events.clear()
        self._sequence.clear()
        self._next_sequence = 0

    def reset(self) -> None:
        """
        Reset execution status while retaining event definitions.
        """

        for event in self._events:
            event.executed = False

    # =========================================================
    # INTERNAL
    # =========================================================

    def _sort_events(self) -> None:
        self._events.sort(
            key=lambda event: (
                event.time,
                event.priority,
                self._sequence[
                    event.event_id
                ],
            )
        )
