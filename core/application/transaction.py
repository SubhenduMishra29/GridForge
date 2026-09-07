# ============================================================
# File: core/application/transaction.py
# GridForge V2 — Application Transaction
# Author: Subhendu Mishra
# ============================================================

"""Atomic Application transaction boundary."""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Tuple


UndoOperation = Callable[[], None]
UndoJournal = Tuple[UndoOperation, ...]


class TransactionState(Enum):
    """Lifecycle state of an Application transaction."""

    OPEN = auto()
    COMMITTING = auto()
    COMMITTED = auto()
    ROLLING_BACK = auto()
    ROLLED_BACK = auto()
    ROLLBACK_FAILED = auto()


class Transaction:
    """Atomic Application execution scope.

    Transaction owns lifecycle, inverse-operation registration, rollback,
    commit, and committed undo-journal handoff. It has no knowledge of Core,
    Network, commands, history, UI, or Qt.
    """

    def __init__(self) -> None:
        self._state = TransactionState.OPEN
        self._undo_operations: list[UndoOperation] = []

    @property
    def state(self) -> TransactionState:
        return self._state

    @property
    def active(self) -> bool:
        return self._state is TransactionState.OPEN

    @property
    def committed(self) -> bool:
        return self._state is TransactionState.COMMITTED

    @property
    def rolled_back(self) -> bool:
        return self._state is TransactionState.ROLLED_BACK

    @property
    def rollback_failed(self) -> bool:
        return self._state is TransactionState.ROLLBACK_FAILED

    @property
    def undo_count(self) -> int:
        return len(self._undo_operations)

    def record_undo(self, operation: UndoOperation) -> None:
        """Register an inverse operation while the transaction is OPEN."""
        self._require_open("record_undo")
        if not callable(operation):
            raise TypeError("Undo operation must be callable.")
        self._undo_operations.append(operation)

    def undo_journal(self) -> UndoJournal:
        """Return an immutable snapshot of registered inverse operations."""
        return tuple(self._undo_operations)

    def commit(self) -> UndoJournal:
        """Commit and return the immutable committed undo journal."""
        self._require_open("commit")
        self._state = TransactionState.COMMITTING
        journal = tuple(self._undo_operations)
        self._undo_operations.clear()
        self._state = TransactionState.COMMITTED
        return journal

    def rollback(self) -> None:
        """Execute inverse operations and record rollback success/failure.

        Rollback enters ROLLING_BACK before inverse operations are attempted.
        All registered operations are attempted in reverse order. A failure
        leaves the transaction in ROLLBACK_FAILED and the first failure is
        re-raised after all rollback operations have been attempted.
        """
        self._require_open("rollback")
        self._state = TransactionState.ROLLING_BACK
        operations = tuple(reversed(self._undo_operations))
        self._undo_operations.clear()

        first_error: BaseException | None = None
        for operation in operations:
            try:
                operation()
            except BaseException as exc:
                if first_error is None:
                    first_error = exc

        if first_error is None:
            self._state = TransactionState.ROLLED_BACK
            return

        self._state = TransactionState.ROLLBACK_FAILED
        raise first_error

    def _require_open(self, operation: str) -> None:
        if self._state is not TransactionState.OPEN:
            raise RuntimeError(
                f"Cannot {operation}: transaction is {self._state.name.lower()}."
            )

    def __repr__(self) -> str:
        return (
            "Transaction("
            f"state={self._state.name}, "
            f"undo_count={len(self._undo_operations)}"
            ")"
        )


__all__ = [
    "UndoOperation",
    "UndoJournal",
    "TransactionState",
    "Transaction",
]
