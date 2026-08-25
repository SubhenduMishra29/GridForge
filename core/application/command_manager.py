# ============================================================
# File: core/application/command_manager.py
# GridForge V2 — Headless Application Command Manager
# Author: Subhendu Mishra
# ============================================================

"""
Headless Application command execution coordinator.

Responsibilities
----------------
- Validate commands.
- Resolve registered command handlers.
- Create transactions.
- Invoke handlers.
- Commit successful transactions.
- Roll back failed transactions.
- Record committed UndoJournals in CommandHistory.
- Execute undo journals.
- Re-execute commands for redo.

CommandManager does not:
- mutate Core directly;
- resolve endpoints;
- contain engineering logic;
- access UI/Qt/SLD state;
- access Core registries directly.

Execution boundary
------------------

    Command
        |
        v
    CommandManager
        |
        v
    CommandHandler
        |
        v
    Application Service
        |
        v
       Core

Transaction boundary
--------------------

    ACTIVE
      |
      +---- handler failure ----> rollback()
      |                              |
      |                              v
      |                         ROLLED_BACK
      |
      +---- handler success ---> commit()
                                     |
                                     v
                                COMMITTED
                                     |
                                     v
                                UndoJournal

After commit:
    rollback is never attempted.

Redo:
    Redo re-executes the original Command through the normal
    command pipeline. It does not replay the old UndoJournal.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .command import Command
from .errors import ApplicationError, ExecutionError
from .history import (
    CommandHistory,
    CommandRecord,
    UndoJournal,
)
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

    CommandManager owns orchestration only.

    Core model state remains owned by the Core layer.
    """

    def __init__(
        self,
        context: Any,
        handlers: Mapping[str, CommandHandler] | None = None,
        history: CommandHistory | None = None,
    ) -> None:
        if context is None:
            raise ValueError("context is required.")

        self._context = context

        self._handlers: dict[
            str,
            CommandHandler,
        ] = dict(handlers or {})

        self._history = (
            history
            if history is not None
            else CommandHistory()
        )

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def history(self) -> CommandHistory:
        """Return the command history."""
        return self._history

    @property
    def registered_commands(self) -> tuple[str, ...]:
        """Return registered command types."""
        return tuple(self._handlers.keys())

    # ========================================================
    # HANDLER REGISTRATION
    # ========================================================

    def register_handler(
        self,
        command_type: str,
        handler: CommandHandler,
    ) -> None:
        """Register a command handler."""

        self._validate_command_type(command_type)

        if not callable(handler):
            raise TypeError(
                "handler must be callable."
            )

        if command_type in self._handlers:
            raise ValueError(
                "Handler already registered for "
                f"command type: {command_type!r}"
            )

        self._handlers[command_type] = handler

    def unregister_handler(
        self,
        command_type: str,
    ) -> None:
        """Remove a command handler if registered."""

        self._handlers.pop(command_type, None)

    def has_handler(
        self,
        command_type: str,
    ) -> bool:
        """Return whether a handler is registered."""

        return command_type in self._handlers

    def is_registered(
        self,
        command_type: str,
    ) -> bool:
        """Return whether a command type is registered."""

        return self.has_handler(command_type)

    # ========================================================
    # EXECUTION
    # ========================================================

    def execute(
        self,
        command: Command,
    ) -> ApplicationResult[Any]:
        """
        Execute a new command.

        A successful command:
            handler -> commit -> history

        A failed command:
            handler -> rollback -> error

        A new successful command clears redo history.
        """

        return self._execute_command(
            command,
            clear_redo=True,
        )

    def _execute_command(
        self,
        command: Command,
        *,
        clear_redo: bool,
    ) -> ApplicationResult[Any]:
        """
        Execute one command through the Application transaction
        boundary.

        The method has three strictly separated phases:

            1. PRE-COMMIT
            2. COMMIT
            3. POST-COMMIT

        Rollback is permitted only before the transaction has
        reached a terminal state.
        """

        self._validate_command(command)

        handler = self._resolve_handler(command)

        transaction = Transaction()

        # ----------------------------------------------------
        # PRE-COMMIT
        # ----------------------------------------------------
        #
        # Any exception here means the transaction is still
        # owned by this execution path and must be rolled back.
        #
        try:
            result = handler(
                command,
                self._context,
                transaction,
            )

            self._validate_handler_result(
                command,
                result,
            )

            if not result.success:
                raise ExecutionError(
                    code="COMMAND_FAILED",
                    message=(
                        result.message
                        or "Command handler reported failure."
                    ),
                    details={
                        "command_type": command.command_type,
                        "command_id": str(
                            command.command_id
                        ),
                        "metadata": dict(
                            result.metadata
                        ),
                    },
                )

        except ApplicationError:
            self._rollback_safely(transaction)
            raise

        except Exception as exc:
            self._rollback_safely(transaction)

            raise ExecutionError(
                code="COMMAND_EXECUTION_FAILED",
                message=(
                    "Command execution failed: "
                    f"{command.command_type}"
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
        # COMMIT
        # ----------------------------------------------------
        #
        # commit() is intentionally outside the handler
        # exception boundary.
        #
        # If commit succeeds, the transaction is closed and
        # MUST NOT be rolled back afterwards.
        #
        try:
            undo_journal = transaction.commit()

        except ApplicationError:
            self._rollback_safely(transaction)
            raise

        except Exception as exc:
            self._rollback_safely(transaction)

            raise ExecutionError(
                code="COMMAND_COMMIT_FAILED",
                message=(
                    "Command transaction commit failed: "
                    f"{command.command_type}"
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
        # POST-COMMIT
        # ----------------------------------------------------
        #
        # The transaction is now COMMITTED.
        #
        # History recording failure must therefore NOT trigger
        # rollback. The Core mutation is already committed.
        #
        try:
            self._record_execution(
                command=command,
                result=result,
                undo_journal=undo_journal,
                clear_redo=clear_redo,
            )

        except ApplicationError:
            raise

        except Exception as exc:
            raise ExecutionError(
                code="COMMAND_HISTORY_RECORD_FAILED",
                message=(
                    "Command committed successfully, "
                    "but its history record could not be stored: "
                    f"{command.command_type}"
                ),
                details={
                    "command_type": command.command_type,
                    "command_id": str(
                        command.command_id
                    ),
                },
                cause=exc,
            ) from exc

        return result

    # ========================================================
    # HISTORY RECORDING
    # ========================================================

    def _record_execution(
        self,
        *,
        command: Command,
        result: ApplicationResult[Any],
        undo_journal: UndoJournal,
        clear_redo: bool,
    ) -> CommandRecord:
        """
        Record a successfully committed command.

        The Transaction is already closed here.
        """

        description = (
            result.message
            or command.command_type
        )

        return self._history.record(
            command,
            description=description,
            undo_operations=undo_journal,
            clear_redo=clear_redo,
        )

    # ========================================================
    # UNDO
    # ========================================================

    def undo(
        self,
    ) -> ApplicationResult[Any] | None:
        """
        Undo the most recent reversible command.

        Undo operations are executed in reverse registration
        order.
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

        if record is None:
            raise ExecutionError(
                code="UNDO_HISTORY_STATE_ERROR",
                message=(
                    "Undo history changed unexpectedly "
                    "while preparing undo."
                ),
                details={},
            )

        try:
            self._execute_undo_journal(record)

        except ApplicationError:
            self._history.push_undo(record)
            raise

        except Exception as exc:
            self._history.push_undo(record)

            raise ExecutionError(
                code="UNDO_FAILED",
                message=(
                    "Undo failed for command: "
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

        self._history.push_redo(record)

        return ApplicationResult.success_result(
            value=None,
            message=(
                "Undid command: "
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

    @staticmethod
    def _execute_undo_journal(
        record: CommandRecord,
    ) -> None:
        """
        Execute inverse operations in reverse order.
        """

        for operation in reversed(
            record.undo_operations
        ):
            operation()

    # ========================================================
    # REDO
    # ========================================================

    def redo(
        self,
    ) -> ApplicationResult[Any] | None:
        """
        Redo the most recent command.

        Redo re-executes the original Command through the normal
        command execution path and creates a fresh transaction
        and UndoJournal.
        """

        record = self._history.pop_redo()

        if record is None:
            return None

        try:
            return self._execute_command(
                record.command,
                clear_redo=False,
            )

        except ApplicationError:
            self._history.push_redo(record)
            raise

        except Exception:
            self._history.push_redo(record)
            raise

    # ========================================================
    # HISTORY STATE
    # ========================================================

    def can_undo(self) -> bool:
        """Return whether an undo operation is available."""

        return self._history.can_undo()

    def can_redo(self) -> bool:
        """Return whether a redo operation is available."""

        return self._history.can_redo()

    def undo_count(self) -> int:
        """Return the number of undo records."""

        return self._history.undo_count()

    def redo_count(self) -> int:
        """Return the number of redo records."""

        return self._history.redo_count()

    def clear_history(self) -> None:
        """Clear undo and redo history."""

        self._history.clear()

    def undo_commands(
        self,
    ) -> tuple[CommandRecord, ...]:
        """Return an immutable undo-history snapshot."""

        return self._history.undo_commands()

    def redo_commands(
        self,
    ) -> tuple[CommandRecord, ...]:
        """Return an immutable redo-history snapshot."""

        return self._history.redo_commands()

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_command_type(
        command_type: str,
    ) -> None:
        """Validate a command type identifier."""

        if not isinstance(command_type, str):
            raise TypeError(
                "command_type must be str."
            )

        if not command_type.strip():
            raise ValueError(
                "command_type must not be empty."
            )

    @classmethod
    def _validate_command(
        cls,
        command: Command,
    ) -> None:
        """Validate the command boundary."""

        if not isinstance(command, Command):
            raise TypeError(
                "CommandManager.execute() requires "
                "a Command instance."
            )

        cls._validate_command_type(
            command.command_type
        )

    @staticmethod
    def _validate_handler_result(
        command: Command,
        result: Any,
    ) -> None:
        """Ensure the handler returned ApplicationResult."""

        if not isinstance(
            result,
            ApplicationResult,
        ):
            raise ExecutionError(
                code="INVALID_HANDLER_RESULT",
                message=(
                    "Command handler returned an invalid "
                    "ApplicationResult."
                ),
                details={
                    "command_type": command.command_type,
                    "result_type": type(result).__name__,
                },
            )

    # ========================================================
    # HANDLER RESOLUTION
    # ========================================================

    def _resolve_handler(
        self,
        command: Command,
    ) -> CommandHandler:
        """Resolve the handler for a command type."""

        handler = self._handlers.get(
            command.command_type
        )

        if handler is None:
            raise ExecutionError(
                code="COMMAND_HANDLER_NOT_FOUND",
                message=(
                    "No handler registered for command type: "
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
        Roll back an active transaction.

        Transaction.rollback() transitions the transaction out
        of ACTIVE before executing inverse operations.

        Therefore:

            ACTIVE -> rollback() -> ROLLED_BACK

        and rollback must never be attempted a second time.

        Any rollback failure is surfaced as an ExecutionError.
        """

        if not transaction.active:
            return

        try:
            transaction.rollback()

        except Exception as exc:
            raise ExecutionError(
                code="TRANSACTION_ROLLBACK_FAILED",
                message="Transaction rollback failed.",
                details={},
                cause=exc,
            ) from exc


__all__ = [
    "CommandManager",
    "CommandHandler",
]
