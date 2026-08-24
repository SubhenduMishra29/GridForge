# ============================================================

# File: core/application/transaction.py

# GridForge V2 — Application Transaction

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Application Transaction.

A Transaction provides atomic execution semantics for one
Application command.

## Architectural position

```
CommandManager
      |
      v
 Transaction
      |
      v
Command Handler
      |
      v
ModelService
      |
      v
Core / Network
```

The Transaction is deliberately unaware of:

```
* Core domain models
* Network internals
* topology
* Y-bus
* UI
* Qt
* plugins
* commands
* ApplicationContext
```

It owns only an ordered undo journal and its lifecycle.

## Design

A command may perform several mutations:

```
create model
register model
connect model
update state
...
```

Each successful mutation may register an inverse operation.

If execution succeeds:

```
transaction.commit()
```

The undo journal is then discarded.

If execution fails:

```
transaction.rollback()
```

Undo operations are executed in reverse order.

## Important

The Transaction does NOT provide database-style isolation.

It provides Application-level atomic rollback.

The caller remains responsible for registering correct inverse
operations for mutations.

## Lifecycle

```
NEW
  |
  v
ACTIVE
  |
  +----------> COMMITTED
  |
  +----------> ROLLED_BACK
```

Only an ACTIVE transaction may accept undo operations or be
committed/rolled back.

Rollback is best-effort across all registered undo operations:
every undo operation is attempted even if an earlier undo
operation fails.

If rollback itself encounters failures, TransactionError is
raised containing the rollback failures.

## Python compatibility

GridForge V2 targets Python 3.10/3.11.
"""

from **future** import annotations

from enum import Enum
from typing import Callable, Iterable

UndoOperation = Callable[[], None]

class TransactionError(RuntimeError):
"""
Base error for Application transaction failures.
"""

class TransactionState(str, Enum):
"""
Lifecycle state of an Application transaction.
"""

```
NEW = "new"
ACTIVE = "active"
COMMITTED = "committed"
ROLLED_BACK = "rolled_back"
```

class TransactionRollbackError(TransactionError):
"""
Raised when one or more undo operations fail during rollback.

```
The transaction is nevertheless transitioned to ROLLED_BACK
before this exception is raised so that rollback cannot be
accidentally attempted a second time.
"""

def __init__(
    self,
    failures: Iterable[BaseException],
) -> None:

    self.failures = tuple(failures)

    if not self.failures:
        raise ValueError(
            "TransactionRollbackError requires at least "
            "one rollback failure."
        )

    super().__init__(
        "Transaction rollback encountered "
        f"{len(self.failures)} failure(s)."
    )
```

class Transaction:
"""
Atomic Application execution scope.

```
Transaction stores inverse operations supplied by the
Application mutation layer.

It does not inspect or snapshot application/domain state.

Example
-------

    transaction = Transaction()

    transaction.begin()

    transaction.record_undo(
        lambda: network.remove_bus(bus)
    )

    transaction.commit()

Failure path
------------

    transaction.begin()

    transaction.record_undo(
        lambda: network.remove_bus(bus)
    )

    try:
        ...
    except Exception:
        transaction.rollback()
        raise
"""

def __init__(self) -> None:

    self._state = TransactionState.NEW

    self._undo_operations: list[UndoOperation] = []

# ============================================================
# STATE
# ============================================================

@property
def state(self) -> TransactionState:
    """
    Return the current transaction lifecycle state.
    """

    return self._state

# ------------------------------------------------------------

@property
def active(self) -> bool:
    """
    Return True when the transaction is ACTIVE.
    """

    return self._state is TransactionState.ACTIVE

# ------------------------------------------------------------

@property
def committed(self) -> bool:
    """
    Return True when the transaction has been committed.
    """

    return self._state is TransactionState.COMMITTED

# ------------------------------------------------------------

@property
def rolled_back(self) -> bool:
    """
    Return True when the transaction has been rolled back.
    """

    return self._state is TransactionState.ROLLED_BACK

# ============================================================
# JOURNAL
# ============================================================

@property
def undo_count(self) -> int:
    """
    Return the number of currently registered undo operations.
    """

    return len(self._undo_operations)

# ============================================================
# LIFECYCLE
# ============================================================

def begin(self) -> None:
    """
    Activate the transaction.

    A Transaction instance can be used only once.

    Raises
    ------

    TransactionError
        If the transaction has already been started,
        committed, or rolled back.
    """

    if self._state is not TransactionState.NEW:
        raise TransactionError(
            "Transaction can only be begun from the NEW state; "
            f"current state is '{self._state.value}'."
        )

    self._state = TransactionState.ACTIVE

# ------------------------------------------------------------

def commit(self) -> None:
    """
    Commit the transaction.

    Committing permanently accepts the mutations represented
    by this transaction and discards its rollback journal.

    Raises
    ------

    TransactionError
        If the transaction is not ACTIVE.
    """

    self._require_active(
        operation="commit",
    )

    self._undo_operations.clear()

    self._state = TransactionState.COMMITTED

# ------------------------------------------------------------

def rollback(self) -> None:
    """
    Roll back the transaction.

    Undo operations execute in strict reverse registration
    order.

    All undo operations are attempted even if one fails.

    The transaction transitions to ROLLED_BACK before a
    TransactionRollbackError is raised.

    Raises
    ------

    TransactionError
        If the transaction is not ACTIVE.

    TransactionRollbackError
        If one or more undo operations fail.
    """

    self._require_active(
        operation="rollback",
    )

    operations = tuple(
        reversed(self._undo_operations)
    )

    failures: list[BaseException] = []

    for undo in operations:

        try:
            undo()

        except BaseException as exc:
            failures.append(exc)

    self._undo_operations.clear()

    self._state = TransactionState.ROLLED_BACK

    if failures:
        raise TransactionRollbackError(
            failures,
        )

# ============================================================
# UNDO JOURNAL
# ============================================================

def record_undo(
    self,
    operation: UndoOperation,
) -> None:
    """
    Register an inverse operation.

    Undo operations are executed in reverse registration
    order during rollback.

    Parameters
    ----------

    operation:
        Zero-argument callable that reverses one successful
        mutation.

    Raises
    ------

    TypeError
        If operation is not callable.

    TransactionError
        If the transaction is not ACTIVE.
    """

    self._require_active(
        operation="record_undo",
    )

    if not callable(operation):
        raise TypeError(
            "Transaction undo operation must be callable."
        )

    self._undo_operations.append(
        operation,
    )

# ------------------------------------------------------------

def record_many(
    self,
    operations: Iterable[UndoOperation],
) -> None:
    """
    Register multiple undo operations.

    Operations are registered in iteration order and therefore
    execute in reverse iteration order during rollback.

    This method validates the iterable incrementally through
    record_undo().
    """

    self._require_active(
        operation="record_many",
    )

    for operation in operations:

        self.record_undo(
            operation,
        )

# ============================================================
# INTERNAL VALIDATION
# ============================================================

def _require_active(
    self,
    *,
    operation: str,
) -> None:
    """
    Require ACTIVE lifecycle state.
    """

    if self._state is not TransactionState.ACTIVE:
        raise TransactionError(
            f"Cannot {operation} transaction while it is "
            f"in '{self._state.value}' state."
        )

# ============================================================
# REPRESENTATION
# ============================================================

def __repr__(self) -> str:

    return (
        "Transaction("
        f"state='{self._state.value}', "
        f"undo_count={len(self._undo_operations)}"
        ")"
    )
```

**all** = [
"UndoOperation",
"TransactionError",
"TransactionRollbackError",
"TransactionState",
"Transaction",
]
