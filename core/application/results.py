# ============================================================
# File: core/application/results.py
# GridForge V2 — Application Result Contract
# ============================================================
"""
GridForge V2
============

Module:
    core.application.results

Purpose
-------
Defines the immutable result contract returned by the headless
Application layer.

Application services and command handlers return ApplicationResult
objects instead of exposing UI-specific state or implementation
details.

Architecture
------------

    Application Command
            |
            v
       Command Handler
            |
            v
      Application Service
            |
            v
      ApplicationResult
            |
            v
      Application Consumer


Result Categories
-----------------
The result contract supports:

    * success
    * validation failure
    * domain failure
    * resource failure
    * execution failure

The result object is immutable.

Python Compatibility
--------------------
GridForge V2 supports Python 3.10 and Python 3.11.

Therefore this module intentionally does NOT use Python 3.12's
PEP 695 generic class syntax:

    class ApplicationResult[T]:

Instead it uses:

    TypeVar
    Generic

which is compatible with Python 3.10/3.11.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Mapping, TypeVar


# =====================================================================
# TYPE VARIABLE
# =====================================================================

T = TypeVar("T")


# =====================================================================
# APPLICATION RESULT
# =====================================================================

@dataclass(frozen=True)
class ApplicationResult(Generic[T]):
    """
    Immutable result returned by the Application layer.

    Parameters
    ----------
    success:
        True when the requested Application operation completed
        successfully.

    value:
        Optional result value produced by the operation.

    message:
        Human-readable description of the result.

    code:
        Stable machine-readable result code.

    category:
        Result classification.

    metadata:
        Optional immutable mapping containing structured result
        information.

    Notes
    -----
    The result object contains Application-level information only.

    It must not contain:

        * Qt objects;
        * UI objects;
        * QGraphicsItem instances;
        * widgets;
        * renderers;
        * canvas state.

    A Core model object may be returned as ``value`` when that object
    is the canonical result of the requested operation.
    """

    success: bool
    value: T | None = None
    message: str = ""
    code: str = ""
    category: str = "success"
    metadata: Mapping[str, Any] | None = None

    # =================================================================
    # SUCCESS FACTORY
    # =================================================================

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

        Parameters
        ----------
        value:
            Optional operation result.

        message:
            Human-readable success message.

        code:
            Stable success code.

        metadata:
            Optional structured result metadata.
        """

        return cls(
            success=True,
            value=value,
            message=message,
            code=code,
            category="success",
            metadata=metadata,
        )

    # =================================================================
    # COMPATIBILITY SUCCESS FACTORY
    # =================================================================

    @classmethod
    def success(
        cls,
        *,
        value: T | None = None,
        message: str = "",
        code: str = "OK",
        metadata: Mapping[str, Any] | None = None,
    ) -> "ApplicationResult[T]":
        """
        Construct a successful ApplicationResult.

        This is the canonical convenience API used by Application
        services.

        Example
        -------
        ::

            return ApplicationResult.success(
                value=bus,
                message="Bus created successfully.",
                metadata={
                    "operation": "create_bus",
                    "element_id": bus.id,
                },
            )
        """

        return cls.success_result(
            value=value,
            message=message,
            code=code,
            metadata=metadata,
        )

    # =================================================================
    # FAILURE FACTORY
    # =================================================================

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

        Parameters
        ----------
        message:
            Human-readable failure description.

        code:
            Stable machine-readable failure code.

        category:
            Failure category.

        value:
            Optional partial/result value.

        metadata:
            Optional structured failure metadata.
        """

        if not message:
            raise ValueError(
                "ApplicationResult failure message "
                "must not be empty."
            )

        if not code:
            raise ValueError(
                "ApplicationResult failure code "
                "must not be empty."
            )

        if not category:
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

    # =================================================================
    # STATUS HELPERS
    # =================================================================

    @property
    def failed(self) -> bool:
        """
        Return True when the operation failed.
        """

        return not self.success

    # -----------------------------------------------------------------

    @property
    def is_success(self) -> bool:
        """
        Return True when the operation succeeded.
        """

        return self.success

    # -----------------------------------------------------------------

    @property
    def is_failure(self) -> bool:
        """
        Return True when the operation failed.
        """

        return not self.success

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __bool__(self) -> bool:
        """
        Allow ApplicationResult to be evaluated as a boolean.

        True  -> successful result
        False -> failed result
        """

        return self.success


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ApplicationResult",
]
