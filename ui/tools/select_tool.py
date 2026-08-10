"""
Select Tool

Location:
---------
ui/tools/select_tool.py

Purpose:
--------
Handles selection and movement of items in the scene.

Features:
---------
- Click to select
- Ctrl/Shift for multi-select
- Drag to move selected buses
- Updates model positions (not scene directly)

Design Notes:
-------------
- Operates on BusItem via `.bus`
- Movement updates model → triggers render
"""

from ui.core.qt import QPointF


class SelectTool:
    tool_id = "select"

    def __init__(self, controller, scene):
        self.controller = controller
        self.scene = scene

        # Selection state
        self.selected_items = []

        # Drag state
        self.dragging = False
        self.last_pos = None

    # ==========================================================
    # INPUT HANDLERS
    # ==========================================================

    def mouse_press(self, event, context):
        pos = event.scenePos()
        modifiers = event.modifiers()

        clicked_item = self._get_item_at(pos)

        # ------------------------------------------------------
        # NO MODIFIER → REPLACE SELECTION
        # ------------------------------------------------------
        if not (modifiers & (modifiers.ControlModifier | modifiers.ShiftModifier)):
            self._clear_selection()

            if clicked_item:
                self._select_item(clicked_item)

        # ------------------------------------------------------
        # MULTI-SELECT MODE
        # ------------------------------------------------------
        else:
            if clicked_item:
                if clicked_item in self.selected_items:
                    self._deselect_item(clicked_item)
                else:
                    self._select_item(clicked_item)

        # ------------------------------------------------------
        # START DRAG
        # ------------------------------------------------------
        if self.selected_items:
            self.dragging = True
            self.last_pos = pos

    # ----------------------------------------------------------

    def mouse_move(self, event, context):
        if not self.dragging:
            return

        pos = event.scenePos()
        delta = pos - self.last_pos
        self.last_pos = pos

        # Move selected buses in MODEL
        for item in self.selected_items:
            if hasattr(item, "bus"):
                bus = item.bus
                bus.x += delta.x()
                bus.y += delta.y()

        # Trigger re-render
        self.controller.notify("model_changed")

    # ----------------------------------------------------------

    def mouse_release(self, event, context):
        self.dragging = False
        self.last_pos = None

    # ==========================================================
    # SELECTION MANAGEMENT
    # ==========================================================

    def _select_item(self, item):
        self.selected_items.append(item)
        item.setSelected(True)

    def _deselect_item(self, item):
        self.selected_items.remove(item)
        item.setSelected(False)

    def _clear_selection(self):
        for item in self.selected_items:
            item.setSelected(False)
        self.selected_items.clear()

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _get_item_at(self, pos: QPointF):
        """
        Returns first selectable item at position.
        """

        items = self.scene.items(pos)

        for item in items:
            if hasattr(item, "bus") or hasattr(item, "line"):
                return item

        return None
