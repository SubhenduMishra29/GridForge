# ============================================================

# File: core/application/results.py

# GridForge V2 — Application Result Contract

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Application Result Contract.

ApplicationResult is the immutable value returned by the
headless Application layer.

## Execution path

```
Command
   |
   v
Handler
   |
   v
Application Service
   |
   v
ApplicationResult
   |
   v
Application Consumer
```

The result is an Application contract.

It must not contain:

```
* Qt objects;
* widgets;
* graphics items;
* renderers;
* canvas state;
* UI controllers.
```

A canonical Core object may be returned as `value` when that
object is the direct result of an Application operation.

## Result categories

Success:

```
category = "success"
```

Failure categories may include:

```
validation
domain
resource
execution
```

The Application layer may add further stable categories when
required, but category names must remain machine-readable.

## Immutability

ApplicationResult is frozen.

Metadata is recursively converted into immutable forms.

## Python compatibility

GridForge V2 targets Python 3.10 and Python 3.11.
"""

from **future** import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Generic, Mapping, TypeVar

# ============================================================

# TYPE VARIABLE

# ============================================================

T = TypeVar("T")

# ============================================================

# IMMUTABILITY

# ============================================================

def _freeze_value(
value: Any,
) -> Any:
"""
Recursively convert common mutable containers to immutable
Application values.
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
Return an immutable metadata mapping.
"""

```
if value is None:
    return None

frozen = _freeze_value(value)

if not isinstance(
    frozen,
    Mapping,
):
    raise TypeError(
        "ApplicationResult metadata must be a mapping."
    )

return frozen
```

# ============================================================

# APPLICATION RESULT

# ============================================================

@dataclass(frozen=True)
class ApplicationResult(Generic[T]):
"""
Immutable Application operation result.

```
Parameters
----------
success:
    True when the operation completed successfully.

value:
    Optional value produced by the operation.

message:
    Human-readable result description.

code:
    Stable machine-readable result code.

category:
    Stable result classification.

metadata:
    Optional immutable structured metadata.
"""

success: bool

value: T | None = None

message: str = ""

code: str = ""

category: str = "success"

metadata: Mapping[str, Any] | None = None

# ========================================================
# VALIDATION
# ========================================================

def __post_init__(self) -> None:
    """
    Validate the result structure and freeze metadata.
    """

    if not isinstance(
        self.success,
        bool,
    ):
        raise TypeError(
            "ApplicationResult success must be bool."
        )

    if not isinstance(
        self.message,
        str,
    ):
        raise TypeError(
            "ApplicationResult message must be str."
        )

    if not isinstance(
        self.code,
        str,
    ):
        raise TypeError(
            "ApplicationResult code must be str."
        )

    if not isinstance(
        self.category,
        str,
    ):
        raise TypeError(
            "ApplicationResult category must be str."
        )

    normalized_category = (
        self.category.strip()
    )

    if not normalized_category:
        raise ValueError(
            "ApplicationResult category "
            "must not be empty."
        )

    object.__setattr__(
        self,
        "category",
        normalized_category,
    )

    if self.success:

        if (
            self.code
            and not self.code.strip()
        ):
            raise ValueError(
                "Successful ApplicationResult code "
                "must not contain only whitespace."
            )

    else:

        if not self.message.strip():
            raise ValueError(
                "Failed ApplicationResult message "
                "must not be empty."
            )

        if not self.code.strip():
            raise ValueError(
                "Failed ApplicationResult code "
                "must not be empty."
            )

    object.__setattr__(
        self,
        "metadata",
        _freeze_mapping(
            self.metadata
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
    code: str = "OK",
    metadata: Mapping[str, Any] | None = None,
) -> "ApplicationResult[T]":
    """
    Construct a successful ApplicationResult.
    """

    return cls(
        success=True,
        value=value,
        message=message,
        code=code,
        category="success",
        metadata=metadata,
    )

# ========================================================
# FAILURE FACTORY
# ========================================================

@classmethod
def failure(
    cls,
    *,
    message: str,
    code: str,
    category: str,
    value: T | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> "ApplicationResult[T]":
    """
    Construct a failed ApplicationResult.
    """

    if not isinstance(
        message,
        str,
    ):
        raise TypeError(
            "ApplicationResult failure message "
            "must be str."
        )

    if not isinstance(
        code,
        str,
    ):
        raise TypeError(
            "ApplicationResult failure code "
            "must be str."
        )

    if not isinstance(
        category,
        str,
    ):
        raise TypeError(
            "ApplicationResult failure category "
            "must be str."
        )

    if not message.strip():
        raise ValueError(
            "ApplicationResult failure message "
            "must not be empty."
        )

    if not code.strip():
        raise ValueError(
            "ApplicationResult failure code "
            "must not be empty."
        )

    if not category.strip():
        raise ValueError(
            "ApplicationResult failure category "
            "must not be empty."
        )

    return cls(
        success=False,
        value=value,
        message=message,
        code=code,
        category=category,
        metadata=metadata,
    )

# ========================================================
# STATUS
# ========================================================

@property
def failed(self) -> bool:
    """
    True when the operation failed.
    """

    return not self.success

@property
def is_success(self) -> bool:
    """
    True when the operation succeeded.
    """

    return self.success

@property
def is_failure(self) -> bool:
    """
    True when the operation failed.
    """

    return not self.success

# ========================================================
# BOOLEAN
# ========================================================

def __bool__(self) -> bool:
    """
    Successful results evaluate to True.
    Failed results evaluate to False.
    """

    return self.success
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"ApplicationResult",
]
