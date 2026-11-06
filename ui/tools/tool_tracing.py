"""
GridForge V2
============

File:
    ui/tools/tool_tracing.py

Purpose
-------
Passive execution tracing for the GridForge UI tool subsystem.

Tool tracing records the chronological flow of tool observations and
provides lightweight trace sessions for development, diagnostics, and
automated testing.

Architectural rules
-------------------
- Tracing is observational only.
- Tracing must not mutate Core state.
- Tracing must not execute Commands.
- Tracing must not activate, deactivate, or select tools.
- Tracing must not own authoritative tool state.
- Tracing must not depend on Qt.
- Tracing must not become an event bus.
- Trace timestamps are diagnostic wall-clock measurements only.
- Tracing may consume ToolObservation instances.
- Tracing must be removable without changing tool semantics.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from time import monotonic
from typing import Any, Callable, Iterable, Mapping, Optional

from .tool_observer import (
    ToolObservation,
    ToolObservationType,
    ToolObserver,
)


# ============================================================
# TRACE LEVEL
# ============================================================


class ToolTraceLevel(str, Enum):
    """
    Diagnostic verbosity levels.
    """

    MINIMAL = "minimal"
    NORMAL = "normal"
    VERBOSE = "verbose"


# ============================================================
# TRACE EVENT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolTraceEvent:
    """
    Immutable representation of one trace event.
    """

    sequence: int

    timestamp: float

    observation_type: ToolObservationType

    tool_id: Optional[str] = None

    tool_name: Optional[str] = None

    event_type: Optional[str] = None

    message: str = ""

    state: Any = None

    previous_state: Any = None

    error_type: Optional[str] = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""

        return {
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "observation_type": (
                self.observation_type.value
            ),
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "event_type": self.event_type,
            "message": self.message,
            "state": self.state,
            "previous_state": self.previous_state,
            "error_type": self.error_type,
            "metadata": dict(self.metadata),
        }


# ============================================================
# TRACE FILTER
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolTraceFilter:
    """
    Immutable filter controlling which observations enter a trace.
    """

    observation_types: frozenset[
        ToolObservationType
    ] = frozenset()

    tool_ids: frozenset[str] = frozenset()

    tool_names: frozenset[str] = frozenset()

    event_types: frozenset[str] = frozenset()

    include_errors: bool = True

    def matches(
        self,
        observation: ToolObservation,
    ) -> bool:
        """Return whether the observation passes the filter."""

        if (
            self.observation_types
            and observation.observation_type
            not in self.observation_types
        ):
            return False

        tool_id, tool_name = _tool_identity(
            observation.tool
        )

        if (
            self.tool_ids
            and tool_id not in self.tool_ids
        ):
            return False

        if (
            self.tool_names
            and tool_name not in self.tool_names
        ):
            return False

        event_type = _event_type(
            observation.event
        )

        if (
            self.event_types
            and event_type not in self.event_types
        ):
            return False

        if (
            not self.include_errors
            and observation.error is not None
        ):
            return False

        return True


# ============================================================
# TRACE SUMMARY
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolTraceSummary:
    """
    Immutable summary of a completed or current trace.
    """

    event_count: int

    observation_counts: Mapping[
        ToolObservationType,
        int,
    ]

    tool_counts: Mapping[
        str,
        int,
    ]

    error_count: int

    first_timestamp: Optional[float]

    last_timestamp: Optional[float]

    duration: Optional[float]

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable summary."""

        return {
            "event_count": self.event_count,
            "observation_counts": {
                key.value: value
                for key, value
                in self.observation_counts.items()
            },
            "tool_counts": dict(
                self.tool_counts
            ),
            "error_count": self.error_count,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "duration": self.duration,
        }


# ============================================================
# TRACE SESSION
# ============================================================


