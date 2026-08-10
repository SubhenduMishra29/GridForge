"""
Bus Tool

Location:
---------
ui/tools/bus_tool.py

Purpose:
--------
Allows user to place buses on the canvas with a single click.

Behavior:
---------
- Click on empty space → create a new bus at that position
- Click on existing bus → ignore (no duplicates)

Design Notes:
-------------
- Stateless tool (no multi-step interaction)
- Writes ONLY to model
- Rendering handled by RenderSystem
"""

from PyQt5.QtCore import QPointF


class BusTool:
    # Unique identifier used by toolbar/controller
    tool_id = "bus"

    def __init__(self, controller, scene):
        self.controller = controller
        self.scene = scene

    # ==========================================================
    # INPUT HANDLERS
    # ==========================================================

    def mouse_press(self, event, context):
        """
        Handles bus placement on click.
        """

        pos = event.scenePos()

        # Prevent placing on top of another bus
        if self._get_bus_at(pos):
            print("[BusTool] Click ignored (bus already exists here)")
            return

        # Create bus in model
        bus = self.controller.model.add_bus(pos.x(), pos.y())

        print(f"[BusTool] Created bus: {bus.id} at ({pos.x()}, {pos.y()})")

        # Notify system to re-render
        self.controller.notify("model_changed")

    # ----------------------------------------------------------

    def mouse_move(self, event, context):
        """
        Reserved for future (hover preview, snap, etc.)
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

        Uses scene item picking.
        """

        items = self.scene.items(pos)

        for item in items:
            if hasattr(item, "bus"):  # BusItem contract
                return item.bus

        return None
