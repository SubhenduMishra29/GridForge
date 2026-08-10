"""
Line Tool

Location:
---------
ui/tools/line_tool.py

Purpose:
--------
Allows user to create a line between two buses using a 2-click workflow.

Behavior:
---------
1st click  → select start bus
2nd click  → select end bus → create line

Design Notes:
-------------
- Tool is STATEFUL (stores start_bus)
- Uses scene picking to detect BusItem
- Writes ONLY to model (never directly draws)
- Renderer handles visual updates
"""

from ui.core.qt import QPointF


class LineTool:
    # Unique identifier used by toolbar/controller
    tool_id = "line"

    def __init__(self, controller, scene):
        self.controller = controller
        self.scene = scene

        # Internal state
        self.start_bus = None

    # ==========================================================
    # INPUT HANDLERS
    # ==========================================================

    def mouse_press(self, event, context):
        """
        Handles click logic for line creation.
        """

        pos = event.scenePos()

        clicked_bus = self._get_bus_at(pos)

        # ------------------------------------------------------
        # FIRST CLICK → SELECT START BUS
        # ------------------------------------------------------
        if self.start_bus is None:
            if clicked_bus:
                self.start_bus = clicked_bus
                print(f"[LineTool] Start bus selected: {clicked_bus.id}")
            return

        # ------------------------------------------------------
        # SECOND CLICK → SELECT END BUS + CREATE LINE
        # ------------------------------------------------------
        if clicked_bus and clicked_bus != self.start_bus:

            end_bus = clicked_bus

            print(f"[LineTool] Creating line: {self.start_bus.id} -> {end_bus.id}")

            # Create line in model
            self.controller.model.add_line(self.start_bus.id, end_bus.id)

            # Trigger render update
            self.controller.notify("model_changed")

        # Reset state regardless of success/failure
        self.start_bus = None

    # ----------------------------------------------------------

    def mouse_move(self, event, context):
        """
        Optional: Could be used for preview line rendering.
        Currently unused.
        """
        pass

    # ----------------------------------------------------------

    def mouse_release(self, event, context):
        pass

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _get_bus_at(self, pos: QPointF):
        """
        Returns the bus model under cursor, if any.

        Strategy:
        ---------
        - Query QGraphicsScene items at position
        - Find BusItem
        - Return its model reference
        """

        items = self.scene.items(pos)

        for item in items:
            if hasattr(item, "bus"):  # BusItem convention
                return item.bus

        return None
