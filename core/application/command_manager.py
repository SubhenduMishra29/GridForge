# ============================================================
# File: core/application/command_manager.py
# GridForge V2 — Headless Application Command Manager
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Headless Application Command Manager.

CommandManager is the Application-layer orchestration boundary
for command execution, transactions, undo, and redo.

Responsibilities
----------------
CommandManager:

    * accepts Application Commands;
    * resolves command handlers;
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

Redo rule
---------

Redo re-executes the original immutable Command through the normal
handler/service/transaction path.

Redo never executes the old UndoJournal.
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
    """

    def __init__(
        self,
        context: Any,
        handlers: Mapping[str, CommandHandler] | None = None,
        history: CommandHistory | None = None,
    ) -> None:
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
        Return the CommandHistory owned by this manager.
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
        Register one handler for one command type.

        Duplicate registrations are rejected.
        """

        if not isinstance(
            command_type,
            str,
        ):
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
                "Handler already registered for "
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

    def is_registered(
        self,
        command_type: str,
    ) -> bool:
        """
        Return whether a command type is registered.

        Public Application-facing registration query.
        """

        return self.has_handler(
            command_type
        )

    def registered_commands(
        self,
    ) -> tuple[str, ...]:
        """
        Return all registered command types.
        """

        return tuple(
            self._handlers.keys()
        )

    # ========================================================
    # NORMAL EXECUTION
    # ========================================================

    def execute(
        self,
        command: Command,
    ) -> ApplicationResult[Any]:
        """
        Execute a new Application command.

        Successful execution:

            * commits the Transaction;
            * records its UndoJournal;
            * clears redo history.

        Failed execution:

            * rolls back the Transaction;
            * leaves history unchanged;
            * raises an ApplicationError.
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

        ``clear_redo=True`` is used for new commands.

        ``clear_redo=False`` is used for redo.
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

            # ------------------------------------------------
            # CRITICAL CONTRACT:
            #
            # Transaction.commit() returns the immutable
            # UndoJournal. Transaction does not retain it
            # after commit.
            # ------------------------------------------------

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
    ) -> None:
        """
        Record a successful committed command.

        ``clear_redo=True``:
            normal new command.

        ``clear_redo=False``:
            successful redo execution.

        The latter preserves the remaining redo stack.
        """

        description = (
            result.message
            if result.message
            else command.command_type
        )

        self._history.record(
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

        CommandHistory never executes the journal.
        CommandManager executes it here.
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

        popped_record = self._history.pop_undo()

        if popped_record is None:
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
                popped_record
            )

            self._history.push_redo(
                popped_record
            )

            return ApplicationResult.success_result(
                value=None,
                message=(
                    "Undid command: "
                    f"{popped_record.command_type}"
                ),
                metadata={
                    "operation": "undo",
                    "command_type": (
                        popped_record.command_type
                    ),
                    "command_id": str(
                        popped_record.command_id
                    ),
                },
            )

        except ApplicationError:
            self._history.push_undo(
                popped_record
            )
            raise

        except Exception as exc:
            self._history.push_undo(
                popped_record
            )

            raise ExecutionError(
                code="UNDO_FAILED",
                message=(
                    "Undo failed for command: "
                    f"{popped_record.command_type}"
                ),
                details={
                    "command_type": (
                        popped_record.command_type
                    ),
                    "command_id": str(
                        popped_record.command_id
                    ),
                },
                cause=exc,
            ) from exc

    def _execute_undo_journal(
        self,
        record: CommandRecord,
    ) -> None:
        """
        Execute the immutable inverse journal.

        Operations are executed in reverse order.

        CommandHistory itself never executes them.
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
        Re-execute the latest command from redo history.

        Redo executes the original Command through the normal
        command pipeline and creates a fresh UndoJournal.

        The remaining redo stack is preserved.
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
        Return whether a command is available for redo.
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
        Clear all command history.
        """

        self._history.clear()

    # ========================================================
    # VALIDATION
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
        Roll back an active transaction without masking the
        original Application exception.

        Transaction itself reports rollback failures.
        CommandManager deliberately preserves the original
        execution exception here.
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
