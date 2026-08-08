# ============================================================
# File: ui/canvas/render_system.py
# Responsible for syncing model to scene visuals
# ============================================================

from ui.items.bus_item import BusItem
from ui.items.line_item import LineItem


class RenderSystem:
    """
    Rebuilds scene from model.
    """

    def __init__(self, scene, controller):
        self.scene = scene
        self.controller = controller

    # --------------------------------------------------
    def rebuild(self):
        self.scene.clear()

        model = self.controller.model

        # Draw buses
        for bus in model.graph.buses.values():
            item = BusItem(bus)
            self.scene.addItem(item)

        # Draw lines
        for line in model.graph.lines.values():
            item = LineItem(line, model)
            self.scene.addItem(item)
