"""
GridForge V2
============

File:
    ui/tools/tool_profile.py

Purpose
-------
Passive profiling support for the GridForge UI tool subsystem.

This module aggregates diagnostic timing information for tool
observations and interactions. Profiling is strictly observational and
must never become part of authoritative application state.

Architectural rules
-------------------
- Profiling must not mutate Core state.
- Profiling must not execute Commands.
- Profiling must not activate/deactivate tools.
- Profiling must not own authoritative tool state.
- Profiling must not depend on Qt.
- Profiling must not become an event bus.
- Profiling timestamps are diagnostic wall-clock measurements.
- Profiling may consume ToolObservation instances.
- Profiling can be disabled without changing tool semantics.
"""

from __future__ import annotations

from collections import defaultdict
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
# PROFILE MODE
# ============================================================


class ToolProfileMode(str, Enum):
    """Profiling collection modes."""

    DISABLED = "disabled"
    AGGREGATE = "aggregate"
    DETAILED = "detailed"


# ============================================================
# PROFILE KEY
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolProfileKey:
    """
    Identifies one profiling stream.
    """

    name: str

    tool_id: Optional[str] = None

    tool_name: Optional[str] = None

    observation_type: Optional[
        ToolObservationType
    ] = None

    event_type: Optional[str] = None

    def as_string(self) -> str:
        """Return a deterministic human-readable key."""

        parts = [self.name]

        if self.tool_name:
            parts.append(
                f"tool={self.tool_name}"
            )

        if self.tool_id:
            parts.append(
                f"id={self.tool_id}"
            )

        if self.observation_type is not None:
            parts.append(
                f"observation="
                f"{self.observation_type.value}"
            )

        if self.event_type:
            parts.append(
                f"event={self.event_type}"
            )

        return "|".join(parts)


