"""
GridForge V2
============

File:
    ui/tools/tool_debug.py

Purpose
-------
Development and diagnostics support for the GridForge UI tool subsystem.

This module provides passive debugging utilities for inspecting tool
lifecycle, interaction, state, and dispatch behaviour.

Architectural rules
-------------------
- Debugging is observational only.
- Debugging must not mutate Core state.
- Debugging must not execute Commands.
- Debugging must not activate or deactivate tools.
- Debugging must not own authoritative tool state.
- Debugging must not depend on Qt.
- Debugging must not become a second event bus.
- Production behaviour must not depend on debug observers.
- Debugging facilities may be disabled without changing tool semantics.

The primary input is ToolObservation from ``tool_observer.py``.
"""

from __future__ import annotations

from collections import Counter, deque
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
# DEBUG MODE
# ============================================================


class ToolDebugMode(str, Enum):
    """
    Debugging operating modes.
    """

    DISABLED = "disabled"
    PASSIVE = "passive"
    TRACE = "trace"


# ============================================================
# DEBUG ENTRY
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolDebugEntry:
    """
    Immutable captured debugging entry.

    The entry contains diagnostic data only. It is not an instruction
    to the tool subsystem.
    """

    sequence: int

    timestamp: float

    observation_type: ToolObservationType

    tool_id: Optional[str] = None

    tool_name: Optional[str] = None

    event_type: Optional[str] = None

    state: Any = None

    previous_state: Any = None

    message: str = ""

    error_type: Optional[str] = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic dictionary."""

        return {
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "observation_type": (
                self.observation_type.value
            ),
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "event_type": self.event_type,
            "state": self.state,
            "previous_state": self.previous_state,
            "message": self.message,
            "error_type": self.error_type,
            "metadata": dict(self.metadata),
        }


# ============================================================
# DEBUG FILTER
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolDebugFilter:
    """
    Immutable filter for diagnostic observations.
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

        tool_id, tool_name = (
            _tool_identity(
                observation.tool
            )
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
# DEBUG STATISTICS
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolDebugStatistics:
    """
    Snapshot of collected debugging statistics.
    """

    total_observations: int

    observation_counts: Mapping[
        ToolObservationType,
        int,
    ]

    tool_counts: Mapping[
        str,
        int,
    ]

    error_count: int

    event_count: int

    lifecycle_count: int

    state_change_count: int

    execution_count: int

    last_sequence: int

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable statistics representation."""

        return {
            "total_observations": (
                self.total_observations
            ),
            "observation_counts": {
                key.value: value
                for key, value
                in self.observation_counts.items()
            },
            "tool_counts": dict(
                self.tool_counts
            ),
            "error_count": self.error_count,
            "event_count": self.event_count,
            "lifecycle_count": self.lifecycle_count,
            "state_change_count": (
                self.state_change_count
            ),
            "execution_count": self.execution_count,
            "last_sequence": self.last_sequence,
        }


# ============================================================
# DEBUG SNAPSHOT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolDebugSnapshot:
    """
    Point-in-time diagnostic snapshot.
    """

    mode: ToolDebugMode

    entries: tuple[
        ToolDebugEntry,
        ...
    ]

    statistics: ToolDebugStatistics

    active_tools: tuple[str, ...]

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable snapshot."""

        return {
            "mode": self.mode.value,
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ],
            "statistics": (
                self.statistics.to_dict()
            ),
            "active_tools": list(
                self.active_tools
            ),
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# DEBUG SINK
# ============================================================


class ToolDebugSink:
    """
    Protocol-like base class for receiving debug entries.

    A concrete sink may forward entries to a console, debugger,
    file logger, test collector, or telemetry system.
    """

    def write(
        self,
        entry: ToolDebugEntry,
    ) -> None:
        """Receive one debug entry."""

        raise NotImplementedError


class NullToolDebugSink(ToolDebugSink):
    """No-op debug sink."""

    def write(
        self,
        entry: ToolDebugEntry,
    ) -> None:
        """Discard the entry."""

        return None


class CallbackToolDebugSink(ToolDebugSink):
    """
    Debug sink backed by a callable.
    """

    def __init__(
        self,
        callback: Callable[
            [ToolDebugEntry],
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
        entry: ToolDebugEntry,
    ) -> None:
        """Forward the entry to the callback."""

        self._callback(
            entry
        )


# ============================================================
# DEBUG COLLECTOR
# ============================================================


class ToolDebugCollector(ToolObserver):
    """
    Passive observer that captures tool observations.

    The collector maintains a bounded in-memory trace and aggregate
    statistics. It never changes tool behaviour.
    """

    def __init__(
        self,
        *,
        mode: ToolDebugMode = (
            ToolDebugMode.PASSIVE
        ),
        max_entries: int = 1000,
        debug_filter: Optional[
            ToolDebugFilter
        ] = None,
        sink: Optional[
            ToolDebugSink
        ] = None,
    ) -> None:
        if not isinstance(
            mode,
            ToolDebugMode,
        ):
            raise TypeError(
                "mode must be ToolDebugMode."
            )

        if (
            not isinstance(
                max_entries,
                int,
            )
            or isinstance(
                max_entries,
                bool,
            )
            or max_entries <= 0
        ):
            raise ValueError(
                "max_entries must be a positive integer."
            )

        self._mode = mode
        self._max_entries = max_entries

        self._filter = (
            debug_filter
            or ToolDebugFilter()
        )

        self._sink = (
            sink
            or NullToolDebugSink()
        )

        self._entries: deque[
            ToolDebugEntry
        ] = deque(
            maxlen=max_entries
        )

        self._observation_counts: Counter[
            ToolObservationType
        ] = Counter()

        self._tool_counts: Counter[
            str
        ] = Counter()

        self._error_count = 0
        self._event_count = 0
        self._lifecycle_count = 0
        self._state_change_count = 0
        self._execution_count = 0

        self._sequence = 0

        self._lock = RLock()

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def mode(self) -> ToolDebugMode:
        """Return the current debug mode."""

        with self._lock:
            return self._mode

    @property
    def max_entries(self) -> int:
        """Return the maximum retained entries."""

        return self._max_entries

    @property
    def debug_filter(self) -> ToolDebugFilter:
        """Return the current filter."""

        with self._lock:
            return self._filter

    @property
    def entry_count(self) -> int:
        """Return the number of retained entries."""

        with self._lock:
            return len(
                self._entries
            )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def set_mode(
        self,
        mode: ToolDebugMode,
    ) -> None:
        """Set the debugging mode."""

        if not isinstance(
            mode,
            ToolDebugMode,
        ):
            raise TypeError(
                "mode must be ToolDebugMode."
            )

        with self._lock:
            self._mode = mode

    def set_filter(
        self,
        debug_filter: ToolDebugFilter,
    ) -> None:
        """Replace the diagnostic filter."""

        if not isinstance(
            debug_filter,
            ToolDebugFilter,
        ):
            raise TypeError(
                "debug_filter must be ToolDebugFilter."
            )

        with self._lock:
            self._filter = debug_filter

    def set_sink(
        self,
        sink: ToolDebugSink,
    ) -> None:
        """Replace the debug sink."""

        if not callable(
            getattr(
                sink,
                "write",
                None,
            )
        ):
            raise TypeError(
                "sink must provide a write() method."
            )

        with self._lock:
            self._sink = sink

    # ========================================================
    # OBSERVER API
    # ========================================================

    def observe(
        self,
        observation: ToolObservation,
    ) -> None:
        """
        Capture one tool observation.

        Disabled mode performs no collection.
        """

        if not isinstance(
            observation,
            ToolObservation,
        ):
            raise TypeError(
                "observation must be ToolObservation."
            )

        with self._lock:
            if (
                self._mode
                == ToolDebugMode.DISABLED
            ):
                return

            if not self._filter.matches(
                observation
            ):
                return

            entry = self._create_entry(
                observation
            )

            self._entries.append(
                entry
            )

            self._update_statistics(
                observation
            )

            sink = self._sink

        sink.write(
            entry
        )

    # ========================================================
    # QUERY
    # ========================================================

    def entries(
        self,
        *,
        limit: Optional[int] = None,
    ) -> tuple[
        ToolDebugEntry,
        ...
    ]:
        """
        Return retained entries.

        Entries are returned oldest-first.
        """

        with self._lock:
            values = tuple(
                self._entries
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
    ) -> Optional[ToolDebugEntry]:
        """Return the most recent entry."""

        with self._lock:
            if not self._entries:
                return None

            return self._entries[-1]

    def clear(
        self,
    ) -> None:
        """Clear retained trace entries and statistics."""

        with self._lock:
            self._entries.clear()
            self._observation_counts.clear()
            self._tool_counts.clear()

            self._error_count = 0
            self._event_count = 0
            self._lifecycle_count = 0
            self._state_change_count = 0
            self._execution_count = 0

            self._sequence = 0

    def statistics(
        self,
    ) -> ToolDebugStatistics:
        """Return an immutable statistics snapshot."""

        with self._lock:
            return ToolDebugStatistics(
                total_observations=sum(
                    self._observation_counts.values()
                ),
                observation_counts=dict(
                    self._observation_counts
                ),
                tool_counts=dict(
                    self._tool_counts
                ),
                error_count=self._error_count,
                event_count=self._event_count,
                lifecycle_count=self._lifecycle_count,
                state_change_count=(
                    self._state_change_count
                ),
                execution_count=self._execution_count,
                last_sequence=self._sequence,
            )

    def snapshot(
        self,
        *,
        active_tools: Iterable[str] = (),
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolDebugSnapshot:
        """Return a point-in-time diagnostic snapshot."""

        with self._lock:
            return ToolDebugSnapshot(
                mode=self._mode,
                entries=tuple(
                    self._entries
                ),
                statistics=ToolDebugStatistics(
                    total_observations=sum(
                        self._observation_counts.values()
                    ),
                    observation_counts=dict(
                        self._observation_counts
                    ),
                    tool_counts=dict(
                        self._tool_counts
                    ),
                    error_count=self._error_count,
                    event_count=self._event_count,
                    lifecycle_count=(
                        self._lifecycle_count
                    ),
                    state_change_count=(
                        self._state_change_count
                    ),
                    execution_count=(
                        self._execution_count
                    ),
                    last_sequence=self._sequence,
                ),
                active_tools=tuple(
                    active_tools
                ),
                metadata=dict(
                    metadata or {}
                ),
            )

    # ========================================================
    # INTERNAL
    # ========================================================

    def _create_entry(
        self,
        observation: ToolObservation,
    ) -> ToolDebugEntry:
        self._sequence += 1

        tool_id, tool_name = (
            _tool_identity(
                observation.tool
            )
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

        return ToolDebugEntry(
            sequence=self._sequence,
            timestamp=monotonic(),
            observation_type=(
                observation.observation_type
            ),
            tool_id=tool_id,
            tool_name=tool_name,
            event_type=event_type,
            state=observation.state,
            previous_state=(
                observation.previous_state
            ),
            message=observation.message,
            error_type=error_type,
            metadata=dict(
                observation.metadata
            ),
        )

    def _update_statistics(
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

        if observation.observation_type in {
            ToolObservationType.EVENT_RECEIVED,
            ToolObservationType.EVENT_HANDLED,
            ToolObservationType.EVENT_IGNORED,
        }:
            self._event_count += 1

        if observation.observation_type in {
            ToolObservationType.ACTIVATING,
            ToolObservationType.ACTIVATED,
            ToolObservationType.DEACTIVATING,
            ToolObservationType.DEACTIVATED,
            ToolObservationType.SUSPENDING,
            ToolObservationType.SUSPENDED,
            ToolObservationType.RESUMING,
            ToolObservationType.RESUMED,
            ToolObservationType.RESETTING,
            ToolObservationType.RESET,
            ToolObservationType.CANCELLING,
            ToolObservationType.CANCELLED,
        }:
            self._lifecycle_count += 1

        if (
            observation.observation_type
            == ToolObservationType.STATE_CHANGED
        ):
            self._state_change_count += 1

        if observation.observation_type in {
            ToolObservationType.EXECUTION_STARTED,
            ToolObservationType.EXECUTION_COMPLETED,
        }:
            self._execution_count += 1


# ============================================================
# DEBUGGER
# ============================================================


class ToolDebugger:
    """
    Higher-level diagnostic facade around ToolDebugCollector.

    ToolDebugger remains passive and does not control tools.
    """

    def __init__(
        self,
        collector: Optional[
            ToolDebugCollector
        ] = None,
    ) -> None:
        self._collector = (
            collector
            or ToolDebugCollector()
        )

    @property
    def collector(self) -> ToolDebugCollector:
        """Return the underlying collector."""

        return self._collector

    @property
    def enabled(self) -> bool:
        """Return whether debugging is enabled."""

        return (
            self._collector.mode
            != ToolDebugMode.DISABLED
        )

    def enable(
        self,
        *,
        trace: bool = False,
    ) -> None:
        """Enable passive or trace debugging."""

        self._collector.set_mode(
            ToolDebugMode.TRACE
            if trace
            else ToolDebugMode.PASSIVE
        )

    def disable(self) -> None:
        """Disable debugging."""

        self._collector.set_mode(
            ToolDebugMode.DISABLED
        )

    def trace(
        self,
        observation: ToolObservation,
    ) -> None:
        """
        Record an observation while explicitly operating in trace mode.
        """

        if not self.enabled:
            return

        self._collector.observe(
            observation
        )

    def snapshot(
        self,
        *,
        active_tools: Iterable[str] = (),
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolDebugSnapshot:
        """Return a diagnostic snapshot."""

        return self._collector.snapshot(
            active_tools=active_tools,
            metadata=metadata,
        )

    def clear(self) -> None:
        """Clear diagnostic history."""

        self._collector.clear()


# ============================================================
# TRACE HELPERS
# ============================================================


class ToolTraceFormatter:
    """
    Human-readable formatter for debug traces.
    """

    def format(
        self,
        entry: ToolDebugEntry,
    ) -> str:
        """Format one trace entry."""

        timestamp = (
            f"{entry.timestamp:.6f}"
        )

        parts = [
            f"#{entry.sequence}",
            timestamp,
            entry.observation_type.value,
        ]

        if entry.tool_name:
            parts.append(
                f"tool={entry.tool_name}"
            )

        if entry.tool_id:
            parts.append(
                f"id={entry.tool_id}"
            )

        if entry.event_type:
            parts.append(
                f"event={entry.event_type}"
            )

        if entry.message:
            parts.append(
                entry.message
            )

        if entry.error_type:
            parts.append(
                f"error={entry.error_type}"
            )

        return " | ".join(
            parts
        )

    def format_many(
        self,
        entries: Iterable[
            ToolDebugEntry
        ],
    ) -> str:
        """Format multiple trace entries."""

        return "\n".join(
            self.format(
                entry
            )
            for entry in entries
        )


# ============================================================
# IDENTITY HELPERS
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
# PUBLIC API
# ============================================================


__all__ = [
    "ToolDebugMode",
    "ToolDebugEntry",
    "ToolDebugFilter",
    "ToolDebugStatistics",
    "ToolDebugSnapshot",
    "ToolDebugSink",
    "NullToolDebugSink",
    "CallbackToolDebugSink",
    "ToolDebugCollector",
    "ToolDebugger",
    "ToolTraceFormatter",
]
