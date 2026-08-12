"""
GridForge Dynamic Simulation Events
===================================

Event scheduling and dispatch infrastructure for time-domain
simulation.

Typical transient-stability events include:

- fault application;
- fault clearing;
- breaker opening;
- breaker closing;
- line outage;
- generator trip;
- load rejection;
- shunt switching;
- control-mode changes.

Architectural responsibilities
-------------------------------
This module:

- stores scheduled simulation events;
- maintains deterministic event ordering;
- identifies events uniquely;
- determines the next pending event;
- detects events crossed by a simulation step;
- dispatches events through callbacks;
- records processed events.

This module does NOT:

- solve the electrical network;
- modify Y-bus directly;
- know how a breaker operates;
- know how a fault is electrically represented;
- own generator state;
- perform numerical integration.

The event action/callback is responsible for applying the physical
change through the authoritative GridForge model/network interfaces.

Event timing
------------
A simulation event occurring at t_event must never be silently skipped
because a numerical integration step crosses it.

For example:

    current time = 0.100 s
    event time   = 0.105 s
    requested dt = 0.010 s

The simulation controller should split the step:

    0.100 -> 0.105
              event
    0.105 -> 0.110

This module provides the event-query functionality required to do so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable


# ======================================================================
# TYPES
# ======================================================================


EventAction = Callable[
    ["SimulationEvent"],
    None,
]


# ======================================================================
# ERRORS
# ======================================================================


class EventError(RuntimeError):
    """Raised when an event-management operation is invalid."""


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
        Absolute simulation time at which the event occurs [s].

    action:
        Callback invoked when the event is processed.

        The callback receives the SimulationEvent instance.

    event_id:
        Optional unique identifier. If omitted, EventManager assigns
        one.

    event_type:
        Descriptive event category.

    target:
        Optional target identifier, such as a breaker, line, generator
        or bus.

    priority:
        Events at the same time are processed in ascending priority
        order.

    description:
        Human-readable description.

    data:
        Optional event-specific metadata.

    one_shot:
        If True, the event is processed only once.

    Notes
    -----
    Event actions should modify GridForge state through the appropriate
    model/network/controller interfaces. They should not bypass the
    authoritative architecture.
    """

    time: float

    action: EventAction

    event_id: str = ""

    event_type: str = "generic"

    target: str | None = None

    priority: int = 0

    description: str = ""

    data: dict[str, Any] = field(
        default_factory=dict
    )

    one_shot: bool = True

    processed: bool = False

    sequence: int = field(
        default=-1,
        repr=False,
    )

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.time,
            (int, float),
        ):
            raise EventError(
                "Event time must be numeric."
            )

        if self.time < 0.0:
            raise EventError(
                "Event time cannot be negative."
            )

        if not callable(
            self.action
        ):
            raise EventError(
                "Event action must be callable."
            )

        if not self.event_type:
            raise EventError(
                "event_type cannot be empty."
            )

    # ------------------------------------------------------------------
    # ORDERING KEY
    # ------------------------------------------------------------------

    @property
    def sort_key(
        self,
    ) -> tuple[
        float,
        int,
        int,
    ]:
        """
        Deterministic event-ordering key.

        Events are ordered by:

            1. simulation time;
            2. priority;
            3. registration sequence.
        """

        return (
            float(self.time),
            int(self.priority),
            int(self.sequence),
        )


# ======================================================================
# EVENT MANAGER
# ======================================================================


