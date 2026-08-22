# ============================================================
# File: core/application/command.py
# GridForge V2 — Headless Application Command Contract
# ============================================================
"""
GridForge V2
============

Module:
    core.application.command

Purpose
-------
Defines the command contract for the GridForge V2 Headless
Application layer.

A Command represents an explicit Application-level intent.

Examples
--------
    CreateBusCommand
    RemoveElementCommand
    ConnectElementCommand
    DisconnectElementCommand
    OpenElementCommand
    CloseElementCommand

A command describes WHAT the caller wants to accomplish.

It does not define:

    * UI behavior;
    * Qt actions;
    * toolbar state;
    * graphics objects;
    * rendering;
    * mouse interaction;
    * canvas state.

Architectural Boundary
----------------------
The intended flow is:

    UI / Plugin
          |
          v
       Command
          |
          v
    CommandManager
          |
          v
    Application Service
          |
          v
    Core

The Command itself is therefore a headless Application contract.

Command responsibilities
------------------------
A Command contains:

    * command identity;
    * semantic command type;
    * immutable input payload;
    * optional correlation metadata.

A Command does NOT:

    * mutate Core directly;
    * own application services;
    * own CommandManager;
    * emit UI signals;
    * maintain history;
    * perform undo/redo;
    * depend on Qt.

Execution responsibilities
--------------------------
Command execution belongs to the Application execution layer.

The intended future architecture is:

    CommandManager
          |
          v
    Command execution
          |
          v
    Application Service
          |
          v
    Core

This separation is important because commands represent intent,
while services perform use-case orchestration.

Payload
-------
The payload contains immutable Application-level input.

It must not contain UI objects.

For example, this is valid:

    {
        "element_id": "bus-001",
        "bus_type": 1,
    }

This is invalid:

    {
        "graphics_item": QGraphicsItem(...)
    }

The latter would violate the headless boundary.

Immutability
------------
Commands are immutable after construction.

This guarantees that a command cannot change while it is:

    * queued;
    * logged;
    * executed;
    * stored in history;
    * passed between Application components.

Python Compatibility
--------------------
GridForge V2 currently targets Python 3.10/3.11.

This module therefore deliberately avoids Python 3.12-only
generic syntax.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Command:
    """
    Base immutable Application command.

    Parameters
    ----------
    command_type:
        Stable semantic identifier for the command.

    payload:
        Immutable command input data represented as a mapping.

    command_id:
        Unique identifier for this command instance.

    correlation_id:
        Optional identifier used to associate the command with
        a larger Application operation or workflow.

    causation_id:
        Optional identifier identifying the command/event that
        caused this command.

    Notes
    -----
    ``command_type`` is a semantic contract.

    Consumers should use it for identification rather than
    relying on Python class names.
    """

    command_type: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    command_id: UUID = field(default_factory=uuid4)

    correlation_id: UUID | None = None
    causation_id: UUID | None = None

    def __post_init__(self) -> None:
        """Validate the structural command contract."""

        if not isinstance(self.command_type, str):
            raise TypeError(
                "Command command_type must be a string."
            )

        if not self.command_type.strip():
            raise ValueError(
                "Command command_type must not be empty."
            )

        if not isinstance(self.payload, Mapping):
            raise TypeError(
                "Command payload must be a mapping."
            )

        if not isinstance(self.command_id, UUID):
            raise TypeError(
                "Command command_id must be a UUID."
            )

        if self.correlation_id is not None and not isinstance(
            self.correlation_id,
            UUID,
        ):
            raise TypeError(
                "Command correlation_id must be a UUID or None."
            )

        if self.causation_id is not None and not isinstance(
            self.causation_id,
            UUID,
        ):
            raise TypeError(
                "Command causation_id must be a UUID or None."
            )


@dataclass(frozen=True)
class CommandMetadata:
    """
    Optional descriptive metadata associated with a command.

    This metadata is intentionally separate from the command
    payload.

    Payload answers:

        "What input does this command require?"

    Metadata answers:

        "How should the Application infrastructure identify
         or describe this command?"

    Examples of appropriate metadata include:

        * display name;
        * category;
        * originating subsystem;
        * plugin identifier.

    UI-specific runtime objects must not be stored here.
    """

    display_name: str | None = None
    category: str | None = None
    origin: str | None = None
    plugin_id: str | None = None

    def __post_init__(self) -> None:
        """Validate optional metadata values."""

        fields = {
            "display_name": self.display_name,
            "category": self.category,
            "origin": self.origin,
            "plugin_id": self.plugin_id,
        }

        for name, value in fields.items():
            if value is not None and not isinstance(value, str):
                raise TypeError(
                    f"CommandMetadata {name} must be a string or None."
                )


__all__ = [
    "Command",
    "CommandMetadata",
]
