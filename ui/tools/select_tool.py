# ============================================================
# File: ui/tools/select_tool.py
# GridForge V2 — Select Tool
# ============================================================
"""
Selection tool for GridForge V2.

The SelectTool converts canvas pointer interaction into selection
intent. It does not own authoritative selection state.

Selection authority remains with SelectionManager.

Responsibilities
----------------
SelectTool:

    - select a graphical object;
    - replace the current selection;
    - extend the selection with modifier-assisted clicks;
    - toggle selection when requested;
    - clear selection when clicking empty canvas;
    - expose a small, deterministic interaction state.

SelectTool does NOT:

    - mutate Core directly;
    - create electrical topology;
    - perform snapping;
    - render objects;
    - navigate the canvas;
    - maintain an independent selection set;
    - execute application commands for selection unless the
      SelectionManager explicitly requires that architecture.

Qt
--
No direct Qt import is used here. Events are treated as opaque
objects and are interpreted through the small event protocol
provided by the GridForge UI layer.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.tools.tool_base import ToolBase


class SelectTool(ToolBase):
    """
    Default GridForge selection tool.

    Selection is delegated to SelectionManager. The tool keeps
    only transient pointer-interaction state.
    """

    TOOL_ID = "select"

    # Common Qt modifier values. Keeping these constants local
    # avoids a direct Qt dependency in the tool.
    _SHIFT_MODIFIER = 0x02000000
    _CTRL_MODIFIER = 0x04000000
    _META_MODIFIER = 0x10000000

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        *,
        command_manager: Optional[Any] = None,
        selection_manager: Optional[Any] = None,
        snap_system: Optional[Any] = None,
        renderer_registry: Optional[Any] = None,
    ) -> None:
        """
        Initialize SelectTool.
        """

        super().__init__(
            controller,
            command_manager=command_manager,
            selection_manager=selection_manager,
            snap_system=snap_system,
            renderer_registry=renderer_registry,
        )

        self._pressed_object_id: Any = None
        self._pressed_position: Any = None
        self._dragging = False

    # ========================================================
    # IDENTITY
    # ========================================================

    @property
    def tool_id(
        self,
    ) -> str:
        """
        Stable ToolManager identifier.
        """

        return self.TOOL_ID

    # --------------------------------------------------------

    @property
    def name(
        self,
    ) -> str:
        """
        Human-readable tool name.
        """

        return "Select"

    # --------------------------------------------------------

    @property
    def description(
        self,
    ) -> str:
        """
        Human-readable tool description.
        """

        return "Select and inspect objects on the canvas."

    # ========================================================
    # ACTIVATION
    # ========================================================

    def on_activate(
        self,
    ) -> None:
        """
        Reset transient interaction state on activation.
        """

        self._clear_pointer_state()

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def on_deactivate(
        self,
    ) -> None:
        """
        Clear transient interaction state on deactivation.
        """

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

        The event may expose one of the following object
        identification protocols:

            event.object_id
            event.object
            event.item
            event.target

        Object extraction is deliberately kept local to the UI
        interaction boundary.
        """

        self._pressed_position = self._extract_position(
            event
        )

        self._pressed_object_id = (
            self._extract_object_id(
                event
            )
        )

        self._dragging = False

        # Empty-canvas press is still consumed by SelectTool.
        return True

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def on_mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Track pointer movement.

        Selection drag semantics are intentionally not invented
        here. A concrete future marquee-selection implementation
        can extend this behavior without changing the tool
        contract.
        """

        if self._pressed_position is None:
            return False

        current_position = self._extract_position(
            event
        )

        if current_position is None:
            return True

        if self._positions_differ(
            self._pressed_position,
            current_position,
        ):
            self._dragging = True

        return True

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def on_mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Complete a click-selection interaction.

        If the pointer moved far enough to constitute a drag,
        selection is not changed here. This keeps SelectTool
        deterministic until marquee selection is explicitly
        introduced.
        """

        object_id = self._extract_object_id(
            event
        )

        if object_id is None:
            object_id = self._pressed_object_id

        try:
            if self._dragging:
                return True

            modifiers = self._extract_modifiers(
                event
            )

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

        finally:
            self._clear_pointer_state()

    # ========================================================
    # DOUBLE CLICK
    # ========================================================

    def on_mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        Consume a double-click without introducing editing
        semantics.

        Editing/properties behavior belongs to the appropriate
        application command or controller layer and is not
        invented by SelectTool.
        """

        object_id = self._extract_object_id(
            event
        )

        if object_id is None:
            return True

        self._select_single(
            object_id
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

        return False

    # ========================================================
    # CANCEL
    # ========================================================

    def on_cancel(
        self,
    ) -> bool:
        """
        Cancel the current pointer interaction.
        """

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

    def on_reset(
        self,
    ) -> None:
        """
        Reset transient selection-tool state.
        """

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
        Apply the canonical selection behavior for an object.
        """

        manager = self.get_selection_manager()

        if self._has_toggle_modifier(
            modifiers
        ):
            self._toggle(
                manager,
                object_id,
            )
            return

        if self._has_additive_modifier(
            modifiers
        ):
            self._select_additive(
                manager,
                object_id,
            )
            return

        self._select_single(
            object_id
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
            self._has_additive_modifier(
                modifiers
            )
            or self._has_toggle_modifier(
                modifiers
            )
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

    def _select_single(
        self,
        object_id: Any,
    ) -> Any:
        """
        Replace the current selection with one object.
        """

        manager = self.get_selection_manager()

        select = getattr(
            manager,
            "select",
            None,
        )

        if not callable(select):
            raise TypeError(
                "SelectionManager must provide select()."
            )

        # SelectionManager owns the exact additive/replacement
        # semantics.
        try:
            return select(
                object_id,
                additive=False,
            )
        except TypeError:
            return select(
                object_id
            )

    # --------------------------------------------------------

    @staticmethod
    def _select_additive(
        manager: Any,
        object_id: Any,
    ) -> Any:
        """
        Add an object to the authoritative selection.
        """

        select = getattr(
            manager,
            "select",
            None,
        )

        if not callable(select):
            raise TypeError(
                "SelectionManager must provide select()."
            )

        try:
            return select(
                object_id,
                additive=True,
            )
        except TypeError:
            return select(
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
        """

        toggle = getattr(
            manager,
            "toggle",
            None,
        )

        if callable(toggle):
            return toggle(
                object_id
            )

        is_selected = getattr(
            manager,
            "is_selected",
            None,
        )

        deselect = getattr(
            manager,
            "deselect",
            None,
        )

        select = getattr(
            manager,
            "select",
            None,
        )

        if not callable(is_selected):
            raise TypeError(
                "SelectionManager must provide toggle() "
                "or is_selected()."
            )

        if is_selected(
            object_id
        ):
            if not callable(deselect):
                raise TypeError(
                    "SelectionManager must provide "
                    "deselect() for toggle fallback."
                )

            return deselect(
                object_id
            )

        if not callable(select):
            raise TypeError(
                "SelectionManager must provide "
                "select() for toggle fallback."
            )

        try:
            return select(
                object_id,
                additive=True,
            )
        except TypeError:
            return select(
                object_id
            )

    # ========================================================
    # EVENT EXTRACTION
    # ========================================================

    @staticmethod
    def _extract_object_id(
        event: Any,
    ) -> Any:
        """
        Extract the authoritative object identifier from an
        interaction event.

        The event protocol is intentionally permissive because
        GraphicsView/InteractionManager may provide different
        event wrappers.

        No object is synthesized when none is available.
        """

        if event is None:
            return None

        # Preferred explicit identifier.
        value = getattr(
            event,
            "object_id",
            None,
        )

        if callable(value):
            value = value()

        if value is not None:
            return value

        # Common aliases used by graphics interaction wrappers.
        for attribute in (
            "entity_id",
            "model_id",
            "item_id",
        ):
            value = getattr(
                event,
                attribute,
                None,
            )

            if callable(value):
                value = value()

            if value is not None:
                return value

        # Object wrapper.
        for attribute in (
            "object",
            "item",
            "target",
        ):
            value = getattr(
                event,
                attribute,
                None,
            )

            if callable(value):
                try:
                    value = value()
                except TypeError:
                    continue

            if value is None:
                continue

            object_id = getattr(
                value,
                "object_id",
                None,
            )

            if callable(object_id):
                object_id = object_id()

            if object_id is not None:
                return object_id

            entity_id = getattr(
                value,
                "entity_id",
                None,
            )

            if callable(entity_id):
                entity_id = entity_id()

            if entity_id is not None:
                return entity_id

            model_id = getattr(
                value,
                "model_id",
                None,
            )

            if callable(model_id):
                model_id = model_id()

            if model_id is not None:
                return model_id

        return None

    # --------------------------------------------------------

    @staticmethod
    def _extract_position(
        event: Any,
    ) -> Any:
        """
        Extract a pointer position from an event.

        No coordinate conversion is performed.
        """

        if event is None:
            return None

        position = getattr(
            event,
            "position",
            None,
        )

        if callable(position):
            try:
                return position()
            except TypeError:
                return None

        if position is not None:
            return position

        return None

    # --------------------------------------------------------

    @staticmethod
    def _extract_modifiers(
        event: Any,
    ) -> int:
        """
        Extract keyboard modifiers from an interaction event.
        """

        if event is None:
            return 0

        modifiers = getattr(
            event,
            "modifiers",
            None,
        )

        if callable(modifiers):
            try:
                modifiers = modifiers()
            except TypeError:
                return 0

        if modifiers is None:
            return 0

        if isinstance(
            modifiers,
            int,
        ):
            return modifiers

        # Test doubles may expose symbolic modifier names.
        if isinstance(
            modifiers,
            str,
        ):
            value = 0
            tokens = {
                token.strip().lower()
                for token in modifiers.split(
                    "|"
                )
            }

            if (
                "shift" in tokens
                or "shiftmodifier" in tokens
            ):
                value |= SelectTool._SHIFT_MODIFIER

            if (
                "ctrl" in tokens
                or "control" in tokens
                or "ctrlmodifier" in tokens
            ):
                value |= SelectTool._CTRL_MODIFIER

            if (
                "meta" in tokens
                or "command" in tokens
                or "metamodifier" in tokens
            ):
                value |= SelectTool._META_MODIFIER

            return value

        return 0

    # ========================================================
    # MODIFIER SEMANTICS
    # ========================================================

    @classmethod
    def _has_additive_modifier(
        cls,
        modifiers: int,
    ) -> bool:
        """
        Return True when the event requests additive selection.

        Shift is the canonical additive modifier.
        """

        return bool(
            modifiers
            & cls._SHIFT_MODIFIER
        )

    # --------------------------------------------------------

    @classmethod
    def _has_toggle_modifier(
        cls,
        modifiers: int,
    ) -> bool:
        """
        Return True when the event requests toggle selection.

        Ctrl is the canonical toggle modifier on Windows/Linux.
        Meta is also accepted for platform-neutral behavior.
        """

        return bool(
            modifiers
            & (
                cls._CTRL_MODIFIER
                | cls._META_MODIFIER
            )
        )

    # ========================================================
    # POINTER STATE
    # ========================================================

    def _clear_pointer_state(
        self,
    ) -> None:
        """
        Clear transient pointer state.
        """

        self._pressed_object_id = None
        self._pressed_position = None
        self._dragging = False

    # --------------------------------------------------------

    @staticmethod
    def _positions_differ(
        first: Any,
        second: Any,
    ) -> bool:
        """
        Determine whether two pointer positions differ.

        The method supports common point-like objects while
        avoiding assumptions about a concrete Qt class.
        """

        if first is second:
            return False

        if first is None or second is None:
            return first is not second

        try:
            return bool(
                first != second
            )
        except Exception:
            return True

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return SelectTool diagnostic state.
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


__all__ = [
    "SelectTool",
]
