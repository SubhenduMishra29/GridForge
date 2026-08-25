# ============================================================
# File: core/application/history.py
# GridForge V2 — Headless Application Command History
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 committed Application command history.

CommandHistory is a state-only history container.

Responsibilities
----------------
CommandHistory:

    * stores committed CommandRecord objects;
    * maintains undo history;
    * maintains redo history;
    * provides history inspection;
    * accepts immutable UndoJournal objects.

CommandHistory does NOT:

    * execute Commands;
    * execute undo operations;
    * mutate Core;
    * resolve handlers;
    * manage Transactions;
    * know about UI or SLD.

CommandManager owns execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .command import Command


# ============================================================
# TYPE DEFINITIONS
# ============================================================

UndoOperation = Callable[[], None]
UndoJournal = tuple[UndoOperation, ...]


# ============================================================
# COMMAND RECORD
# ============================================================

@dataclass(frozen=True, slots=True)
class CommandRecord:
    """
    Immutable record of one successfully committed command.
    """

    command: Command
    executed_at: datetime
    description: str | None = None
    undo_operations: UndoJournal = ()

    @property
    def command_type(self) -> str:
        """
        Return the command type identifier.
        """

        return self.command.command_type

    @property
    def command_id(self) -> str:
        """
        Return the command identifier as a string.
        """

        return str(self.command.command_id)

    @property
    def reversible(self) -> bool:
        """
        Return True when the command has undo operations.
        """

        return bool(self.undo_operations)

    @property
    def undo_operation_count(self) -> int:
        """
        Return the number of inverse operations.
        """

        return len(self.undo_operations)


# ============================================================
# COMMAND HISTORY
# ============================================================

class CommandHistory:
    """
    State-only Application undo/redo history.

    The history layer never executes an undo operation.
    CommandManager owns execution.
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
        undo_operations: UndoJournal = (),
        clear_redo: bool = True,
    ) -> CommandRecord:
        """
        Record a successfully committed command.

        Parameters
        ----------
        command:
            Immutable Application Command.

        description:
            Optional human-readable description.

        undo_operations:
            Immutable UndoJournal returned by Transaction.commit().

        clear_redo:
            True for a new command.

            False when recording a successful redo execution.
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

        normalized_operations = (
            self._normalize_undo_operations(
                undo_operations
            )
        )

        record = CommandRecord(
            command=command,
            executed_at=datetime.now(timezone.utc),
            description=description,
            undo_operations=normalized_operations,
        )

        self._undo_stack.append(record)

        if clear_redo:
            self._redo_stack.clear()

        return record

    # ========================================================
    # UNDO
    # ========================================================

    def has_history(self) -> bool:
        """
        Return True when undo history exists.
        """

        return bool(self._undo_stack)

    def can_undo(self) -> bool:
        """
        Return True when the latest command is reversible.
        """

        record = self.peek_undo()

        return (
            record is not None
            and record.reversible
        )

    def undo_count(self) -> int:
        """
        Return total number of undo records.
        """

        return len(self._undo_stack)

    def reversible_undo_count(self) -> int:
        """
        Return number of reversible undo records.
        """

        return sum(
            1
            for record in self._undo_stack
            if record.reversible
        )

    def peek_undo(self) -> CommandRecord | None:
        """
        Return the latest undo record without removing it.
        """

        if not self._undo_stack:
            return None

        return self._undo_stack[-1]

    def pop_undo(self) -> CommandRecord | None:
        """
        Remove and return the latest undo record.
        """

        if not self._undo_stack:
            return None

        return self._undo_stack.pop()

    def push_undo(
        self,
        record: CommandRecord,
    ) -> None:
        """
        Restore a record to the undo stack.
        """

        self._validate_record(record)
        self._undo_stack.append(record)

    # ========================================================
    # REDO
    # ========================================================

    def can_redo(self) -> bool:
        """
        Return True when a redo record exists.
        """

        return self.peek_redo() is not None

    def redo_count(self) -> int:
        """
        Return total number of redo records.
        """

        return len(self._redo_stack)

    def peek_redo(self) -> CommandRecord | None:
        """
        Return the latest redo record without removing it.
        """

        if not self._redo_stack:
            return None

        return self._redo_stack[-1]

    def pop_redo(self) -> CommandRecord | None:
        """
        Remove and return the latest redo record.
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

        self._validate_record(record)
        self._redo_stack.append(record)

    # ========================================================
    # INSPECTION
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
        Return the display name of the latest undo command.
        """

        record = self.peek_undo()

        if record is None:
            return None

        return (
            record.description
            or record.command_type
        )

    def redo_name(self) -> str | None:
        """
        Return the display name of the latest redo command.
        """

        record = self.peek_redo()

        if record is None:
            return None

        return (
            record.description
            or record.command_type
        )

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
        Reset all history.
        """

        self.clear()

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_record(
        record: CommandRecord,
    ) -> None:
        """
        Validate a CommandRecord.
        """

        if not isinstance(
            record,
            CommandRecord,
        ):
            raise TypeError(
                "Expected CommandRecord."
            )

    @staticmethod
    def _normalize_undo_operations(
        undo_operations: UndoJournal,
    ) -> UndoJournal:
        """
        Normalize and validate an UndoJournal.
        """

        if undo_operations is None:
            return ()

        try:
            operations = tuple(
                undo_operations
            )
        except TypeError as exc:
            raise TypeError(
                "undo_operations must be iterable."
            ) from exc

        if not all(
            callable(operation)
            for operation in operations
        ):
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
