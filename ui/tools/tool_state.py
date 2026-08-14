# ============================================================
# File: ui/tools/tool_state.py
# GridForge V2 — Tool State
# ============================================================
"""
Tool-state definitions for GridForge V2.

This module contains lightweight, UI-independent state objects
used to describe the transient interaction state of tools.

Tool state is NOT authoritative project state.

Core remains authoritative for:
    - electrical topology;
    - equipment identity;
    - network connectivity;
    - project revision;
    - domain state.

Tool state exists only for interaction/UI coordination.

Frozen concrete tool set
------------------------
    SelectTool
    BusTool
    LineTool

No Qt dependency is permitted in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


class ToolPhase(str, Enum):
    """
    Generic lifecycle phase of a UI tool.
    """

    INACTIVE = "inactive"
    READY = "ready"
    ACTIVE = "active"
    PREVIEW = "preview"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class ToolState:
    """
    Immutable snapshot of generic tool state.

    Parameters
    ----------
    tool_id:
        Stable tool identifier.

    active:
        Whether the tool is currently active.

    phase:
        Current interaction phase.

    data:
        Tool-specific transient state.

    revision:
        Monotonically increasing local state revision.

    Notes
    -----
    ``data`` is intentionally opaque to this generic state
    container. Concrete tools may expose additional state without
    forcing ToolManager or the renderer to understand tool-specific
    internals.
    """

    tool_id: str
    active: bool = False
    phase: ToolPhase = ToolPhase.INACTIVE
    data: Mapping[str, Any] = field(
        default_factory=dict
    )
    revision: int = 0

    def __post_init__(
        self,
    ) -> None:
        """
        Validate the state snapshot.
        """

        if not isinstance(
            self.tool_id,
            str,
        ) or not self.tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string."
            )

        if not isinstance(
            self.phase,
            ToolPhase,
        ):
            raise TypeError(
                "phase must be a ToolPhase."
            )

        if self.revision < 0:
            raise ValueError(
                "revision must be non-negative."
            )

        if not isinstance(
            self.data,
            Mapping,
        ):
            raise TypeError(
                "data must implement Mapping."
            )

    # ========================================================
    # STATE TRANSITIONS
    # ========================================================

    def activated(
        self,
        *,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolState":
        """
        Return an activated state snapshot.
        """

        return ToolState(
            tool_id=self.tool_id,
            active=True,
            phase=ToolPhase.READY,
            data=(
                dict(self.data)
                if data is None
                else dict(data)
            ),
            revision=self.revision + 1,
        )

    # --------------------------------------------------------

    def deactivated(
        self,
    ) -> "ToolState":
        """
        Return an inactive state snapshot.
        """

        return ToolState(
            tool_id=self.tool_id,
            active=False,
            phase=ToolPhase.INACTIVE,
            data={},
            revision=self.revision + 1,
        )

    # --------------------------------------------------------

    def preview(
        self,
        *,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolState":
        """
        Return a preview-phase state snapshot.
        """

        return ToolState(
            tool_id=self.tool_id,
            active=True,
            phase=ToolPhase.PREVIEW,
            data=(
                dict(self.data)
                if data is None
                else dict(data)
            ),
            revision=self.revision + 1,
        )

    # --------------------------------------------------------

    def cancelled(
        self,
    ) -> "ToolState":
        """
        Return a cancelled state snapshot.

        The tool remains active so it can immediately accept a
        new interaction.
        """

        return ToolState(
            tool_id=self.tool_id,
            active=True,
            phase=ToolPhase.CANCELLED,
            data={},
            revision=self.revision + 1,
        )

    # --------------------------------------------------------

    def ready(
        self,
        *,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolState":
        """
        Return an active/ready state snapshot.
        """

        return ToolState(
            tool_id=self.tool_id,
            active=True,
            phase=ToolPhase.READY,
            data=(
                dict(self.data)
                if data is None
                else dict(data)
            ),
            revision=self.revision + 1,
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
        Return one tool-specific state value.
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
        Return whether a state key exists.
        """

        return key in self.data

    # --------------------------------------------------------

    def with_data(
        self,
        **values: Any,
    ) -> "ToolState":
        """
        Return a new state with additional/updated data.

        Existing state data is preserved.
        """

        updated = dict(
            self.data
        )

        updated.update(
            values
        )

        return ToolState(
            tool_id=self.tool_id,
            active=self.active,
            phase=self.phase,
            data=updated,
            revision=self.revision + 1,
        )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the state into a diagnostic dictionary.
        """

        return {
            "tool_id": self.tool_id,
            "active": self.active,
            "phase": self.phase.value,
            "data": dict(self.data),
            "revision": self.revision,
        }


@dataclass(frozen=True, slots=True)
class SelectToolState:
    """
    Transient state specific to SelectTool.
    """

    selected_ids: tuple[str, ...] = ()
    selection_started: bool = False
    dragging: bool = False

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert selection state into a diagnostic dictionary.
        """

        return {
            "selected_ids": self.selected_ids,
            "selection_started": self.selection_started,
            "dragging": self.dragging,
        }


@dataclass(frozen=True, slots=True)
class BusToolState:
    """
    Transient state specific to BusTool.

    A BusTool is a single-click creation tool, so it normally has
    no persistent interaction phase beyond its latest placement
    position.
    """

    position: Any = None
    placement_pending: bool = False

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert bus-tool state into a diagnostic dictionary.
        """

        return {
            "position": self.position,
            "placement_pending": self.placement_pending,
        }


@dataclass(frozen=True, slots=True)
class LineToolState:
    """
    Transient state specific to LineTool.

    The first endpoint is retained until either:

        - a valid second endpoint completes the line;
        - the interaction is cancelled;
        - the tool is deactivated/reset.
    """

    start_point: Any = None
    current_point: Any = None
    start_position: Any = None
    current_position: Any = None
    preview_active: bool = False

    @property
    def has_start_point(
        self,
    ) -> bool:
        """
        Return whether the first endpoint has been acquired.
        """

        return self.start_point is not None

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert line-tool state into a diagnostic dictionary.
        """

        return {
            "start_point": self.start_point,
            "current_point": self.current_point,
            "start_position": self.start_position,
            "current_position": self.current_position,
            "preview_active": self.preview_active,
        }


__all__ = [
    "ToolPhase",
    "ToolState",
    "SelectToolState",
    "BusToolState",
    "LineToolState",
]
