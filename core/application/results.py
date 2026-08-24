# ============================================================
# File: core/application/results.py
# GridForge V2 — Application Result Contract
# Author: Subhendu Mishra
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

Therefore this module intentionally uses TypeVar and Generic
rather than Python 3.12 PEP 695 generic class syntax.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Generic, Mapping, TypeVar


# =====================================================================
# TYPE VARIABLE
# =====================================================================

T = TypeVar("T")


# =====================================================================
# IMMUTABILITY HELPERS
# =====================================================================

def _freeze_value(value: Any) -> Any:
    """
    Recursively convert common mutable containers into immutable forms.

    Mapping
        -> MappingProxyType

    list / tuple
        -> tuple

    set / frozenset
        -> frozenset

    Other values
        -> returned unchanged

    Notes
    -----
    This provides defensive immutability for Application metadata.

    It does not attempt to clone arbitrary user-defined objects.
    Such objects should not be placed in metadata unless their own
    immutability is guaranteed.
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
    Return an immutable representation of a metadata mapping.
    """

    if value is None:
        return None

    frozen = _freeze_value(value)

    if not isinstance(frozen, Mapping):
        raise TypeError(
            "ApplicationResult metadata must be a mapping."
        )

    return frozen


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

    A canonical Core model object may be returned as ``value`` when
    that object is the result of the requested Application operation.
    """

    success: bool
    value: T | None = None
    message: str = ""
    code: str = ""
    category: str = "success"
    metadata: Mapping[str, Any] | None = None

    # =================================================================
    # POST-INITIALIZATION
    # =================================================================

    def __post_init__(self) -> None:
        """
        Normalize metadata into an immutable representation.
        """

        frozen_metadata = _freeze_mapping(self.metadata)

        object.__setattr__(
            self,
            "metadata",
            frozen_metadata,
        )

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
            Stable machine-readable success code.

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

        True
            Successful result.

        False
            Failed result.
        """

        return self.success


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ApplicationResult",
]
