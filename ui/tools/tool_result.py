# ============================================================
# File: ui/tools/tool_result.py
# GridForge V2 — Tool Result
# ============================================================
"""
Normalized result contract for GridForge V2 UI tools.

ToolResult communicates what a tool did with an interaction.
It is deliberately separate from Core/domain results.

Architecture
------------

    ToolEvent
        │
        ▼
    ToolManager
        │
        ▼
    ToolBase / Concrete Tool
        │
        ▼
    ToolResult
        │
        ├── handled
        ├── consumed
        ├── changed
        ├── command
        ├── preview
        └── metadata
             │
             ▼
    InteractionController / UI Composition

Responsibilities
----------------
ToolResult:

    - describe interaction handling;
    - communicate event consumption;
    - describe transient UI changes;
    - optionally carry a command created by a tool;
    - carry preview information;
    - carry tool-specific metadata.

ToolResult does NOT:

    - execute commands;
    - mutate Core;
    - maintain command history;
    - perform electrical validation;
    - own Qt objects;
    - replace domain/application results.

Command execution remains the responsibility of the command
pipeline.

No Qt dependency is permitted in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


# ============================================================
# RESULT STATUS
# ============================================================


class ToolResultStatus(str, Enum):
    """
    High-level outcome of a tool interaction.
    """

    IGNORED = "ignored"
    HANDLED = "handled"
    CONSUMED = "consumed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================
# TOOL RESULT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolResult:
    """
    Immutable result returned from a tool interaction.

    Parameters
    ----------
    status:
        High-level interaction status.

    handled:
        Whether the active tool recognized the event.

    consumed:
        Whether downstream interaction processing should stop.

    changed:
        Whether transient UI/tool state changed.

    command:
        Optional command object created by the tool.

        The command is not executed by ToolResult.

    preview:
        Optional transient preview payload.

    message:
        Optional human-readable diagnostic/status message.

    data:
        Additional tool-specific metadata.

    error:
        Optional exception/error object for a failed interaction.

    """

    status: ToolResultStatus = ToolResultStatus.IGNORED

    handled: bool = False
    consumed: bool = False
    changed: bool = False

    command: Any = None
    preview: Any = None

    message: Optional[str] = None
    data: Mapping[str, Any] = field(
        default_factory=dict
    )

    error: Optional[BaseException] = None

    def __post_init__(
        self,
    ) -> None:
        """
        Validate the result.
        """

        if not isinstance(
            self.status,
            ToolResultStatus,
        ):
            raise TypeError(
                "status must be a ToolResultStatus."
            )

        if not isinstance(
            self.data,
            Mapping,
        ):
            raise TypeError(
                "data must implement Mapping."
            )

        if self.error is not None and not isinstance(
            self.error,
            BaseException,
        ):
            raise TypeError(
                "error must be a BaseException or None."
            )

        if (
            self.status == ToolResultStatus.FAILED
            and self.error is None
            and not self.message
        ):
            raise ValueError(
                "A failed ToolResult must provide an error "
                "or diagnostic message."
            )

    # ========================================================
    # STATE QUERIES
    # ========================================================

    @property
    def is_ignored(
        self,
    ) -> bool:
        """
        Return whether the event was ignored.
        """

        return (
            self.status
            == ToolResultStatus.IGNORED
        )

    # --------------------------------------------------------

    @property
    def is_handled(
        self,
    ) -> bool:
        """
        Return whether the event was handled.
        """

        return self.handled

    # --------------------------------------------------------

    @property
    def is_consumed(
        self,
    ) -> bool:
        """
        Return whether downstream handling should stop.
        """

        return self.consumed

    # --------------------------------------------------------

    @property
    def is_changed(
        self,
    ) -> bool:
        """
        Return whether transient tool/UI state changed.
        """

        return self.changed

    # --------------------------------------------------------

    @property
    def is_completed(
        self,
    ) -> bool:
        """
        Return whether an interaction completed successfully.
        """

        return (
            self.status
            == ToolResultStatus.COMPLETED
        )

    # --------------------------------------------------------

    @property
    def is_cancelled(
        self,
    ) -> bool:
        """
        Return whether the interaction was cancelled.
        """

        return (
            self.status
            == ToolResultStatus.CANCELLED
        )

    # --------------------------------------------------------

    @property
    def is_failed(
        self,
    ) -> bool:
        """
        Return whether the interaction failed.
        """

        return (
            self.status
            == ToolResultStatus.FAILED
        )

    # --------------------------------------------------------

    @property
    def has_command(
        self,
    ) -> bool:
        """
        Return whether the result carries a command.
        """

        return self.command is not None

    # --------------------------------------------------------

    @property
    def has_preview(
        self,
    ) -> bool:
        """
        Return whether the result carries preview information.
        """

        return self.preview is not None

    # ========================================================
    # DATA ACCESS
    # ========================================================

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Return a metadata value.
        """

        return self.data.get(
            key,
            default,
        )

    # --------------------------------------------------------

    def has(
        self,
        key: str,
    ) -> bool:
        """
        Return whether a metadata key exists.
        """

        return key in self.data

    # ========================================================
    # FACTORIES
    # ========================================================

    @classmethod
    def ignored(
        cls,
        *,
        message: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolResult":
        """
        Create an ignored result.
        """

        return cls(
            status=ToolResultStatus.IGNORED,
            handled=False,
            consumed=False,
            changed=False,
            message=message,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def handled(
        cls,
        *,
        consumed: bool = True,
        changed: bool = False,
        message: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolResult":
        """
        Create a handled result.
        """

        return cls(
            status=(
                ToolResultStatus.CONSUMED
                if consumed
                else ToolResultStatus.HANDLED
            ),
            handled=True,
            consumed=consumed,
            changed=changed,
            message=message,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def changed(
        cls,
        *,
        consumed: bool = True,
        message: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolResult":
        """
        Create a handled result representing transient state change.
        """

        return cls(
            status=(
                ToolResultStatus.CONSUMED
                if consumed
                else ToolResultStatus.HANDLED
            ),
            handled=True,
            consumed=consumed,
            changed=True,
            message=message,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def completed(
        cls,
        *,
        command: Any = None,
        changed: bool = True,
        message: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolResult":
        """
        Create a successfully completed result.

        ``command`` is descriptive only; execution remains outside
        this object.
        """

        return cls(
            status=ToolResultStatus.COMPLETED,
            handled=True,
            consumed=True,
            changed=changed,
            command=command,
            message=message,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def cancelled(
        cls,
        *,
        changed: bool = True,
        message: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolResult":
        """
        Create a cancellation result.
        """

        return cls(
            status=ToolResultStatus.CANCELLED,
            handled=True,
            consumed=True,
            changed=changed,
            message=message,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def failed(
        cls,
        error: Optional[BaseException] = None,
        *,
        message: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
        consumed: bool = True,
    ) -> "ToolResult":
        """
        Create a failed interaction result.
        """

        if (
            error is None
            and not message
        ):
            raise ValueError(
                "ToolResult.failed() requires an error "
                "or message."
            )

        return cls(
            status=ToolResultStatus.FAILED,
            handled=True,
            consumed=consumed,
            changed=False,
            message=message,
            data={} if data is None else dict(data),
            error=error,
        )

    # ========================================================
    # TRANSFORMATION
    # ========================================================

    def with_data(
        self,
        **values: Any,
    ) -> "ToolResult":
        """
        Return a copy with updated metadata.
        """

        data = dict(
            self.data
        )

        data.update(
            values
        )

        return ToolResult(
            status=self.status,
            handled=self.handled,
            consumed=self.consumed,
            changed=self.changed,
            command=self.command,
            preview=self.preview,
            message=self.message,
            data=data,
            error=self.error,
        )

    # --------------------------------------------------------

    def with_preview(
        self,
        preview: Any,
    ) -> "ToolResult":
        """
        Return a copy containing preview information.
        """

        return ToolResult(
            status=self.status,
            handled=self.handled,
            consumed=self.consumed,
            changed=True,
            command=self.command,
            preview=preview,
            message=self.message,
            data=dict(self.data),
            error=self.error,
        )

    # --------------------------------------------------------

    def with_command(
        self,
        command: Any,
    ) -> "ToolResult":
        """
        Return a copy containing a command.
        """

        return ToolResult(
            status=self.status,
            handled=self.handled,
            consumed=self.consumed,
            changed=self.changed,
            command=command,
            preview=self.preview,
            message=self.message,
            data=dict(self.data),
            error=self.error,
        )

    # --------------------------------------------------------

    def consume(
        self,
    ) -> "ToolResult":
        """
        Return a copy marked as consumed.
        """

        status = self.status

        if status == ToolResultStatus.HANDLED:
            status = ToolResultStatus.CONSUMED

        return ToolResult(
            status=status,
            handled=True,
            consumed=True,
            changed=self.changed,
            command=self.command,
            preview=self.preview,
            message=self.message,
            data=dict(self.data),
            error=self.error,
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the result to a diagnostic dictionary.

        Exception objects are represented by their type and
        message rather than serialized directly.
        """

        error_data = None

        if self.error is not None:
            error_data = {
                "type": type(
                    self.error
                ).__name__,
                "message": str(
                    self.error
                ),
            }

        return {
            "status": self.status.value,
            "handled": self.handled,
            "consumed": self.consumed,
            "changed": self.changed,
            "has_command": self.has_command,
            "has_preview": self.has_preview,
            "message": self.message,
            "data": dict(self.data),
            "error": error_data,
        }


__all__ = [
    "ToolResultStatus",
    "ToolResult",
]
