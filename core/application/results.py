# ============================================================

# File: core/application/results.py

# GridForge V2 — Application Result Contract

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Application Result Contract.

ApplicationResult is the successful-result value object exchanged
between Application Services, Command Handlers, CommandManager,
and the public Application façade.

The failure contract is exception-based.

## Successful operation

```
Application Service
      |
      v
ApplicationResult[T]
      |
      +-- success
      +-- value
      +-- message
      +-- metadata
      |
      v
Command Handler
      |
      v
Transaction / History
```

## Expected Application failure

```
Application Service
      |
      v
ApplicationError
      |
      +-- ValidationError
      +-- ResourceError
      +-- DomainError
      +-- ExecutionError
```

ApplicationResult therefore does not need to represent ordinary
Application failures.

## Headless boundary

This module must not depend on:

```
* Qt;
* PySide6;
* PyQt;
* UI;
* SLD;
* canvas;
* renderers;
* Core implementation details.
```

## Generic contract

ApplicationResult[T] carries the canonical object returned by an
Application Service.

Examples:

```
ApplicationResult[Bus]
ApplicationResult[Line]
ApplicationResult[Transformer]
```

The result value is intentionally not copied or transformed.
The Application Service remains responsible for returning the
canonical Core object.

## Metadata

Service metadata is exposed as an immutable mapping.

Typical metadata includes:

```
operation
element_id
element_type
```

ApplicationResult does not interpret these values.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Generic, Mapping, TypeVar

T = TypeVar("T")

# ============================================================

# APPLICATION RESULT

# ============================================================

@dataclass(frozen=True, slots=True)
class ApplicationResult(Generic[T]):
"""
Immutable successful Application operation result.

```
Parameters
----------
success:
    Indicates whether the Application operation succeeded.

    Application services currently construct successful results
    only, while expected failures are represented by
    ApplicationError subclasses.

value:
    Canonical Core object returned by the service.

message:
    Human-readable description of the successful operation.

metadata:
    Immutable auxiliary operation information.
"""

success: bool
value: T | None
message: str
metadata: Mapping[str, Any]

def __post_init__(self) -> None:
    """
    Normalize and defensively freeze result metadata.
    """

    if not isinstance(
        self.success,
        bool,
    ):
        raise TypeError(
            "ApplicationResult.success must be bool."
        )

    if not isinstance(
        self.message,
        str,
    ):
        raise TypeError(
            "ApplicationResult.message must be str."
        )

    metadata = self.metadata

    if metadata is None:
        metadata = {}

    if not isinstance(
        metadata,
        Mapping,
    ):
        raise TypeError(
            "ApplicationResult.metadata must be a mapping."
        )

    object.__setattr__(
        self,
        "metadata",
        MappingProxyType(
            dict(metadata)
        ),
    )

# ========================================================
# SUCCESS FACTORY
# ========================================================

@classmethod
def success_result(
    cls,
    *,
    value: T | None = None,
    message: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> ApplicationResult[T]:
    """
    Construct a successful ApplicationResult.

    This is the canonical constructor used by Application
    Services.

    Parameters
    ----------
    value:
        Canonical Core object produced by the operation.

    message:
        Human-readable operation description.

    metadata:
        Optional operation metadata.
    """

    if metadata is None:
        metadata = {}

    return cls(
        success=True,
        value=value,
        message=message,
        metadata=metadata,
    )

# ========================================================
# SERVICE-COMPATIBLE FACTORY
# ========================================================

@classmethod
def success(
    cls,
    *,
    value: T | None = None,
    message: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> ApplicationResult[T]:
    """
    Canonical Application Service success factory.

    ModelService uses this API when returning successful
    operations.
    """

    return cls.success_result(
        value=value,
        message=message,
        metadata=metadata,
    )

# ========================================================
# CONVENIENCE ACCESS
# ========================================================

def has_value(self) -> bool:
    """
    Return True when the result contains a value.
    """

    return self.value is not None

def get_metadata(
    self,
    key: str,
    default: Any = None,
) -> Any:
    """
    Read one metadata value without exposing a mutable mapping.
    """

    return self.metadata.get(
        key,
        default,
    )
```

# ============================================================

# PUBLIC API

# ============================================================

__all__ = [
"ApplicationResult",
]
