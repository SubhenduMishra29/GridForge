"""
Bus Renderer

Location:
---------
ui/renderers/bus_renderer.py

Purpose:
--------
Defines how a Bus model element is converted into a visual QGraphicsItem.

This is a renderer plugin used by the RenderSystem via the RendererRegistry.

Responsibilities:
-----------------
- Accept a Bus model instance
- Create and return the corresponding QGraphicsItem
- Apply any required visual configuration

It does NOT:
------------
- Modify the model
- Handle interaction logic
- Manage scene lifecycle

Contract:
---------
Must implement:
    create_item(element, controller) → QGraphicsItem
"""

from ui.items.bus_item import BusItem
from core.models.bus import Bus


class BusRenderer:
    """
    Renderer for Bus model elements.
    """
    model_type = Bus   # 🔥 REQUIRED FOR AUTO LOADER

    @staticmethod
    def create_item(bus, controller):
        """
        Create a BusItem from a Bus model.

        Parameters:
        -----------
        bus : Bus
            The model instance representing a bus

        controller : Controller
            Provides access to application state (optional use)

        Returns:
        --------
        QGraphicsItem (BusItem)
        """

        # ------------------------------------------------------
        # Create the visual item
        # ------------------------------------------------------
        item = BusItem(bus)

        # ------------------------------------------------------
        # Optional: attach controller if needed later
        # (kept for extensibility, not required now)
        # ------------------------------------------------------
        if hasattr(item, "set_controller"):
            item.set_controller(controller)

        return item