class EventManager:
    """
    Deterministic event scheduler and dispatcher.

    Parameters
    ----------
    time_tolerance:
        Numerical tolerance used when determining whether a simulation
        time has reached an event.
    """

    def __init__(
        self,
        time_tolerance: float = 1e-9,
    ) -> None:

        if time_tolerance <= 0.0:
            raise ValueError(
                "time_tolerance must be "
                "greater than zero."
            )

        self.time_tolerance = float(
            time_tolerance
        )

        self.events: list[
            SimulationEvent
        ] = []

        self._event_ids: set[str] = set()

        self._sequence = 0

    # ==================================================================
    # REGISTRATION
    # ==================================================================

    def add_event(
        self,
        event: SimulationEvent | None = None,
        *,
        time: float | None = None,
        action: EventAction | None = None,
        event_id: str = "",
        event_type: str = "generic",
        target: str | None = None,
        priority: int = 0,
        description: str = "",
        data: dict[str, Any] | None = None,
        one_shot: bool = True,
    ) -> SimulationEvent:
        """
        Register a simulation event.

        Either provide an existing ``SimulationEvent`` or supply the
        event fields directly.

        Returns
        -------
        SimulationEvent
            The registered event.
        """

        if event is None:

            if time is None:
                raise EventError(
                    "time is required when "
                    "event is not supplied."
                )

            if action is None:
                raise EventError(
                    "action is required when "
                    "event is not supplied."
                )

            event = SimulationEvent(
                time=float(time),
                action=action,
                event_id=event_id,
                event_type=event_type,
                target=target,
                priority=priority,
                description=description,
                data=(
                    {}
                    if data is None
                    else dict(data)
                ),
                one_shot=one_shot,
            )

        if event.event_id:

            if event.event_id in (
                self._event_ids
            ):
                raise EventError(
                    "Duplicate event id "
                    f"'{event.event_id}'."
                )

        else:

            event.event_id = (
                self._generate_event_id()
            )

        event.sequence = (
            self._sequence
        )

        self._sequence += 1

        self._event_ids.add(
            event.event_id
        )

        self.events.append(
            event
        )

        self._sort()

        return event

    # ==================================================================
    # CONVENIENCE
    # ==================================================================

    def add(
        self,
        time: float,
        action: EventAction,
        **kwargs: Any,
    ) -> SimulationEvent:
        """
        Convenience alias for ``add_event``.
        """

        return self.add_event(
            time=time,
            action=action,
            **kwargs,
        )

    # ==================================================================
    # EVENT QUERIES
    # ==================================================================

    def pending_events(
        self,
    ) -> tuple[
        SimulationEvent,
        ...
    ]:
        """
        Return all unprocessed events.
        """

        return tuple(
            event
            for event in self.events
            if not event.processed
        )

    def next_event(
        self,
        current_time: float,
    ) -> SimulationEvent | None:
        """
        Return the first pending event at or after ``current_time``.

        Parameters
        ----------
        current_time:
            Current simulation time.

        Returns
        -------
        SimulationEvent | None
            Next pending event.
        """

        for event in self.events:

            if event.processed:
                continue

            if (
                event.time
                >= current_time
                - self.time_tolerance
            ):
                return event

        return None

    def next_event_time(
        self,
        current_time: float,
    ) -> float | None:
        """
        Return the time of the next pending event.
        """

        event = self.next_event(
            current_time
        )

        if event is None:
            return None

        return float(
            event.time
        )

    def events_between(
        self,
        start_time: float,
        end_time: float,
        *,
        include_start: bool = False,
        include_end: bool = True,
    ) -> tuple[
        SimulationEvent,
        ...
    ]:
        """
        Return pending events inside a simulation-time interval.

        This is used by the simulation controller to detect whether a
        proposed integration step crosses an event.
        """

        if end_time < start_time:
            raise EventError(
                "end_time cannot be earlier "
                "than start_time."
            )

        result: list[
            SimulationEvent
        ] = []

        for event in self.events:

            if event.processed:
                continue

            if include_start:

                after_start = (
                    event.time
                    >= start_time
                    - self.time_tolerance
                )

            else:

                after_start = (
                    event.time
                    > start_time
                    + self.time_tolerance
                )

            if include_end:

                before_end = (
                    event.time
                    <= end_time
                    + self.time_tolerance
                )

            else:

                before_end = (
                    event.time
                    < end_time
                    - self.time_tolerance
                )

            if (
                after_start
                and before_end
            ):
                result.append(
                    event
                )

        result.sort(
            key=lambda item:
                item.sort_key
        )

        return tuple(
            result
        )

    def due_events(
        self,
        current_time: float,
    ) -> tuple[
        SimulationEvent,
        ...
    ]:
        """
        Return all events whose scheduled time has been reached.

        Events are returned in deterministic order but are not processed.
        """

        result: list[
            SimulationEvent
        ] = []

        for event in self.events:

            if event.processed:
                continue

            if (
                event.time
                <= current_time
                + self.time_tolerance
            ):
                result.append(
                    event
                )

        result.sort(
            key=lambda item:
                item.sort_key
        )

        return tuple(
            result
        )

    # ==================================================================
    # PROCESSING
    # ==================================================================

    def process(
        self,
        current_time: float,
    ) -> tuple[
        SimulationEvent,
        ...
    ]:
        """
        Process all events due at ``current_time``.

        Returns
        -------
        tuple[SimulationEvent, ...]
            Events processed during this call.
        """

        processed: list[
            SimulationEvent
        ] = []

        for event in self.due_events(
            current_time
        ):

            event.action(
                event
            )

            if event.one_shot:
                event.processed = True

            processed.append(
                event
            )

        return tuple(
            processed
        )

    # ==================================================================
    # MANAGEMENT
    # ==================================================================

    def cancel(
        self,
        event_id: str,
    ) -> bool:
        """
        Mark an event as processed/cancelled.

        Returns True if the event existed and was pending.
        """

        for event in self.events:

            if (
                event.event_id
                == event_id
            ):

                if event.processed:
                    return False

                event.processed = True

                return True

        return False

    def reset(
        self,
    ) -> None:
        """
        Reset all one-shot events to an unprocessed state.
        """

        for event in self.events:

            if event.one_shot:
                event.processed = False

    def clear(
        self,
    ) -> None:
        """
        Remove all scheduled events.
        """

        self.events.clear()

        self._event_ids.clear()

        self._sequence = 0

    def remove(
        self,
        event_id: str,
    ) -> bool:
        """
        Remove a scheduled event by identifier.
        """

        for index, event in enumerate(
            self.events
        ):

            if (
                event.event_id
                == event_id
            ):

                del self.events[
                    index
                ]

                self._event_ids.discard(
                    event_id
                )

                return True

        return False

    # ==================================================================
    # INTERNAL
    # ==================================================================

    def _generate_event_id(
        self,
    ) -> str:

        while True:

            event_id = (
                f"event_{self._sequence:06d}"
            )

            if event_id not in (
                self._event_ids
            ):
                return event_id

            self._sequence += 1

    def _sort(
        self,
    ) -> None:

        self.events.sort(
            key=lambda event:
                event.sort_key
        )


# ======================================================================
# PUBLIC EXPORTS
# ======================================================================


__all__ = [
    "EventAction",
    "EventError",
    "SimulationEvent",
    "EventManager",
]
```
