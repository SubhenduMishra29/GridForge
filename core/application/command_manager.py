# ============================================================

# File: core/application/command_manager.py

# GridForge V2 — Headless Application Command Manager

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Application Command Manager.

CommandManager is the atomic execution boundary of the
headless Application layer.

## Architectural position

```
UI / Plugin / Automation
          |
          v
   CommandManager
          |
   +------+------+
   |             |
   v             v
```

Transaction      Handler
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
* successful-command history recording;
* Application command capability discovery.
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

Every registered command is executed inside exactly one
Application Transaction.

Successful execution:

```
begin
    |
    v
handler
    |
    v
commit
    |
    v
history.record()
```

Failed execution:

```
begin
    |
    v
handler
    |
    v
rollback
    |
    v
failure returned/raised
```

History is updated only after transaction.commit() succeeds.

A failed or rolled-back command is never recorded in history.

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

Handlers are responsible for registering inverse operations
with the supplied transaction after successful mutations.

CommandManager alone controls:

```
begin()
commit()
rollback()
```

Handlers MUST NOT commit or rollback the transaction.

## Python Compatibility

GridForge V2 targets Python 3.10/3.11.
"""

from **future** import annotations

from dataclasses import dataclass
from typing import Callable

from .command import Command
from .context import ApplicationContext
from .errors import ApplicationError, ExecutionError
from .history import CommandHistory
from .results import ApplicationResult
from .transaction import Transaction, TransactionError

CommandHandler = Callable[
[
Command,
ApplicationContext,
Transaction,
],
ApplicationResult,
]

@dataclass(frozen=True)
class CommandRegistration:
"""
Immutable registration record for an Application command.
"""

```
command_type: str
handler: CommandHandler
```

class CommandManager:
"""
Headless Application command dispatcher.