# ============================================================
# PROFILE SAMPLE
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolProfileSample:
    """
    Immutable profiling sample.
    """

    key: ToolProfileKey

    duration: float

    timestamp: float

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""

        return {
            "key": self.key.as_string(),
            "duration": self.duration,
            "timestamp": self.timestamp,
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# PROFILE VALUE
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolProfileValue:
    """
    Aggregate statistics for one profiling stream.
    """

    key: ToolProfileKey

    count: int

    total: float

    minimum: Optional[float]

    maximum: Optional[float]

    average: Optional[float]

    last: Optional[float]

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""

        return {
            "key": self.key.as_string(),
            "count": self.count,
            "total": self.total,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "average": self.average,
            "last": self.last,
        }


# ============================================================
# PROFILE FILTER
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolProfileFilter:
    """
    Immutable filter for profiling observations.
    """

    observation_types: frozenset[
        ToolObservationType
    ] = frozenset()

    tool_ids: frozenset[str] = frozenset()

    tool_names: frozenset[str] = frozenset()

    event_types: frozenset[str] = frozenset()

    def matches(
        self,
        observation: ToolObservation,
    ) -> bool:
        """Return whether an observation is eligible."""

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

        return True


# ============================================================
# PROFILE STORE
# ============================================================


@dataclass(slots=True)
class _MutableProfile:
    """
    Internal mutable aggregate.
    """

    count: int = 0

    total: float = 0.0

    minimum: Optional[float] = None

    maximum: Optional[float] = None

    last: Optional[float] = None


class ToolProfileStore:
    """
    Thread-safe in-memory profiling store.

    This store contains diagnostics only. It is not authoritative
    application state.
    """

    def __init__(
        self,
        *,
        mode: ToolProfileMode = (
            ToolProfileMode.AGGREGATE
        ),
        max_samples: int = 5000,
    ) -> None:
        if not isinstance(
            mode,
            ToolProfileMode,
        ):
            raise TypeError(
                "mode must be ToolProfileMode."
            )

        if (
            not isinstance(
                max_samples,
                int,
            )
            or isinstance(
                max_samples,
                bool,
            )
            or max_samples <= 0
        ):
            raise ValueError(
                "max_samples must be a positive integer."
            )

        self._mode = mode
        self._max_samples = max_samples

        self._profiles: dict[
            ToolProfileKey,
            _MutableProfile,
        ] = {}

        self._samples: list[
            ToolProfileSample
        ] = []

        self._lock = RLock()

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def mode(self) -> ToolProfileMode:
        """Return the current profiling mode."""

        with self._lock:
            return self._mode

    @property
    def max_samples(self) -> int:
        """Return the sample retention limit."""

        return self._max_samples

    @property
    def enabled(self) -> bool:
        """Return whether profiling is enabled."""

        with self._lock:
            return (
                self._mode
                != ToolProfileMode.DISABLED
            )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def set_mode(
        self,
        mode: ToolProfileMode,
    ) -> None:
        """Change profiling mode."""

        if not isinstance(
            mode,
            ToolProfileMode,
        ):
            raise TypeError(
                "mode must be ToolProfileMode."
            )

        with self._lock:
            self._mode = mode

    # ========================================================
    # RECORD
    # ========================================================

    def record(
        self,
        key: ToolProfileKey,
        duration: float,
        *,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> Optional[ToolProfileSample]:
        """
        Record one profiling measurement.

        Disabled profiling returns None.
        """

        if not isinstance(
            key,
            ToolProfileKey,
        ):
            raise TypeError(
                "key must be ToolProfileKey."
            )

        duration = _finite_non_negative_float(
            duration
        )

        with self._lock:
            if (
                self._mode
                == ToolProfileMode.DISABLED
            ):
                return None

            profile = self._profiles.setdefault(
                key,
                _MutableProfile()
            )

            profile.count += 1
            profile.total += duration
            profile.last = duration

            if (
                profile.minimum is None
                or duration < profile.minimum
            ):
                profile.minimum = duration

            if (
                profile.maximum is None
                or duration > profile.maximum
            ):
                profile.maximum = duration

            sample = ToolProfileSample(
                key=key,
                duration=duration,
                timestamp=monotonic(),
                metadata=dict(
                    metadata or {}
                ),
            )

            if (
                self._mode
                == ToolProfileMode.DETAILED
            ):
                self._samples.append(
                    sample
                )

                if len(
                    self._samples
                ) > self._max_samples:
                    del self._samples[
                        : len(self._samples)
                        - self._max_samples
                    ]

            return sample

    # ========================================================
    # QUERY
    # ========================================================

    def get(
        self,
        key: ToolProfileKey,
    ) -> Optional[ToolProfileValue]:
        """Return aggregate data for a profiling key."""

        if not isinstance(
            key,
            ToolProfileKey,
        ):
            raise TypeError(
                "key must be ToolProfileKey."
            )

        with self._lock:
            profile = self._profiles.get(
                key
            )

            if profile is None:
                return None

            average = (
                profile.total / profile.count
                if profile.count
                else None
            )

            return ToolProfileValue(
                key=key,
                count=profile.count,
                total=profile.total,
                minimum=profile.minimum,
                maximum=profile.maximum,
                average=average,
                last=profile.last,
            )

    def values(
        self,
    ) -> tuple[
        ToolProfileValue,
        ...
    ]:
        """Return all aggregate profiling values."""

        with self._lock:
            keys = tuple(
                self._profiles
            )

        values = []

        for key in keys:
            value = self.get(
                key
            )

            if value is not None:
                values.append(
                    value
                )

        return tuple(
            values
        )

    def samples(
        self,
        *,
        limit: Optional[int] = None,
    ) -> tuple[
        ToolProfileSample,
        ...
    ]:
        """Return retained detailed samples."""

        with self._lock:
            samples = tuple(
                self._samples
            )

        if limit is None:
            return samples

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

        return samples[-limit:]

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
        key: Optional[ToolProfileKey] = None,
    ) -> None:
        """
        Reset one profiling stream or all profiling data.
        """

        with self._lock:
            if key is None:
                self._profiles.clear()
                self._samples.clear()
                return

            if not isinstance(
                key,
                ToolProfileKey,
            ):
                raise TypeError(
                    "key must be ToolProfileKey."
                )

            self._profiles.pop(
                key,
                None,
            )

            self._samples = [
                sample
                for sample in self._samples
                if sample.key != key
            ]


# ============================================================
# PROFILE TIMER
# ============================================================


class ToolProfileTimer:
    """
    Context-manager for diagnostic timing.

    The measured time is wall-clock diagnostic time and is not related
    to simulation time.
    """

    def __init__(
        self,
        store: ToolProfileStore,
        key: ToolProfileKey,
        *,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> None:
        if not isinstance(
            store,
            ToolProfileStore,
        ):
            raise TypeError(
                "store must be ToolProfileStore."
            )

        if not isinstance(
            key,
            ToolProfileKey,
        ):
            raise TypeError(
                "key must be ToolProfileKey."
            )

        self._store = store
        self._key = key
        self._metadata = dict(
            metadata or {}
        )

        self._started_at: Optional[
            float
        ] = None

        self._elapsed: Optional[
            float
        ] = None

    @property
    def elapsed(self) -> Optional[float]:
        """Return elapsed time, if stopped."""

        return self._elapsed

    def start(self) -> "ToolProfileTimer":
        """Start the timer."""

        self._started_at = monotonic()
        self._elapsed = None
        return self

    def stop(self) -> Optional[ToolProfileSample]:
        """Stop and record the timer."""

        if self._started_at is None:
            raise RuntimeError(
                "Timer has not been started."
            )

        self._elapsed = (
            monotonic()
            - self._started_at
        )

        return self._store.record(
            self._key,
            self._elapsed,
            metadata=self._metadata,
        )

    def __enter__(
        self,
    ) -> "ToolProfileTimer":
        return self.start()

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        if self._started_at is not None:
            self.stop()


# ============================================================
# OBSERVATION PROFILER
# ============================================================


class ToolObservationProfiler(ToolObserver):
    """
    Passive profiler that measures intervals between relevant tool
    observations.

    The profiler uses observation timestamps only for diagnostic
    analysis. It does not impose timing on the tool subsystem.
    """

    def __init__(
        self,
        store: Optional[
            ToolProfileStore
        ] = None,
        *,
        profile_filter: Optional[
            ToolProfileFilter
        ] = None,
    ) -> None:
        self._store = (
            store
            or ToolProfileStore()
        )

        self._filter = (
            profile_filter
            or ToolProfileFilter()
        )

        self._last_observation: dict[
            tuple[
                Optional[str],
                Optional[str],
            ],
            float,
        ] = {}

        self._lock = RLock()

    @property
    def store(self) -> ToolProfileStore:
        """Return the profiling store."""

        return self._store

    @property
    def profile_filter(self) -> ToolProfileFilter:
        """Return the active filter."""

        return self._filter

    def set_filter(
        self,
        profile_filter: ToolProfileFilter,
    ) -> None:
        """Replace the profiling filter."""

        if not isinstance(
            profile_filter,
            ToolProfileFilter,
        ):
            raise TypeError(
                "profile_filter must be ToolProfileFilter."
            )

        with self._lock:
            self._filter = profile_filter

    def observe(
        self,
        observation: ToolObservation,
    ) -> None:
        """
        Record diagnostic inter-observation timing.

        Each tool has its own timing stream.
        """

        if not isinstance(
            observation,
            ToolObservation,
        ):
            raise TypeError(
                "observation must be ToolObservation."
            )

        with self._lock:
            if not self._filter.matches(
                observation
            ):
                return

            if not self._store.enabled:
                return

            tool_id, tool_name = _tool_identity(
                observation.tool
            )

            identity = (
                tool_id,
                tool_name,
            )

            now = monotonic()
            previous = self._last_observation.get(
                identity
            )

            self._last_observation[
                identity
            ] = now

            if previous is None:
                return

            duration = (
                now - previous
            )

            key = ToolProfileKey(
                name="tool.observation.interval",
                tool_id=tool_id,
                tool_name=tool_name,
                observation_type=(
                    observation.observation_type
                ),
                event_type=_event_type(
                    observation.event
                ),
            )

            self._store.record(
                key,
                duration,
                metadata=observation.metadata,
            )

    def reset_timing(
        self,
    ) -> None:
        """Clear diagnostic timing baselines."""

        with self._lock:
            self._last_observation.clear()


# ============================================================
# PROFILE SESSION
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolProfileSession:
    """
    Immutable profile session report.
    """

    started_at: float

    ended_at: Optional[float]

    values: tuple[
        ToolProfileValue,
        ...
    ]

    samples: tuple[
        ToolProfileSample,
        ...
    ]

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    @property
    def duration(self) -> Optional[float]:
        """Return session duration."""

        if self.ended_at is None:
            return None

        return max(
            0.0,
            self.ended_at
            - self.started_at,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable session report."""

        return {
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration": self.duration,
            "values": [
                value.to_dict()
                for value in self.values
            ],
            "samples": [
                sample.to_dict()
                for sample in self.samples
            ],
            "metadata": dict(
                self.metadata
            ),
        }


class ToolProfiler:
    """
    High-level profiling facade.

    The profiler is diagnostic only and has no authority over tool
    execution.
    """

    def __init__(
        self,
        store: Optional[
            ToolProfileStore
        ] = None,
    ) -> None:
        self._store = (
            store
            or ToolProfileStore()
        )

        self._started_at: Optional[
            float
        ] = None

        self._lock = RLock()

    @property
    def store(self) -> ToolProfileStore:
        """Return the profile store."""

        return self._store

    @property
    def active(self) -> bool:
        """Return whether a profiling session is active."""

        with self._lock:
            return (
                self._started_at is not None
            )

    def start(
        self,
        *,
        reset: bool = True,
    ) -> None:
        """Start a profiling session."""

        with self._lock:
            if reset:
                self._store.reset()

            self._started_at = monotonic()

    def stop(
        self,
        *,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolProfileSession:
        """Stop and return a profiling session."""

        with self._lock:
            if self._started_at is None:
                raise RuntimeError(
                    "Profiler is not active."
                )

            started_at = self._started_at
            ended_at = monotonic()

            self._started_at = None

            return ToolProfileSession(
                started_at=started_at,
                ended_at=ended_at,
                values=self._store.values(),
                samples=self._store.samples(),
                metadata=dict(
                    metadata or {}
                ),
            )

    def snapshot(
        self,
        *,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolProfileSession:
        """Return a non-stopping snapshot."""

        with self._lock:
            now = monotonic()

            started_at = (
                self._started_at
                if self._started_at is not None
                else now
            )

            return ToolProfileSession(
                started_at=started_at,
                ended_at=None,
                values=self._store.values(),
                samples=self._store.samples(),
                metadata=dict(
                    metadata or {}
                ),
            )

    def timer(
        self,
        name: str,
        *,
        tool: Any = None,
        observation_type: Optional[
            ToolObservationType
        ] = None,
        event: Any = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolProfileTimer:
        """Create a diagnostic timer."""

        tool_id, tool_name = _tool_identity(
            tool
        )

        key = ToolProfileKey(
            name=name,
            tool_id=tool_id,
            tool_name=tool_name,
            observation_type=observation_type,
            event_type=_event_type(
                event
            ),
        )

        return ToolProfileTimer(
            self._store,
            key,
            metadata=metadata,
        )


# ============================================================
# REPORTER
# ============================================================


class ToolProfileReporter:
    """Generates reports from a profile store."""

    def __init__(
        self,
        store: ToolProfileStore,
    ) -> None:
        if not isinstance(
            store,
            ToolProfileStore,
        ):
            raise TypeError(
                "store must be ToolProfileStore."
            )

        self._store = store

    def report(
        self,
    ) -> tuple[
        ToolProfileValue,
        ...
    ]:
        """Return all aggregate profile values."""

        return self._store.values()

    def slowest(
        self,
        *,
        limit: int = 10,
    ) -> tuple[
        ToolProfileValue,
        ...
    ]:
        """Return the slowest profiling streams by average duration."""

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

        values = [
            value
            for value in self._store.values()
            if value.average is not None
        ]

        values.sort(
            key=lambda value: (
                value.average
                if value.average is not None
                else 0.0
            ),
            reverse=True,
        )

        return tuple(
            values[:limit]
        )


# ============================================================
# HELPERS
# ============================================================


def _finite_non_negative_float(
    value: float,
) -> float:
    if isinstance(
        value,
        bool,
    ):
        raise TypeError(
            "Duration must be numeric."
        )

    try:
        numeric = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise TypeError(
            "Duration must be numeric."
        ) from exc

    if numeric != numeric:
        raise ValueError(
            "Duration must be finite."
        )

    if numeric in {
        float("inf"),
        float("-inf"),
    }:
        raise ValueError(
            "Duration must be finite."
        )

    if numeric < 0.0:
        raise ValueError(
            "Duration must not be negative."
        )

    return numeric


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


def create_tool_profiler(
    *,
    mode: ToolProfileMode = (
        ToolProfileMode.AGGREGATE
    ),
    max_samples: int = 5000,
) -> ToolProfiler:
    """
    Create a standard diagnostic profiler.
    """

    return ToolProfiler(
        ToolProfileStore(
            mode=mode,
            max_samples=max_samples,
        )
    )


__all__ = [
    "ToolProfileMode",
    "ToolProfileKey",
    "ToolProfileSample",
    "ToolProfileValue",
    "ToolProfileFilter",
    "ToolProfileStore",
    "ToolProfileTimer",
    "ToolObservationProfiler",
    "ToolProfileSession",
    "ToolProfiler",
    "ToolProfileReporter",
    "create_tool_profiler",
]
