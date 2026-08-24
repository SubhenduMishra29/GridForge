# ============================================================
# File: core/application/transaction.py
# GridForge V2 — Application Transaction
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Application Transaction.

Transaction provides an atomic execution scope for an Application
command.

Responsibilities
----------------
Transaction owns:

    * transaction lifecycle
    * undo-operation registration
    * rollback
    * commit
    * committed undo-journal handoff

Transaction does NOT:

    * know about Core domain types
    * know about Network
    * execute commands
    * manage command history
    * implement redo
    * depend on UI

Lifecycle
---------

    ACTIVE
       │
       ├── record_undo(...)
       ├── rollback()
       │       ↓
       │   ROLLED_BACK
       │
       └── commit()
               ↓
           COMMITTED

A transaction can be committed or rolled back exactly once.

Committed Undo Journal
----------------------

``commit()`` returns an immutable tuple containing the registered
undo operations.

This is the explicit boundary between Transaction and History:

    Transaction
        ↓
    committed UndoJournal
        ↓
    CommandManager
        ↓
    CommandHistory

Transaction itself does not retain the committed journal after
commit.

Headless Requirement
--------------------

No dependency on:

    * Qt
    * PySide6
    * UI
    * SLD
    * Canvas
    * Network
    * Core model
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Tuple


# ============================================================
# TYPE DEFINITIONS
# ============================================================

UndoOperation = Callable[[], None]

UndoJournal = Tuple[UndoOperation, ...]


# ============================================================
# TRANSACTION STATE
# ============================================================

class TransactionState(Enum):
    """
    Lifecycle state of an Application transaction.
    """

    ACTIVE = auto()
    COMMITTED = auto()
    ROLLED_BACK = auto()


# ============================================================
# TRANSACTION
# ============================================================

class Transaction:
    """
    Atomic Application execution scope.

    A Transaction collects inverse operations while an Application
    command executes.

    The registered operations are executed in reverse registration
    order during rollback.

    On successful commit, the operations are returned as an immutable
    UndoJournal for CommandManager/CommandHistory.

    Transaction does not know what the operations do.
    """

    def __init__(self) -> None:

        self._state = TransactionState.ACTIVE

        self._undo_operations: list[UndoOperation] = []

    # ========================================================
    # STATE
    # ========================================================

    @property
    def state(self) -> TransactionState:
        """
        Return the current transaction lifecycle state.
        """

        return self._state

    @property
    def active(self) -> bool:
        """
        Return True when the transaction is active.
        """

        return self._state is TransactionState.ACTIVE

    @property
    def committed(self) -> bool:
        """
        Return True when the transaction has been committed.
        """

        return self._state is TransactionState.COMMITTED

    @property
    def rolled_back(self) -> bool:
        """
        Return True when the transaction has been rolled back.
        """

        return self._state is TransactionState.ROLLED_BACK

    # ========================================================
    # UNDO REGISTRATION
    # ========================================================

    def record_undo(
        self,
        operation: UndoOperation,
    ) -> None:
        """
        Register an inverse operation.

        Operations execute in reverse registration order during
        rollback.

        The transaction must still be ACTIVE.
        """

        self._require_active(
            operation="record_undo",
        )

        if not callable(operation):
            raise TypeError(
                "Undo operation must be callable."
            )

        self._undo_operations.append(operation)

    # ========================================================
    # INSPECTION
    # ========================================================

    @property
    def undo_count(self) -> int:
        """
        Return the number of currently registered undo operations.

        This is meaningful only while the transaction is ACTIVE.
        """

        return len(self._undo_operations)

    def undo_journal(self) -> UndoJournal:
        """
        Return an immutable snapshot of the currently registered
        undo operations.

        This method does not change transaction state.
        """

        return tuple(self._undo_operations)

    # ========================================================
    # COMMIT
    # ========================================================

    def commit(self) -> UndoJournal:
        """
        Commit the transaction.

        Returns
        -------
        UndoJournal
            Immutable tuple containing the registered inverse
            operations.

        The journal is captured before internal transaction state
        is cleared.

        After commit, the transaction cannot be modified.
        """

        self._require_active(
            operation="commit",
        )

        journal = tuple(
            self._undo_operations
        )

        self._undo_operations.clear()

        self._state = TransactionState.COMMITTED

        return journal

    # ========================================================
    # ROLLBACK
    # ========================================================

    def rollback(self) -> None:
        """
        Roll back the transaction.

        Undo operations execute in reverse registration order.

        If an undo operation fails, rollback continues attempting
        remaining operations. The first failure is re-raised after
        all rollback operations have been attempted.

        After rollback, the transaction is permanently closed.
        """

        self._require_active(
            operation="rollback",
        )

        operations = tuple(
            reversed(self._undo_operations)
        )

        self._undo_operations.clear()

        self._state = TransactionState.ROLLED_BACK

        first_error: BaseException | None = None

        for operation in operations:

            try:
                operation()

            except BaseException as exc:

                if first_error is None:
                    first_error = exc

        if first_error is not None:
            raise first_error

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    def _require_active(
        self,
        *,
        operation: str,
    ) -> None:
        """
        Ensure the transaction is still active.
        """

        if self._state is not TransactionState.ACTIVE:

            raise RuntimeError(
                f"Cannot {operation}: transaction is "
                f"{self._state.name.lower()}."
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:

        return (
            "Transaction("
            f"state={self._state.name}, "
            f"undo_count={len(self._undo_operations)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "UndoOperation",
    "UndoJournal",
    "TransactionState",
    "Transaction",
]
