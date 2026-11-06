"""
GridForge V2
============

File:
    ui/tools/tool_observer.py

Purpose
-------
Observation interface for the GridForge UI tool subsystem.

ToolObserver provides a passive observation boundary for tool lifecycle,
interaction, state, and execution notifications.

Architectural rules
-------------------
- Observers are passive.
- Observers must not mutate Core state.
- Observers must not execute Commands.
- Observers must not activate/deactivate tools.
- Observers must not own tool state.
- Observers must not become an event bus.
- Qt-specific observers may adapt this interface externally.
- ToolManager remains authoritative for tool lifecycle.
- ToolDispatcher remains authoritative for event dispatch.
- CommandController remains authoritative for command orchestration.

The observer layer exists primarily for:
    - status/UI synchronization;
    - diagnostics;
    - telemetry;
    - logging;
    - instrumentation;
    - development-time inspection.

It intentionally does not impose a GUI framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Optional, Protocol


# ============================================================
# OBSERVER EVENT TYPE
# ============================================================


class ToolObservationType(str, Enum):
    """
    Categories of observations emitted by the tool subsystem.
    """

    ACTIVATING = "activating"
    ACTIVATED = "activated"

    DEACTIVATING = "deactivating"
    DEACTIVATED = "deactivated"

    SUSPENDING = "suspending"
    SUSPENDED = "suspended"

    RESUMING = "resuming"
    RESUMED = "resumed"

    RESETTING = "resetting"
    RESET = "reset"

    CANCELLING = "cancelling"
    CANCELLED = "cancelled"

    EVENT_RECEIVED = "event_received"
    EVENT_HANDLED = "event_handled"
    EVENT_IGNORED = "event_ignored"

    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"

    STATE_CHANGED = "state_changed"

    REQUIREMENTS_CHANGED = "requirements_changed"

    ERROR = "error"


# ============================================================
# OBSERVATION SEVERITY
# ============================================================


class ToolObservationSeverity(str, Enum):
    """
    Severity associated with an observation.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# ============================================================
# OBSERVATION RECORD
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolObservation:
    """
    Immutable observation emitted by the tool subsystem.

    This object is descriptive only. It does not represent an
    instruction and must never be interpreted as a command.
    """

    observation_type: ToolObservationType

    tool: Any = None

    previous_tool: Any = None

    next_tool: Any = None

    event: Any = None

    result: Any = None

    state: Any = None

    previous_state: Any = None

    context: Any = None

    error: Optional[BaseException] = None

    severity: ToolObservationSeverity = (
        ToolObservationSeverity.INFO
    )

    message: str = ""

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    @property
    def failed(self) -> bool:
        """Return whether the observation represents an error."""

        return self.error is not None

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "observation_type": self.observation_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "failed": self.failed,
            "metadata": dict(self.metadata),
        }


# ============================================================
# OBSERVER RESULT
# ============================================================


class ToolObserverResult(str, Enum):
    """
    Result of notifying an observer.

    Observers are passive, so the result is informational only.
    """

    ACCEPTED = "accepted"
    FAILED = "failed"


# ============================================================
# OBSERVER ERROR
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolObserverError:
    """
    Captured observer failure.
    """

    observer_name: str

    observation_type: ToolObservationType

    exception: BaseException

    observation: ToolObservation

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "observer_name": self.observer_name,
            "observation_type": (
                self.observation_type.value
            ),
            "exception_type": type(
                self.exception
            ).__name__,
            "message": str(
                self.exception
            ),
        }


# ============================================================
# OBSERVER PROTOCOL
# ============================================================


class ToolObserver(Protocol):
    """
    Protocol implemented by passive tool observers.
    """

    def observe(
        self,
        observation: ToolObservation,
    ) -> None:
        """
        Receive one tool observation.

        Implementations must not mutate the tool subsystem through
        this callback.
        """
        ...


