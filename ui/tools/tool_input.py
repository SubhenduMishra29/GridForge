# ============================================================
# File: ui/tools/tool_input.py
# GridForge V2 — Tool Input
# ============================================================
"""
Normalized input state used by the GridForge V2 tool system.

ToolInput represents the current interaction context supplied to
a tool. It is intentionally separate from ToolEvent:

    ToolEvent
        A discrete interaction occurrence.

    ToolInput
        The current normalized input state/context.

The Qt interaction layer is responsible for converting native Qt
input into these UI-independent structures.

Architecture
------------

    Qt / GraphicsView
           │
           ▼
      InteractionController
           │
           ├── ToolEvent
           └── ToolInput
                 │
                 ▼
             ToolManager
                 │
                 ▼
             Active Tool

ToolInput does NOT:

    - access Qt;
    - mutate Core;
    - perform snapping;
    - perform topology validation;
    - execute commands;
    - own application state.

No Qt dependency is permitted in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from ui.tools.tool_event import (
    ToolKeyModifier,
    ToolMouseButton,
)


@dataclass(frozen=True, slots=True)
class ToolInput:
    """
    Immutable normalized input state.

    Coordinates are deliberately represented as ``Any`` so the
    input boundary can work with the project's coordinate type
    without introducing a Qt dependency.

    Parameters
    ----------
    scene_position:
        Current position in scene coordinates.

    canvas_position:
        Optional position in canvas-local coordinates.

    view_position:
        Optional position in view/widget coordinates.

    buttons:
        Mouse buttons currently held.

    modifiers:
        Keyboard modifiers currently active.

    key:
        Currently processed key identifier, when applicable.

    text:
        Text associated with the current keyboard input.

    hovered_object_id:
        Object currently under the pointer, when resolved.

    hovered_terminal_id:
        Terminal currently under the pointer, when resolved.

    connection_point:
        Resolved connection point, when available.

    snap_position:
        Position resolved by the snapping layer, when available.

    snapped:
        Whether the current position has been resolved by snapping.

    payload:
        Additional normalized input metadata.
    """

    scene_position: Any = None
    canvas_position: Any = None
    view_position: Any = None

    buttons: ToolMouseButton = ToolMouseButton.NONE
    modifiers: ToolKeyModifier = ToolKeyModifier.NONE

    key: Optional[str] = None
    text: Optional[str] = None

    hovered_object_id: Optional[str] = None
    hovered_terminal_id: Optional[str] = None

    connection_point: Any = None
    snap_position: Any = None
    snapped: bool = False

    payload: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Validate the normalized input state."""

        if not isinstance(
            self.buttons,
            ToolMouseButton,
        ):
            raise TypeError(
                "buttons must be a ToolMouseButton."
            )

        if not isinstance(
            self.modifiers,
            ToolKeyModifier,
        ):
            raise TypeError(
                "modifiers must be a ToolKeyModifier."
            )

        if not isinstance(
            self.snapped,
            bool,
        ):
            raise TypeError(
                "snapped must be a bool."
            )

        if not isinstance(
            self.payload,
            Mapping,
        ):
            raise TypeError(
                "payload must implement Mapping."
            )

        if self.hovered_object_id is not None:
            if not isinstance(
                self.hovered_object_id,
                str,
            ) or not self.hovered_object_id.strip():
                raise ValueError(
                    "hovered_object_id must be None or "
                    "a non-empty string."
                )

        if self.hovered_terminal_id is not None:
            if not isinstance(
                self.hovered_terminal_id,
                str,
            ) or not self.hovered_terminal_id.strip():
                raise ValueError(
                    "hovered_terminal_id must be None or "
                    "a non-empty string."
                )

    # ========================================================
    # BUTTON HELPERS
    # ========================================================

    def has_button(
        self,
        button: ToolMouseButton,
    ) -> bool:
        """Return whether a mouse button is currently held."""

        if not isinstance(
            button,
            ToolMouseButton,
        ):
            raise TypeError(
                "button must be a ToolMouseButton."
            )

        return bool(
            self.buttons & button
        )

    @property
    def left_button(self) -> bool:
        """Return whether the left mouse button is held."""

        return self.has_button(
            ToolMouseButton.LEFT
        )

    @property
    def right_button(self) -> bool:
        """Return whether the right mouse button is held."""

        return self.has_button(
            ToolMouseButton.RIGHT
        )

    @property
    def middle_button(self) -> bool:
        """Return whether the middle mouse button is held."""

        return self.has_button(
            ToolMouseButton.MIDDLE
        )

    # ========================================================
    # MODIFIER HELPERS
    # ========================================================

    def has_modifier(
        self,
        modifier: ToolKeyModifier,
    ) -> bool:
        """Return whether a keyboard modifier is active."""

        if not isinstance(
            modifier,
            ToolKeyModifier,
        ):
            raise TypeError(
                "modifier must be a ToolKeyModifier."
            )

        return bool(
            self.modifiers & modifier
        )

    @property
    def shift(self) -> bool:
        """Return whether Shift is active."""

        return self.has_modifier(
            ToolKeyModifier.SHIFT
        )

    @property
    def control(self) -> bool:
        """Return whether Control is active."""

        return self.has_modifier(
            ToolKeyModifier.CONTROL
        )

    @property
    def alt(self) -> bool:
        """Return whether Alt is active."""

        return self.has_modifier(
            ToolKeyModifier.ALT
        )

    @property
    def meta(self) -> bool:
        """Return whether Meta/Command is active."""

        return self.has_modifier(
            ToolKeyModifier.META
        )

    # ========================================================
    # POINTER / CONNECTION STATE
    # ========================================================

    @property
    def has_position(self) -> bool:
        """Return whether a scene position is available."""

        return self.scene_position is not None

    @property
    def has_hover_object(self) -> bool:
        """Return whether an object is currently hovered."""

        return self.hovered_object_id is not None

    @property
    def has_hover_terminal(self) -> bool:
        """Return whether a terminal is currently hovered."""

        return self.hovered_terminal_id is not None

    @property
    def has_connection_point(self) -> bool:
        """Return whether a connection point is available."""

        return self.connection_point is not None

    @property
    def has_snap_position(self) -> bool:
        """Return whether a snapped position is available."""

        return self.snap_position is not None

    @property
    def effective_position(self) -> Any:
        """
        Return the position a tool should normally use.

        A resolved snap position takes precedence over the raw
        scene position. The snapping system remains responsible
        for determining the snap result.
        """

        if self.snapped and self.snap_position is not None:
            return self.snap_position

        return self.scene_position

    # ========================================================
    # PAYLOAD
    # ========================================================

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Return an additional input value."""

        return self.payload.get(
            key,
            default,
        )

    def has(
        self,
        key: str,
    ) -> bool:
        """Return whether an additional input value exists."""

        return key in self.payload

    # ========================================================
    # TRANSFORMATION
    # ========================================================

    def with_snap(
        self,
        snap_position: Any,
        *,
        snapped: bool = True,
    ) -> "ToolInput":
        """
        Return a copy containing a resolved snap position.

        Snap computation itself belongs to SnapSystem; this method
        only carries the already-resolved result.
        """

        return ToolInput(
            scene_position=self.scene_position,
            canvas_position=self.canvas_position,
            view_position=self.view_position,
            buttons=self.buttons,
            modifiers=self.modifiers,
            key=self.key,
            text=self.text,
            hovered_object_id=self.hovered_object_id,
            hovered_terminal_id=self.hovered_terminal_id,
            connection_point=self.connection_point,
            snap_position=snap_position,
            snapped=snapped,
            payload=dict(self.payload),
        )

    def with_connection(
        self,
        connection_point: Any,
        *,
        terminal_id: Optional[str] = None,
        object_id: Optional[str] = None,
    ) -> "ToolInput":
        """
        Return a copy containing resolved connection information.
        """

        return ToolInput(
            scene_position=self.scene_position,
            canvas_position=self.canvas_position,
            view_position=self.view_position,
            buttons=self.buttons,
            modifiers=self.modifiers,
            key=self.key,
            text=self.text,
            hovered_object_id=(
                object_id
                if object_id is not None
                else self.hovered_object_id
            ),
            hovered_terminal_id=(
                terminal_id
                if terminal_id is not None
                else self.hovered_terminal_id
            ),
            connection_point=connection_point,
            snap_position=self.snap_position,
            snapped=self.snapped,
            payload=dict(self.payload),
        )

    def with_payload(
        self,
        **values: Any,
    ) -> "ToolInput":
        """Return a copy with updated payload values."""

        payload = dict(
            self.payload
        )
        payload.update(
            values
        )

        return ToolInput(
            scene_position=self.scene_position,
            canvas_position=self.canvas_position,
            view_position=self.view_position,
            buttons=self.buttons,
            modifiers=self.modifiers,
            key=self.key,
            text=self.text,
            hovered_object_id=self.hovered_object_id,
            hovered_terminal_id=self.hovered_terminal_id,
            connection_point=self.connection_point,
            snap_position=self.snap_position,
            snapped=self.snapped,
            payload=payload,
        )

    # ========================================================
    # EVENT CONVERSION
    # ========================================================

    @classmethod
    def from_event(
        cls,
        event: Any,
        *,
        snap_position: Any = None,
        snapped: bool = False,
    ) -> "ToolInput":
        """
        Create ToolInput from a normalized ToolEvent.

        This is a pure data conversion. It does not perform
        snapping, hit testing, or connection resolution.
        """

        # Import locally to keep the module's dependency surface
        # explicit while allowing callers to pass only ToolEvent.
        from ui.tools.tool_event import ToolEvent

        if not isinstance(
            event,
            ToolEvent,
        ):
            raise TypeError(
                "event must be a ToolEvent."
            )

        return cls(
            scene_position=event.scene_position,
            canvas_position=event.canvas_position,
            view_position=event.view_position,
            buttons=event.buttons,
            modifiers=event.modifiers,
            key=event.key,
            text=event.text,
            hovered_object_id=event.object_id,
            hovered_terminal_id=event.terminal_id,
            connection_point=event.connection_point,
            snap_position=snap_position,
            snapped=snapped,
            payload=dict(event.data),
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Return a diagnostic dictionary."""

        return {
            "scene_position": self.scene_position,
            "canvas_position": self.canvas_position,
            "view_position": self.view_position,
            "buttons": self.buttons.name,
            "modifiers": self.modifiers.name,
            "key": self.key,
            "text": self.text,
            "hovered_object_id": self.hovered_object_id,
            "hovered_terminal_id": self.hovered_terminal_id,
            "connection_point": self.connection_point,
            "snap_position": self.snap_position,
            "snapped": self.snapped,
            "effective_position": self.effective_position,
            "payload": dict(self.payload),
        }


__all__ = [
    "ToolInput",
]
