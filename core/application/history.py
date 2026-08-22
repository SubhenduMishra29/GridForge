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
Owns Application-layer command history.

History records successful Application commands.

IMPORTANT
---------
A command being present in history does NOT automatically mean
that it is undoable.

Undo requires an explicit reversible-command contract.

Therefore this module distinguishes:

    history availability
        from
    undo/redo executability.

Architecture
------------

    Command
       |
       v
    CommandManager
       |
       +----> CommandHistory
       |
       +----> Application Service
                    |
                    v
                   Core

The history layer never mutates Core.

Headless Requirement
--------------------
No dependency on:

    * Qt
    * PySide6
    * UI
    * SLD
    * Canvas
    * Renderers
    * Controllers

Python Compatibility
--------------------
Python 3.10 / 3.11.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .command import Command
from .reversible import is_reversible


@dataclass(frozen=True)
class CommandRecord:
    """
    Immutable record of a successfully executed Application command.
    """

    command: Command
    executed_at: datetime
    description: str | None = None

    @property
    def command_type(self) -> str:
        """Return the command's semantic type."""
        return self.command.command_type

    @property
    def command_id(self) -> str:
        """Return the command instance identifier."""
        return str(self.command.command_id)

    @property
    def reversible(self) -> bool:
        """
        Return whether the recorded command explicitly supports
        reversibility.
        """
        return is_reversible(self.command)


class CommandHistory:
    """
    Application-owned command history.

    This object stores successful command records.

    It does not execute commands.

    It does not modify Core state.
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

        A new successful command invalidates the redo stack.
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
    # UNDO CAPABILITY
    # ========================================================

    def has_history(self) -> bool:
        """
        Return whether any successful command has been recorded.
        """
        return bool(self._undo_stack)

    def can_undo(self) -> bool:
        """
        Return whether the next history entry is explicitly
        reversible.
        """

        record = self.peek_undo()

        if record is None:
            return False

        return record.reversible

    def undo_count(self) -> int:
        """
        Return the number of recorded commands.
        """
        return len(self._undo_stack)

    def reversible_undo_count(self) -> int:
        """
        Return the number of currently recorded reversible commands.

        This does not imply that every earlier command can be
        independently undone without respecting stack order.
        """

        return sum(
            1
            for record in self._undo_stack
            if record.reversible
        )

    def peek_undo(self) -> CommandRecord | None:
        """
        Return the most recent history record without removing it.
        """

        if not self._undo_stack:
            return None

        return self._undo_stack[-1]

    def pop_undo(self) -> CommandRecord | None:
        """
        Remove and return the most recent undo record.

        This only changes history.

        It does NOT execute an inverse command.
        """

        if not self._undo_stack:
            return None

        return self._undo_stack.pop()

    # ========================================================
    # REDO CAPABILITY
    # ========================================================

    def can_redo(self) -> bool:
        """
        Return whether the next redo record is explicitly
        reversible.
        """

        record = self.peek_redo()

        if record is None:
            return False

        return record.reversible

    def redo_count(self) -> int:
        """
        Return the number of redo records.
        """
        return len(self._redo_stack)

    def peek_redo(self) -> CommandRecord | None:
        """
        Return the most recent redo record without removing it.
        """

        if not self._redo_stack:
            return None

        return self._redo_stack[-1]

    def pop_redo(self) -> CommandRecord | None:
        """
        Remove and return the most recent redo record.

        This only changes history.
        """

        if not self._redo_stack:
            return None

        return self._redo_stack.pop()

    def push_redo(
        self,
        record: CommandRecord,
    ) -> None:
        """
        Add a record to the redo stack.
        """

        if not isinstance(record, CommandRecord):
            raise TypeError(
                "push_redo requires a CommandRecord."
            )

        self._redo_stack.append(record)

    # ========================================================
    # HISTORY INSPECTION
    # ========================================================

    def undo_commands(
        self,
    ) -> tuple[CommandRecord, ...]:
        """
        Return an immutable snapshot of the undo history.
        """
        return tuple(self._undo_stack)

    def redo_commands(
        self,
    ) -> tuple[CommandRecord, ...]:
        """
        Return an immutable snapshot of the redo history.
        """
        return tuple(self._redo_stack)

    def undo_name(self) -> str | None:
        """
        Return the next undo command description/type.
        """

        record = self.peek_undo()

        if record is None:
            return None

        return record.description or record.command_type

    def redo_name(self) -> str | None:
        """
        Return the next redo command description/type.
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
        Clear only redo history.
        """

        self._redo_stack.clear()

    def reset(self) -> None:
        """
        Reset the complete Application history.
        """

        self.clear()


__all__ = [
    "CommandRecord",
    "CommandHistory",
]
