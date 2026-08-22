# ============================================================
# File: core/application/errors.py
# GridForge V2 — Headless Application Errors
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

The Application layer must distinguish between:

    1. expected operational failures; and
    2. unexpected programming/infrastructure failures.

Expected failures are represented by ``ApplicationError`` or one
of its semantic subclasses.

Unexpected exceptions must NOT be silently swallowed and converted
into generic errors.

Architectural Role
------------------
This module belongs entirely to the headless Application layer.

It has no dependency on:

    * Qt;
    * PySide6;
    * PyQt;
    * UI;
    * SLD;
    * canvas;
    * rendering;
    * plugins;
    * Core controllers.

The error object is an outcome/contract object. It does not perform
application recovery and does not display anything to the user.

Error Structure
---------------
An ApplicationError contains:

    code
        Stable machine-readable identifier.

    message
        Human-readable diagnostic message.

    category
        Semantic class of the failure.

    severity
        Diagnostic severity.

    details
        Optional structured contextual information.

    cause
        Optional underlying exception for diagnostic purposes.

The ``code`` is the programmatic contract.

Consumers MUST NOT depend on parsing ``message``.

Example
-------
A command attempting to operate on a nonexistent element may
produce:

    ApplicationError(
        code="ELEMENT_NOT_FOUND",
        message="The requested element does not exist.",
        category="resource",
    )

The UI may translate that error into a dialog, status message,
SLD highlighting, or another presentation mechanism.

The Application layer itself must not perform that translation.

Error Categories
----------------
The initial semantic categories are:

    validation
        Invalid command/input supplied by the caller.

    domain
        A Core/domain rule prevents the operation.

    resource
        Required object/resource is unavailable.

    execution
        A known failure occurred while executing an operation.

These categories are intentionally small. More specialized
categories should only be introduced when the repository and
Application use cases demonstrate a real need.

Immutability
------------
Application errors are immutable after construction.

This prevents a caller from modifying an error after it has crossed
the Application boundary.

Exception Compatibility
-----------------------
``ApplicationError`` derives from ``Exception`` so it can also be
used when an Application operation needs exception semantics.

The structured fields remain the authoritative diagnostic data.

Important
---------
This module does NOT define a global registry of error codes.

Concrete error codes should be introduced together with the
Application operations that actually require them. This prevents
premature creation of arbitrary error vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ApplicationError(Exception):
    """
    Base structured error crossing the Application boundary.

    Parameters
    ----------
    code:
        Stable machine-readable error identifier.

    message:
        Human-readable description of the failure.

    category:
        Semantic category of the failure.

    severity:
        Diagnostic severity.

    details:
        Optional structured contextual information.

    cause:
        Optional underlying exception retained for diagnostics.

    Notes
    -----
    ``message`` is deliberately not used as a machine-readable
    identifier. Consumers must use ``code`` instead.
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
        Validate the structural integrity of the error.

        The Application boundary must never expose malformed error
        objects such as errors without a code or message.
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

        if self.details is not None and not isinstance(
            self.details,
            Mapping,
        ):
            raise ValueError(
                "ApplicationError details must be a mapping or None."
            )

        Exception.__init__(self, self.message)


class ValidationError(ApplicationError):
    """
    Expected failure caused by invalid Application input.

    This represents failures such as:

        * invalid command arguments;
        * invalid operation parameters;
        * malformed Application requests.

    Domain invariants remain owned by the Core domain objects.
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


class DomainError(ApplicationError):
    """
    Expected failure caused by a Core/domain rule.

    This allows the Application boundary to expose a structured
    domain failure without exposing Core implementation details
    directly to UI or plugin consumers.
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


class ResourceError(ApplicationError):
    """
    Expected failure caused by an unavailable resource.

    Typical examples include:

        * requested element does not exist;
        * requested study does not exist;
        * required Application resource is unavailable.
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
