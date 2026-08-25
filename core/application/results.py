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

Expected Application failures are represented by ApplicationError
subclasses rather than by ApplicationResult.
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
    Immutable Application operation result.

    Parameters
    ----------
    success:
        Indicates whether the Application operation succeeded.

    value:
        Canonical Core object returned by the service.

    message:
        Human-readable description of the operation.

    metadata:
        Immutable auxiliary operation information.
    """

    success: bool
    value: T | None
    message: str
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError(
                "ApplicationResult.success must be bool."
            )

        if not isinstance(self.message, str):
            raise TypeError(
                "ApplicationResult.message must be str."
            )

        metadata = self.metadata

        if metadata is None:
            metadata = {}

        if not isinstance(metadata, Mapping):
            raise TypeError(
                "ApplicationResult.metadata must be a mapping."
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(metadata)),
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

        This is the ONLY success factory.

        The name deliberately avoids collision with the
        instance field ``success``.
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
        Read one metadata value.
        """

        return self.metadata.get(
            key,
            default,
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ApplicationResult",
]
