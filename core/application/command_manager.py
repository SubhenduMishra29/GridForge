# ============================================================

# File: core/application/command_manager.py

# GridForge V2 — Headless Application Command Manager

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Headless Application Command Manager.

CommandManager is the Application-layer orchestration boundary for
command execution, transactions, undo, and redo.

## Responsibilities

CommandManager:

```
* accepts Application Commands;
* resolves command handlers;
* creates a Transaction for each execution;
* invokes the handler;
* commits successful transactions;
* records committed history;
* rolls back failed transactions;
* executes undo journals;
* coordinates redo.
```

CommandManager does NOT:

```
* own electrical/domain state;
* mutate Core directly;
* perform topology operations directly;
* contain engineering algorithms;
* access Qt or UI;
* resolve SLD objects;
* contain equipment-specific engineering logic.
```

## Execution boundary

```
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
```

## Transaction boundary

```
CommandManager
    |
    +---- Transaction
    |       |
    |       +---- mutation
    |       +---- undo journal
    |       +---- rollback
    |       +---- commit
    |
    +---- CommandHistory
            |
            +---- committed records
            +---- undo stack
            +---- redo stack
```

## Redo rule

Redo is NOT execution of the old undo journal.

Redo re-executes the original Command through the normal
handler/service/transaction path and therefore produces:

```
* a new transaction;
* a new ApplicationResult;
* potentially a new canonical Core object;
* a new undo journal.
```

The remaining redo stack must survive successful redo.

If redo fails:

```
* the new transaction is rolled back;
* the original redo record is restored;
* undo history is unchanged;
* redo history is unchanged.
```

CommandHistory remains a storage/orchestration primitive.
It never executes undo operations itself.
"""

from **future** import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .command import Command
from .errors import ApplicationError, ExecutionError
from .history import CommandHistory, CommandRecord
from .results import ApplicationResult
from .transaction import Transaction

# ============================================================

# TYPE ALIASES

# ============================================================

CommandHandler = Callable[
[Command, Any, Transaction],
ApplicationResult[Any],
]

# ============================================================

# COMMAND MANAGER

# ============================================================

class CommandManager:
"""
Headless Application command execution coordinator.

