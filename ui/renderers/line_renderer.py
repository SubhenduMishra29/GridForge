"""
Line Renderer

Location:
---------
ui/renderers/line_renderer.py

Purpose:
--------
Defines how a Line model element is converted into a visual QGraphicsItem.

This renderer is slightly more complex than BusRenderer because:
- A line typically depends on other model elements (e.g., buses/nodes)
- It may require access to the full model for resolving connections

Responsibilities:
-----------------
- Accept a Line model instance
- Resolve required references (e.g., endpoints)
- Create and return the corresponding QGraphicsItem

It does NOT:
------------
- Modify the model
- Handle user interaction
- Manage scene lifecycle

Contract:
---------
Must implement:
    create_item(element, controller) → QGraphicsItem
"""

from ui.items.line_item import LineItem


class LineRenderer:
    """
    Renderer for Line model elements.
    """

    @staticmethod
    def create_item(line, controller):
        """
        Create a LineItem from a Line model.

        Parameters:
        -----------
        line : Line
            The model instance representing a connection between elements

        controller : Controller
            Provides access to the full model (used for resolving endpoints)

        Returns:
        --------
        QGraphicsItem (LineItem)
        """

        # ------------------------------------------------------
        # Access model (needed for resolving references)
        # ------------------------------------------------------
        model = controller.model

        # ------------------------------------------------------
        # Create the visual item
        # LineItem is expected to internally resolve:
        # - start bus
        # - end bus
        # - positions
        # ------------------------------------------------------
        item = LineItem(line, model)

        # ------------------------------------------------------
        # Optional future hook for controller-aware items
        # ------------------------------------------------------
        if hasattr(item, "set_controller"):
            item.set_controller(controller)

        return item
