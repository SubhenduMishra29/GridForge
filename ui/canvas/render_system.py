"""
Render System

Location:
---------
ui/canvas/render_system.py

Purpose:
--------
Synchronizes the model (data) with the QGraphicsScene (visuals).

This is a FULL REBUILD renderer:
- Clears scene
- Recreates all items from model

Responsibilities:
-----------------
1. Convert model objects → QGraphicsItems
2. Ensure visual state matches model state
3. Restore selection after rebuild

Important Design Rule:
----------------------
RenderSystem NEVER modifies the model.
It is strictly one-way: MODEL → VIEW
"""

from ui.items.bus_item import BusItem
from ui.items.line_item import LineItem


class RenderSystem:
    """
    Rebuilds scene from model.
    """

    def __init__(self, scene, controller):
        """
        Parameters:
        -----------
        scene : QGraphicsScene
        controller : Controller
        """
        self.scene = scene
        self.controller = controller

    # ==========================================================
    # MAIN ENTRY POINT
    # ==========================================================

    def rebuild(self):
        """
        Rebuild the entire scene from the model.

        Triggered by:
        -------------
        - model_changed
        - selection_changed (optional but recommended)

        Steps:
        ------
        1. Clear scene
        2. Draw buses
        3. Draw lines
        4. Restore selection
        """

        # ------------------------------------------------------
        # 1. Clear scene
        # ------------------------------------------------------
        self.scene.clear()

        model = self.controller.model

        # ------------------------------------------------------
        # 2. Draw BUSES
        # ------------------------------------------------------
        for bus in model.graph.buses.values():

            item = BusItem(bus)

            # Restore selection state
            if bus.id in self.controller.selected_ids:
                item.setSelected(True)

            self.scene.addItem(item)

        # ------------------------------------------------------
        # 3. Draw LINES
        # ------------------------------------------------------
        for line in model.graph.lines.values():

            item = LineItem(line, model)

            # Restore selection state
            if line.id in self.controller.selected_ids:
                item.setSelected(True)

            self.scene.addItem(item)

        # ------------------------------------------------------
        # DONE
        # ------------------------------------------------------
        print("[RenderSystem] Scene rebuilt")