class ToolTraceSession:
    """
    Collects a bounded chronological trace.

    A session is diagnostic state and has no authority over the
    tool subsystem.
    """

    def __init__(
        self,
        *,
        session_id: Optional[str] = None,
        level: ToolTraceLevel = (
            ToolTraceLevel.NORMAL
        ),
        trace_filter: Optional[
            ToolTraceFilter
        ] = None,
        max_events: int = 5000,
    ) -> None:
        if not isinstance(
            level,
            ToolTraceLevel,
        ):
            raise TypeError(
                "level must be ToolTraceLevel."
            )

        if (
            not isinstance(
                max_events,
                int,
            )
            or isinstance(
                max_events,
                bool,
            )
            or max_events <= 0
        ):
            raise ValueError(
                "max_events must be a positive integer."
            )

        self._session_id = session_id
        self._level = level
        self._filter = (
            trace_filter
            or ToolTraceFilter()
        )
        self._max_events = max_events

        self._events: list[
            ToolTraceEvent
        ] = []

        self._observation_counts: Counter[
            ToolObservationType
        ] = Counter()

        self._tool_counts: Counter[
            str
        ] = Counter()

        self._error_count = 0
        self._sequence = 0

        self._started_at: Optional[
            float
        ] = None

        self._ended_at: Optional[
            float
        ] = None

        self._active = False

        self._lock = RLock()

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def session_id(self) -> Optional[str]:
        """Return the diagnostic session identifier."""

        return self._session_id

    @property
    def level(self) -> ToolTraceLevel:
        """Return the current trace level."""

        with self._lock:
            return self._level

    @property
    def trace_filter(self) -> ToolTraceFilter:
        """Return the current trace filter."""

        with self._lock:
            return self._filter

    @property
    def max_events(self) -> int:
        """Return the maximum retained event count."""

        return self._max_events

    @property
    def active(self) -> bool:
        """Return whether the session is active."""

        with self._lock:
            return self._active

    @property
    def event_count(self) -> int:
        """Return the number of retained events."""

        with self._lock:
            return len(
                self._events
            )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def start(self) -> None:
        """
        Start or restart the trace session.

        Starting a session clears previous events.
        """

        with self._lock:
            self._events.clear()
            self._observation_counts.clear()
            self._tool_counts.clear()

            self._error_count = 0
            self._sequence = 0

            self._started_at = monotonic()
            self._ended_at = None
            self._active = True

    def stop(self) -> None:
        """Stop the trace session."""

        with self._lock:
            if not self._active:
                return

            self._ended_at = monotonic()
            self._active = False

    def clear(self) -> None:
        """Clear trace contents without changing configuration."""

        with self._lock:
            self._events.clear()
            self._observation_counts.clear()
            self._tool_counts.clear()

            self._error_count = 0
            self._sequence = 0

            self._started_at = (
                monotonic()
                if self._active
                else None
            )

            self._ended_at = None

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def set_level(
        self,
        level: ToolTraceLevel,
    ) -> None:
        """Set trace verbosity."""

        if not isinstance(
            level,
            ToolTraceLevel,
        ):
            raise TypeError(
                "level must be ToolTraceLevel."
            )

        with self._lock:
            self._level = level

    def set_filter(
        self,
        trace_filter: ToolTraceFilter,
    ) -> None:
        """Replace the trace filter."""

        if not isinstance(
            trace_filter,
            ToolTraceFilter,
        ):
            raise TypeError(
                "trace_filter must be ToolTraceFilter."
            )

        with self._lock:
            self._filter = trace_filter

    # ========================================================
    # RECORDING
    # ========================================================

    def record(
        self,
        observation: ToolObservation,
    ) -> Optional[ToolTraceEvent]:
        """
        Record one observation.

        Returns the resulting trace event, or None when the observation
        is filtered or the session is inactive.
        """

        if not isinstance(
            observation,
            ToolObservation,
        ):
            raise TypeError(
                "observation must be ToolObservation."
            )

        with self._lock:
            if not self._active:
                return None

            if not self._filter.matches(
                observation
            ):
                return None

            event = self._build_event(
                observation
            )

            self._events.append(
                event
            )

            if len(
                self._events
            ) > self._max_events:
                del self._events[
                    : len(self._events)
                    - self._max_events
                ]

            self._update_counts(
                observation
            )

            return event

    # ========================================================
    # QUERY
    # ========================================================

    def events(
        self,
        *,
        limit: Optional[int] = None,
    ) -> tuple[
        ToolTraceEvent,
        ...
    ]:
        """Return retained events in chronological order."""

        with self._lock:
            values = tuple(
                self._events
            )

        if limit is None:
            return values

        if (
            not isinstance(
                limit,
                int,
            )
            or isinstance(
                limit,
                bool,
            )
            or limit < 0
        ):
            raise ValueError(
                "limit must be a non-negative integer."
            )

        if limit == 0:
            return ()

        return values[-limit:]

    def latest(
        self,
    ) -> Optional[ToolTraceEvent]:
        """Return the latest retained event."""

        with self._lock:
            if not self._events:
                return None

            return self._events[-1]

    def summary(
        self,
    ) -> ToolTraceSummary:
        """Return a point-in-time trace summary."""

        with self._lock:
            first_timestamp = (
                self._events[0].timestamp
                if self._events
                else None
            )

            last_timestamp = (
                self._events[-1].timestamp
                if self._events
                else None
            )

            if (
                first_timestamp is not None
                and last_timestamp is not None
            ):
                duration = (
                    last_timestamp
                    - first_timestamp
                )
            else:
                duration = None

            return ToolTraceSummary(
                event_count=len(
                    self._events
                ),
                observation_counts=dict(
                    self._observation_counts
                ),
                tool_counts=dict(
                    self._tool_counts
                ),
                error_count=self._error_count,
                first_timestamp=first_timestamp,
                last_timestamp=last_timestamp,
                duration=duration,
            )

    def export(
        self,
    ) -> tuple[
        dict[str, Any],
        ...
    ]:
        """Export retained trace events as dictionaries."""

        return tuple(
            event.to_dict()
            for event in self.events()
        )

    # ========================================================
    # INTERNAL
    # ========================================================

    def _build_event(
        self,
        observation: ToolObservation,
    ) -> ToolTraceEvent:
        self._sequence += 1

        tool_id, tool_name = _tool_identity(
            observation.tool
        )

        event_type = _event_type(
            observation.event
        )

        error_type = (
            type(
                observation.error
            ).__name__
            if observation.error is not None
            else None
        )

        metadata = dict(
            observation.metadata
        )

        if self._level == ToolTraceLevel.MINIMAL:
            metadata = {}

        return ToolTraceEvent(
            sequence=self._sequence,
            timestamp=monotonic(),
            observation_type=(
                observation.observation_type
            ),
            tool_id=tool_id,
            tool_name=tool_name,
            event_type=event_type,
            message=(
                observation.message
                if self._level
                != ToolTraceLevel.MINIMAL
                else ""
            ),
            state=(
                observation.state
                if self._level
                == ToolTraceLevel.VERBOSE
                else None
            ),
            previous_state=(
                observation.previous_state
                if self._level
                == ToolTraceLevel.VERBOSE
                else None
            ),
            error_type=error_type,
            metadata=metadata,
        )

    def _update_counts(
        self,
        observation: ToolObservation,
    ) -> None:
        self._observation_counts[
            observation.observation_type
        ] += 1

        _, tool_name = _tool_identity(
            observation.tool
        )

        if tool_name:
            self._tool_counts[
                tool_name
            ] += 1

        if observation.error is not None:
            self._error_count += 1