# ============================================================
# OBSERVER REGISTRATION
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolObserverRecord:
    """
    Registration descriptor for an observer.
    """

    name: str

    observer: ToolObserver

    observation_types: frozenset[
        ToolObservationType
    ]

    priority: int = 0

    enabled: bool = True

    once: bool = False

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def matches(
        self,
        observation_type: ToolObservationType,
    ) -> bool:
        """Return whether this observer accepts an observation."""

        return (
            self.enabled
            and (
                not self.observation_types
                or observation_type
                in self.observation_types
            )
        )


# ============================================================
# NOTIFICATION RESULT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolObservationDispatch:
    """
    Aggregate result from notifying observers.
    """

    observation: ToolObservation

    notified: tuple[str, ...] = ()

    errors: tuple[
        ToolObserverError,
        ...
    ] = ()

    @property
    def failed(self) -> bool:
        """Return whether any observer failed."""

        return bool(self.errors)

    @property
    def success(self) -> bool:
        """Return whether all notified observers succeeded."""

        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "observation": self.observation.to_dict(),
            "notified": list(self.notified),
            "errors": [
                error.to_dict()
                for error in self.errors
            ],
        }


# ============================================================
# OBSERVER ERROR POLICY
# ============================================================


class ToolObserverErrorPolicy(str, Enum):
    """
    Policy used when an observer raises an exception.
    """

    PROPAGATE = "propagate"
    COLLECT = "collect"
    IGNORE = "ignore"


# ============================================================
# OBSERVER REGISTRY
# ============================================================


