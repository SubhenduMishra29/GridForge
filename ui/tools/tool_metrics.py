"""
GridForge V2
============

File:
    ui/tools/tool_metrics.py

Purpose
-------
Passive metrics collection for the GridForge UI tool subsystem.

This module records operational metrics derived from ToolObservation
events. Metrics are diagnostic/telemetry data only and must never become
authoritative application state.

Architectural rules
-------------------
- Metrics are observational only.
- Metrics must not mutate Core state.
- Metrics must not execute Commands.
- Metrics must not activate/deactivate tools.
- Metrics must not own tool lifecycle state.
- Metrics must not depend on Qt.
- Metrics must not become an event bus.
- Metrics may consume ToolObservation from tool_observer.py.
- Metrics collection must be safe to disable.
- Metrics must not change tool execution semantics.
- Timing measurements are diagnostic and are not simulation time.
"""

from __future__ import annotations

from collections import Counter, defaultdict
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
# METRIC TYPES
# ============================================================


class ToolMetricType(str, Enum):
    """
    Supported metric categories.
    """

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    DURATION = "duration"


class ToolMetricCategory(str, Enum):
    """
    Logical categories for collected tool metrics.
    """

    LIFECYCLE = "lifecycle"
    INPUT = "input"
    INTERACTION = "interaction"
    EXECUTION = "execution"
    STATE = "state"
    REQUIREMENTS = "requirements"
    ERROR = "error"
    GENERAL = "general"


# ============================================================
# METRIC SAMPLE
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolMetricSample:
    """
    Immutable metric sample.

    ``timestamp`` uses monotonic time and is intended only for local
    diagnostic measurements.
    """

    name: str

    metric_type: ToolMetricType

    value: float

    timestamp: float

    category: ToolMetricCategory = (
        ToolMetricCategory.GENERAL
    )

    tool_id: Optional[str] = None

    tool_name: Optional[str] = None

    observation_type: Optional[
        ToolObservationType
    ] = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "name": self.name,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "category": self.category.value,
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "observation_type": (
                self.observation_type.value
                if self.observation_type is not None
                else None
            ),
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# METRIC VALUE
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolMetricValue:
    """
    Immutable aggregate value for a metric.
    """

    name: str

    metric_type: ToolMetricType

    value: float

    count: int = 0

    minimum: Optional[float] = None

    maximum: Optional[float] = None

    total: float = 0.0

    average: Optional[float] = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "name": self.name,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "count": self.count,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "total": self.total,
            "average": self.average,
            "metadata": dict(
                self.metadata
            ),
        }


# ============================================================
# METRIC STORE
# ============================================================