# ============================================================
# TRACE OBSERVER
# ============================================================


class ToolTracer(ToolObserver):
    """
    ToolObserver implementation that feeds observations into a
    ToolTraceSession.
    """

    def __init__(
        self,
        session: Optional[
            ToolTraceSession
        ] = None,
    ) -> None:
        self._session = (
            session
            or ToolTraceSession()
        )

    @property
    def session(self) -> ToolTraceSession:
        """Return the trace session."""

        return self._session

    def observe(
        self,
        observation: ToolObservation,
    ) -> None:
        """Forward one observation to the trace session."""

        self._session.record(
            observation
        )


# ============================================================
# TRACE SINK
# ============================================================


class ToolTraceSink:
    """
    Destination interface for completed trace events.
    """

    def write(
        self,
        event: ToolTraceEvent,
    ) -> None:
        """Consume one trace event."""

        raise NotImplementedError


class NullToolTraceSink(ToolTraceSink):
    """No-op trace sink."""

    def write(
        self,
        event: ToolTraceEvent,
    ) -> None:
        return None


class CallbackToolTraceSink(ToolTraceSink):
    """Trace sink backed by a callback."""

    def __init__(
        self,
        callback: Callable[
            [ToolTraceEvent],
            None,
        ],
    ) -> None:
        if not callable(
            callback
        ):
            raise TypeError(
                "callback must be callable."
            )

        self._callback = callback

    def write(
        self,
        event: ToolTraceEvent,
    ) -> None:
        self._callback(
            event
        )


# ============================================================
# TRACE FORWARDER
# ============================================================


class ToolTraceForwarder(ToolObserver):
    """
    Observer that records observations and forwards resulting trace
    events to a diagnostic sink.

    The sink receives immutable trace events only.
    """

    def __init__(
        self,
        session: Optional[
            ToolTraceSession
        ] = None,
        *,
        sink: Optional[
            ToolTraceSink
        ] = None,
    ) -> None:
        self._session = (
            session
            or ToolTraceSession()
        )

        self._sink = (
            sink
            or NullToolTraceSink()
        )

    @property
    def session(self) -> ToolTraceSession:
        """Return the trace session."""

        return self._session

    @property
    def sink(self) -> ToolTraceSink:
        """Return the configured sink."""

        return self._sink

    def observe(
        self,
        observation: ToolObservation,
    ) -> None:
        """Record and forward one observation."""

        event = self._session.record(
            observation
        )

        if event is not None:
            self._sink.write(
                event
            )


# ============================================================
# TRACE FORMATTER
# ============================================================


