# ============================================================
# File: core/application/errors.py
# GridForge V2 — Headless Application Errors
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2
============

Module:
    core.application.errors

Purpose
-------
Defines the structured error contract used at the GridForge V2
Headless Application boundary.

Application errors provide stable machine-readable diagnostics
without exposing UI or presentation concerns.

Error hierarchy
---------------

    ApplicationError
        |
        +-- ValidationError
        +-- DomainError
        +-- ResourceError
        +-- ExecutionError

The Application layer translates expected Core/domain failures
into this structured boundary where appropriate.

Unexpected programming errors must not be silently swallowed.

Headless Requirement
--------------------
This module must remain completely independent of:

    * Qt;
    * PySide6;
    * PyQt5;
    * PyQt6;
    * UI;
    * SLD;
    * canvas;
    * rendering;
    * plugins;
    * Core controllers.

Immutability
------------
Application errors are immutable after construction.

Structured ``details`` are defensively frozen so that callers
cannot mutate diagnostic information after the error crosses
the Application boundary.

Error Contract
--------------
``code``
    Stable machine-readable identifier.

``message``
    Human-readable diagnostic message.

``category``
    Semantic error category.

``severity``
    Diagnostic severity.

``details``
    Optional immutable structured diagnostic information.

``cause``
    Optional underlying exception retained for diagnostics.

Consumers must use ``code`` rather than parsing ``message``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


# =====================================================================
# IMMUTABILITY HELPERS
# =====================================================================

def _freeze_value(value: Any) -> Any:
    """
    Recursively convert common mutable containers into immutable forms.
    """

    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _freeze_value(item)
                for key, item in value.items()
            }
        )

    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, (set, frozenset)):
        return frozenset(
            _freeze_value(item)
            for item in value
        )

    return value


def _freeze_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """
    Return an immutable representation of a mapping.
    """

    if value is None:
        return None

    frozen = _freeze_value(value)

    if not isinstance(frozen, Mapping):
        raise TypeError(
            "ApplicationError details must be a mapping."
        )

    return frozen


# =====================================================================
# BASE APPLICATION ERROR
# =====================================================================

@dataclass(frozen=True)
class ApplicationError(Exception):
    """
    Base structured error crossing the Application boundary.

    Parameters
    ----------
    code:
        Stable machine-readable error identifier.

    message:
        Human-readable description.

    category:
        Semantic error category.

    severity:
        Diagnostic severity.

    details:
        Optional immutable structured diagnostic information.

    cause:
        Optional underlying exception retained for diagnostics.
    """

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
        Validate and freeze the Application error contract.
        """

        if not isinstance(self.code, str) or not self.code.strip():
            raise ValueError(
                "ApplicationError code must be a non-empty string."
            )

        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError(
                "ApplicationError message must be a non-empty string."
            )

        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError(
                "ApplicationError category must be a non-empty string."
            )

        if not isinstance(self.severity, str) or not self.severity.strip():
            raise ValueError(
                "ApplicationError severity must be a non-empty string."
            )

        frozen_details = _freeze_mapping(self.details)

        object.__setattr__(
            self,
            "details",
            frozen_details,
        )

        Exception.__init__(self, self.message)


# =====================================================================
# VALIDATION ERROR
# =====================================================================

class ValidationError(ApplicationError):
    """
    Expected failure caused by invalid Application input.
    """

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


# =====================================================================
# DOMAIN ERROR
# =====================================================================

class DomainError(ApplicationError):
    """
    Expected failure caused by a Core/domain rule.
    """

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


# =====================================================================
# RESOURCE ERROR
# =====================================================================

class ResourceError(ApplicationError):
    """
    Expected failure caused by an unavailable resource.
    """

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


# =====================================================================
# EXECUTION ERROR
# =====================================================================

class ExecutionError(ApplicationError):
    """
    Expected failure during Application/Core execution.

    ``cause`` may preserve the underlying exception for diagnostics
    while exposing a stable Application-level error contract.
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


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ApplicationError",
    "ValidationError",
    "DomainError",
    "ResourceError",
    "ExecutionError",
]
