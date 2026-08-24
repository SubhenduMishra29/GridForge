# ============================================================

# File: core/application/history.py

# GridForge V2 — Headless Application Command History

# Author: Subhendu Mishra

# ============================================================

"""Committed Application command history.

CommandHistory stores committed command records and never executes
commands or undo operations. CommandManager owns execution.
"""

from **future** import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

from .command import Command

UndoOperation = Callable[[], None]
UndoJournal = tuple[UndoOperation, ...]

@dataclass(frozen=True, slots=True)
class CommandRecord:
"""Immutable record of a successfully committed command."""

```
command: Command
executed_at: datetime
description: Optional[str] = None
undo_operations: UndoJournal = ()

@property
def command_type(self) -> str:
    return self.command.command_type

@property
def command_id(self) -> str:
    return str(self.command.command_id)

@property
def reversible(self) -> bool:
    return bool(self.undo_operations)

@property
def undo_operation_count(self) -> int:
    return len(self.undo_operations)
```

class CommandHistory:
"""State-only undo/redo history owned by the Application layer."""

```
def __init__(self) -> None:
    self._undo_stack: list[CommandRecord] = []
    self._redo_stack: list[CommandRecord] = []

def record(
    self,
    command: Command,
    *,
    description: Optional[str] = None,
    undo_operations: UndoJournal = (),
    clear_redo: bool = True,
) -> CommandRecord:
    """Record a committed command.

    New commands use ``clear_redo=True``.
    Redo replay uses ``clear_redo=False``.
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
        undo_operations=self._normalize_undo_operations(
            undo_operations
        ),
    )

    self._undo_stack.append(record)

    if clear_redo:
        self._redo_stack.clear()

    return record

def has_history(self) -> bool:
    return bool(self._undo_stack)

def can_undo(self) -> bool:
    record = self.peek_undo()
    return record is not None and record.reversible

def undo_count(self) -> int:
    return len(self._undo_stack)

def reversible_undo_count(self) -> int:
    return sum(
        1
        for record in self._undo_stack
        if record.reversible
    )

def peek_undo(self) -> Optional[CommandRecord]:
    return (
        self._undo_stack[-1]
        if self._undo_stack
        else None
    )

def pop_undo(self) -> Optional[CommandRecord]:
    return (
        self._undo_stack.pop()
        if self._undo_stack
        else None
    )

def push_undo(
    self,
    record: CommandRecord,
) -> None:
    """Restore a record to the undo stack."""
    self._validate_record(record)
    self._undo_stack.append(record)

def can_redo(self) -> bool:
    return self.peek_redo() is not None

def redo_count(self) -> int:
    return len(self._redo_stack)

def peek_redo(self) -> Optional[CommandRecord]:
    return (
        self._redo_stack[-1]
        if self._redo_stack
        else None
    )

def pop_redo(self) -> Optional[CommandRecord]:
    return (
        self._redo_stack.pop()
        if self._redo_stack
        else None
    )

def push_redo(
    self,
    record: CommandRecord,
) -> None:
    self._validate_record(record)
    self._redo_stack.append(record)

def undo_commands(self) -> tuple[CommandRecord, ...]:
    return tuple(self._undo_stack)

def redo_commands(self) -> tuple[CommandRecord, ...]:
    return tuple(self._redo_stack)

def undo_name(self) -> Optional[str]:
    record = self.peek_undo()

    if record is None:
        return None

    return record.description or record.command_type

def redo_name(self) -> Optional[str]:
    record = self.peek_redo()

    if record is None:
        return None

    return record.description or record.command_type

def clear(self) -> None:
    self._undo_stack.clear()
    self._redo_stack.clear()

def clear_redo(self) -> None:
    self._redo_stack.clear()

def reset(self) -> None:
    self.clear()

@staticmethod
def _validate_record(
    record: CommandRecord,
) -> None:
    if not isinstance(record, CommandRecord):
        raise TypeError(
            "Expected CommandRecord."
        )

@staticmethod
def _normalize_undo_operations(
    undo_operations: UndoJournal,
) -> UndoJournal:
    if undo_operations is None:
        return ()

    try:
        operations = tuple(undo_operations)
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
```

**all** = [
"UndoOperation",
"UndoJournal",
"CommandRecord",
"CommandHistory",
]
