# ============================================================
# File: ui/tools/tool_event.py
# GridForge V2 — Tool Events
# ============================================================
"""
UI-independent interaction event definitions for GridForge V2.

ToolEvent provides a normalized event contract between the canvas
interaction layer and ToolManager/ToolBase.

The event layer deliberately contains no Qt types.

Architecture
------------

    Qt / GraphicsView
           │
           ▼
    InteractionController
           │
           ▼
       ToolEvent
           │
           ▼
       ToolManager
           │
           ▼
       Active Tool

Responsibilities
----------------
ToolEvent:

    - describe pointer and keyboard interaction;
    - carry scene/canvas coordinates;
    - carry resolved connection-point information;
    - carry modifier/button information;
    - provide normalized event semantics.

ToolEvent does NOT:

    - mutate Core;
    - perform snapping;
    - perform electrical validation;
    - create commands;
    - own Qt event objects;
    - route events.

Qt adaptation belongs in the UI/interaction boundary.

No Qt dependency is permitted here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from typing import Any, Mapping, Optional


# ============================================================
# EVENT TYPES
# ============================================================


class ToolEventType(str, Enum):
    """
    Normalized tool interaction event types.
    """

    MOUSE_PRESS = "mouse_press"
    MOUSE_MOVE = "mouse_move"
    MOUSE_RELEASE = "mouse_release"
    MOUSE_DOUBLE_CLICK = "mouse_double_click"

    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"

    CANCEL = "cancel"
    RESET = "reset"


# ============================================================
# POINTER BUTTONS
# ============================================================


class ToolMouseButton(Flag):
    """
    Normalized mouse-button flags.

    Flag semantics allow combinations when an input adapter needs
    to represent multiple currently pressed buttons.
    """

    NONE = 0
    LEFT = auto()
    RIGHT = auto()
    MIDDLE = auto()


# ============================================================
# KEY MODIFIERS
# ============================================================


class ToolKeyModifier(Flag):
    """
    Normalized keyboard modifier flags.
    """

    NONE = 0
    SHIFT = auto()
    CONTROL = auto()
    ALT = auto()
    META = auto()


# ============================================================
# TOOL EVENT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolEvent:
    """
    Normalized interaction event delivered to a UI tool.

    Parameters
    ----------
    event_type:
        Type of interaction.

    scene_position:
        Position in canvas/scene coordinates.

    canvas_position:
        Optional canvas-local position.

    view_position:
        Optional view/widget position.

    button:
        Mouse button associated with the event.

    buttons:
        Buttons currently held.

    modifiers:
        Keyboard modifiers currently active.

    key:
        Normalized key identifier for keyboard events.

    text:
        Optional textual representation of the key.

    connection_point:
        Optional already-resolved connection-point reference.

    terminal_id:
        Optional terminal identifier.

    object_id:
        Optional object/entity identifier.

    data:
        Additional immutable event metadata.

    accepted:
        Whether an upstream layer has already marked the event
        as accepted.

    Qt types
    --------
    None. Coordinates may be represented by tuples, lightweight
    geometry objects, or project-specific coordinate types.
    """

    event_type: ToolEventType

    scene_position: Any = None
    canvas_position: Any = None
    view_position: Any = None

    button: ToolMouseButton = ToolMouseButton.NONE
    buttons: ToolMouseButton = ToolMouseButton.NONE
    modifiers: ToolKeyModifier = ToolKeyModifier.NONE

    key: Optional[str] = None
    text: Optional[str] = None

    connection_point: Any = None
    terminal_id: Optional[str] = None
    object_id: Optional[str] = None

    data: Mapping[str, Any] = field(
        default_factory=dict
    )

    accepted: bool = False

    def __post_init__(
        self,
    ) -> None:
        """
        Validate the normalized event.
        """

        if not isinstance(
            self.event_type,
            ToolEventType,
        ):
            raise TypeError(
                "event_type must be a ToolEventType."
            )

        if not isinstance(
            self.button,
            ToolMouseButton,
        ):
            raise TypeError(
                "button must be a ToolMouseButton."
            )

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
            self.data,
            Mapping,
        ):
            raise TypeError(
                "data must implement Mapping."
            )

    # ========================================================
    # EVENT CLASSIFICATION
    # ========================================================

    @property
    def is_mouse_event(
        self,
    ) -> bool:
        """
        Return whether the event is a mouse/pointer event.
        """

        return self.event_type in {
            ToolEventType.MOUSE_PRESS,
            ToolEventType.MOUSE_MOVE,
            ToolEventType.MOUSE_RELEASE,
            ToolEventType.MOUSE_DOUBLE_CLICK,
        }

    # --------------------------------------------------------

    @property
    def is_keyboard_event(
        self,
    ) -> bool:
        """
        Return whether the event is a keyboard event.
        """

        return self.event_type in {
            ToolEventType.KEY_PRESS,
            ToolEventType.KEY_RELEASE,
        }

    # --------------------------------------------------------

    @property
    def is_press(
        self,
    ) -> bool:
        """
        Return whether this is a mouse-press event.
        """

        return (
            self.event_type
            == ToolEventType.MOUSE_PRESS
        )

    # --------------------------------------------------------

    @property
    def is_move(
        self,
    ) -> bool:
        """
        Return whether this is a mouse-move event.
        """

        return (
            self.event_type
            == ToolEventType.MOUSE_MOVE
        )

    # --------------------------------------------------------

    @property
    def is_release(
        self,
    ) -> bool:
        """
        Return whether this is a mouse-release event.
        """

        return (
            self.event_type
            == ToolEventType.MOUSE_RELEASE
        )

    # --------------------------------------------------------

    @property
    def is_double_click(
        self,
    ) -> bool:
        """
        Return whether this is a mouse double-click event.
        """

        return (
            self.event_type
            == ToolEventType.MOUSE_DOUBLE_CLICK
        )

    # --------------------------------------------------------

    @property
    def is_key_press(
        self,
    ) -> bool:
        """
        Return whether this is a keyboard press.
        """

        return (
            self.event_type
            == ToolEventType.KEY_PRESS
        )

    # --------------------------------------------------------

    @property
    def is_key_release(
        self,
    ) -> bool:
        """
        Return whether this is a keyboard release.
        """

        return (
            self.event_type
            == ToolEventType.KEY_RELEASE
        )

    # ========================================================
    # BUTTON HELPERS
    # ========================================================

    def has_button(
        self,
        button: ToolMouseButton,
    ) -> bool:
        """
        Return whether a button is present in the event.
        """

        return bool(
            self.button & button
        )

    # --------------------------------------------------------

    def has_held_button(
        self,
        button: ToolMouseButton,
    ) -> bool:
        """
        Return whether a button is currently held.
        """

        return bool(
            self.buttons & button
        )

    # --------------------------------------------------------

    @property
    def left_button(
        self,
    ) -> bool:
        """
        Return whether the left button is associated with the event.
        """

        return self.has_button(
            ToolMouseButton.LEFT
        )

    # --------------------------------------------------------

    @property
    def right_button(
        self,
    ) -> bool:
        """
        Return whether the right button is associated with the event.
        """

        return self.has_button(
            ToolMouseButton.RIGHT
        )

    # --------------------------------------------------------

    @property
    def middle_button(
        self,
    ) -> bool:
        """
        Return whether the middle button is associated with the event.
        """

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
        """
        Return whether a modifier is active.
        """

        return bool(
            self.modifiers & modifier
        )

    # --------------------------------------------------------

    @property
    def shift(
        self,
    ) -> bool:
        """
        Return whether Shift is active.
        """

        return self.has_modifier(
            ToolKeyModifier.SHIFT
        )

    # --------------------------------------------------------

    @property
    def control(
        self,
    ) -> bool:
        """
        Return whether Control is active.
        """

        return self.has_modifier(
            ToolKeyModifier.CONTROL
        )

    # --------------------------------------------------------

    @property
    def alt(
        self,
    ) -> bool:
        """
        Return whether Alt is active.
        """

        return self.has_modifier(
            ToolKeyModifier.ALT
        )

    # --------------------------------------------------------

    @property
    def meta(
        self,
    ) -> bool:
        """
        Return whether Meta/Command is active.
        """

        return self.has_modifier(
            ToolKeyModifier.META
        )

    # ========================================================
    # CONNECTION HELPERS
    # ========================================================

    @property
    def has_connection_point(
        self,
    ) -> bool:
        """
        Return whether an explicit connection point is available.
        """

        return self.connection_point is not None

    # --------------------------------------------------------

    @property
    def has_terminal(
        self,
    ) -> bool:
        """
        Return whether a terminal identifier is available.
        """

        return self.terminal_id is not None

    # --------------------------------------------------------

    @property
    def has_object(
        self,
    ) -> bool:
        """
        Return whether an object identifier is available.
        """

        return self.object_id is not None

    # ========================================================
    # DATA ACCESS
    # ========================================================

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Return an additional event-data value.
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
        Return whether additional event data contains a key.
        """

        return key in self.data

    # ========================================================
    # EVENT TRANSFORMATION
    # ========================================================

    def with_connection(
        self,
        connection_point: Any,
        *,
        terminal_id: Optional[str] = None,
        object_id: Optional[str] = None,
    ) -> "ToolEvent":
        """
        Return a copy containing resolved connection information.
        """

        return ToolEvent(
            event_type=self.event_type,
            scene_position=self.scene_position,
            canvas_position=self.canvas_position,
            view_position=self.view_position,
            button=self.button,
            buttons=self.buttons,
            modifiers=self.modifiers,
            key=self.key,
            text=self.text,
            connection_point=connection_point,
            terminal_id=(
                terminal_id
                if terminal_id is not None
                else self.terminal_id
            ),
            object_id=(
                object_id
                if object_id is not None
                else self.object_id
            ),
            data=dict(self.data),
            accepted=self.accepted,
        )

    # --------------------------------------------------------

    def with_data(
        self,
        **values: Any,
    ) -> "ToolEvent":
        """
        Return a copy with updated additional data.
        """

        data = dict(
            self.data
        )

        data.update(
            values
        )

        return ToolEvent(
            event_type=self.event_type,
            scene_position=self.scene_position,
            canvas_position=self.canvas_position,
            view_position=self.view_position,
            button=self.button,
            buttons=self.buttons,
            modifiers=self.modifiers,
            key=self.key,
            text=self.text,
            connection_point=self.connection_point,
            terminal_id=self.terminal_id,
            object_id=self.object_id,
            data=data,
            accepted=self.accepted,
        )

    # --------------------------------------------------------

    def accept(
        self,
    ) -> "ToolEvent":
        """
        Return a copy marked as accepted.
        """

        return ToolEvent(
            event_type=self.event_type,
            scene_position=self.scene_position,
            canvas_position=self.canvas_position,
            view_position=self.view_position,
            button=self.button,
            buttons=self.buttons,
            modifiers=self.modifiers,
            key=self.key,
            text=self.text,
            connection_point=self.connection_point,
            terminal_id=self.terminal_id,
            object_id=self.object_id,
            data=dict(self.data),
            accepted=True,
        )

    # ========================================================
    # FACTORIES
    # ========================================================

    @classmethod
    def mouse_press(
        cls,
        *,
        scene_position: Any = None,
        canvas_position: Any = None,
        view_position: Any = None,
        button: ToolMouseButton = ToolMouseButton.LEFT,
        buttons: ToolMouseButton = ToolMouseButton.LEFT,
        modifiers: ToolKeyModifier = ToolKeyModifier.NONE,
        connection_point: Any = None,
        terminal_id: Optional[str] = None,
        object_id: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolEvent":
        """
        Construct a mouse-press event.
        """

        return cls(
            event_type=ToolEventType.MOUSE_PRESS,
            scene_position=scene_position,
            canvas_position=canvas_position,
            view_position=view_position,
            button=button,
            buttons=buttons,
            modifiers=modifiers,
            connection_point=connection_point,
            terminal_id=terminal_id,
            object_id=object_id,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def mouse_move(
        cls,
        *,
        scene_position: Any = None,
        canvas_position: Any = None,
        view_position: Any = None,
        buttons: ToolMouseButton = ToolMouseButton.NONE,
        modifiers: ToolKeyModifier = ToolKeyModifier.NONE,
        connection_point: Any = None,
        terminal_id: Optional[str] = None,
        object_id: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolEvent":
        """
        Construct a mouse-move event.
        """

        return cls(
            event_type=ToolEventType.MOUSE_MOVE,
            scene_position=scene_position,
            canvas_position=canvas_position,
            view_position=view_position,
            buttons=buttons,
            modifiers=modifiers,
            connection_point=connection_point,
            terminal_id=terminal_id,
            object_id=object_id,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def mouse_release(
        cls,
        *,
        scene_position: Any = None,
        canvas_position: Any = None,
        view_position: Any = None,
        button: ToolMouseButton = ToolMouseButton.LEFT,
        buttons: ToolMouseButton = ToolMouseButton.NONE,
        modifiers: ToolKeyModifier = ToolKeyModifier.NONE,
        connection_point: Any = None,
        terminal_id: Optional[str] = None,
        object_id: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolEvent":
        """
        Construct a mouse-release event.
        """

        return cls(
            event_type=ToolEventType.MOUSE_RELEASE,
            scene_position=scene_position,
            canvas_position=canvas_position,
            view_position=view_position,
            button=button,
            buttons=buttons,
            modifiers=modifiers,
            connection_point=connection_point,
            terminal_id=terminal_id,
            object_id=object_id,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def mouse_double_click(
        cls,
        *,
        scene_position: Any = None,
        canvas_position: Any = None,
        view_position: Any = None,
        button: ToolMouseButton = ToolMouseButton.LEFT,
        buttons: ToolMouseButton = ToolMouseButton.LEFT,
        modifiers: ToolKeyModifier = ToolKeyModifier.NONE,
        connection_point: Any = None,
        terminal_id: Optional[str] = None,
        object_id: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolEvent":
        """
        Construct a mouse-double-click event.
        """

        return cls(
            event_type=ToolEventType.MOUSE_DOUBLE_CLICK,
            scene_position=scene_position,
            canvas_position=canvas_position,
            view_position=view_position,
            button=button,
            buttons=buttons,
            modifiers=modifiers,
            connection_point=connection_point,
            terminal_id=terminal_id,
            object_id=object_id,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def key_press(
        cls,
        *,
        key: Optional[str] = None,
        text: Optional[str] = None,
        modifiers: ToolKeyModifier = ToolKeyModifier.NONE,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolEvent":
        """
        Construct a key-press event.
        """

        return cls(
            event_type=ToolEventType.KEY_PRESS,
            modifiers=modifiers,
            key=key,
            text=text,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def key_release(
        cls,
        *,
        key: Optional[str] = None,
        text: Optional[str] = None,
        modifiers: ToolKeyModifier = ToolKeyModifier.NONE,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolEvent":
        """
        Construct a key-release event.
        """

        return cls(
            event_type=ToolEventType.KEY_RELEASE,
            modifiers=modifiers,
            key=key,
            text=text,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def cancel(
        cls,
        *,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolEvent":
        """
        Construct a cancellation event.
        """

        return cls(
            event_type=ToolEventType.CANCEL,
            data={} if data is None else dict(data),
        )

    # --------------------------------------------------------

    @classmethod
    def reset(
        cls,
        *,
        data: Optional[Mapping[str, Any]] = None,
    ) -> "ToolEvent":
        """
        Construct a reset event.
        """

        return cls(
            event_type=ToolEventType.RESET,
            data={} if data is None else dict(data),
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the event into a diagnostic dictionary.
        """

        return {
            "event_type": self.event_type.value,
            "scene_position": self.scene_position,
            "canvas_position": self.canvas_position,
            "view_position": self.view_position,
            "button": self.button.name,
            "buttons": self.buttons.name,
            "modifiers": self.modifiers.name,
            "key": self.key,
            "text": self.text,
            "connection_point": self.connection_point,
            "terminal_id": self.terminal_id,
            "object_id": self.object_id,
            "data": dict(self.data),
            "accepted": self.accepted,
        }


__all__ = [
    "ToolEventType",
    "ToolMouseButton",
    "ToolKeyModifier",
    "ToolEvent",
]