```
CommandManager is the sole owner of command execution
transaction lifecycle and Application command history.
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

    self._handlers: dict[str, CommandHandler] = {}

# ============================================================
# CONTEXT
# ============================================================

@property
def context(self) -> ApplicationContext:
    """
    Return the Application dependency context.
    """

    return self._context

# ============================================================
# HISTORY
# ============================================================

@property
def history(self) -> CommandHistory:
    """
    Return the Application-owned command history.
    """

    return self._history

# ------------------------------------------------------------

def can_undo(self) -> bool:
    """
    Return whether Application history contains an undo record.
    """

    return self._history.can_undo()

# ------------------------------------------------------------

def can_redo(self) -> bool:
    """
    Return whether Application history contains a redo record.
    """

    return self._history.can_redo()

# ============================================================
# REGISTRATION
# ============================================================

def register(
    self,
    command_type: str,
    handler: CommandHandler,
) -> None:
    """
    Register a handler for an Application command type.
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
            f"Command already registered: {command_type}"
        )

    self._handlers[command_type] = handler

# ------------------------------------------------------------

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

    return (
        self._handlers.pop(
            command_type,
            None,
        )
        is not None
    )

# ------------------------------------------------------------

def is_registered(
    self,
    command_type: str,
) -> bool:
    """
    Return whether a command type has a registered handler.
    """

    return command_type in self._handlers

# ------------------------------------------------------------

def registered_commands(self) -> tuple[str, ...]:
    """
    Return registered command types as an immutable tuple.
    """

    return tuple(
        self._handlers.keys()
    )

# ============================================================
# EXECUTION
# ============================================================

def execute(
    self,
    command: Command,
) -> ApplicationResult:
    """
    Execute one registered Application command atomically.

    Transaction lifecycle is owned entirely by CommandManager.

    Successful path:

        transaction.begin()
        handler(...)
        transaction.commit()
        history.record()

    Failure path:

        transaction.begin()
        handler(...)
        transaction.rollback()

    Unexpected exceptions are converted into ExecutionError
    after rollback has completed.

    Raises
    ------

    TypeError
        If command is not a Command.

    ApplicationError
        Expected Application-level failure.

    ExecutionError
        Unexpected execution failure, invalid result, or
        transaction failure.
    """

    if not isinstance(command, Command):
        raise TypeError(
            "CommandManager.execute requires a Command."
        )

    handler = self._handlers.get(
        command.command_type,
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

    # --------------------------------------------------------
    # BEGIN
    # --------------------------------------------------------

    try:
        transaction.begin()

    except Exception as exc:
        raise ExecutionError(
            code="TRANSACTION_BEGIN_FAILED",
            message=(
                f"Transaction could not be started for "
                f"command '{command.command_type}'."
            ),
            details={
                "command_type": command.command_type,
                "command_id": str(
                    command.command_id
                ),
            },
            cause=exc,
        ) from exc

    # --------------------------------------------------------
    # HANDLER EXECUTION
    # --------------------------------------------------------

    try:

        result = handler(
            command,
            self._context,
            transaction,
        )

    except ApplicationError:

        self._rollback_after_failure(
            transaction=transaction,
            command=command,
        )

        raise

    except Exception as exc:

        rollback_error = (
            self._rollback_after_failure(
                transaction=transaction,
                command=command,
            )
        )

        if rollback_error is not None:

            raise ExecutionError(
                code="COMMAND_ROLLBACK_FAILED",
                message=(
                    f"Command '{command.command_type}' "
                    "failed and its transaction could not "
                    "be completely rolled back."
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

    # --------------------------------------------------------
    # RESULT VALIDATION
    # --------------------------------------------------------

    if not isinstance(
        result,
        ApplicationResult,
    ):

        rollback_error = (
            self._rollback_after_failure(
                transaction=transaction,
                command=command,
            )
        )

        if rollback_error is not None:

            raise ExecutionError(
                code="COMMAND_ROLLBACK_FAILED",
                message=(
                    f"Command '{command.command_type}' "
                    "returned an invalid result and its "
                    "transaction rollback failed."
                ),
                details={
                    "command_type": (
                        command.command_type
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
            },
        )

    # --------------------------------------------------------
    # APPLICATION FAILURE RESULT
    # --------------------------------------------------------

    if not result.success:

        rollback_error = (
            self._rollback_after_failure(
                transaction=transaction,
                command=command,
            )
        )

        if rollback_error is not None:

            raise ExecutionError(
                code="COMMAND_ROLLBACK_FAILED",
                message=(
                    f"Command '{command.command_type}' "
                    "returned a failure result and its "
                    "transaction rollback failed."
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

    # --------------------------------------------------------
    # COMMIT
    # --------------------------------------------------------

    try:

        transaction.commit()

    except TransactionError as exc:

        rollback_error = (
            self._rollback_after_commit_failure(
                transaction=transaction,
                command=command,
            )
        )

        if rollback_error is not None:

            raise ExecutionError(
                code="TRANSACTION_COMMIT_FAILED",
                message=(
                    f"Command '{command.command_type}' "
                    "could not commit and rollback also "
                    "failed."
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

    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    try:

        self._history.record(
            command,
            description=result.message,
        )

    except Exception as exc:

        # IMPORTANT:
        #
        # The transaction has already committed.
        # Therefore Core state MUST NOT be rolled back here.
        #
        # History failure is an Application-history failure,
        # not a Core mutation failure.

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

# ============================================================
# ROLLBACK HELPERS
# ============================================================

@staticmethod
def _rollback_after_failure(
    *,
    transaction: Transaction,
    command: Command,
) -> Exception | None:
    """
    Roll back an ACTIVE transaction after command failure.

    Returns the rollback exception, if any.

    The original command failure must remain the primary
    failure whenever rollback succeeds.
    """

    if not transaction.active:
        return None

    try:

        transaction.rollback()

    except Exception as exc:

        return exc

    return None

# ------------------------------------------------------------

@staticmethod
def _rollback_after_commit_failure(
    *,
    transaction: Transaction,
    command: Command,
) -> Exception | None:
    """
    Attempt rollback after an unsuccessful commit operation.

    Normally Transaction.commit() transitions atomically from
    ACTIVE to COMMITTED. This helper exists defensively for
    Transaction implementations that may fail before changing
    lifecycle state.
    """

    if not transaction.active:
        return None

    try:

        transaction.rollback()

    except Exception as exc:

        return exc

    return None
```

**all** = [
"CommandHandler",
"CommandRegistration",
"CommandManager",
]
