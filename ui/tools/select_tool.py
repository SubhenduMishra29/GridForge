# ============================================================
# File: ui/tools/select_tool.py
# GridForge V2 — Select Tool
# ============================================================
"""
Selection and movement interaction tool for GridForge.

Responsibilities
----------------
SelectTool is responsible for:

    - selecting canvas elements;
    - replacing the current selection;
    - extending/toggling the selection;
    - maintaining temporary drag state;
    - resolving the clicked canvas item through
      InteractionManager;
    - requesting model movement through Controller.

SelectTool does NOT:

    - own the QGraphicsScene;
    - perform scene-coordinate conversion itself;
    - implement snapping;
    - create QGraphicsItems;
    - render objects;
    - mutate Core model objects directly;
    - create commands directly;
    - manage tool lifecycle globally;
    - manage PreviewLayer;
    - perform electrical calculations.

Architecture
------------

    InteractionManager
        │
        ├── Qt event routing
        ├── scene coordinates
        └── canvas item lookup
                │
                ▼
            SelectTool
                │
                ▼
            Controller
                │
                ▼
          Command / Core
                │
                ▼
             Model

ToolManager owns activation/deactivation of this tool.

Selection state maintained here is transient UI interaction
state. Persistent application state remains outside the tool.

Important
---------
All Qt imports must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QPointF
from ui.core.tool_registry import register_tool


@register_tool("select")
class SelectTool:
    """
    GridForge selection and movement tool.

    The tool operates through InteractionManager rather than
    accessing the QGraphicsScene directly.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        interaction_manager: Any,
    ) -> None:
        """
        Initialize the SelectTool.

        Parameters
        ----------
        controller:
            GridForge Controller.

        interaction_manager:
            GridForge InteractionManager responsible for
            interaction infrastructure.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        if interaction_manager is None:
            raise ValueError(
                "interaction_manager must not be None."
            )

        self.controller = controller
        self.im = interaction_manager

        # ----------------------------------------------------
        # Transient selection state.
        #
        # Selection belongs to the interaction layer. It is not
        # persisted as Core model state by this tool.
        # ----------------------------------------------------

        self.selected_items: list[Any] = []

        # ----------------------------------------------------
        # Drag state.
        # ----------------------------------------------------

        self.dragging = False
        self.last_pos: Optional[QPointF] = None

    # ========================================================
    # TOOL LIFECYCLE
    # ========================================================

    def activate(self) -> None:
        """
        Activate the selection tool.

        Activation starts a clean drag interaction.

        Existing selection is intentionally preserved because
        changing tools should not implicitly destroy application
        selection state.
        """

        self._cancel_drag()

    # --------------------------------------------------------

    def deactivate(self) -> None:
        """
        Deactivate the selection tool.

        Any unfinished drag interaction is cancelled.

        Selection itself is preserved.
        """

        self._cancel_drag()

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def mouse_press(
        self,
        event: Any,
    ) -> None:
        """
        Handle a mouse-press event.

        Selection behavior
        ------------------
        No modifier:
            Replace the current selection.

        Ctrl/Shift:
            Toggle the clicked item in the selection.

        Clicking empty space:
            Clears selection when no modifier is active.

        A drag begins only when a selectable item is selected.
        """

        pos = self.im.map_to_scene(
            event
        )

        item = self._get_item_at(
            pos
        )

        modifiers = event.modifiers()

        if self._has_selection_modifier(
            modifiers
        ):
            if item is not None:

                if item in self.selected_items:
                    self._deselect_item(
                        item
                    )
                else:
                    self._select_item(
                        item
                    )

        else:
            self._clear_selection()

            if item is not None:
                self._select_item(
                    item
                )

        # ----------------------------------------------------
        # Start drag only when an item is selected.
        # ----------------------------------------------------

        if item is not None and item in self.selected_items:
            self.dragging = True
            self.last_pos = QPointF(
                pos.x(),
                pos.y(),
            )
        else:
            self._cancel_drag()

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def mouse_move(
        self,
        event: Any,
    ) -> None:
        """
        Handle mouse movement during a selection drag.

        The tool computes only transient displacement.

        Persistent movement is delegated to Controller.
        """

        if not self.dragging:
            return

        if self.last_pos is None:
            return

        pos = self.im.map_to_scene(
            event
        )

        delta = pos - self.last_pos

        # Ignore zero movement.
        if delta.x() == 0.0 and delta.y() == 0.0:
            return

        self.last_pos = QPointF(
            pos.x(),
            pos.y(),
        )

        self._move_selection(
            delta
        )

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def mouse_release(
        self,
        event: Any,
    ) -> None:
        """
        Finish the current drag interaction.

        The actual model mutation has already been delegated
        during mouse movement.
        """

        self._cancel_drag()

    # ========================================================
    # KEY PRESS
    # ========================================================

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Handle optional keyboard interaction.

        ESC cancels an active drag but does not clear selection.

        Returns
        -------
        bool
            True when the event was consumed.
        """

        key = event.key()

        if self._is_escape_key(
            key
        ):
            if self.dragging:
                self._cancel_drag()
                return True

        return False

    # ========================================================
    # SELECTION MANAGEMENT
    # ========================================================

    def _select_item(
        self,
        item: Any,
    ) -> None:
        """
        Add an item to the current selection.
        """

        if item in self.selected_items:
            return

        self.selected_items.append(
            item
        )

        set_selected = getattr(
            item,
            "setSelected",
            None,
        )

        if callable(set_selected):
            set_selected(True)

    # --------------------------------------------------------

    def _deselect_item(
        self,
        item: Any,
    ) -> None:
        """
        Remove an item from the current selection.
        """

        if item not in self.selected_items:
            return

        self.selected_items.remove(
            item
        )

        set_selected = getattr(
            item,
            "setSelected",
            None,
        )

        if callable(set_selected):
            set_selected(False)

    # --------------------------------------------------------

    def _clear_selection(
        self,
    ) -> None:
        """
        Clear the current visual selection.
        """

        for item in list(
            self.selected_items
        ):
            set_selected = getattr(
                item,
                "setSelected",
                None,
            )

            if callable(set_selected):
                set_selected(False)

        self.selected_items.clear()

    # ========================================================
    # ITEM RESOLUTION
    # ========================================================

    def _get_item_at(
        self,
        pos: QPointF,
    ) -> Optional[Any]:
        """
        Resolve a selectable canvas item at a scene position.

        Scene/item lookup belongs to InteractionManager.

        Supported InteractionManager contracts are:

            get_item_at(position)

        or:

            item_at(position)

        The tool deliberately does not access QGraphicsScene
        directly.
        """

        getter = getattr(
            self.im,
            "get_item_at",
            None,
        )

        if callable(getter):
            item = getter(
                pos
            )

            return (
                item
                if self._is_selectable(item)
                else None
            )

        getter = getattr(
            self.im,
            "item_at",
            None,
        )

        if callable(getter):
            item = getter(
                pos
            )

            return (
                item
                if self._is_selectable(item)
                else None
            )

        raise AttributeError(
            "InteractionManager must provide "
            "get_item_at() or item_at()."
        )

    # --------------------------------------------------------

    @staticmethod
    def _is_selectable(
        item: Any,
    ) -> bool:
        """
        Determine whether a canvas item is selectable.

        GridForge render items are expected to expose a model
        reference. Generic Qt infrastructure objects are not
        considered selectable merely because they are under the
        cursor.
        """

        if item is None:
            return False

        if hasattr(
            item,
            "model",
        ):
            return True

        if hasattr(
            item,
            "bus",
        ):
            return True

        if hasattr(
            item,
            "line",
        ):
            return True

        return False

    # ========================================================
    # MOVEMENT
    # ========================================================

    def _move_selection(
        self,
        delta: QPointF,
    ) -> None:
        """
        Request movement of the selected model objects.

        SelectTool does NOT modify Core objects directly.

        The Controller is the application boundary responsible
        for turning this interaction into the appropriate
        command/Core mutation.
        """

        move_selected = getattr(
            self.controller,
            "move_selected",
            None,
        )

        if callable(move_selected):
            move_selected(
                list(
                    self.selected_items
                ),
                delta.x(),
                delta.y(),
            )
            return

        move_elements = getattr(
            self.controller,
            "move_elements",
            None,
        )

        if callable(move_elements):
            move_elements(
                list(
                    self.selected_items
                ),
                delta.x(),
                delta.y(),
            )
            return

        raise AttributeError(
            "Controller must provide move_selected() "
            "or move_elements() for SelectTool movement."
        )

    # ========================================================
    # DRAG STATE
    # ========================================================

    def _cancel_drag(
        self,
    ) -> None:
        """
        Cancel only the current drag interaction.
        """

        self.dragging = False
        self.last_pos = None

    # ========================================================
    # MODIFIER HELPERS
    # ========================================================

    @staticmethod
    def _has_selection_modifier(
        modifiers: Any,
    ) -> bool:
        """
        Return True when Ctrl or Shift is active.

        Qt modifier constants are obtained from the event's
        modifier type rather than imported directly from a Qt
        binding.
        """

        modifier_type = type(
            modifiers
        )

        control = getattr(
            modifier_type,
            "ControlModifier",
            None,
        )

        shift = getattr(
            modifier_type,
            "ShiftModifier",
            None,
        )

        if control is None or shift is None:
            return False

        return bool(
            modifiers & (
                control | shift
            )
        )

    # --------------------------------------------------------

    @staticmethod
    def _is_escape_key(
        key: Any,
    ) -> bool:
        """
        Detect the Qt Escape key without importing a Qt binding
        directly into the tool.
        """

        key_type = type(
            key
        )

        escape = getattr(
            key_type,
            "Key_Escape",
            None,
        )

        if escape is None:
            return False

        return key == escape

    # ========================================================
    # PUBLIC SELECTION API
    # ========================================================

    def clear_selection(
        self,
    ) -> None:
        """
        Clear the current selection.
        """

        self._clear_selection()

    # --------------------------------------------------------

    def get_selection(
        self,
    ) -> list[Any]:
        """
        Return a detached copy of the current selection.
        """

        return list(
            self.selected_items
        )

    # --------------------------------------------------------

    def get_selected_count(
        self,
    ) -> int:
        """
        Return the number of currently selected items.
        """

        return len(
            self.selected_items
        )

    # ========================================================
    # STATE / DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return read-only diagnostic state.
        """

        return {
            "selected_count": len(
                self.selected_items
            ),
            "dragging": self.dragging,
            "has_last_position": (
                self.last_pos is not None
            ),
        }

    # --------------------------------------------------------

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "SelectTool("
            f"selected={len(self.selected_items)}, "
            f"dragging={self.dragging}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "SelectTool",
]
```
