# ============================================================
# File: ui/renderers/bus_renderer.py
# GridForge Bus Renderer
# ============================================================

"""
GridForge Bus Renderer
======================

Converts a Core Bus model object into its graphical
representation used by the GridForge canvas.

Architecture
------------

    core.model.bus.Bus
            │
            ▼
       BusRenderer
            │
            ▼
         BusItem
            │
            ▼
      QGraphicsScene

The renderer:

    - declares the Core model type it renders;
    - creates the corresponding graphics item;
    - does not own renderer state;
    - does not modify the Core model;
    - does not perform snapping;
    - does not handle tools;
    - does not manage selection;
    - does not manage the scene.

Renderer registration is performed by RendererLoader.

Qt dependencies belong to the graphics-item layer.
"""

from __future__ import annotations

from typing import Any

from core.model.bus import Bus


class BusRenderer:
    """
    Renderer for the GridForge Core Bus model.

    Renderer instances contain no persistent rendering state.
    """

    # ========================================================
    # RENDERER CONTRACT
    # ========================================================

    model_type = Bus

    # ========================================================
    # ITEM CREATION
    # ========================================================

    @staticmethod
    def create_item(
        element: Bus,
        controller: Any,
    ) -> Any:
        """
        Create the graphical representation of a Bus.

        Parameters
        ----------
        element:
            Core GridForge Bus model object.

        controller:
            GridForge application controller.

        Returns
        -------
        Any
            BusItem representing the supplied Bus.
        """

        if not isinstance(element, Bus):
            raise TypeError(
                "BusRenderer.create_item() requires a "
                "core.model.bus.Bus instance."
            )

        from ui.items.bus_item import BusItem

        return BusItem(
            element,
            controller,
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "BusRenderer",
]
