"""
GridForge V2
============

File:
    ui/plugins/plugin_events.py

Purpose
-------
Defines lifecycle events emitted by the GridForge UI plugin layer.

Architectural rules
-------------------
- Events describe lifecycle activity; they do not perform it.
- No concrete plugin imports are performed here.
- Events are UI/application-infrastructure events, not domain events.
- PluginStateStore remains the runtime-state authority.
- PluginManager remains the lifecycle-orchestration authority.
- PluginRegistry remains the plugin-instance/lifecycle authority.
- Events must not become a second plugin state machine.
- Events must not become a second dependency-resolution system.
- The event dispatcher is responsible only for event delivery.
- Plugin events must never replace Core domain events.
- Event sequence numbers are diagnostic ordering metadata only.
- Monotonic event timing is diagnostic timing only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Any, Mapping, Optional
from uuid import uuid4


# ============================================================
# EVENT TYPE
# ============================================================


class PluginEventType(str, Enum):
    """
    Canonical plugin lifecycle event types.

    Event types describe observable lifecycle activity.
    They do not perform, authorize, or recover from lifecycle
    operations.
    """

    DEFINED = "defined"

    LOAD_REQUESTED = "load_requested"
    LOADED = "loaded"

    INITIALIZE_REQUESTED = "initialize_requested"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"

    ENABLED = "enabled"
    DISABLED = "disabled"

    SHUTDOWN_REQUESTED = "shutdown_requested"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"

    UNLOAD_REQUESTED = "unload_requested"
    UNLOADED = "unloaded"

    FAILED = "failed"

    RESET = "reset"


# ============================================================
# EVENT TYPE GROUPS
# ============================================================


_LIFECYCLE_EVENT_TYPES = frozenset(
    PluginEventType
)


_TERMINAL_EVENT_TYPES = frozenset(
    {
        PluginEventType.SHUTDOWN,
        PluginEventType.UNLOADED,
        PluginEventType.FAILED,
    }
)


# ============================================================
# EVENT SOURCE
# ============================================================


class PluginEventSource(str, Enum):
    """
    Identifies the subsystem responsible for emitting an event.

    The source identifies the emitter of the observation. It does not
    transfer lifecycle ownership to the event subsystem.
    """

    LOADER = "loader"
    REGISTRY = "registry"
    MANAGER = "manager"
    PLUGIN = "plugin"
    SYSTEM = "system"


# ============================================================
# BASE EVENT
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginEvent:
    """
    Immutable plugin lifecycle event.

    PluginEvent is a transport/observation record only.

    It contains:
        - event identity;
        - event type;
        - plugin identity;
        - event source;
        - monotonic timing information;
        - optional event-stream ordering information;
        - diagnostic metadata.

    It does not contain:
        - callbacks;
        - plugin instances;
        - lifecycle commands;
        - PluginStateStore state;
        - dependency-resolution state;
        - Qt objects.

    Timing semantics
    ----------------
    ``timestamp`` is a monotonic, process-relative timing value
    obtained from ``time.monotonic()``.

    It must not be interpreted as:
        - Unix time;
        - wall-clock time;
        - UTC time;
        - a persistent timestamp.

    It is suitable for:
        - ordering observations within a process;
        - measuring lifecycle durations;
        - diagnostics;
        - performance instrumentation.

    Sequence semantics
    ------------------
    ``sequence`` is optional diagnostic event-stream ordering metadata.

    It is not:
        - plugin lifecycle state;
        - PluginStateStore state;
        - a dependency-resolution value;
        - a generation number.

    A dispatcher or other event-stream owner may assign it.
    """

    event_type: PluginEventType

    plugin_id: str

    source: PluginEventSource = PluginEventSource.SYSTEM

    event_id: str = field(
        default_factory=lambda: uuid4().hex
    )

    timestamp: float = field(
        default_factory=monotonic
    )

    sequence: Optional[int] = None

    metadata: Mapping[
        str,
        Any,
    ] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        # ----------------------------------------------------
        # Type validation
        # ----------------------------------------------------

        if not isinstance(
            self.event_type,
            PluginEventType,
        ):
            raise TypeError(
                "event_type must be a PluginEventType."
            )

        if not isinstance(
            self.plugin_id,
            str,
        ):
            raise TypeError(
                "plugin_id must be a string."
            )

        if not self.plugin_id.strip():
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

        if not isinstance(
            self.source,
            PluginEventSource,
        ):
            raise TypeError(
                "source must be a PluginEventSource."
            )

        if not isinstance(
            self.event_id,
            str,
        ):
            raise TypeError(
                "event_id must be a string."
            )

        if not self.event_id.strip():
            raise ValueError(
                "event_id must be a non-empty string."
            )

        if (
            not isinstance(
                self.timestamp,
                (int, float),
            )
            or isinstance(
                self.timestamp,
                bool,
            )
        ):
            raise TypeError(
                "timestamp must be a numeric value."
            )

        if self.sequence is not None:
            if (
                not isinstance(
                    self.sequence,
                    int,
                )
                or isinstance(
                    self.sequence,
                    bool,
                )
            ):
                raise TypeError(
                    "sequence must be an integer or None."
                )

            if self.sequence < 0:
                raise ValueError(
                    "sequence cannot be negative."
                )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a Mapping."
            )

        # ----------------------------------------------------
        # Immutable event snapshot
        # ----------------------------------------------------
        #
        # The dataclass itself is frozen, but Mapping values can
        # otherwise retain the caller's mapping object. Copy the
        # mapping so that later changes to the caller-owned mapping
        # do not alter the event's top-level metadata snapshot.
        #

        object.__setattr__(
            self,
            "metadata",
            dict(
                self.metadata
            ),
        )


# ============================================================
# ERROR EVENT
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginErrorEvent(
    PluginEvent
):
    """
    Immutable plugin lifecycle failure event.

    Failure information is observational.

    The event does not determine whether the plugin is:
        - disabled;
        - reset;
        - retried;
        - unloaded;
        - reinitialized;
        - recovered.

    Lifecycle response remains owned by PluginManager and
    PluginRegistry.
    """

    error_type: str = ""

    error_message: str = ""

    recoverable: bool = False

    operation: Optional[str] = None

    traceback: Optional[str] = None

    def __post_init__(self) -> None:
        super().__post_init__()

        if not isinstance(
            self.error_type,
            str,
        ):
            raise TypeError(
                "error_type must be a string."
            )

        if not self.error_type.strip():
            raise ValueError(
                "error_type must be a non-empty string."
            )

        if not isinstance(
            self.error_message,
            str,
        ):
            raise TypeError(
                "error_message must be a string."
            )

        if not self.error_message.strip():
            raise ValueError(
                "error_message must be a non-empty string."
            )

        if not isinstance(
            self.recoverable,
            bool,
        ):
            raise TypeError(
                "recoverable must be bool."
            )

        if (
            self.operation is not None
            and not isinstance(
                self.operation,
                str,
            )
        ):
            raise TypeError(
                "operation must be a string or None."
            )

        if (
            self.traceback is not None
            and not isinstance(
                self.traceback,
                str,
            )
        ):
            raise TypeError(
                "traceback must be a string or None."
            )


# ============================================================
# EVENT FACTORY HELPER
# ============================================================


def _metadata(
    metadata: Optional[
        Mapping[str, Any]
    ],
) -> dict[str, Any]:
    """
    Create an independent metadata snapshot.
    """

    if metadata is None:
        return {}

    if not isinstance(
        metadata,
        Mapping,
    ):
        raise TypeError(
            "metadata must be a Mapping or None."
        )

    return dict(
        metadata
    )


def _event(
    event_type: PluginEventType,
    plugin_id: str,
    *,
    source: PluginEventSource,
    metadata: Optional[
        Mapping[str, Any]
    ],
) -> PluginEvent:
    """
    Create a standard lifecycle event.

    Validation of event fields is delegated to PluginEvent.
    """

    return PluginEvent(
        event_type=event_type,
        plugin_id=plugin_id,
        source=source,
        metadata=_metadata(
            metadata
        ),
    )


# ============================================================
# EVENT FACTORIES
# ============================================================


def plugin_defined(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """
    Create a plugin-defined event.

    The Manager is the normal source because plugin definitions
    are composition metadata owned by PluginManager.
    """

    return _event(
        PluginEventType.DEFINED,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_load_requested(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a plugin-load-requested event."""

    return _event(
        PluginEventType.LOAD_REQUESTED,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_loaded(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.LOADER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a plugin-loaded event."""

    return _event(
        PluginEventType.LOADED,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_initialize_requested(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create an initialization-requested event."""

    return _event(
        PluginEventType.INITIALIZE_REQUESTED,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_initializing(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create an initializing event."""

    return _event(
        PluginEventType.INITIALIZING,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_initialized(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a plugin-initialized event."""

    return _event(
        PluginEventType.INITIALIZED,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_enabled(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a plugin-enabled event."""

    return _event(
        PluginEventType.ENABLED,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_disabled(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a plugin-disabled event."""

    return _event(
        PluginEventType.DISABLED,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_shutdown_requested(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a shutdown-requested event."""

    return _event(
        PluginEventType.SHUTDOWN_REQUESTED,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_shutting_down(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a shutting-down event."""

    return _event(
        PluginEventType.SHUTTING_DOWN,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_shutdown(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a plugin-shutdown event."""

    return _event(
        PluginEventType.SHUTDOWN,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_unload_requested(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create an unload-requested event."""

    return _event(
        PluginEventType.UNLOAD_REQUESTED,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_unloaded(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a plugin-unloaded event."""

    return _event(
        PluginEventType.UNLOADED,
        plugin_id,
        source=source,
        metadata=metadata,
    )


def plugin_failed(
    plugin_id: str,
    error: BaseException | str,
    *,
    operation: Optional[str] = None,
    recoverable: bool = False,
    source: PluginEventSource = PluginEventSource.MANAGER,
    traceback: Optional[str] = None,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginErrorEvent:
    """
    Create a plugin failure event.

    Traceback capture is intentionally left to the caller. This
    factory does not implicitly capture process exception state.
    """

    if isinstance(
        error,
        BaseException,
    ):
        error_type = type(
            error
        ).__name__

        error_message = str(
            error
        )
    else:
        error_type = "PluginError"
        error_message = str(
            error
        )

    return PluginErrorEvent(
        event_type=PluginEventType.FAILED,
        plugin_id=plugin_id,
        source=source,
        error_type=error_type,
        error_message=error_message,
        recoverable=recoverable,
        operation=operation,
        traceback=traceback,
        metadata=_metadata(
            metadata
        ),
    )


def plugin_reset(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.MANAGER,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """
    Create a plugin-reset event.

    RESET is observational only. It does not define the resulting
    PluginStateStore state and does not itself perform a reset.
    """

    return _event(
        PluginEventType.RESET,
        plugin_id,
        source=source,
        metadata=metadata,
    )


# ============================================================
# EVENT PREDICATES
# ============================================================


def is_lifecycle_event(
    event: PluginEvent,
) -> bool:
    """
    Return whether an event belongs to the canonical plugin
    lifecycle event stream.

    PluginEvent currently represents only lifecycle events, but the
    explicit type-set check keeps this predicate semantically useful
    if additional non-lifecycle PluginEvent types are introduced
    later.
    """

    if not isinstance(
        event,
        PluginEvent,
    ):
        raise TypeError(
            "event must be a PluginEvent."
        )

    return event.event_type in (
        _LIFECYCLE_EVENT_TYPES
    )


def is_failure_event(
    event: PluginEvent,
) -> bool:
    """Return whether an event represents plugin failure."""

    if not isinstance(
        event,
        PluginEvent,
    ):
        raise TypeError(
            "event must be a PluginEvent."
        )

    return (
        event.event_type
        == PluginEventType.FAILED
    )


def is_terminal_event(
    event: PluginEvent,
) -> bool:
    """
    Return whether an event represents a completed terminal action.

    FAILED is terminal for the particular lifecycle attempt, but it
    does not imply that the plugin has been unloaded, destroyed, or
    placed into any particular recovery state.
    """

    if not isinstance(
        event,
        PluginEvent,
    ):
        raise TypeError(
            "event must be a PluginEvent."
        )

    return event.event_type in (
        _TERMINAL_EVENT_TYPES
    )


# ============================================================
# EVENT SERIALIZATION
# ============================================================


def event_to_dict(
    event: PluginEvent,
) -> dict[str, Any]:
    """
    Convert a plugin event to a diagnostic dictionary.

    The result is intended for logging, diagnostics, telemetry, and
    debugging only.

    It is not an authoritative representation of plugin runtime
    state and must not be used to reconstruct PluginStateStore.
    """

    if not isinstance(
        event,
        PluginEvent,
    ):
        raise TypeError(
            "event must be a PluginEvent."
        )

    data: dict[str, Any] = {
        "event_id": event.event_id,
        "event_type": event.event_type.value,
        "plugin_id": event.plugin_id,
        "source": event.source.value,
        "timestamp": event.timestamp,
        "sequence": event.sequence,
        "metadata": dict(
            event.metadata
        ),
    }

    if isinstance(
        event,
        PluginErrorEvent,
    ):
        data.update(
            {
                "error_type": event.error_type,
                "error_message": event.error_message,
                "recoverable": event.recoverable,
                "operation": event.operation,
                "traceback": event.traceback,
            }
        )

    return data


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "PluginEventType",
    "PluginEventSource",
    "PluginEvent",
    "PluginErrorEvent",
    "plugin_defined",
    "plugin_load_requested",
    "plugin_loaded",
    "plugin_initialize_requested",
    "plugin_initializing",
    "plugin_initialized",
    "plugin_enabled",
    "plugin_disabled",
    "plugin_shutdown_requested",
    "plugin_shutting_down",
    "plugin_shutdown",
    "plugin_unload_requested",
    "plugin_unloaded",
    "plugin_failed",
    "plugin_reset",
    "is_lifecycle_event",
    "is_failure_event",
    "is_terminal_event",
    "event_to_dict",
]
