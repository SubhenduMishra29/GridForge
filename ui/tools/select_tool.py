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
#     SelectTool translates pointer interaction into requests to
#     the authoritative SelectionManager.
#
# Boundaries:
#     - SelectionManager owns persistent selection state.
#     - Controller remains authoritative for application state.
#     - SelectTool owns only transient pointer interaction state.
#     - No Qt dependency is introduced here.
#     - No Core model mutation is performed here.
#     - No rendering is performed here.
#     - No navigation is performed here.
#
# ============================================================

from __future__ import annotations

from typing import Any, Optional, Tuple

from .tool_base import ToolBase


class SelectTool(ToolBase):
    """
    Default object-selection tool.

    SelectTool converts pointer interaction into selection
    requests. Persistent selection remains owned by the
    SelectionManager / Controller boundary.

    The tool does not maintain an authoritative selection
    collection.
    """

    TOOL_ID = "select"

    # Qt modifier values are intentionally represented by their
    # standard integer values so this module remains Qt-independent.
    SHIFT_MODIFIER = 0x02000000
    CTRL_MODIFIER = 0x04000000
    META_MODIFIER = 0x10000000

    # --------------------------------------------------------
    # INITIALIZATION
    # --------------------------------------------------------

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
        return "Select and manipulate SLD objects."

    # ========================================================
    # ACTIVATION
    # ========================================================

    def on_activate(self) -> None:
        """Initialize transient state when the tool activates."""
        self._clear_pointer_state()

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def on_deactivate(self) -> None:
        """Clear transient pointer state."""
        self._clear_pointer_state()

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def on_mouse_press(
        self,
        event: Any,
    ) -> bool:
        """
        Begin a selection interaction.

        Expected event attributes:
            object_id
            position
            modifiers

        Missing optional attributes are treated conservatively.
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

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def on_mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Track pointer movement during a selection interaction.

        SelectTool does not perform object movement. Movement,
        if supported by the application, belongs to the relevant
        command/controller layer.
        """

        self._ensure_active()

        if self._pressed_position is None:
            return False

        position = self.event_position(event)

        if position != self._pressed_position:
            self._dragging = True

        return self._dragging

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def on_mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Finish the current pointer interaction.
        """

        self._ensure_active()

        handled = (
            self._pressed_object_id is not None
            or self._pressed_position is not None
            or self._dragging
        )

        self._clear_pointer_state()

        return handled

    # ========================================================
    # DOUBLE CLICK
    # ========================================================

    def on_mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        Handle a double-click.

        SelectTool does not own object editing/opening behavior.
        A double-click therefore performs the normal selection
        action only.
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
        Handle selection-specific keyboard input.

        Delete/backspace is intentionally not implemented here.
        Deletion is a Core-backed command and belongs to the
        command/controller layer.
        """

        self._ensure_active()

        return False

    # ========================================================
    # CANCEL
    # ========================================================

    def on_cancel(self) -> bool:
        """
        Cancel the current pointer interaction.
        """

        self._ensure_active()

        had_state = (
            self._pressed_object_id is not None
            or self._pressed_position is not None
            or self._dragging
        )

        self._clear_pointer_state()

        return had_state

    # ========================================================
    # RESET
    # ========================================================

    def on_reset(self) -> None:
        """
        Reset transient selection-tool state.
        """

        self._ensure_active()

        self._clear_pointer_state()

    # ========================================================
    # OBJECT CLICK
    # ========================================================

    def _handle_object_click(
        self,
        object_id: Any,
        modifiers: int,
    ) -> None:
        """
        Apply canonical selection behavior for an object.

        SelectionManager remains authoritative.
        """

        manager = self.get_selection_manager()

        if self._has_toggle_modifier(modifiers):
            self._toggle(
                manager,
                object_id,
            )
            return

        if self._has_additive_modifier(modifiers):
            self._select_additive(
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
        Clear selection when clicking empty canvas unless an
        additive/toggle modifier is active.
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
        Replace the current selection with one object.

        Uses the locked SelectionManager.select_single() API.
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
    def _select_additive(
        manager: Any,
        object_id: Any,
    ) -> Any:
        """
        Add one object to the authoritative selection.

        Uses the locked SelectionManager.add_to_selection()
        API.
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
    def _toggle(
        manager: Any,
        object_id: Any,
    ) -> Any:
        """
        Toggle one object through SelectionManager.

        SelectionManager does not own a toggle() method, so the
        operation is expressed through its authoritative
        selection API.
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

        if is_selected(object_id):
            return SelectTool._deselect(
                manager,
                object_id,
            )

        return SelectTool._select_additive(
            manager,
            object_id,
        )

    # --------------------------------------------------------

    @staticmethod
    def _deselect(
        manager: Any,
        object_id: Any,
    ) -> Any:
        """
        Remove one object from the authoritative selection.

        SelectionManager's public contract does not currently
        expose a deselect() operation. Therefore this operation
        is delegated through the controller boundary when
        available.
        """

        controller = getattr(
            manager,
            "controller",
            None,
        )

        if controller is None:
            raise TypeError(
                "SelectionManager must provide a controller "
                "for deselection."
            )

        deselect = getattr(
            controller,
            "deselect",
            None,
        )

        if callable(deselect):
            return deselect(
                object_id
            )

        remove_from_selection = getattr(
            controller,
            "remove_from_selection",
            None,
        )

        if callable(remove_from_selection):
            return remove_from_selection(
                object_id
            )

        clear_selection = getattr(
            controller,
            "clear_selection",
            None,
        )

        selected_ids = getattr(
            controller,
            "selected_ids",
            (),
        )

        if callable(clear_selection):
            remaining = tuple(
                selected_id
                for selected_id in selected_ids
                if selected_id != object_id
            )

            if not remaining:
                return clear_selection()

        raise TypeError(
            "Controller must provide a deselection operation."
        )

    # ========================================================
    # MODIFIERS
    # ========================================================

    @classmethod
    def _has_additive_modifier(
        cls,
        modifiers: int,
    ) -> bool:
        """
        Return whether additive selection is requested.

        Shift is the canonical additive modifier. Meta is also
        accepted for platform-independent command-style
        selection.
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
        Return whether toggle selection is requested.

        Ctrl is the canonical toggle modifier. On platforms
        using Meta as the command modifier, Meta is also accepted.
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
        Extract an object identifier from an opaque event.

        Supported event representations:
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
        Extract modifier flags from an opaque event.
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

        if modifiers is None:
            return 0

        if isinstance(event, dict):
            modifiers = event.get(
                "modifiers",
                modifiers,
            )

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
        """Clear all transient pointer state."""

        self._pressed_object_id = None
        self._pressed_position = None
        self._dragging = False

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(self) -> dict[str, Any]:
        """
        Return a diagnostic snapshot.
        """

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
