# ============================================================
# File: core/application/history.py
# GridForge V2 — Headless Application Command History
# ============================================================
"""
GridForge V2
============

Module:
    core.application.history

Purpose
-------
Defines Application-layer command history.

Command history belongs to the Application layer because
undo/redo is an Application interaction concern, not a Core
domain concern.

The Core remains responsible for domain state and domain
operations.

Architectural flow
------------------

    UI / Plugin / Automation
              |
              v
       Application
              |
              v
       CommandManager
              |
              v
       Command Handler
              |
              v
       Application Service
              |
              v
             Core

History is maintained alongside Application command execution.

Responsibilities
----------------
ApplicationHistory owns:

    * executed command records;
    * undo stack;
    * redo stack;
    * history inspection;
    * history clearing.

It does NOT:

    * execute commands;
    * mutate Core;
    * know about Qt;
    * know about UI;
    * know about SLD/canvas;
    * calculate engineering results;
    * access Network internals.

Undo / Redo
-----------
This module intentionally stores Application command records.

Actual inverse execution is NOT invented here.

A command must explicitly provide an undo strategy before the
Application can safely perform undo.

Therefore this initial implementation establishes the history
boundary and metadata contract without pretending that every
command is reversible.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .command import Command


@dataclass(frozen=True)
class CommandRecord:
    """
    Immutable record of an Application command execution.

    Parameters
    ----------
    command:
        Original immutable Application command.

    executed_at:
        UTC timestamp at which the command was recorded.

    description:
        Optional human-readable description.
    """

    command: Command
    executed_at: datetime
    description: str | None = None

    @property
    def command_type(self) -> str:
        """Return the semantic command type."""
        return self.command.command_type

    @property
    def command_id(self) -> str:
        """Return the command instance identifier."""
        return str(self.command.command_id)


class CommandHistory:
    """
    Headless Application command history.

    The history object stores immutable command records.

    It does not execute commands and therefore has no dependency
    on the Core execution mechanism.
    """

    def __init__(self) -> None:
        self._undo_stack: list[CommandRecord] = []
        self._redo_stack: list[CommandRecord] = []

    # ========================================================
    # RECORDING
    # ========================================================

    def record(
        self,
        command: Command,
        *,
        description: str | None = None,
    ) -> CommandRecord:
        """
        Record a successfully executed command.

        Recording a new command invalidates the redo stack.

        The command should only be recorded after successful
        Application execution.
        """

        if not isinstance(command, Command):
            raise TypeError(
                "CommandHistory.record requires a Command."
            )

        if description is not None and not isinstance(
            description,
            str,
        ):
            raise TypeError(
                "description must be a string or None."
            )

        record = CommandRecord(
            command=command,
            executed_at=datetime.now(timezone.utc),
            description=description,
        )

        self._undo_stack.append(record)
        self._redo_stack.clear()

        return record

    # ========================================================
    # UNDO STACK
    # ========================================================

    def can_undo(self) -> bool:
        """Return whether an undo record exists."""
        return bool(self._undo_stack)

    def undo_count(self) -> int:
        """Return the number of records in the undo stack."""
        return len(self._undo_stack)

    def peek_undo(self) -> CommandRecord | None:
        """
        Return the most recent undo record without removing it.
        """
        if not self._undo_stack:
            return None

        return self._undo_stack[-1]

    def pop_undo(self) -> CommandRecord | None:
        """
        Remove and return the most recent undo record.

        This operation only changes history state.

        It does NOT undo Core/Application state.
        """
        if not self._undo_stack:
            return None

        return self._undo_stack.pop()

    # ========================================================
    # REDO STACK
    # ========================================================

    def can_redo(self) -> bool:
        """Return whether a redo record exists."""
        return bool(self._redo_stack)

    def redo_count(self) -> int:
        """Return the number of records in the redo stack."""
        return len(self._redo_stack)

    def peek_redo(self) -> CommandRecord | None:
        """
        Return the most recent redo record without removing it.
        """
        if not self._redo_stack:
            return None

        return self._redo_stack[-1]

    def push_redo(
        self,
        record: CommandRecord,
    ) -> None:
        """
        Move a record into the redo stack.

        No Core operation is performed.
        """

        if not isinstance(record, CommandRecord):
            raise TypeError(
                "push_redo requires a CommandRecord."
            )

        self._redo_stack.append(record)

    def pop_redo(self) -> CommandRecord | None:
        """
        Remove and return the most recent redo record.
        """
        if not self._redo_stack:
            return None

        return self._redo_stack.pop()

    # ========================================================
    # HISTORY QUERIES
    # ========================================================

    def undo_commands(self) -> tuple[CommandRecord, ...]:
        """
        Return an immutable snapshot of undo history.
        """
        return tuple(self._undo_stack)

    def redo_commands(self) -> tuple[CommandRecord, ...]:
        """
        Return an immutable snapshot of redo history.
        """
        return tuple(self._redo_stack)

    def undo_name(self) -> str | None:
        """
        Return the description/type of the next undo operation.
        """
        record = self.peek_undo()

        if record is None:
            return None

        return record.description or record.command_type

    def redo_name(self) -> str | None:
        """
        Return the description/type of the next redo operation.
        """
        record = self.peek_redo()

        if record is None:
            return None

        return record.description or record.command_type

    # ========================================================
    # CLEARING
    # ========================================================

    def clear(self) -> None:
        """
        Clear both undo and redo history.
        """
        self._undo_stack.clear()
        self._redo_stack.clear()

    def clear_redo(self) -> None:
        """
        Clear only the redo stack.
        """
        self._redo_stack.clear()

    def reset(self) -> None:
        """
        Reset Application command history.
        """
        self.clear()


__all__ = [
    "CommandRecord",
    "CommandHistory",
]