class ToolTraceFormatter:
    """
    Human-readable formatter for trace events.
    """

    def format(
        self,
        event: ToolTraceEvent,
    ) -> str:
        """Format one event."""

        parts = [
            f"#{event.sequence}",
            f"{event.timestamp:.6f}",
            event.observation_type.value,
        ]

        if event.tool_name:
            parts.append(
                f"tool={event.tool_name}"
            )

        if event.tool_id:
            parts.append(
                f"id={event.tool_id}"
            )

        if event.event_type:
            parts.append(
                f"event={event.event_type}"
            )

        if event.message:
            parts.append(
                event.message
            )

        if event.error_type:
            parts.append(
                f"error={event.error_type}"
            )

        return " | ".join(
            parts
        )

    def format_many(
        self,
        events: Iterable[
            ToolTraceEvent
        ],
    ) -> str:
        """Format multiple events."""

        return "\n".join(
            self.format(
                event
            )
            for event in events
        )


# ============================================================
# TRACE MANAGER
# ============================================================


class ToolTraceManager:
    """
    Lightweight manager for named diagnostic trace sessions.

    This manager manages diagnostics only; it does not manage tools.
    """

    def __init__(
        self,
    ) -> None:
        self._sessions: dict[
            str,
            ToolTraceSession,
        ] = {}

        self._lock = RLock()

    def create(
        self,
        session_id: str,
        *,
        level: ToolTraceLevel = (
            ToolTraceLevel.NORMAL
        ),
        trace_filter: Optional[
            ToolTraceFilter
        ] = None,
        max_events: int = 5000,
    ) -> ToolTraceSession:
        """Create and register a named trace session."""

        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            raise ValueError(
                "session_id must be a non-empty string."
            )

        with self._lock:
            if session_id in self._sessions:
                raise ValueError(
                    (
                        f"Trace session {session_id!r} "
                        "already exists."
                    )
                )

            session = ToolTraceSession(
                session_id=session_id,
                level=level,
                trace_filter=trace_filter,
                max_events=max_events,
            )

            self._sessions[
                session_id
            ] = session

            return session

    def get(
        self,
        session_id: str,
    ) -> Optional[ToolTraceSession]:
        """Return a named session."""

        with self._lock:
            return self._sessions.get(
                session_id
            )

    def remove(
        self,
        session_id: str,
    ) -> Optional[ToolTraceSession]:
        """Remove and return a named session."""

        with self._lock:
            return self._sessions.pop(
                session_id,
                None,
            )

    def clear(self) -> None:
        """Remove all registered sessions."""

        with self._lock:
            self._sessions.clear()

    def sessions(
        self,
    ) -> tuple[
        ToolTraceSession,
        ...
    ]:
        """Return all registered sessions."""

        with self._lock:
            return tuple(
                self._sessions.values()
            )


# ============================================================
# HELPERS
# ============================================================


def _tool_identity(
    tool: Any,
) -> tuple[
    Optional[str],
    Optional[str],
]:
    if tool is None:
        return None, None

    tool_id = getattr(
        tool,
        "tool_id",
        None,
    )

    if tool_id is None:
        tool_id = getattr(
            tool,
            "id",
            None,
        )

    tool_name = getattr(
        tool,
        "name",
        None,
    )

    if tool_name is None:
        tool_name = tool.__class__.__name__

    return (
        str(tool_id)
        if tool_id is not None
        else None,
        str(tool_name)
        if tool_name is not None
        else None,
    )


def _event_type(
    event: Any,
) -> Optional[str]:
    if event is None:
        return None

    event_type = getattr(
        event,
        "event_type",
        None,
    )

    if event_type is None:
        event_type = getattr(
            event,
            "type",
            None,
        )

    if event_type is None:
        event_type = event.__class__.__name__

    return str(
        event_type
    )


# ============================================================
# FACTORY
# ============================================================


def create_tool_tracer(
    *,
    session_id: Optional[str] = None,
    level: ToolTraceLevel = (
        ToolTraceLevel.NORMAL
    ),
    max_events: int = 5000,
) -> ToolTracer:
    """
    Create a standard ToolTracer.

    The returned tracer is created with an inactive session. Call
    ``tracer.session.start()`` when tracing is required.
    """

    return ToolTracer(
        ToolTraceSession(
            session_id=session_id,
            level=level,
            max_events=max_events,
        )
    )


__all__ = [
    "ToolTraceLevel",
    "ToolTraceEvent",
    "ToolTraceFilter",
    "ToolTraceSummary",
    "ToolTraceSession",
    "ToolTracer",
    "ToolTraceSink",
    "NullToolTraceSink",
    "CallbackToolTraceSink",
    "ToolTraceForwarder",
    "ToolTraceFormatter",
    "ToolTraceManager",
    "create_tool_tracer",
]