```
Parameters
----------
context:
    ApplicationContext supplied by the Application composition
    boundary.

handlers:
    Mapping of command type identifiers to command handlers.

history:
    Optional CommandHistory instance. A new history is created
    when omitted.
"""

def __init__(
    self,
    context: Any,
    handlers: Mapping[str, CommandHandler] | None = None,
    history: CommandHistory | None = None,
) -> None:
    self._context = context
    self._handlers: dict[str, CommandHandler] = dict(
        handlers or {}
    )
    self._history = history or CommandHistory()

# ========================================================
# PROPERTIES
# ========================================================

@property
def history(self) -> CommandHistory:
    """
    Return the command history owned by this manager.
    """

    return self._history

# ========================================================
# HANDLER REGISTRATION
# ========================================================

def register_handler(
    self,
    command_type: str,
    handler: CommandHandler,
) -> None:
    """
    Register a handler for a command type.

    Duplicate registrations are rejected to prevent silent
    replacement of Application behavior.
    """

    if not isinstance(command_type, str):
        raise TypeError(
            "command_type must be str."
        )

    if not command_type:
        raise ValueError(
            "command_type must not be empty."
        )

    if not callable(handler):
        raise TypeError(
            "handler must be callable."
        )

    if command_type in self._handlers:
        raise ValueError(
            f"Handler already registered for "
            f"command type: {command_type!r}"
        )

    self._handlers[command_type] = handler

def unregister_handler(
    self,
    command_type: str,
) -> None:
    """
    Remove a registered handler.

    Missing handlers are ignored.
    """

    self._handlers.pop(
        command_type,
        None,
    )

def has_handler(
    self,
    command_type: str,
) -> bool:
    """
    Return whether a handler is registered.
    """

    return command_type in self._handlers

# ========================================================
# NORMAL EXECUTION
# ========================================================

def execute(
    self,
    command: Command,
) -> ApplicationResult[Any]:
    """
    Execute a new Application command.

    A successful execution:

        * commits its transaction;
        * records its undo journal;
        * clears redo history.

    A failed execution:

        * rolls back its transaction;
        * leaves history unchanged;
        * re-raises the ApplicationError.

    This is the only normal entry point for new commands.
    """

    return self._execute_command(
        command,
        clear_redo=True,
    )

# ========================================================
# INTERNAL EXECUTION
# ========================================================

def _execute_command(
    self,
    command: Command,
    *,
    clear_redo: bool,
) -> ApplicationResult[Any]:
    """
    Execute one command through the complete Application
    transaction boundary.

    Parameters
    ----------
    command:
        Immutable Application command.

    clear_redo:
        True for a new user command.

        False for redo.

    Redo therefore uses exactly the same handler/service
    pipeline but has special history bookkeeping.
    """

    self._validate_command(
        command
    )

    handler = self._resolve_handler(
        command
    )

    transaction = Transaction(
        self._context
    )

    try:
        result = handler(
            command,
            self._context,
            transaction,
        )

        if not isinstance(
            result,
            ApplicationResult,
        ):
            raise ExecutionError(
                code="INVALID_HANDLER_RESULT",
                message=(
                    "Command handler returned an "
                    "invalid ApplicationResult."
                ),
                details={
                    "command_type": command.command_type,
                    "result_type": type(result).__name__,
                },
            )

        transaction.commit()

        self._record_execution(
            command=command,
            result=result,
            transaction=transaction,
            clear_redo=clear_redo,
        )

        return result

    except ApplicationError:
        self._rollback_safely(
            transaction
        )
        raise

    except Exception as exc:
        self._rollback_safely(
            transaction
        )

        raise ExecutionError(
            code="COMMAND_EXECUTION_FAILED",
            message=(
                f"Command execution failed: "
                f"{command.command_type}"
            ),
            details={
                "command_type": command.command_type,
                "command_id": str(command.command_id),
            },
            cause=exc,
        ) from exc

# ========================================================
# HISTORY RECORDING
# ========================================================

def _record_execution(
    self,
    *,
    command: Command,
    result: ApplicationResult[Any],
    transaction: Transaction,
    clear_redo: bool,
) -> None:
    """
    Record a successful command execution.

    New commands clear redo history.

    Redo executions preserve the remaining redo stack.
    """

    undo_operations = tuple(
        transaction.undo_operations
    )

    description = (
        result.message
        if result.message
        else command.command_type
    )

    if clear_redo:
        self._history.record(
            command,
            description=description,
            undo_operations=undo_operations,
        )
        return

    # ----------------------------------------------------
    # REDO
    # ----------------------------------------------------
    #
    # CommandHistory.record() intentionally clears redo.
    #
    # Redo is different from a new command: the remaining
    # redo records must survive.
    #
    # Capture the remaining redo stack, record the freshly
    # executed command, then restore the remaining records.
    # ----------------------------------------------------

    remaining_redo = self._history.redo_records()

    self._history.record(
        command,
        description=description,
        undo_operations=undo_operations,
    )

    self._history.clear_redo()

    for record in remaining_redo:
        self._history.push_redo(
            record
        )

# ========================================================
# UNDO
# ========================================================

def undo(self) -> ApplicationResult[Any] | None:
    """
    Undo the most recent reversible command.

    The CommandHistory record is moved from undo to redo
    before its journal is executed.

    On failure, the record is restored to the undo stack.

    Undo does not invoke the original command.
    """

    record = self._history.peek_undo()

    if record is None:
        return None

    if not record.reversible:
        raise ExecutionError(
            code="COMMAND_NOT_REVERSIBLE",
            message=(
                "The most recent command cannot be undone."
            ),
            details={
                "command_type": record.command_type,
                "command_id": str(
                    record.command_id
                ),
            },
        )

    record = self._history.pop_undo()

    try:
        self._execute_undo_operations(
            record
        )

        self._history.push_redo(
            record
        )

        return ApplicationResult.success(
            value=None,
            message=(
                f"Undid command: "
                f"{record.command_type}"
            ),
            metadata={
                "operation": "undo",
                "command_type": record.command_type,
                "command_id": str(
                    record.command_id
                ),
            },
        )

    except ApplicationError:
        self._history.restore_undo(
            record
        )
        raise

    except Exception as exc:
        self._history.restore_undo(
            record
        )

        raise ExecutionError(
            code="UNDO_FAILED",
            message=(
                f"Undo failed for command: "
                f"{record.command_type}"
            ),
            details={
                "command_type": record.command_type,
                "command_id": str(
                    record.command_id
                ),
            },
            cause=exc,
        ) from exc

def _execute_undo_operations(
    self,
    record: CommandRecord,
) -> None:
    """
    Execute the immutable undo journal belonging to a
    committed command record.

    CommandHistory stores the journal but never executes it.
    """

    for operation in reversed(
        record.undo_operations
    ):
        operation()

# ========================================================
# REDO
# ========================================================

def redo(self) -> ApplicationResult[Any] | None:
    """
    Re-execute the most recent command on the redo stack.

    Redo is controlled replay of the original Command.

    It does NOT execute the old undo journal.

    On success:

        undo += fresh execution
        redo -= exactly one record

    On failure:

        undo unchanged
        redo unchanged
        Core unchanged
    """

    record = self._history.peek_redo()

    if record is None:
        return None

    record = self._history.pop_redo()

    try:
        result = self._execute_command(
            record.command,
            clear_redo=False,
        )

        return result

    except ApplicationError:
        self._history.push_redo(
            record
        )
        raise

    except Exception:
        self._history.push_redo(
            record
        )
        raise

# ========================================================
# HISTORY STATE
# ========================================================

def can_undo(self) -> bool:
    """
    Return whether the latest command is reversible.
    """

    return self._history.can_undo()

def can_redo(self) -> bool:
    """
    Return whether a command is available for redo.
    """

    return self._history.can_redo()

def undo_count(self) -> int:
    """
    Return total undo-history count.
    """

    return self._history.undo_count()

def redo_count(self) -> int:
    """
    Return total redo-history count.
    """

    return self._history.redo_count()

def clear_history(self) -> None:
    """
    Clear all command history.
    """

    self._history.clear()

# ========================================================
# INTERNAL VALIDATION
# ========================================================

@staticmethod
def _validate_command(
    command: Command,
) -> None:
    """
    Validate the Application command boundary.
    """

    if not isinstance(
        command,
        Command,
    ):
        raise TypeError(
            "CommandManager.execute() requires "
            "a Command instance."
        )

    if not command.command_type:
        raise ValueError(
            "Command command_type must not be empty."
        )

def _resolve_handler(
    self,
    command: Command,
) -> CommandHandler:
    """
    Resolve the registered handler for a command.
    """

    handler = self._handlers.get(
        command.command_type
    )

    if handler is None:
        raise ExecutionError(
            code="COMMAND_HANDLER_NOT_FOUND",
            message=(
                f"No handler registered for "
                f"command type: "
                f"{command.command_type}"
            ),
            details={
                "command_type": command.command_type,
            },
        )

    return handler

# ========================================================
# SAFE ROLLBACK
# ========================================================

@staticmethod
def _rollback_safely(
    transaction: Transaction,
) -> None:
    """
    Roll back a transaction without masking the original
    Application exception.

    Transaction rollback failures are deliberately ignored
    here because the original exception is the primary
    Application failure. A production logging/diagnostics
    layer may record rollback failures separately.
    """

    try:
        transaction.rollback()
    except Exception:
        pass
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"CommandManager",
"CommandHandler",
]
