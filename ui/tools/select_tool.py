# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/tools/select_tool.py
#
# Purpose:
#     Selection interaction tool for the GridForge UI.
#
# Architectural Role:
#     SelectTool translates pointer interaction into requests
#     to the authoritative SelectionManager.
#
# Ownership:
#     - SelectionManager / Controller own persistent selection.
#     - SelectTool owns only transient pointer state.
#     - ToolManager owns tool lifecycle.
#     - Core owns domain/model state.
#
# Restrictions:
#     - No direct Core mutation.
#     - No rendering.
#     - No navigation.
#     - No coordinate-system ownership.
#     - No Qt dependency.
#     - No duplicated persistent selection state.
#
# ============================================================

from __future__ import annotations

from typing import Any, Optional, Tuple

from .tool_base import ToolBase


class SelectTool(ToolBase):
    """
    Default GridForge object-selection tool.

    SelectTool converts pointer interaction into selection
    requests. Persistent selection remains owned by the
    SelectionManager / Controller boundary.
    """

    TOOL_ID = "select"

    # Qt-independent modifier values.
    SHIFT_MODIFIER = 0x02000000
    CTRL_MODIFIER = 0x04000000
    META_MODIFIER = 0x10000000

    def __init__(
        self,
        controller: Any,
        command_manager: Any,
        selection_manager: Any,
        snap_system: Any,
        renderer_registry: Any,
    ) -> None:
        super().__init__(
            controller=controller,
            command_manager=command_manager,
            selection_manager=selection_manager,
            snap_system=snap_system,
            renderer_registry=renderer_registry,
        )

        # Transient pointer state only.
        self._pressed_object_id: Any = None
        self._pressed_position: Optional[
            Tuple[float, float]
        ] = None
        self._dragging = False

    # ========================================================
    # METADATA
    # ========================================================

    @property
    def tool_id(self) -> str:
        """Return the stable tool identifier."""
        return self.TOOL_ID

    @property
    def name(self) -> str:
        """Return the user-facing tool name."""
        return "Select"

    @property
    def description(self) -> str:
        """Return the tool description."""
        return "Select GridForge UI objects."

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def on_activate(self) -> None:
        """Reset transient state when activated."""
        self._clear_pointer_state()

    def on_deactivate(self) -> None:
        """Reset transient state when deactivated."""
        self._clear_pointer_state()

    # ========================================================
    # MOUSE
    # ========================================================

    def on_mouse_press(
        self,
        event: Any,
    ) -> bool:
        """
        Handle a pointer press.

        Expected event information:

            object_id
            position
            modifiers

        object_id may be absent/None for empty-canvas clicks.
        """

        self._ensure_active()

        object_id = self._event_object_id(event)
        position = self.event_position(event)
        modifiers = self._event_modifiers(event)

        self._pressed_object_id = object_id
        self._pressed_position = position
        self._dragging = False

        if object_id is None:
            self._handle_empty_canvas_click(
                modifiers
            )
            return True

        self._handle_object_click(
            object_id,
            modifiers,
        )

        return True

    # --------------------------------------------------------

    def on_mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Track pointer movement.

        SelectTool does not move objects. Object manipulation
        belongs to its dedicated command/controller path.
        """

        self._ensure_active()

        if self._pressed_position is None:
            return False

        position = self.event_position(event)

        if position != self._pressed_position:
            self._dragging = True

        return self._dragging

    # --------------------------------------------------------

    def on_mouse_release(
        self,
        event: Any,
    ) -> bool:
        """Finish the current pointer interaction."""

        self._ensure_active()

        handled = (
            self._pressed_object_id is not None
            or self._pressed_position is not None
            or self._dragging
        )

        self._clear_pointer_state()

        return handled

    # --------------------------------------------------------

    def on_mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        Perform the normal selection action for a double-click.

        Opening/editing behavior is intentionally outside this
        tool.
        """

        self._ensure_active()

        object_id = self._event_object_id(event)

        if object_id is None:
            return False

        modifiers = self._event_modifiers(event)

        self._handle_object_click(
            object_id,
            modifiers,
        )

        return True

    # ========================================================
    # KEYBOARD
    # ========================================================

    def on_key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Handle selection-tool keyboard input.

        Destructive commands are deliberately not implemented
        here; they belong to CommandManager/Core.
        """

        self._ensure_active()
        return False

    # ========================================================
    # CANCEL / RESET
    # ========================================================

    def on_cancel(self) -> bool:
        """Cancel the current transient pointer interaction."""

        self._ensure_active()

        had_state = (
            self._pressed_object_id is not None
            or self._pressed_position is not None
            or self._dragging
        )

        self._clear_pointer_state()

        return had_state

    def on_reset(self) -> None:
        """Reset transient pointer state."""

        self._ensure_active()
        self._clear_pointer_state()

    # ========================================================
    # SELECTION DISPATCH
    # ========================================================

    def _handle_object_click(
        self,
        object_id: Any,
        modifiers: int,
    ) -> None:
        """
        Dispatch object selection through SelectionManager.
        """

        manager = self.get_selection_manager()

        if self._has_toggle_modifier(modifiers):
            self._toggle_selection(
                manager,
                object_id,
            )
            return

        if self._has_additive_modifier(modifiers):
            self._add_to_selection(
                manager,
                object_id,
            )
            return

        self._select_single(
            manager,
            object_id,
        )

    # --------------------------------------------------------

    def _handle_empty_canvas_click(
        self,
        modifiers: int,
    ) -> None:
        """
        Clear selection when clicking empty canvas.

        Modifier-assisted clicks preserve the existing
        selection.
        """

        if (
            self._has_additive_modifier(modifiers)
            or self._has_toggle_modifier(modifiers)
        ):
            return

        manager = self.get_selection_manager()

        clear = getattr(
            manager,
            "clear",
            None,
        )

        if not callable(clear):
            raise TypeError(
                "SelectionManager must provide clear()."
            )

        clear()

    # ========================================================
    # SELECTION OPERATIONS
    # ========================================================

    @staticmethod
    def _select_single(
        manager: Any,
        object_id: Any,
    ) -> Any:
        """
        Replace selection with one object.

        Canonical SelectionManager API:
            select_single(object_id)
        """

        select_single = getattr(
            manager,
            "select_single",
            None,
        )

        if not callable(select_single):
            raise TypeError(
                "SelectionManager must provide "
                "select_single()."
            )

        return select_single(
            object_id
        )

    # --------------------------------------------------------

    @staticmethod
    def _add_to_selection(
        manager: Any,
        object_id: Any,
    ) -> Any:
        """
        Add an object to the existing selection.

        Canonical SelectionManager API:
            add_to_selection(object_id)
        """

        add_to_selection = getattr(
            manager,
            "add_to_selection",
            None,
        )

        if not callable(add_to_selection):
            raise TypeError(
                "SelectionManager must provide "
                "add_to_selection()."
            )

        return add_to_selection(
            object_id
        )

    # --------------------------------------------------------

    @staticmethod
    def _toggle_selection(
        manager: Any,
        object_id: Any,
    ) -> Any:
        """
        Toggle an object through the authoritative Controller.

        SelectionManager does not expose toggle_selection().
        Its controller is the authoritative owner of persistent
        application selection.
        """

        is_selected = getattr(
            manager,
            "is_selected",
            None,
        )

        if not callable(is_selected):
            raise TypeError(
                "SelectionManager must provide "
                "is_selected()."
            )

        controller = getattr(
            manager,
            "controller",
            None,
        )

        if controller is None:
            raise TypeError(
                "SelectionManager must expose its controller."
            )

        toggle_selection = getattr(
            controller,
            "toggle_selection",
            None,
        )

        if not callable(toggle_selection):
            raise TypeError(
                "Controller must provide "
                "toggle_selection()."
            )

        # is_selected() is deliberately queried before the
        # controller operation. This keeps the tool's decision
        # boundary explicit while the Controller performs the
        # actual persistent state mutation.
        is_selected(object_id)

        return toggle_selection(
            object_id
        )

    # ========================================================
    # MODIFIER HANDLING
    # ========================================================

    @classmethod
    def _has_additive_modifier(
        cls,
        modifiers: int,
    ) -> bool:
        """
        Return True for additive-selection modifiers.

        Shift is canonical. Meta is also accepted for
        command-style platform conventions.
        """

        return bool(
            modifiers
            & (
                cls.SHIFT_MODIFIER
                | cls.META_MODIFIER
            )
        )

    # --------------------------------------------------------

    @classmethod
    def _has_toggle_modifier(
        cls,
        modifiers: int,
    ) -> bool:
        """
        Return True for toggle-selection modifiers.

        Ctrl is canonical. Meta is also accepted.
        """

        return bool(
            modifiers
            & (
                cls.CTRL_MODIFIER
                | cls.META_MODIFIER
            )
        )

    # ========================================================
    # EVENT HELPERS
    # ========================================================

    @staticmethod
    def _event_object_id(
        event: Any,
    ) -> Any:
        """
        Extract object_id from an opaque event.

        Supported forms:

            event.object_id
            event["object_id"]
        """

        if event is None:
            return None

        object_id = getattr(
            event,
            "object_id",
            None,
        )

        if object_id is not None:
            return object_id

        if isinstance(event, dict):
            return event.get(
                "object_id"
            )

        return None

    # --------------------------------------------------------

    @staticmethod
    def _event_modifiers(
        event: Any,
    ) -> int:
        """
        Extract integer-compatible modifier flags.
        """

        if event is None:
            return 0

        modifiers = getattr(
            event,
            "modifiers",
            0,
        )

        if callable(modifiers):
            modifiers = modifiers()

        if isinstance(event, dict):
            modifiers = event.get(
                "modifiers",
                modifiers,
            )

        if modifiers is None:
            return 0

        try:
            return int(
                modifiers
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise TypeError(
                "event modifiers must be integer-compatible."
            ) from exc

    # ========================================================
    # TRANSIENT STATE
    # ========================================================

    def _clear_pointer_state(self) -> None:
        """Clear SelectTool-owned transient pointer state."""

        self._pressed_object_id = None
        self._pressed_position = None
        self._dragging = False

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(self) -> dict[str, Any]:
        """Return the base tool state plus transient state."""

        state = super().get_state()

        state.update(
            {
                "pressed_object_id": (
                    self._pressed_object_id
                ),
                "pressed_position": (
                    self._pressed_position
                ),
                "dragging": self._dragging,
            }
        )

        return state


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "SelectTool",
]
