# ============================================================

# File: core/application/command_manager.py

# GridForge V2 — Headless Application Command Manager

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Application Command Manager.

CommandManager is the execution coordinator of the headless
Application layer.

## Architectural position

```
UI / Plugin / Automation
          |
          v
       Command
          |
          v
   CommandManager
      /       \
     v         v
```

Transaction    Handler
|
v
Application Service
|
v
Core

## Responsibilities

CommandManager owns:

```
* command registration;
* command dispatch;
* synchronous command execution;
* transaction lifecycle;
* committed command history;
* undo execution;
* redo coordination.
```

CommandManager does NOT own:

```
* Core domain state;
* Network internals;
* topology;
* Y-bus;
* UI state;
* Qt;
* SLD/canvas state;
* rendering;
* plugin lifecycle;
* domain calculations.
```

## Transaction boundary

Every command handler executes inside one ACTIVE Transaction.

Successful execution:

```
handler
   |
   v
transaction.commit()
   |
   v
UndoJournal
   |
   v
CommandHistory.record()
```

Failed execution:

```
handler failure
   |
   v
transaction.rollback()
```

History is updated only after a successful commit.

## Undo

Undo executes the committed undo journal in reverse registration
order.

History itself does not execute undo operations.

## Redo

Redo re-enters the normal Application command execution path.

Redo therefore does not directly mutate Core.

## Handler contract

Handlers receive:

```
command
application context
active transaction
```

and return:

```
ApplicationResult
```

Handlers may register inverse operations with the transaction.

Handlers MUST NOT:

```
* commit the transaction;
* rollback the transaction;
* manipulate CommandHistory.
```

## Headless requirement

This module has no UI or Qt dependencies.

## Python compatibility

GridForge V2 targets Python 3.10 / 3.11.
"""

from **future** import annotations

from dataclasses import dataclass
from typing import Callable

from .command import Command
from .context import ApplicationContext
from .errors import ApplicationError, ExecutionError
from .history import CommandHistory, UndoJournal
from .results import ApplicationResult
from .transaction import Transaction

# ============================================================

# TYPES

# ============================================================

CommandHandler = Callable[
[
Command,
ApplicationContext,
Transaction,
],
ApplicationResult,
]

# ============================================================

# COMMAND REGISTRATION

# ============================================================

@dataclass(frozen=True)
class CommandRegistration:
"""
Immutable registration record for an Application command.
"""

```
command_type: str
handler: CommandHandler
```

# ============================================================

# COMMAND MANAGER

# ============================================================

class CommandManager:
"""
Headless Application command dispatcher.

