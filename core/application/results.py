# ============================================================

# File: core/application/errors.py

# GridForge V2 — Headless Application Errors

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Headless Application Error Contract.

Application errors are structured exceptions crossing the
headless Application boundary.

## Hierarchy

```
ApplicationError
    |
    +-- ValidationError
    +-- DomainError
    +-- ResourceError
    +-- ExecutionError
```

Application errors provide:

```
* stable machine-readable error codes;
* human-readable diagnostics;
* semantic categories;
* immutable diagnostic details;
* optional underlying causes.
```

Consumers must use `code` and `category` rather than parsing
`message`.

## Expected failures

Expected validation, domain, resource, and execution failures may
cross the Application boundary as ApplicationError subclasses.

Unexpected programming errors must not be silently converted into
ApplicationError.

## Headless boundary

This module must never depend on:

```
* Qt;
* PySide6;
* PyQt5;
* PyQt6;
* UI;
* SLD;
* canvas;
* rendering;
* plugins.
```

## Immutability

Error instances are immutable after construction.

`details` is recursively converted to immutable Application
values.

`cause` is retained only for diagnostic exception chaining.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

# ============================================================

# IMMUTABILITY HELPERS

# ============================================================

def _freeze_value(
value: Any,
) -> Any:
"""
Recursively freeze common mutable containers.
"""

```
if isinstance(
    value,
    Mapping,
):
    return MappingProxyType(
        {
            key: _freeze_value(item)
            for key, item in value.items()
        }
    )

if isinstance(
    value,
    (list, tuple),
):
    return tuple(
        _freeze_value(item)
        for item in value
    )

if isinstance(
    value,
    (set, frozenset),
):
    return frozenset(
        _freeze_value(item)
        for item in value
    )

return value
```

def _freeze_mapping(
value: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
"""
Freeze an optional diagnostic mapping.
"""

```
if value is None:
    return None

if not isinstance(
    value,
    Mapping,
):
    raise TypeError(
        "ApplicationError details must be a mapping."
    )

return _freeze_value(value)
```

# ============================================================

# BASE APPLICATION ERROR

# ============================================================

@dataclass(frozen=True)
class ApplicationError(Exception):
"""
Base immutable Application-layer exception.
"""

```
code: str

message: str

category: str = "application"

severity: str = "error"

details: Mapping[str, Any] | None = None

cause: BaseException | None = field(
    default=None,
    repr=False,
    compare=False,
)

def __post_init__(self) -> None:
    """
    Validate and freeze the error contract.
    """

    if not isinstance(
        self.code,
        str,
    ):
        raise TypeError(
            "ApplicationError code must be a string."
        )

    if not self.code.strip():
        raise ValueError(
            "ApplicationError code must not be empty."
        )

    if not isinstance(
        self.message,
        str,
    ):
        raise TypeError(
            "ApplicationError message must be a string."
        )

    if not self.message.strip():
        raise ValueError(
            "ApplicationError message must not be empty."
        )

    if not isinstance(
        self.category,
        str,
    ):
        raise TypeError(
            "ApplicationError category must be a string."
        )

    if not self.category.strip():
        raise ValueError(
            "ApplicationError category must not be empty."
        )

    if not isinstance(
        self.severity,
        str,
    ):
        raise TypeError(
            "ApplicationError severity must be a string."
        )

    if not self.severity.strip():
        raise ValueError(
            "ApplicationError severity must not be empty."
        )

    object.__setattr__(
        self,
        "code",
        self.code.strip(),
    )

    object.__setattr__(
        self,
        "category",
        self.category.strip(),
    )

    object.__setattr__(
        self,
        "severity",
        self.severity.strip(),
    )

    object.__setattr__(
        self,
        "details",
        _freeze_mapping(
            self.details
        ),
    )

    # Exception.args is required for normal Python exception
    # behaviour and traceback rendering.
    Exception.__init__(
        self,
        self.message,
    )
```

# ============================================================

# VALIDATION ERROR

# ============================================================

class ValidationError(
ApplicationError,
):
"""
Invalid Application-level input.
"""

```
def __init__(
    self,
    code: str,
    message: str,
    *,
    details: Mapping[str, Any] | None = None,
) -> None:

    super().__init__(
        code=code,
        message=message,
        category="validation",
        details=details,
    )
```

# ============================================================

# DOMAIN ERROR

# ============================================================

class DomainError(
ApplicationError,
):
"""
Failure caused by a Core/domain engineering rule.
"""

```
def __init__(
    self,
    code: str,
    message: str,
    *,
    details: Mapping[str, Any] | None = None,
) -> None:

    super().__init__(
        code=code,
        message=message,
        category="domain",
        details=details,
    )
```

# ============================================================

# RESOURCE ERROR

# ============================================================

class ResourceError(
ApplicationError,
):
"""
Failure caused by an unavailable or missing resource.
"""

```
def __init__(
    self,
    code: str,
    message: str,
    *,
    details: Mapping[str, Any] | None = None,
) -> None:

    super().__init__(
        code=code,
        message=message,
        category="resource",
        details=details,
    )
```

# ============================================================

# EXECUTION ERROR

# ============================================================

class ExecutionError(
ApplicationError,
):
"""
Failure occurring while executing an Application operation.

```
``cause`` preserves the underlying exception for diagnostics.
"""

def __init__(
    self,
    code: str,
    message: str,
    *,
    details: Mapping[str, Any] | None = None,
    cause: BaseException | None = None,
) -> None:

    super().__init__(
        code=code,
        message=message,
        category="execution",
        details=details,
        cause=cause,
    )
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"ApplicationError",
"ValidationError",
"DomainError",
"ResourceError",
"ExecutionError",
]
