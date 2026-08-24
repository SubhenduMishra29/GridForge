# ============================================================
# File: core/application/history.py
# GridForge V2 — Headless Application Command History
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2
============

Module:
    core.application.history

Purpose
-------
Owns committed Application command history.

CommandHistory is a state container only.

It does not:
    * execute commands
    * execute undo operations
    * mutate Core
    * resolve domain objects
    * access Network
    * access Application Services

Undo execution is owned by CommandManager.

Transaction and History have distinct responsibilities:

    Transaction
        temporary execution / rollback scope

    CommandHistory
        persistent post-commit undo / redo journal

A command is undoable only when its committed execution contains
an executable undo journal.

Command-level ``inverse()`` support is optional metadata and is
NOT used as the authoritative test for executed undoability.

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
from typing import Callable, Optional, Tuple

from .command import Command


# ============================================================
# TYPE ALIASES
# ============================================================

UndoOperation = Callable[[], None]

UndoJournal = Tuple[UndoOperation, ...]


# ============================================================
# COMMAND RECORD
# ============================================================

@dataclass(frozen=True)
class CommandRecord:
    """
    Immutable record of a successfully committed Application
    command.

    ``undo_operations`` contains the committed inverse journal
    produced by the Transaction used during command execution.

    The record does not execute these operations.

    CommandManager owns execution.
    """

    command: Command

    executed_at: datetime

    description: Optional[str] = None

    undo_operations: UndoJournal = ()

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
        Return whether this committed command has an executable
        undo journal.

        This is the authoritative Application-level definition
        of post-execution undoability.
        """

        return bool(self.undo_operations)

    @property
    def undo_operation_count(self) -> int:
        """Return the number of committed undo operations."""

        return len(self.undo_operations)


# ============================================================
# COMMAND HISTORY
# ============================================================

class CommandHistory:
    """
    Application-owned command history.

    CommandHistory stores committed command records.

    It does not execute commands or mutate Core.

    Undo and redo execution are coordinated by CommandManager.
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
        description: Optional[str] = None,
        undo_operations: UndoJournal = (),
    ) -> CommandRecord:
        """
        Record a successfully committed Application command.

        A new successful command invalidates the redo stack.

        Parameters
        ----------
        command:
            Successfully executed Application command.

        description:
            Optional human-readable description.

        undo_operations:
            Immutable committed undo journal produced by the
            command's Transaction.

        Returns
        -------
        CommandRecord
            The newly created history record.
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

        normalized_operations = self._normalize_undo_operations(
            undo_operations
        )

        record = CommandRecord(
            command=command,
            executed_at=datetime.now(timezone.utc),
            description=description,
            undo_operations=normalized_operations,
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
        Return whether the next history entry has an executable
        committed undo journal.
        """

        record = self.peek_undo()

        if record is None:
            return False

        return record.reversible

    def undo_count(self) -> int:
        """
        Return the total number of records on the undo stack.
        """

        return len(self._undo_stack)

    def reversible_undo_count(self) -> int:
        """
        Return the number of undo-stack records containing an
        executable undo journal.

        This does not imply that arbitrary earlier records may be
        independently undone out of stack order.
        """

        return sum(
            1
            for record in self._undo_stack
            if record.reversible
        )

    def peek_undo(self) -> Optional[CommandRecord]:
        """
        Return the most recent undo record without removing it.
        """

        if not self._undo_stack:
            return None

        return self._undo_stack[-1]

    def pop_undo(self) -> Optional[CommandRecord]:
        """
        Remove and return the most recent undo record.

        This only changes history.

        It does NOT execute the undo journal.
        """

        if not self._undo_stack:
            return None

        return self._undo_stack.pop()

    # ========================================================
    # REDO CAPABILITY
    # ========================================================

    def can_redo(self) -> bool:
        """
        Return whether the next redo record is executable through
        the Application command pipeline.

        A redo record is considered executable when it contains
        a command.

        CommandManager is responsible for replaying that command.
        """

        return self.peek_redo() is not None

    def redo_count(self) -> int:
        """
        Return the number of records on the redo stack.
        """

        return len(self._redo_stack)

    def peek_redo(self) -> Optional[CommandRecord]:
        """
        Return the most recent redo record without removing it.
        """

        if not self._redo_stack:
            return None

        return self._redo_stack[-1]

    def pop_redo(self) -> Optional[CommandRecord]:
        """
        Remove and return the most recent redo record.

        This only changes history.

        It does NOT execute the command.
        """

        if not self._redo_stack:
            return None

        return self._redo_stack.pop()

    def push_redo(
        self,
        record: CommandRecord,
    ) -> None:
        """
        Add a committed command record to the redo stack.

        The record must retain its committed undo journal so that
        a subsequent redo execution can establish a fresh
        transaction/history state.
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

    def undo_name(self) -> Optional[str]:
        """
        Return the next undo command description or type.
        """

        record = self.peek_undo()

        if record is None:
            return None

        return record.description or record.command_type

    def redo_name(self) -> Optional[str]:
        """
        Return the next redo command description or type.
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

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    @staticmethod
    def _normalize_undo_operations(
        undo_operations: UndoJournal,
    ) -> UndoJournal:
        """
        Validate and normalize an undo journal.

        History stores the journal but never executes it.
        """

        if undo_operations is None:
            return ()

        try:
            operations = tuple(undo_operations)

        except TypeError as exc:

            raise TypeError(
                "undo_operations must be an iterable of callables."
            ) from exc

        for operation in operations:

            if not callable(operation):

                raise TypeError(
                    "Every undo operation must be callable."
                )

        return operations


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "UndoOperation",
    "UndoJournal",
    "CommandRecord",
    "CommandHistory",
]
