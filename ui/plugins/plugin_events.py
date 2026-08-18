"""
GridForge V2
============

File:
    ui/plugins/plugin_events.py

Purpose
-------
Defines immutable lifecycle events emitted by the GridForge UI plugin
infrastructure.

Architectural role
------------------
Plugin events are observational infrastructure events.

They describe:
    - lifecycle requests;
    - lifecycle transitions;
    - lifecycle completion;
    - lifecycle failures;
    - diagnostic information.

They do NOT:
    - execute lifecycle operations;
    - authorize lifecycle operations;
    - own plugin runtime state;
    - resolve dependencies;
    - order lifecycle operations;
    - own plugin instances;
    - replace PluginStateStore;
    - replace PluginRegistry;
    - replace PluginManager;
    - represent Core/domain events;
    - contain Qt objects.

Lifecycle ownership
-------------------
PluginManager owns:
    - lifecycle orchestration;
    - dependency resolution;
    - lifecycle ordering.

PluginRegistry owns:
    - plugin instances;
    - low-level lifecycle execution.

PluginStateStore owns:
    - canonical observable runtime state.

Plugin events provide:
    - an observational event stream for diagnostics,
      monitoring, logging, and UI infrastructure.

Events are not a second state machine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from types import MappingProxyType
from typing import Any, Mapping, Optional
from uuid import uuid4


# ============================================================
# EVENT TYPE
# ============================================================


class PluginEventType(str, Enum):
    """
    Canonical UI-plugin lifecycle event types.

    Event types describe observable activity only.

    They do not authorize or perform the associated lifecycle
    operation.
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
    Identifies the subsystem that emitted an event.

    This is diagnostic attribution only. It does not transfer
    lifecycle ownership to the event subsystem.
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
    Immutable observational plugin lifecycle event.

    The event contains facts about lifecycle activity.

    It contains no:
        - plugin instance;
        - lifecycle command;
        - callback;
        - PluginState;
        - dependency graph;
        - PluginContext;
        - Qt object.
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

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Validate and freeze the event snapshot."""

        # ----------------------------------------------------
        # Event type
        # ----------------------------------------------------

        if not isinstance(
            self.event_type,
            PluginEventType,
        ):
            raise TypeError(
                "event_type must be a PluginEventType."
            )

        # ----------------------------------------------------
        # Plugin ID
        # ----------------------------------------------------

        self._validate_plugin_id(
            self.plugin_id
        )

        # ----------------------------------------------------
        # Source
        # ----------------------------------------------------

        if not isinstance(
            self.source,
            PluginEventSource,
        ):
            raise TypeError(
                "source must be a PluginEventSource."
            )

        # ----------------------------------------------------
        # Event ID
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Sequence
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a Mapping."
            )

        # ----------------------------------------------------
        # Immutable metadata snapshot
        # ----------------------------------------------------

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )

    @staticmethod
    def _validate_plugin_id(
        plugin_id: str,
    ) -> None:
        """Validate a plugin identifier."""

        if not isinstance(
            plugin_id,
            str,
        ):
            raise TypeError(
                "plugin_id must be a string."
            )

        if not plugin_id.strip():
            raise ValueError(
                "plugin_id must be a non-empty string."
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

    Failure events describe an unsuccessful lifecycle operation.

    They do not determine recovery policy. Recovery remains owned by
    PluginManager / PluginRegistry.
    """

    error_type: str = ""

    error_message: str = ""

    recoverable: bool = False

    operation: Optional[str] = None

    traceback: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate the base event and failure-specific data."""

        PluginEvent.__post_init__(self)

        # ----------------------------------------------------
        # Error type
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Error message
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Recoverability
        # ----------------------------------------------------

        if not isinstance(
            self.recoverable,
            bool,
        ):
            raise TypeError(
                "recoverable must be bool."
            )

        # ----------------------------------------------------
        # Operation
        # ----------------------------------------------------

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
            isinstance(
                self.operation,
                str,
            )
            and not self.operation.strip()
        ):
            raise ValueError(
                "operation must be non-empty when provided."
            )

        # ----------------------------------------------------
        # Traceback
        # ----------------------------------------------------

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
# INTERNAL HELPERS
# ============================================================


def _metadata(
    metadata: Optional[
        Mapping[str, Any]
    ],
) -> Mapping[str, Any]:
    """
    Create an independent metadata snapshot.

    The returned mapping is immutable.
    """

    if metadata is None:
        return MappingProxyType({})

    if not isinstance(
        metadata,
        Mapping,
    ):
        raise TypeError(
            "metadata must be a Mapping or None."
        )

    return MappingProxyType(
        dict(metadata)
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
    """Create a standard immutable lifecycle event."""

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
    """Create a plugin-definition event."""

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
    """Create an initialization-started event."""

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
    """Create a successful initialization event."""

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
    """Create a shutdown-started event."""

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
    """Create a successful plugin-shutdown event."""

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
    source: PluginEventSource = PluginEventSource.REGISTRY,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> PluginEvent:
    """Create a successful plugin-unloaded event."""

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
    Create a plugin lifecycle failure event.

    The failure event records the error only. It does not prescribe
    recovery.
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
        ).strip()

        if not error_message:
            error_message = (
                "Plugin lifecycle operation failed."
            )

    elif isinstance(
        error,
        str,
    ):
        error_type = "PluginError"
        error_message = error.strip()

        if not error_message:
            error_message = (
                "Plugin lifecycle operation failed."
            )

    else:
        raise TypeError(
            "error must be an exception or string."
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
    """Create a plugin-runtime-reset event."""

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
    Return whether the object is a plugin lifecycle event.

    All PluginEvent instances belong to this infrastructure event
    stream. This predicate exists primarily as a type-safe public
    boundary for event consumers.
    """

    if not isinstance(
        event,
        PluginEvent,
    ):
        raise TypeError(
            "event must be a PluginEvent."
        )

    return True


def is_failure_event(
    event: PluginEvent,
) -> bool:
    """Return whether the event represents a lifecycle failure."""

    if not isinstance(
        event,
        PluginEvent,
    ):
        raise TypeError(
            "event must be a PluginEvent."
        )

    return (
        event.event_type
        is PluginEventType.FAILED
    )


def is_terminal_event(
    event: PluginEvent,
) -> bool:
    """
    Return whether the event terminates the current lifecycle attempt.

    FAILED is terminal for the attempted operation only. It does not
    imply shutdown, unload, destruction, or recovery.
    """

    if not isinstance(
        event,
        PluginEvent,
    ):
        raise TypeError(
            "event must be a PluginEvent."
        )

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
    Convert an event to a diagnostic dictionary.

    The returned dictionary is independent from the event and is
    intended for logging, diagnostics, persistence, or inspection.

    It is not authoritative runtime state.
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
