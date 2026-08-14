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
- Events describe plugin lifecycle changes; they do not perform them.
- No concrete plugin imports are performed here.
- Events are UI/application-infrastructure events, not domain events.
- Plugin state remains separate from plugin event transport.
- The event bus/dispatcher is responsible for delivery.
- Plugins must not use these events as a replacement for Core domain
  events.
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
    Canonical lifecycle event types for UI plugins.
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
# EVENT SOURCE
# ============================================================


class PluginEventSource(str, Enum):
    """
    Identifies the subsystem that emitted a plugin event.
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
    Base immutable plugin lifecycle event.

    Events are data only. They do not contain callbacks or executable
    lifecycle operations.
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
        if not isinstance(
            self.plugin_id,
            str,
        ) or not self.plugin_id.strip():
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

        if not isinstance(
            self.event_id,
            str,
        ) or not self.event_id.strip():
            raise ValueError(
                "event_id must be a non-empty string."
            )

        if self.sequence is not None and self.sequence < 0:
            raise ValueError(
                "sequence cannot be negative."
            )


# ============================================================
# STATE EVENT
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginStateEvent(
    PluginEvent
):
    """
    Event representing a plugin lifecycle state transition.
    """

    previous_state: Optional[str] = None

    current_state: Optional[str] = None

    error: Optional[str] = None


# ============================================================
# ERROR EVENT
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginErrorEvent(
    PluginEvent
):
    """
    Event representing a plugin lifecycle failure.
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

        if not isinstance(
            self.error_message,
            str,
        ):
            raise TypeError(
                "error_message must be a string."
            )


# ============================================================
# DEPENDENCY EVENT
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginDependencyEvent(
    PluginEvent
):
    """
    Event describing dependency-related plugin activity.
    """

    dependency_id: str = ""

    dependency_state: Optional[str] = None

    satisfied: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()

        if not isinstance(
            self.dependency_id,
            str,
        ) or not self.dependency_id.strip():
            raise ValueError(
                "dependency_id must be a non-empty string."
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
    """Create a plugin-defined event."""

    return PluginEvent(
        event_type=PluginEventType.DEFINED,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
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

    return PluginEvent(
        event_type=PluginEventType.LOAD_REQUESTED,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
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

    return PluginEvent(
        event_type=PluginEventType.LOADED,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
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

    return PluginEvent(
        event_type=PluginEventType.INITIALIZE_REQUESTED,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
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

    return PluginEvent(
        event_type=PluginEventType.INITIALIZING,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
    )


def plugin_initialized(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.PLUGIN,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a plugin-initialized event."""

    return PluginEvent(
        event_type=PluginEventType.INITIALIZED,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
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

    return PluginEvent(
        event_type=PluginEventType.ENABLED,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
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

    return PluginEvent(
        event_type=PluginEventType.DISABLED,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
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

    return PluginEvent(
        event_type=PluginEventType.SHUTDOWN_REQUESTED,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
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

    return PluginEvent(
        event_type=PluginEventType.SHUTTING_DOWN,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
    )


def plugin_shutdown(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.PLUGIN,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a plugin-shutdown event."""

    return PluginEvent(
        event_type=PluginEventType.SHUTDOWN,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
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

    return PluginEvent(
        event_type=PluginEventType.UNLOAD_REQUESTED,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
    )


def plugin_unloaded(
    plugin_id: str,
    *,
    source: PluginEventSource = PluginEventSource.REGISTRY,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a plugin-unloaded event."""

    return PluginEvent(
        event_type=PluginEventType.UNLOADED,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
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
    """Create a plugin failure event."""

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
        metadata=dict(
            metadata or {}
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
    """Create a plugin-reset event."""

    return PluginEvent(
        event_type=PluginEventType.RESET,
        plugin_id=plugin_id,
        source=source,
        metadata=dict(
            metadata or {}
        ),
    )


# ============================================================
# EVENT PREDICATES
# ============================================================


def is_lifecycle_event(
    event: PluginEvent,
) -> bool:
    """
    Return whether an event represents normal plugin lifecycle flow.
    """

    return event.event_type not in {
        PluginEventType.FAILED,
    }


def is_failure_event(
    event: PluginEvent,
) -> bool:
    """Return whether an event represents plugin failure."""

    return event.event_type == PluginEventType.FAILED


def is_terminal_event(
    event: PluginEvent,
) -> bool:
    """
    Return whether an event represents a completed terminal action.
    """

    return event.event_type in {
        PluginEventType.SHUTDOWN,
        PluginEventType.UNLOADED,
        PluginEventType.FAILED,
    }


# ============================================================
# EVENT SERIALIZATION
# ============================================================


def event_to_dict(
    event: PluginEvent,
) -> dict[str, Any]:
    """
    Convert a plugin event into a serializable dictionary.

    This is intended for diagnostics/logging, not persistence of
    authoritative application state.
    """

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
        PluginStateEvent,
    ):
        data.update(
            {
                "previous_state": event.previous_state,
                "current_state": event.current_state,
                "error": event.error,
            }
        )

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

    if isinstance(
        event,
        PluginDependencyEvent,
    ):
        data.update(
            {
                "dependency_id": event.dependency_id,
                "dependency_state": event.dependency_state,
                "satisfied": event.satisfied,
            }
        )

    return data


__all__ = [
    "PluginEventType",
    "PluginEventSource",
    "PluginEvent",
    "PluginStateEvent",
    "PluginErrorEvent",
    "PluginDependencyEvent",
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