```
CommandManager is the sole coordinator of:

    command dispatch
    transaction lifecycle
    committed command history
    undo
    redo
"""

def __init__(
    self,
    context: ApplicationContext,
    history: CommandHistory | None = None,
) -> None:

    if context is None:
        raise ValueError(
            "CommandManager context must not be None."
        )

    self._context = context

    self._history = (
        history
        if history is not None
        else CommandHistory()
    )

    self._handlers: dict[
        str,
        CommandHandler,
    ] = {}

    self._registrations: dict[
        str,
        CommandRegistration,
    ] = {}

# ========================================================
# CONTEXT
# ========================================================

@property
def context(self) -> ApplicationContext:
    """
    Return the Application dependency context.
    """

    return self._context

# ========================================================
# HISTORY
# ========================================================

@property
def history(self) -> CommandHistory:
    """
    Return the Application-owned command history.
    """

    return self._history

# --------------------------------------------------------

def can_undo(self) -> bool:
    """
    Return whether the most recent command is undoable.
    """

    return self._history.can_undo()

# --------------------------------------------------------

def can_redo(self) -> bool:
    """
    Return whether a command can be replayed.
    """

    return self._history.can_redo()

# ========================================================
# REGISTRATION
# ========================================================

def register(
    self,
    command_type: str,
    handler: CommandHandler,
) -> None:
    """
    Register a handler for a semantic command type.
    """

    if not isinstance(command_type, str):
        raise TypeError(
            "command_type must be a string."
        )

    command_type = command_type.strip()

    if not command_type:
        raise ValueError(
            "command_type must not be empty."
        )

    if not callable(handler):
        raise TypeError(
            "command handler must be callable."
        )

    if command_type in self._handlers:
        raise ValueError(
            f"Command already registered: "
            f"{command_type}"
        )

    registration = CommandRegistration(
        command_type=command_type,
        handler=handler,
    )

    self._handlers[command_type] = handler
    self._registrations[command_type] = registration

# --------------------------------------------------------

def unregister(
    self,
    command_type: str,
) -> bool:
    """
    Remove a registered command handler.

    Returns True when a handler was removed.
    """

    if not isinstance(command_type, str):
        raise TypeError(
            "command_type must be a string."
        )

    command_type = command_type.strip()

    removed = self._handlers.pop(
        command_type,
        None,
    )

    self._registrations.pop(
        command_type,
        None,
    )

    return removed is not None

# --------------------------------------------------------

def is_registered(
    self,
    command_type: str,
) -> bool:
    """
    Return whether a command type is registered.
    """

    if not isinstance(command_type, str):
        return False

    return command_type in self._handlers

# --------------------------------------------------------

def registered_commands(self) -> tuple[str, ...]:
    """
    Return registered semantic command types.
    """

    return tuple(
        self._handlers.keys()
    )

# --------------------------------------------------------

def registration(
    self,
    command_type: str,
) -> CommandRegistration | None:
    """
    Return an immutable registration record.
    """

    return self._registrations.get(
        command_type
    )

# ========================================================
# EXECUTION
# ========================================================

def execute(
    self,
    command: Command,
) -> ApplicationResult:
    """
    Execute one registered command atomically.

    Successful execution:

        handler
            |
            v
        commit()
            |
            v
        history.record()

    Failed execution:

        handler failure
            |
            v
        rollback()

    A command is recorded only after commit succeeds.
    """

    if not isinstance(command, Command):
        raise TypeError(
            "CommandManager.execute requires a Command."
        )

    handler = self._handlers.get(
        command.command_type
    )

    if handler is None:
        raise ExecutionError(
            code="COMMAND_NOT_REGISTERED",
            message=(
                "No handler is registered for command "
                f"'{command.command_type}'."
            ),
            details={
                "command_type": command.command_type,
                "command_id": str(
                    command.command_id
                ),
            },
        )

    transaction = Transaction()

    # ----------------------------------------------------
    # HANDLER
    # ----------------------------------------------------

    try:

        result = handler(
            command,
            self._context,
            transaction,
        )

    except ApplicationError:

        rollback_error = (
            self._rollback(
                transaction,
            )
        )

        if rollback_error is not None:

            raise ExecutionError(
                code="COMMAND_ROLLBACK_FAILED",
                message=(
                    f"Command '{command.command_type}' "
                    "failed and rollback also failed."
                ),
                details={
                    "command_type": (
                        command.command_type
                    ),
                    "command_id": str(
                        command.command_id
                    ),
                },
                cause=rollback_error,
            )

        raise

    except Exception as exc:

        rollback_error = (
            self._rollback(
                transaction,
            )
        )

        if rollback_error is not None:

            raise ExecutionError(
                code="COMMAND_ROLLBACK_FAILED",
                message=(
                    f"Command '{command.command_type}' "
                    "failed and rollback also failed."
                ),
                details={
                    "command_type": (
                        command.command_type
                    ),
                    "command_id": str(
                        command.command_id
                    ),
                },
                cause=rollback_error,
            ) from exc

        raise ExecutionError(
            code="COMMAND_EXECUTION_FAILED",
            message=(
                f"Command '{command.command_type}' "
                "failed during execution."
            ),
            details={
                "command_type": command.command_type,
                "command_id": str(
                    command.command_id
                ),
            },
            cause=exc,
        ) from exc

    # ----------------------------------------------------
    # RESULT CONTRACT
    # ----------------------------------------------------

    if not isinstance(
        result,
        ApplicationResult,
    ):

        rollback_error = (
            self._rollback(
                transaction,
            )
        )

        if rollback_error is not None:

            raise ExecutionError(
                code="COMMAND_ROLLBACK_FAILED",
                message=(
                    f"Command '{command.command_type}' "
                    "returned an invalid result and "
                    "rollback failed."
                ),
                details={
                    "command_type": (
                        command.command_type
                    ),
                    "command_id": str(
                        command.command_id
                    ),
                },
                cause=rollback_error,
            )

        raise ExecutionError(
            code="INVALID_COMMAND_RESULT",
            message=(
                f"Command handler for "
                f"'{command.command_type}' did not return "
                "an ApplicationResult."
            ),
            details={
                "command_type": command.command_type,
                "command_id": str(
                    command.command_id
                ),
            },
        )

    # ----------------------------------------------------
    # APPLICATION FAILURE RESULT
    # ----------------------------------------------------

    if not result.success:

        rollback_error = (
            self._rollback(
                transaction,
            )
        )

        if rollback_error is not None:

            raise ExecutionError(
                code="COMMAND_ROLLBACK_FAILED",
                message=(
                    f"Command '{command.command_type}' "
                    "returned a failure result and "
                    "rollback failed."
                ),
                details={
                    "command_type": (
                        command.command_type
                    ),
                    "command_id": str(
                        command.command_id
                    ),
                },
                cause=rollback_error,
            )

        return result

    # ----------------------------------------------------
    # COMMIT
    # ----------------------------------------------------

    try:

        undo_journal: UndoJournal = (
            transaction.commit()
        )

    except Exception as exc:

        rollback_error = (
            self._rollback(
                transaction,
            )
        )

        if rollback_error is not None:

            raise ExecutionError(
                code="TRANSACTION_COMMIT_FAILED",
                message=(
                    f"Command '{command.command_type}' "
                    "could not commit and rollback "
                    "also failed."
                ),
                details={
                    "command_type": (
                        command.command_type
                    ),
                    "command_id": str(
                        command.command_id
                    ),
                },
                cause=rollback_error,
            ) from exc

        raise ExecutionError(
            code="TRANSACTION_COMMIT_FAILED",
            message=(
                f"Command '{command.command_type}' "
                "could not commit."
            ),
            details={
                "command_type": (
                    command.command_type
                ),
                "command_id": str(
                    command.command_id
                ),
            },
            cause=exc,
        ) from exc

    # ----------------------------------------------------
    # HISTORY
    # ----------------------------------------------------

    try:

        self._history.record(
            command,
            description=(
                result.message or None
            ),
            undo_operations=undo_journal,
        )

    except Exception as exc:

        # The transaction has already committed.
        #
        # Core state must NOT be rolled back here.
        #
        # History recording failure is an Application
        # infrastructure failure after successful mutation.

        raise ExecutionError(
            code="COMMAND_HISTORY_RECORD_FAILED",
            message=(
                f"Command '{command.command_type}' "
                "committed successfully but could not "
                "be recorded in command history."
            ),
            details={
                "command_type": (
                    command.command_type
                ),
                "command_id": str(
                    command.command_id
                ),
            },
            cause=exc,
        ) from exc

    return result

# ========================================================
# UNDO
# ========================================================

def undo(self) -> ApplicationResult | None:
    """
    Undo the most recent committed undoable command.

    The history record is not removed until every inverse
    operation succeeds.

    Undo operations execute in reverse registration order.
    """

    record = self._history.peek_undo()

    if record is None:
        return None

    if not record.reversible:
        raise ExecutionError(
            code="COMMAND_NOT_UNDOABLE",
            message=(
                f"Command '{record.command_type}' "
                "does not contain a committed undo journal."
            ),
            details={
                "command_type": record.command_type,
                "command_id": record.command_id,
            },
        )

    operations = tuple(
        reversed(record.undo_operations)
    )

    for operation in operations:

        try:

            operation()

        except Exception as exc:

            raise ExecutionError(
                code="UNDO_FAILED",
                message=(
                    f"Undo failed for command "
                    f"'{record.command_type}'."
                ),
                details={
                    "command_type": (
                        record.command_type
                    ),
                    "command_id": (
                        record.command_id
                    ),
                },
                cause=exc,
            ) from exc

    committed_record = (
        self._history.pop_undo()
    )

    if committed_record is None:
        raise ExecutionError(
            code="UNDO_HISTORY_STATE_ERROR",
            message=(
                "Undo operations completed but the "
                "corresponding history record disappeared."
            ),
        )

    self._history.push_redo(
        committed_record
    )

    return ApplicationResult.success_result(
        message=(
            f"Undid command "
            f"'{committed_record.command_type}'."
        ),
        code="UNDO_OK",
        metadata={
            "command_type": (
                committed_record.command_type
            ),
            "command_id": (
                committed_record.command_id
            ),
        },
    )

# ========================================================
# REDO
# ========================================================

def redo(self) -> ApplicationResult | None:
    """
    Re-execute the most recent undone command through the
    normal Application command pipeline.

    The original command is never mutated.

    A fresh Transaction is created by execute().
    """

    record = self._history.peek_redo()

    if record is None:
        return None

    redo_record = self._history.pop_redo()

    if redo_record is None:
        return None

    try:

        return self.execute(
            redo_record.command
        )

    except Exception:

        # The command was not successfully replayed.
        #
        # Restore the redo entry so the user can retry.

        self._history.push_redo(
            redo_record
        )

        raise

# ========================================================
# ROLLBACK HELPER
# ========================================================

@staticmethod
def _rollback(
    transaction: Transaction,
) -> Exception | None:
    """
    Roll back an active transaction.

    Returns the rollback exception when rollback itself fails.
    """

    if not transaction.active:
        return None

    try:

        transaction.rollback()

    except Exception as exc:

        return exc

    return None
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"CommandHandler",
"CommandRegistration",
"CommandManager",
]
