# ============================================================
# File: core/application/command_manager.py
# GridForge V2 — Headless Application Command Manager
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Headless Application Command Manager
====================================================

CommandManager is the Application-layer orchestration boundary
for command execution, transactions, undo, and redo.

Responsibilities
----------------

CommandManager:

    * accepts Application Commands;
    * resolves registered command handlers;
    * creates Transactions;
    * invokes handlers;
    * commits successful Transactions;
    * records committed UndoJournals;
    * rolls back failed Transactions;
    * executes undo journals;
    * coordinates redo.

CommandManager does NOT:

    * own electrical/domain state;
    * mutate Core directly;
    * perform topology operations directly;
    * contain engineering algorithms;
    * access Qt or UI;
    * resolve SLD objects;
    * contain equipment-specific engineering logic.

Execution boundary
------------------

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

Undo
----

Transaction.commit() returns an immutable UndoJournal.

CommandManager owns execution of that journal.

CommandHistory stores the journal but never executes it.

Redo
----

Redo never executes an old UndoJournal.

Redo re-executes the original immutable Command through the
normal CommandManager -> Handler -> Service -> Core path.

Author:
    Subhendu Mishra
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

    It does not own Core state.
    """

    def __init__(
        self,
        context: Any,
        handlers: Mapping[
            str,
            CommandHandler,
        ] | None = None,
        history: CommandHistory | None = None,
    ) -> None:

        if context is None:
            raise ValueError(
                "context is required."
            )

        self._context = context

        self._handlers: dict[
            str,
            CommandHandler,
        ] = dict(
            handlers or {}
        )

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
        """
        Return the Application command history.
        """

        return self._history

    @property
    def registered_commands(self) -> tuple[str, ...]:
        """
        Return all currently registered command types.
        """

        return tuple(
            self._handlers.keys()
        )

    # ========================================================
    # HANDLER REGISTRATION
    # ========================================================

    def register_handler(
        self,
        command_type: str,
        handler: CommandHandler,
    ) -> None:
        """
        Register a command handler.

        Duplicate command registrations are rejected.
        """

        self._validate_command_type(
            command_type
        )

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
        """
        Remove a registered command handler.

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

    def is_registered(
        self,
        command_type: str,
    ) -> bool:
        """
        Public Application-facing registration query.
        """

        return self.has_handler(
            command_type
        )

    # ========================================================
    # EXECUTION
    # ========================================================

    def execute(
        self,
        command: Command,
    ) -> ApplicationResult[Any]:
        """
        Execute a new Application command.

        A successful new command:

            1. executes through its handler;
            2. commits its Transaction;
            3. records the resulting UndoJournal;
            4. clears existing redo history.

        A failed command:

            1. rolls back its active Transaction;
            2. leaves command history unchanged;
            3. propagates an ApplicationError.
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
        Execute one command through the complete Application
        transaction boundary.

        Parameters
        ----------
        clear_redo:
            True for a newly issued command.

            False for redo execution.
        """

        self._validate_command(
            command
        )

        handler = self._resolve_handler(
            command
        )

        transaction = Transaction()

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
                self._rollback_safely(
                    transaction
                )

                raise ExecutionError(
                    code="COMMAND_FAILED",
                    message=(
                        result.message
                        or (
                            "Command handler reported "
                            "failure."
                        )
                    ),
                    details={
                        "command_type": (
                            command.command_type
                        ),
                        "command_id": str(
                            command.command_id
                        ),
                        "metadata": dict(
                            result.metadata
                        ),
                    },
                )

            # Transaction.commit() is the sole boundary at
            # which the immutable UndoJournal is produced.
            undo_journal = transaction.commit()

            self._record_execution(
                command=command,
                result=result,
                undo_journal=undo_journal,
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
                    "Command execution failed: "
                    f"{command.command_type}"
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
        Record one successfully committed command.
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
        Undo the latest reversible command.

        The stored UndoJournal is executed in reverse order.

        CommandHistory remains state-only; CommandManager owns
        actual undo execution.
        """

        record = self._history.peek_undo()

        if record is None:
            return None

        if not record.reversible:
            raise ExecutionError(
                code="COMMAND_NOT_REVERSIBLE",
                message=(
                    "The most recent command "
                    "cannot be undone."
                ),
                details={
                    "command_type": (
                        record.command_type
                    ),
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
            self._execute_undo_journal(
                record
            )

        except ApplicationError:
            self._history.push_undo(
                record
            )
            raise

        except Exception as exc:
            self._history.push_undo(
                record
            )

            raise ExecutionError(
                code="UNDO_FAILED",
                message=(
                    "Undo failed for command: "
                    f"{record.command_type}"
                ),
                details={
                    "command_type": (
                        record.command_type
                    ),
                    "command_id": str(
                        record.command_id
                    ),
                },
                cause=exc,
            ) from exc

        self._history.push_redo(
            record
        )

        return ApplicationResult.success_result(
            value=None,
            message=(
                "Undid command: "
                f"{record.command_type}"
            ),
            metadata={
                "operation": "undo",
                "command_type": (
                    record.command_type
                ),
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
        Execute the inverse operations in reverse order.

        Transaction.commit() preserves registration order.
        Therefore undo must reverse that order.
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
        Redo the latest command.

        Redo:

            1. removes the latest redo record temporarily;
            2. re-executes its original immutable Command;
            3. creates a fresh Transaction;
            4. creates a fresh UndoJournal;
            5. records the new execution.

        The existing redo stack is preserved while executing the
        command.
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
        Return whether a redo command exists.
        """

        return self._history.can_redo()

    def undo_count(self) -> int:
        """
        Return the number of undo records.
        """

        return self._history.undo_count()

    def redo_count(self) -> int:
        """
        Return the number of redo records.
        """

        return self._history.redo_count()

    def clear_history(self) -> None:
        """
        Clear both undo and redo history.
        """

        self._history.clear()

    def undo_commands(
        self,
    ) -> tuple[CommandRecord, ...]:
        """
        Return an immutable snapshot of undo history.
        """

        return self._history.undo_commands()

    def redo_commands(
        self,
    ) -> tuple[CommandRecord, ...]:
        """
        Return an immutable snapshot of redo history.
        """

        return self._history.redo_commands()

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_command_type(
        command_type: str,
    ) -> None:
        """
        Validate a command type identifier.
        """

        if not isinstance(
            command_type,
            str,
        ):
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

        cls._validate_command_type(
            command.command_type
        )

    @staticmethod
    def _validate_handler_result(
        command: Command,
        result: Any,
    ) -> None:
        """
        Ensure handlers return the canonical ApplicationResult.
        """

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
                    "command_type": (
                        command.command_type
                    ),
                    "result_type": (
                        type(result).__name__
                    ),
                },
            )

    def _resolve_handler(
        self,
        command: Command,
    ) -> CommandHandler:
        """
        Resolve the handler registered for a command type.
        """

        handler = self._handlers.get(
            command.command_type
        )

        if handler is None:
            raise ExecutionError(
                code="COMMAND_HANDLER_NOT_FOUND",
                message=(
                    "No handler registered for "
                    f"command type: "
                    f"{command.command_type}"
                ),
                details={
                    "command_type": (
                        command.command_type
                    ),
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

        If rollback itself fails, the original command exception
        is intentionally preserved by this orchestration layer.
        """

        if not transaction.active:
            return

        try:
            transaction.rollback()
        except Exception:
            pass


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "CommandManager",
    "CommandHandler",
]