class ToolMetricStore:
    """
    Thread-safe in-memory store for tool metrics.

    The store is intentionally simple and local. It is not a global
    telemetry service.
    """

    def __init__(
        self,
        *,
        enabled: bool = True,
    ) -> None:
        if not isinstance(
            enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be bool."
            )

        self._enabled = enabled

        self._counter_values: Counter[
            str
        ] = Counter()

        self._gauge_values: dict[
            str,
            float,
        ] = {}

        self._histogram_values: dict[
            str,
            list[float],
        ] = defaultdict(list)

        self._metadata: dict[
            str,
            dict[str, Any],
        ] = {}

        self._metric_types: dict[
            str,
            ToolMetricType,
        ] = {}

        self._lock = RLock()

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def enabled(self) -> bool:
        """Return whether metric collection is enabled."""

        with self._lock:
            return self._enabled

    # ========================================================
    # ENABLE / DISABLE
    # ========================================================

    def enable(self) -> None:
        """Enable metric collection."""

        with self._lock:
            self._enabled = True

    def disable(self) -> None:
        """Disable metric collection."""

        with self._lock:
            self._enabled = False

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        name: str,
        metric_type: ToolMetricType,
        *,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> None:
        """
        Register a metric definition.

        Re-registering the same metric with a different type raises.
        """

        _validate_metric_name(
            name
        )

        if not isinstance(
            metric_type,
            ToolMetricType,
        ):
            raise TypeError(
                "metric_type must be ToolMetricType."
            )

        with self._lock:
            existing = self._metric_types.get(
                name
            )

            if (
                existing is not None
                and existing != metric_type
            ):
                raise ValueError(
                    (
                        f"Metric {name!r} is already registered "
                        f"as {existing.value}."
                    )
                )

            self._metric_types[
                name
            ] = metric_type

            if metadata:
                self._metadata.setdefault(
                    name,
                    {}
                ).update(
                    metadata
                )

    # ========================================================
    # WRITE
    # ========================================================

    def increment(
        self,
        name: str,
        value: float = 1.0,
        *,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> float:
        """Increment a counter metric."""

        self._ensure_enabled()

        self._ensure_registered(
            name,
            ToolMetricType.COUNTER,
            metadata=metadata,
        )

        numeric_value = _finite_float(
            value
        )

        with self._lock:
            self._counter_values[
                name
            ] += numeric_value

            return float(
                self._counter_values[
                    name
                ]
            )

    def set_gauge(
        self,
        name: str,
        value: float,
        *,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> float:
        """Set a gauge metric."""

        self._ensure_enabled()

        self._ensure_registered(
            name,
            ToolMetricType.GAUGE,
            metadata=metadata,
        )

        numeric_value = _finite_float(
            value
        )

        with self._lock:
            self._gauge_values[
                name
            ] = numeric_value

            return numeric_value

    def observe(
        self,
        name: str,
        value: float,
        *,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> float:
        """Add a value to a histogram metric."""

        self._ensure_enabled()

        self._ensure_registered(
            name,
            ToolMetricType.HISTOGRAM,
            metadata=metadata,
        )

        numeric_value = _finite_float(
            value
        )

        with self._lock:
            self._histogram_values[
                name
            ].append(
                numeric_value
            )

            return numeric_value

    # ========================================================
    # READ
    # ========================================================

    def get(
        self,
        name: str,
    ) -> Optional[ToolMetricValue]:
        """Return an aggregate metric value."""

        _validate_metric_name(
            name
        )

        with self._lock:
            metric_type = self._metric_types.get(
                name
            )

            if metric_type is None:
                return None

            metadata = dict(
                self._metadata.get(
                    name,
                    {},
                )
            )

            if metric_type == ToolMetricType.COUNTER:
                value = float(
                    self._counter_values.get(
                        name,
                        0.0,
                    )
                )

                return ToolMetricValue(
                    name=name,
                    metric_type=metric_type,
                    value=value,
                    count=1,
                    total=value,
                    average=value,
                    metadata=metadata,
                )

            if metric_type == ToolMetricType.GAUGE:
                value = float(
                    self._gauge_values.get(
                        name,
                        0.0,
                    )
                )

                return ToolMetricValue(
                    name=name,
                    metric_type=metric_type,
                    value=value,
                    count=1,
                    total=value,
                    average=value,
                    metadata=metadata,
                )

            values = tuple(
                self._histogram_values.get(
                    name,
                    (),
                )
            )

            if not values:
                return ToolMetricValue(
                    name=name,
                    metric_type=metric_type,
                    value=0.0,
                    count=0,
                    minimum=None,
                    maximum=None,
                    total=0.0,
                    average=None,
                    metadata=metadata,
                )

            total = sum(
                values
            )

            average = (
                total / len(values)
            )

            return ToolMetricValue(
                name=name,
                metric_type=metric_type,
                value=values[-1],
                count=len(values),
                minimum=min(values),
                maximum=max(values),
                total=total,
                average=average,
                metadata=metadata,
            )

    def all(
        self,
    ) -> tuple[
        ToolMetricValue,
        ...
    ]:
        """Return all registered metrics."""

        with self._lock:
            names = tuple(
                self._metric_types
            )

        values = []

        for name in names:
            metric = self.get(
                name
            )

            if metric is not None:
                values.append(
                    metric
                )

        return tuple(
            values
        )

    def value(
        self,
        name: str,
        default: float = 0.0,
    ) -> float:
        """Return the current scalar metric value."""

        metric = self.get(
            name
        )

        if metric is None:
            return default

        return metric.value

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
        name: Optional[str] = None,
    ) -> None:
        """
        Reset one metric or all metric values.

        Definitions and metadata are retained.
        """

        with self._lock:
            if name is None:
                self._counter_values.clear()
                self._gauge_values.clear()
                self._histogram_values.clear()
                return

            _validate_metric_name(
                name
            )

            metric_type = self._metric_types.get(
                name
            )

            if metric_type is None:
                return

            if metric_type == ToolMetricType.COUNTER:
                self._counter_values.pop(
                    name,
                    None,
                )

            elif metric_type == ToolMetricType.GAUGE:
                self._gauge_values.pop(
                    name,
                    None,
                )

            elif metric_type in {
                ToolMetricType.HISTOGRAM,
                ToolMetricType.DURATION,
            }:
                self._histogram_values.pop(
                    name,
                    None,
                )

    # ========================================================
    # INTERNAL
    # ========================================================

    def _ensure_enabled(self) -> None:
        with self._lock:
            if not self._enabled:
                raise RuntimeError(
                    "Tool metric collection is disabled."
                )

    def _ensure_registered(
        self,
        name: str,
        metric_type: ToolMetricType,
        *,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> None:
        with self._lock:
            existing = self._metric_types.get(
                name
            )

            if existing is None:
                self.register(
                    name,
                    metric_type,
                    metadata=metadata,
                )
                return

            if existing != metric_type:
                raise ValueError(
                    (
                        f"Metric {name!r} is registered as "
                        f"{existing.value}, not {metric_type.value}."
                    )
                )

            if metadata:
                self._metadata.setdefault(
                    name,
                    {},
                ).update(
                    metadata
                )


# ============================================================
# DURATION MEASUREMENT
# ============================================================


class ToolMetricTimer:
    """
    Context-manager timer for diagnostic durations.

    The measured duration is wall-clock diagnostic time using
    ``time.monotonic()``. It is not simulation time.
    """

    def __init__(
        self,
        store: ToolMetricStore,
        metric_name: str,
        *,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> None:
        if not isinstance(
            store,
            ToolMetricStore,
        ):
            raise TypeError(
                "store must be ToolMetricStore."
            )

        _validate_metric_name(
            metric_name
        )

        self._store = store
        self._metric_name = metric_name
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
        """Return measured duration in seconds."""

        return self._elapsed

    def start(self) -> "ToolMetricTimer":
        """Start the timer."""

        self._started_at = monotonic()
        self._elapsed = None
        return self

    def stop(self) -> float:
        """Stop the timer and record the duration."""

        if self._started_at is None:
            raise RuntimeError(
                "Timer has not been started."
            )

        self._elapsed = (
            monotonic()
            - self._started_at
        )

        self._store._ensure_enabled()

        self._store._ensure_registered(
            self._metric_name,
            ToolMetricType.HISTOGRAM,
            metadata=self._metadata,
        )

        self._store.observe(
            self._metric_name,
            self._elapsed,
            metadata=self._metadata,
        )

        return self._elapsed

    def __enter__(
        self,
    ) -> "ToolMetricTimer":
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
# OBSERVATION MAPPER
# ============================================================


class ToolMetricMapper:
    """
    Converts ToolObservation events into standard metric updates.
    """

    _CATEGORY_MAP = {
        ToolObservationType.ACTIVATING: (
            ToolMetricCategory.LIFECYCLE
        ),
        ToolObservationType.ACTIVATED: (
            ToolMetricCategory.LIFECYCLE
        ),
        ToolObservationType.DEACTIVATING: (
            ToolMetricCategory.LIFECYCLE
        ),
        ToolObservationType.DEACTIVATED: (
            ToolMetricCategory.LIFECYCLE
        ),
        ToolObservationType.SUSPENDING: (
            ToolMetricCategory.LIFECYCLE
        ),
        ToolObservationType.SUSPENDED: (
            ToolMetricCategory.LIFECYCLE
        ),
        ToolObservationType.RESUMING: (
            ToolMetricCategory.LIFECYCLE
        ),
        ToolObservationType.RESUMED: (
            ToolMetricCategory.LIFECYCLE
        ),
        ToolObservationType.RESETTING: (
            ToolMetricCategory.LIFECYCLE
        ),
        ToolObservationType.RESET: (
            ToolMetricCategory.LIFECYCLE
        ),
        ToolObservationType.CANCELLING: (
            ToolMetricCategory.INTERACTION
        ),
        ToolObservationType.CANCELLED: (
            ToolMetricCategory.INTERACTION
        ),
        ToolObservationType.EVENT_RECEIVED: (
            ToolMetricCategory.INPUT
        ),
        ToolObservationType.EVENT_HANDLED: (
            ToolMetricCategory.INTERACTION
        ),
        ToolObservationType.EVENT_IGNORED: (
            ToolMetricCategory.INPUT
        ),
        ToolObservationType.EXECUTION_STARTED: (
            ToolMetricCategory.EXECUTION
        ),
        ToolObservationType.EXECUTION_COMPLETED: (
            ToolMetricCategory.EXECUTION
        ),
        ToolObservationType.STATE_CHANGED: (
            ToolMetricCategory.STATE
        ),
        ToolObservationType.REQUIREMENTS_CHANGED: (
            ToolMetricCategory.REQUIREMENTS
        ),
        ToolObservationType.ERROR: (
            ToolMetricCategory.ERROR
        ),
    }

    def record(
        self,
        store: ToolMetricStore,
        observation: ToolObservation,
    ) -> tuple[
        ToolMetricSample,
        ...
    ]:
        """
        Convert one observation into metric samples and store them.
        """

        if not isinstance(
            store,
            ToolMetricStore,
        ):
            raise TypeError(
                "store must be ToolMetricStore."
            )

        if not isinstance(
            observation,
            ToolObservation,
        ):
            raise TypeError(
                "observation must be ToolObservation."
            )

        tool_id, tool_name = _tool_identity(
            observation.tool
        )

        category = self._CATEGORY_MAP.get(
            observation.observation_type,
            ToolMetricCategory.GENERAL,
        )

        samples: list[
            ToolMetricSample
        ] = []

        base_metadata = dict(
            observation.metadata
        )

        if tool_id is not None:
            base_metadata.setdefault(
                "tool_id",
                tool_id,
            )

        if tool_name is not None:
            base_metadata.setdefault(
                "tool_name",
                tool_name,
            )

        counter_name = (
            "tool.observations.total"
        )

        store.increment(
            counter_name,
            metadata={
                "category": category.value,
            },
        )

        samples.append(
            ToolMetricSample(
                name=counter_name,
                metric_type=ToolMetricType.COUNTER,
                value=1.0,
                timestamp=monotonic(),
                category=category,
                tool_id=tool_id,
                tool_name=tool_name,
                observation_type=(
                    observation.observation_type
                ),
                metadata=base_metadata,
            )
        )

        type_name = (
            "tool.observations."
            f"{observation.observation_type.value}"
        )

        store.increment(
            type_name,
            metadata=base_metadata,
        )

        samples.append(
            ToolMetricSample(
                name=type_name,
                metric_type=ToolMetricType.COUNTER,
                value=1.0,
                timestamp=monotonic(),
                category=category,
                tool_id=tool_id,
                tool_name=tool_name,
                observation_type=(
                    observation.observation_type
                ),
                metadata=base_metadata,
            )
        )

        if tool_name is not None:
            tool_metric_name = (
                "tool.by_name."
                f"{_safe_metric_component(tool_name)}"
            )

            store.increment(
                tool_metric_name,
                metadata=base_metadata,
            )

            samples.append(
                ToolMetricSample(
                    name=tool_metric_name,
                    metric_type=ToolMetricType.COUNTER,
                    value=1.0,
                    timestamp=monotonic(),
                    category=category,
                    tool_id=tool_id,
                    tool_name=tool_name,
                    observation_type=(
                        observation.observation_type
                    ),
                    metadata=base_metadata,
                )
            )

        if observation.error is not None:
            error_metric = (
                "tool.errors.total"
            )

            store.increment(
                error_metric,
                metadata=base_metadata,
            )

            samples.append(
                ToolMetricSample(
                    name=error_metric,
                    metric_type=ToolMetricType.COUNTER,
                    value=1.0,
                    timestamp=monotonic(),
                    category=ToolMetricCategory.ERROR,
                    tool_id=tool_id,
                    tool_name=tool_name,
                    observation_type=(
                        observation.observation_type
                    ),
                    metadata=base_metadata,
                )
            )

        return tuple(
            samples
        )


# ============================================================
# METRICS OBSERVER
# ============================================================


class ToolMetrics(ToolObserver):
    """
    Passive ToolObserver implementation for metric collection.
    """

    def __init__(
        self,
        store: Optional[
            ToolMetricStore
        ] = None,
        *,
        mapper: Optional[
            ToolMetricMapper
        ] = None,
    ) -> None:
        self._store = (
            store
            or ToolMetricStore()
        )

        self._mapper = (
            mapper
            or ToolMetricMapper()
        )

    @property
    def store(self) -> ToolMetricStore:
        """Return the metric store."""

        return self._store

    @property
    def mapper(self) -> ToolMetricMapper:
        """Return the metric mapper."""

        return self._mapper

    def observe(
        self,
        observation: ToolObservation,
    ) -> None:
        """Collect metrics from one observation."""

        self._mapper.record(
            self._store,
            observation,
        )


# ============================================================
# METRIC REPORT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolMetricReport:
    """
    Immutable aggregate report of tool metrics.
    """

    metrics: tuple[
        ToolMetricValue,
        ...
    ]

    generated_at: float

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def get(
        self,
        name: str,
    ) -> Optional[ToolMetricValue]:
        """Return one metric from the report."""

        for metric in self.metrics:
            if metric.name == name:
                return metric

        return None

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable report."""

        return {
            "metrics": [
                metric.to_dict()
                for metric in self.metrics
            ],
            "generated_at": self.generated_at,
            "metadata": dict(
                self.metadata
            ),
        }


class ToolMetricReporter:
    """
    Generates immutable reports from a ToolMetricStore.
    """

    def __init__(
        self,
        store: ToolMetricStore,
    ) -> None:
        if not isinstance(
            store,
            ToolMetricStore,
        ):
            raise TypeError(
                "store must be ToolMetricStore."
            )

        self._store = store

    @property
    def store(self) -> ToolMetricStore:
        """Return the underlying store."""

        return self._store

    def report(
        self,
        *,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolMetricReport:
        """Generate a metric report."""

        return ToolMetricReport(
            metrics=self._store.all(),
            generated_at=monotonic(),
            metadata=dict(
                metadata or {}
            ),
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _validate_metric_name(
    name: str,
) -> None:
    if not isinstance(
        name,
        str,
    ):
        raise TypeError(
            "Metric name must be a string."
        )

    if not name.strip():
        raise ValueError(
            "Metric name must not be empty."
        )


def _finite_float(
    value: float,
) -> float:
    if isinstance(
        value,
        bool,
    ):
        raise TypeError(
            "Metric value must be numeric."
        )

    try:
        numeric_value = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise TypeError(
            "Metric value must be numeric."
        ) from exc

    if numeric_value != numeric_value:
        raise ValueError(
            "Metric value must be finite."
        )

    if numeric_value in {
        float("inf"),
        float("-inf"),
    }:
        raise ValueError(
            "Metric value must be finite."
        )

    return numeric_value


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


def _safe_metric_component(
    value: str,
) -> str:
    """
    Normalize a value for use as a metric-name component.

    Metric names remain deterministic and human-readable.
    """

    characters = []

    for character in str(
        value
    ):
        if (
            character.isalnum()
            or character in {
                "_",
                "-",
            }
        ):
            characters.append(
                character
            )
        else:
            characters.append(
                "_"
            )

    normalized = "".join(
        characters
    ).strip(
        "_"
    )

    return normalized or "unknown"


# ============================================================
# FACTORY
# ============================================================


def create_tool_metrics(
    *,
    enabled: bool = True,
) -> ToolMetrics:
    """
    Create a standard ToolMetrics observer.
    """

    return ToolMetrics(
        ToolMetricStore(
            enabled=enabled
        )
    )


__all__ = [
    "ToolMetricType",
    "ToolMetricCategory",
    "ToolMetricSample",
    "ToolMetricValue",
    "ToolMetricStore",
    "ToolMetricTimer",
    "ToolMetricMapper",
    "ToolMetrics",
    "ToolMetricReport",
    "ToolMetricReporter",
    "create_tool_metrics",
]
