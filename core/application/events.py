# ============================================================
# File: core/application/events.py
# GridForge V2 — Headless Application Events
# ============================================================
"""
GridForge V2
============

Module:
    core.application.events

Purpose
-------
Defines the immutable event contract used by the GridForge V2
Headless Application layer.

An Application Event represents a fact that has already occurred
as the result of an Application operation.

Examples
--------
    ElementCreated
    ElementRemoved
    ElementUpdated
    TopologyChanged
    NetworkChanged
    OperationCompleted

An event is NOT:

    * a command;
    * a request;
    * a callback;
    * a Qt signal;
    * a UI event;
    * a tool event;
    * a domain model;
    * a global event bus.

Architectural Boundary
----------------------
The Application event contract is headless.

It MUST NOT depend on:

    * PySide6;
    * PyQt;
    * Qt;
    * UI controllers;
    * SLD;
    * canvas;
    * renderers;
    * plugin implementations.

The Application layer may publish events to registered consumers.
The consumers may include the UI or plugins, but the event itself
must contain no presentation-specific state.

Dependency Direction
--------------------
The intended direction is:

    Core operation
         |
         v
    Application Service
         |
         v
    Application Event
         |
         +------> UI
         |
         +------> Plugins
         |
         +------> Automation
         |
         +------> Other Application consumers

Event vs Command
----------------
A command expresses intent:

    "Create this bus."

An event expresses fact:

    "This bus was created."

Commands therefore enter the Application layer.

Events leave the Application layer.

Immutability
------------
Application events are immutable after publication.

This is important because an event may be delivered to multiple
independent consumers. One consumer must not be able to modify
the event observed by another consumer.

Payload
-------
The event payload is intentionally represented as structured
metadata rather than as a UI-specific object.

The payload should contain stable application-level information,
for example:

    {
        "element_id": "...",
        "element_type": "bus"
    }

It should not contain:

    * QGraphicsItem;
    * QWidget;
    * QGraphicsScene;
    * renderer objects;
    * Qt signals;
    * UI controllers.

Event Identity
--------------
Each event receives a unique identifier.

The identifier is useful for:

    * diagnostics;
    * event tracing;
    * logging;
    * correlation.

It is not intended to become a persistence identifier.

Timestamp
---------
Each event records its creation time in UTC.

The timestamp is generated when the event is constructed.

No local timezone assumptions are made.

Correlation
-----------
``correlation_id`` may associate an event with an Application
operation or command execution.

``causation_id`` may identify the event or operation that directly
caused the current event.

Both are optional and are intended for infrastructure/diagnostic
use.

Important
---------
This module defines the EVENT DATA CONTRACT only.

It does not implement event dispatch.

The EventBus/dispatcher belongs to a later Application infrastructure
layer and must not be introduced prematurely.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4


def _immutable_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """
    Convert a mapping into an immutable top-level mapping.

    Nested mappings are recursively converted so that Application
    event payloads cannot be mutated through nested dictionaries.
    Lists, tuples, sets, and other values are preserved as supplied;
    event payloads should therefore contain immutable application
    metadata wherever nested mutable containers would otherwise be
    exposed.
    """

    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise TypeError(
            "Event payload must be a mapping."
        )

    def freeze(
        item: Any,
    ) -> Any:
        if isinstance(item, Mapping):
            return MappingProxyType(
                {
                    key: freeze(val)
                    for key, val in item.items()
                }
            )

        if isinstance(item, list):
            return tuple(
                freeze(element)
                for element in item
            )

        if isinstance(item, set):
            return frozenset(
                freeze(element)
                for element in item
            )

        if isinstance(item, tuple):
            return tuple(
                freeze(element)
                for element in item
            )

        return item

    return MappingProxyType(
        {
            key: freeze(item)
            for key, item in value.items()
        }
    )


@dataclass(frozen=True)
class ApplicationEvent:
    """
    Base immutable Application event.

    Parameters
    ----------
    event_type:
        Stable semantic event type.

    payload:
        Structured immutable event data.

    event_id:
        Unique identifier for this event instance.

    occurred_at:
        UTC timestamp at which the event was created.

    correlation_id:
        Optional identifier connecting the event to an
        Application operation.

    causation_id:
        Optional identifier of the immediate cause.

    Notes
    -----
    ``event_type`` is deliberately separate from the Python class
    name. This allows the semantic event contract to remain stable
    even if implementation classes are reorganized.
    """

    event_type: str
    payload: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    event_id: UUID = field(default_factory=uuid4)

    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    correlation_id: UUID | None = None
    causation_id: UUID | None = None

    def __post_init__(self) -> None:
        """Validate and normalize the event contract."""

        if not isinstance(self.event_type, str):
            raise TypeError(
                "ApplicationEvent event_type must be a string."
            )

        if not self.event_type.strip():
            raise ValueError(
                "ApplicationEvent event_type must not be empty."
            )

        if not isinstance(self.payload, Mapping):
            raise TypeError(
                "ApplicationEvent payload must be a mapping."
            )

        # Normalize payload even when a caller supplied a normal dict.
        object.__setattr__(
            self,
            "payload",
            _immutable_mapping(self.payload),
        )

        if not isinstance(self.event_id, UUID):
            raise TypeError(
                "ApplicationEvent event_id must be a UUID."
            )

        if not isinstance(self.occurred_at, datetime):
            raise TypeError(
                "ApplicationEvent occurred_at must be a datetime."
            )

        if self.occurred_at.tzinfo is None:
            raise ValueError(
                "ApplicationEvent occurred_at must be timezone-aware."
            )

        if self.occurred_at.utcoffset() is None:
            raise ValueError(
                "ApplicationEvent occurred_at must be timezone-aware."
            )


# ============================================================
# Standard Application Event Types
# ============================================================


@dataclass(frozen=True)
class ElementCreated(ApplicationEvent):
    """
    Event emitted after a Core network element has been created.

    The event does not contain the UI representation of the element.

    Expected payload example:

        {
            "element_id": "bus-001",
            "element_type": "bus",
        }
    """

    def __init__(
        self,
        *,
        element_id: str,
        element_type: str,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "element_id": element_id,
            "element_type": element_type,
        }

        if metadata:
            payload.update(metadata)

        super().__init__(
            event_type="element.created",
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


@dataclass(frozen=True)
class ElementRemoved(ApplicationEvent):
    """
    Event emitted after a Core network element has been removed.
    """

    def __init__(
        self,
        *,
        element_id: str,
        element_type: str,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "element_id": element_id,
            "element_type": element_type,
        }

        if metadata:
            payload.update(metadata)

        super().__init__(
            event_type="element.removed",
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


@dataclass(frozen=True)
class ElementUpdated(ApplicationEvent):
    """
    Event emitted after an existing Core element has been updated.

    The payload should describe the identity and nature of the
    update without embedding UI state.
    """

    def __init__(
        self,
        *,
        element_id: str,
        element_type: str,
        changes: Mapping[str, Any] | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "element_id": element_id,
            "element_type": element_type,
            "changes": dict(changes or {}),
        }

        super().__init__(
            event_type="element.updated",
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


@dataclass(frozen=True)
class TopologyChanged(ApplicationEvent):
    """
    Event emitted after a successful topology-affecting operation.

    The event describes the fact that topology changed. It does not
    expose the internal NetworkX representation.
    """

    def __init__(
        self,
        *,
        operation: str,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "operation": operation,
        }

        if metadata:
            payload.update(metadata)

        super().__init__(
            event_type="topology.changed",
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


@dataclass(frozen=True)
class NetworkChanged(ApplicationEvent):
    """
    Event emitted when a successful Application operation changes
    the assembled network state.
    """

    def __init__(
        self,
        *,
        operation: str,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "operation": operation,
        }

        if metadata:
            payload.update(metadata)

        super().__init__(
            event_type="network.changed",
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


@dataclass(frozen=True)
class OperationCompleted(ApplicationEvent):
    """
    Event emitted when an Application operation completes.

    This event is intended for Application-level observability and
    integration rather than UI notification.

    ``operation`` identifies the semantic operation rather than
    exposing the implementation class.
    """

    def __init__(
        self,
        *,
        operation: str,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "operation": operation,
        }

        if metadata:
            payload.update(metadata)

        super().__init__(
            event_type="operation.completed",
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


__all__ = [
    "ApplicationEvent",
    "ElementCreated",
    "ElementRemoved",
    "ElementUpdated",
    "TopologyChanged",
    "NetworkChanged",
    "OperationCompleted",
]