class ToolObservers:
    """
    Registry and dispatcher for passive tool observers.

    This class is deliberately local and explicit. It is not a
    process-wide event bus.
    """

    def __init__(
        self,
        *,
        error_policy: ToolObserverErrorPolicy = (
            ToolObserverErrorPolicy.COLLECT
        ),
    ) -> None:
        if not isinstance(
            error_policy,
            ToolObserverErrorPolicy,
        ):
            raise TypeError(
                "error_policy must be "
                "ToolObserverErrorPolicy."
            )

        self._error_policy = error_policy

        self._observers: dict[
            str,
            ToolObserverRecord,
        ] = {}

        self._registration_counter = 0

        self._registration_order: dict[
            str,
            int,
        ] = {}

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def error_policy(
        self,
    ) -> ToolObserverErrorPolicy:
        """Return the configured observer error policy."""

        return self._error_policy

    @property
    def count(self) -> int:
        """Return the number of registered observers."""

        return len(
            self._observers
        )

    @property
    def names(self) -> tuple[str, ...]:
        """Return observer names in registration order."""

        return tuple(
            self._observers
        )

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        observer: ToolObserver,
        *,
        name: Optional[str] = None,
        observation_types: Iterable[
            ToolObservationType
        ] = (),
        priority: int = 0,
        enabled: bool = True,
        once: bool = False,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
        replace: bool = False,
    ) -> str:
        """
        Register a passive observer.

        Higher-priority observers are notified first.
        """

        if not callable(
            getattr(
                observer,
                "observe",
                None,
            )
        ):
            raise TypeError(
                "observer must provide an observe() method."
            )

        normalized_types = frozenset(
            observation_types
        )

        if any(
            not isinstance(
                item,
                ToolObservationType,
            )
            for item in normalized_types
        ):
            raise TypeError(
                (
                    "observation_types must contain only "
                    "ToolObservationType values."
                )
            )

        if name is None:
            name = self._generate_name(
                observer
            )
        else:
            name = name.strip()

            if not name:
                raise ValueError(
                    "Observer name must not be empty."
                )

        if (
            name in self._observers
            and not replace
        ):
            raise ValueError(
                f"Observer {name!r} is already registered."
            )

        self._registration_counter += 1

        self._observers[name] = ToolObserverRecord(
            name=name,
            observer=observer,
            observation_types=normalized_types,
            priority=priority,
            enabled=enabled,
            once=once,
            metadata=dict(
                metadata or {}
            ),
        )

        self._registration_order[name] = (
            self._registration_counter
        )

        return name

    def unregister(
        self,
        name: str,
    ) -> bool:
        """Remove an observer."""

        removed = (
            self._observers.pop(
                name,
                None,
            )
            is not None
        )

        if removed:
            self._registration_order.pop(
                name,
                None,
            )

        return removed

    def clear(self) -> None:
        """Remove all observers."""

        self._observers.clear()
        self._registration_order.clear()

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether an observer exists."""

        return name in self._observers

    # ========================================================
    # ENABLE / DISABLE
    # ========================================================

    def enable(
        self,
        name: str,
    ) -> bool:
        """Enable an observer."""

        record = self._observers.get(
            name
        )

        if record is None:
            return False

        self._observers[name] = ToolObserverRecord(
            name=record.name,
            observer=record.observer,
            observation_types=record.observation_types,
            priority=record.priority,
            enabled=True,
            once=record.once,
            metadata=record.metadata,
        )

        return True

    def disable(
        self,
        name: str,
    ) -> bool:
        """Disable an observer."""

        record = self._observers.get(
            name
        )

        if record is None:
            return False

        self._observers[name] = ToolObserverRecord(
            name=record.name,
            observer=record.observer,
            observation_types=record.observation_types,
            priority=record.priority,
            enabled=False,
            once=record.once,
            metadata=record.metadata,
        )

        return True

    # ========================================================
    # OBSERVATION
    # ========================================================

    def notify(
        self,
        observation: ToolObservation,
    ) -> ToolObservationDispatch:
        """
        Notify all matching observers.

        Observer ordering is deterministic:
            1. descending priority;
            2. registration order.

        Observer failures never alter the observation itself.
        """

        if not isinstance(
            observation,
            ToolObservation,
        ):
            raise TypeError(
                "observation must be ToolObservation."
            )

        records = sorted(
            (
                record
                for record in self._observers.values()
                if record.matches(
                    observation.observation_type
                )
            ),
            key=lambda record: (
                -record.priority,
                self._registration_order[
                    record.name
                ],
            ),
        )

        notified: list[str] = []
        errors: list[
            ToolObserverError
        ] = []

        for record in records:
            notified.append(
                record.name
            )

            try:
                record.observer.observe(
                    observation
                )

            except BaseException as exc:
                if (
                    self._error_policy
                    == ToolObserverErrorPolicy.PROPAGATE
                ):
                    raise

                if (
                    self._error_policy
                    == ToolObserverErrorPolicy.COLLECT
                ):
                    errors.append(
                        ToolObserverError(
                            observer_name=record.name,
                            observation_type=(
                                observation.observation_type
                            ),
                            exception=exc,
                            observation=observation,
                        )
                    )

            if record.once:
                self.unregister(
                    record.name
                )

        return ToolObservationDispatch(
            observation=observation,
            notified=tuple(
                notified
            ),
            errors=tuple(
                errors
            ),
        )

    # ========================================================
    # CONVENIENCE NOTIFICATIONS
    # ========================================================

    def activating(
        self,
        *,
        tool: Any,
        previous_tool: Any = None,
        next_tool: Any = None,
        context: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool activation is beginning."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.ACTIVATING
                ),
                tool=tool,
                previous_tool=previous_tool,
                next_tool=next_tool,
                context=context,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def activated(
        self,
        *,
        tool: Any,
        previous_tool: Any = None,
        context: Any = None,
        result: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool activation completed."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.ACTIVATED
                ),
                tool=tool,
                previous_tool=previous_tool,
                context=context,
                result=result,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def deactivating(
        self,
        *,
        tool: Any,
        context: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool deactivation is beginning."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.DEACTIVATING
                ),
                tool=tool,
                context=context,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def deactivated(
        self,
        *,
        tool: Any,
        context: Any = None,
        result: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool deactivation completed."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.DEACTIVATED
                ),
                tool=tool,
                context=context,
                result=result,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def suspending(
        self,
        *,
        tool: Any,
        context: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool suspension is beginning."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.SUSPENDING
                ),
                tool=tool,
                context=context,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def suspended(
        self,
        *,
        tool: Any,
        context: Any = None,
        result: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool suspension completed."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.SUSPENDED
                ),
                tool=tool,
                context=context,
                result=result,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def resuming(
        self,
        *,
        tool: Any,
        context: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool resume is beginning."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.RESUMING
                ),
                tool=tool,
                context=context,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def resumed(
        self,
        *,
        tool: Any,
        context: Any = None,
        result: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool resume completed."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.RESUMED
                ),
                tool=tool,
                context=context,
                result=result,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def resetting(
        self,
        *,
        tool: Any,
        context: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool reset is beginning."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.RESETTING
                ),
                tool=tool,
                context=context,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def reset(
        self,
        *,
        tool: Any,
        context: Any = None,
        result: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool reset completed."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.RESET
                ),
                tool=tool,
                context=context,
                result=result,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def cancelling(
        self,
        *,
        tool: Any,
        context: Any = None,
        event: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that cancellation is beginning."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.CANCELLING
                ),
                tool=tool,
                event=event,
                context=context,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def cancelled(
        self,
        *,
        tool: Any,
        context: Any = None,
        event: Any = None,
        result: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that cancellation completed."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.CANCELLED
                ),
                tool=tool,
                event=event,
                context=context,
                result=result,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def event_received(
        self,
        *,
        tool: Any,
        event: Any,
        context: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that a tool event was received."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.EVENT_RECEIVED
                ),
                tool=tool,
                event=event,
                context=context,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def event_handled(
        self,
        *,
        tool: Any,
        event: Any,
        context: Any = None,
        result: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that a tool event was handled."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.EVENT_HANDLED
                ),
                tool=tool,
                event=event,
                context=context,
                result=result,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def event_ignored(
        self,
        *,
        tool: Any,
        event: Any,
        context: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that a tool ignored an event."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.EVENT_IGNORED
                ),
                tool=tool,
                event=event,
                context=context,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def execution_started(
        self,
        *,
        tool: Any,
        event: Any = None,
        context: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool execution started."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.EXECUTION_STARTED
                ),
                tool=tool,
                event=event,
                context=context,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def execution_completed(
        self,
        *,
        tool: Any,
        event: Any = None,
        context: Any = None,
        result: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool execution completed."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.EXECUTION_COMPLETED
                ),
                tool=tool,
                event=event,
                context=context,
                result=result,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def state_changed(
        self,
        *,
        tool: Any,
        state: Any,
        previous_state: Any = None,
        context: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool state changed."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.STATE_CHANGED
                ),
                tool=tool,
                state=state,
                previous_state=previous_state,
                context=context,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def requirements_changed(
        self,
        *,
        tool: Any,
        result: Any = None,
        context: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that tool requirements changed."""

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.REQUIREMENTS_CHANGED
                ),
                tool=tool,
                result=result,
                context=context,
                message=message,
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    def error(
        self,
        *,
        tool: Any,
        error: BaseException,
        event: Any = None,
        context: Any = None,
        message: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolObservationDispatch:
        """Notify that a tool operation failed."""

        if not isinstance(
            error,
            BaseException,
        ):
            raise TypeError(
                "error must be a BaseException."
            )

        return self.notify(
            ToolObservation(
                observation_type=(
                    ToolObservationType.ERROR
                ),
                tool=tool,
                event=event,
                context=context,
                error=error,
                severity=(
                    ToolObservationSeverity.ERROR
                ),
                message=message
                or str(error),
                metadata=dict(
                    metadata or {}
                ),
            )
        )

    # ========================================================
    # INTERNAL
    # ========================================================

    def _generate_name(
        self,
        observer: ToolObserver,
    ) -> str:
        """Generate a unique observer name."""

        self._registration_counter += 1

        class_name = observer.__class__.__name__

        return (
            f"{class_name}:"
            f"{self._registration_counter}"
        )


# ============================================================
# NULL OBSERVER
# ============================================================


class NullToolObserver:
    """
    No-op observer.

    Useful as a default observer endpoint where the surrounding
    orchestration should not need conditional checks.
    """

    def observe(
        self,
        observation: ToolObservation,
    ) -> None:
        """Ignore the observation."""

        return None


# ============================================================
# CALLBACK OBSERVER
# ============================================================


class CallbackToolObserver:
    """
    Adapter that turns a callable into a ToolObserver.
    """

    def __init__(
        self,
        callback,
    ) -> None:
        if not callable(
            callback
        ):
            raise TypeError(
                "callback must be callable."
            )

        self._callback = callback

    @property
    def callback(self):
        """Return the wrapped callback."""

        return self._callback

    def observe(
        self,
        observation: ToolObservation,
    ) -> None:
        """Forward the observation to the callback."""

        self._callback(
            observation
        )


# ============================================================
# FILTERED OBSERVER
# ============================================================


class FilteredToolObserver:
    """
    Observer adapter that forwards only matching observations.

    This is useful for diagnostics without introducing additional
    observer registrations.
    """

    def __init__(
        self,
        observer: ToolObserver,
        observation_types: Iterable[
            ToolObservationType
        ],
    ) -> None:
        if not callable(
            getattr(
                observer,
                "observe",
                None,
            )
        ):
            raise TypeError(
                "observer must provide an observe() method."
            )

        types = frozenset(
            observation_types
        )

        if any(
            not isinstance(
                item,
                ToolObservationType,
            )
            for item in types
        ):
            raise TypeError(
                (
                    "observation_types must contain only "
                    "ToolObservationType values."
                )
            )

        self._observer = observer
        self._observation_types = types

    def observe(
        self,
        observation: ToolObservation,
    ) -> None:
        """Forward matching observations."""

        if (
            observation.observation_type
            in self._observation_types
        ):
            self._observer.observe(
                observation
            )


# ============================================================
# OBSERVATION HELPERS
# ============================================================


def observe(
    observers: ToolObservers,
    observation: ToolObservation,
) -> ToolObservationDispatch:
    """
    Dispatch an observation through a ToolObservers instance.
    """

    if not isinstance(
        observers,
        ToolObservers,
    ):
        raise TypeError(
            "observers must be ToolObservers."
        )

    return observers.notify(
        observation
    )


def observation(
    observation_type: ToolObservationType,
    *,
    tool: Any = None,
    previous_tool: Any = None,
    next_tool: Any = None,
    event: Any = None,
    result: Any = None,
    state: Any = None,
    previous_state: Any = None,
    context: Any = None,
    error: Optional[BaseException] = None,
    severity: ToolObservationSeverity = (
        ToolObservationSeverity.INFO
    ),
    message: str = "",
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> ToolObservation:
    """
    Convenience factory for ToolObservation.
    """

    if not isinstance(
        observation_type,
        ToolObservationType,
    ):
        raise TypeError(
            "observation_type must be "
            "ToolObservationType."
        )

    return ToolObservation(
        observation_type=observation_type,
        tool=tool,
        previous_tool=previous_tool,
        next_tool=next_tool,
        event=event,
        result=result,
        state=state,
        previous_state=previous_state,
        context=context,
        error=error,
        severity=severity,
        message=message,
        metadata=dict(
            metadata or {}
        ),
    )


__all__ = [
    "ToolObservationType",
    "ToolObservationSeverity",
    "ToolObservation",
    "ToolObserverResult",
    "ToolObserverError",
    "ToolObserver",
    "ToolObserverRecord",
    "ToolObservationDispatch",
    "ToolObserverErrorPolicy",
    "ToolObservers",
    "NullToolObserver",
    "CallbackToolObserver",
    "FilteredToolObserver",
    "observe",
    "observation",
]
