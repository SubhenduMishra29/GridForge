# ============================================================
# File: ui/tools/tool_actions.py
# GridForge V2 — Tool Actions
# ============================================================
"""
Semantic actions for the GridForge V2 tool system.

This module defines intent-level actions that may be triggered by
tool interactions, shortcuts, or UI controls.

Actions are descriptors only.

They do NOT:
    - mutate Core;
    - execute commands;
    - modify project state;
    - perform electrical validation;
    - access Qt widgets;
    - directly activate tools.

The ToolController / CommandController / application controller
layers remain responsible for executing the appropriate action.

Frozen concrete tools
---------------------
    SelectTool
    BusTool
    LineTool

No Qt dependency is permitted in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


# ============================================================
# ACTION TYPES
# ============================================================


class ToolActionType(str, Enum):
    """
    Semantic actions exposed by the GridForge tool layer.
    """

    NONE = "none"

    SELECT = "select"
    SELECT_ADD = "select_add"
    SELECT_REMOVE = "select_remove"
    SELECT_CLEAR = "select_clear"

    CREATE_BUS = "create_bus"
    CREATE_LINE = "create_line"

    CANCEL = "cancel"
    RESET = "reset"

    DELETE_SELECTION = "delete_selection"
    DUPLICATE_SELECTION = "duplicate_selection"

    START_PREVIEW = "start_preview"
    UPDATE_PREVIEW = "update_preview"
    COMMIT_PREVIEW = "commit_preview"

    PAN = "pan"
    ZOOM = "zoom"


# ============================================================
# ACTION SOURCE
# ============================================================


class ToolActionSource(str, Enum):
    """
    Source of a semantic tool action.
    """

    POINTER = "pointer"
    KEYBOARD = "keyboard"
    TOOLBAR = "toolbar"
    CONTEXT_MENU = "context_menu"
    PROGRAMMATIC = "programmatic"


# ============================================================
# TOOL ACTION
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolAction:
    """
    Immutable semantic action produced by a UI tool.

    Parameters
    ----------
    action_type:
        Semantic operation requested by the tool.

    source:
        Origin of the action.

    tool_id:
        Tool that generated the action.

    target_id:
        Optional target object identifier.

    terminal_id:
        Optional target terminal identifier.

    position:
        Optional scene/canvas position.

    start_position:
        Optional first point of a two-point interaction.

    end_position:
        Optional second point of a two-point interaction.

    payload:
        Additional action-specific information.

    """

    action_type: ToolActionType

    source: ToolActionSource = ToolActionSource.PROGRAMMATIC

    tool_id: Optional[str] = None

    target_id: Optional[str] = None
    terminal_id: Optional[str] = None

    position: Any = None
    start_position: Any = None
    end_position: Any = None

    payload: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(
        self,
    ) -> None:
        """
        Validate the action.
        """

        if not isinstance(
            self.action_type,
            ToolActionType,
        ):
            raise TypeError(
                "action_type must be a ToolActionType."
            )

        if not isinstance(
            self.source,
            ToolActionSource,
        ):
            raise TypeError(
                "source must be a ToolActionSource."
            )

        if self.tool_id is not None:
            if not isinstance(
                self.tool_id,
                str,
            ) or not self.tool_id.strip():
                raise ValueError(
                    "tool_id must be None or a non-empty string."
                )

        if self.target_id is not None:
            if not isinstance(
                self.target_id,
                str,
            ) or not self.target_id.strip():
                raise ValueError(
                    "target_id must be None or a non-empty string."
                )

        if self.terminal_id is not None:
            if not isinstance(
                self.terminal_id,
                str,
            ) or not self.terminal_id.strip():
                raise ValueError(
                    "terminal_id must be None or a non-empty string."
                )

        if not isinstance(
            self.payload,
            Mapping,
        ):
            raise TypeError(
                "payload must implement Mapping."
            )

    # ========================================================
    # FACTORIES
    # ========================================================

    @classmethod
    def none(
        cls,
        *,
        tool_id: Optional[str] = None,
        source: ToolActionSource = (
            ToolActionSource.PROGRAMMATIC
        ),
    ) -> "ToolAction":
        """
        Create a no-op action.
        """

        return cls(
            action_type=ToolActionType.NONE,
            source=source,
            tool_id=tool_id,
        )

    # --------------------------------------------------------

    @classmethod
    def select(
        cls,
        target_id: str,
        *,
        tool_id: str = "select",
        source: ToolActionSource = (
            ToolActionSource.POINTER
        ),
        position: Any = None,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> "ToolAction":
        """
        Create a selection action.
        """

        return cls(
            action_type=ToolActionType.SELECT,
            source=source,
            tool_id=tool_id,
            target_id=target_id,
            position=position,
            payload={} if payload is None else dict(payload),
        )

    # --------------------------------------------------------

    @classmethod
    def select_add(
        cls,
        target_id: str,
        *,
        tool_id: str = "select",
        source: ToolActionSource = (
            ToolActionSource.POINTER
        ),
        position: Any = None,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> "ToolAction":
        """
        Create an additive selection action.
        """

        return cls(
            action_type=ToolActionType.SELECT_ADD,
            source=source,
            tool_id=tool_id,
            target_id=target_id,
            position=position,
            payload={} if payload is None else dict(payload),
        )

    # --------------------------------------------------------

    @classmethod
    def select_remove(
        cls,
        target_id: str,
        *,
        tool_id: str = "select",
        source: ToolActionSource = (
            ToolActionSource.POINTER
        ),
        position: Any = None,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> "ToolAction":
        """
        Create a subtractive selection action.
        """

        return cls(
            action_type=ToolActionType.SELECT_REMOVE,
            source=source,
            tool_id=tool_id,
            target_id=target_id,
            position=position,
            payload={} if payload is None else dict(payload),
        )

    # --------------------------------------------------------

    @classmethod
    def clear_selection(
        cls,
        *,
        tool_id: str = "select",
        source: ToolActionSource = (
            ToolActionSource.POINTER
        ),
        payload: Optional[Mapping[str, Any]] = None,
    ) -> "ToolAction":
        """
        Create a clear-selection action.
        """

        return cls(
            action_type=ToolActionType.SELECT_CLEAR,
            source=source,
            tool_id=tool_id,
            payload={} if payload is None else dict(payload),
        )

    # --------------------------------------------------------

    @classmethod
    def create_bus(
        cls,
        position: Any,
        *,
        tool_id: str = "bus",
        source: ToolActionSource = (
            ToolActionSource.POINTER
        ),
        payload: Optional[Mapping[str, Any]] = None,
    ) -> "ToolAction":
        """
        Create a bus-creation action.
        """

        return cls(
            action_type=ToolActionType.CREATE_BUS,
            source=source,
            tool_id=tool_id,
            position=position,
            payload={} if payload is None else dict(payload),
        )

    # --------------------------------------------------------

    @classmethod
    def create_line(
        cls,
        start_position: Any,
        end_position: Any,
        *,
        tool_id: str = "line",
        source: ToolActionSource = (
            ToolActionSource.POINTER
        ),
        payload: Optional[Mapping[str, Any]] = None,
    ) -> "ToolAction":
        """
        Create a line-creation action.
        """

        return cls(
            action_type=ToolActionType.CREATE_LINE,
            source=source,
            tool_id=tool_id,
            start_position=start_position,
            end_position=end_position,
            payload={} if payload is None else dict(payload),
        )

    # --------------------------------------------------------

    @classmethod
    def cancel(
        cls,
        *,
        tool_id: Optional[str] = None,
        source: ToolActionSource = (
            ToolActionSource.POINTER
        ),
        payload: Optional[Mapping[str, Any]] = None,
    ) -> "ToolAction":
        """
        Create a cancellation action.
        """

        return cls(
            action_type=ToolActionType.CANCEL,
            source=source,
            tool_id=tool_id,
            payload={} if payload is None else dict(payload),
        )

    # --------------------------------------------------------

    @classmethod
    def reset(
        cls,
        *,
        tool_id: Optional[str] = None,
        source: ToolActionSource = (
            ToolActionSource.PROGRAMMATIC
        ),
        payload: Optional[Mapping[str, Any]] = None,
    ) -> "ToolAction":
        """
        Create a reset action.
        """

        return cls(
            action_type=ToolActionType.RESET,
            source=source,
            tool_id=tool_id,
            payload={} if payload is None else dict(payload),
        )

    # ========================================================
    # QUERIES
    # ========================================================

    @property
    def is_noop(
        self,
    ) -> bool:
        """
        Return whether this action is a no-op.
        """

        return (
            self.action_type
            == ToolActionType.NONE
        )

    # --------------------------------------------------------

    @property
    def is_selection_action(
        self,
    ) -> bool:
        """
        Return whether this is a selection operation.
        """

        return self.action_type in {
            ToolActionType.SELECT,
            ToolActionType.SELECT_ADD,
            ToolActionType.SELECT_REMOVE,
            ToolActionType.SELECT_CLEAR,
        }

    # --------------------------------------------------------

    @property
    def is_creation_action(
        self,
    ) -> bool:
        """
        Return whether this action requests object creation.
        """

        return self.action_type in {
            ToolActionType.CREATE_BUS,
            ToolActionType.CREATE_LINE,
        }

    # --------------------------------------------------------

    @property
    def is_preview_action(
        self,
    ) -> bool:
        """
        Return whether this action concerns preview state.
        """

        return self.action_type in {
            ToolActionType.START_PREVIEW,
            ToolActionType.UPDATE_PREVIEW,
            ToolActionType.COMMIT_PREVIEW,
        }

    # --------------------------------------------------------

    @property
    def is_cancel(
        self,
    ) -> bool:
        """
        Return whether this action cancels an interaction.
        """

        return (
            self.action_type
            == ToolActionType.CANCEL
        )

    # --------------------------------------------------------

    @property
    def is_reset(
        self,
    ) -> bool:
        """
        Return whether this action resets tool state.
        """

        return (
            self.action_type
            == ToolActionType.RESET
        )

    # ========================================================
    # DATA ACCESS
    # ========================================================

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Return a payload value.
        """

        return self.payload.get(
            key,
            default,
        )

    # --------------------------------------------------------

    def has(
        self,
        key: str,
    ) -> bool:
        """
        Return whether a payload key exists.
        """

        return key in self.payload

    # ========================================================
    # TRANSFORMATION
    # ========================================================

    def with_payload(
        self,
        **values: Any,
    ) -> "ToolAction":
        """
        Return a copy with additional/updated payload values.
        """

        payload = dict(
            self.payload
        )

        payload.update(
            values
        )

        return ToolAction(
            action_type=self.action_type,
            source=self.source,
            tool_id=self.tool_id,
            target_id=self.target_id,
            terminal_id=self.terminal_id,
            position=self.position,
            start_position=self.start_position,
            end_position=self.end_position,
            payload=payload,
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the action to a diagnostic dictionary.
        """

        return {
            "action_type": self.action_type.value,
            "source": self.source.value,
            "tool_id": self.tool_id,
            "target_id": self.target_id,
            "terminal_id": self.terminal_id,
            "position": self.position,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "payload": dict(self.payload),
        }

    # --------------------------------------------------------

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            f"{type(self).__name__}("
            f"action_type={self.action_type.value!r}, "
            f"tool_id={self.tool_id!r}"
            ")"
        )


__all__ = [
    "ToolActionType",
    "ToolActionSource",
    "ToolAction",
]
