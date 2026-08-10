# ============================================================
# File: ui/renderers/bus_renderer.py
# GridForge Bus Renderer
# ============================================================
#
# PURPOSE
# -------
# Converts a Core Bus model object into its graphical
# representation used by the GridForge canvas.
#
#
# ARCHITECTURE
# ------------
#
#     Core Bus Model
#           │
#           ▼
#      BusRenderer
#           │
#           ▼
#        BusItem
#           │
#           ▼
#      QGraphicsScene
#
#
# IMPORTANT
# ---------
#
# This class is a RENDERER.
#
# It does NOT:
#
#     - modify the Bus model
#     - handle mouse events
#     - perform snapping
#     - determine the active tool
#     - manage selection state
#     - manage the graphics scene
#
#
# Hover highlighting belongs to BusItem because hover is a
# graphics/interaction state, not a rendering-registry concern.
#
#
# Qt IMPORT RULE
# --------------
#
# Qt classes MUST be imported through:
#
#     ui.core.qt
#
# Never import PySide6/PyQt directly from this file.
#
#
# RENDERER CONTRACT
# -----------------
#
# RenderSystem expects every renderer to provide:
#
#     create_item(element, controller)
#
# Therefore BusRenderer implements exactly that contract.
#
# ============================================================

from __future__ import annotations

from typing import Any


class BusRenderer:
    """
    Renderer responsible for converting a Bus model object
    into a BusItem graphics object.

    The renderer itself contains no persistent UI state.

    This is intentional.

    Renderer instances are therefore safe to create whenever
    RenderSystem requires them.
    """

    # ========================================================
    # ITEM CREATION
    # ========================================================

    @staticmethod
    def create_item(
        element: Any,
        controller: Any,
    ) -> Any:
        """
        Create the graphics representation of a Bus.

        Parameters
        ----------
        element:
            GridForge Bus model object.

        controller:
            GridForge Controller.

            It is passed to the BusItem so that the graphics
            item can communicate with the application through
            the Controller when required.

        Returns
        -------
        BusItem
            Graphics representation of the Bus.

        Notes
        -----
        The renderer deliberately imports BusItem locally.

        This keeps renderer registration independent from
        RenderSystem.

        The RenderSystem itself never imports BusItem.
        """

        # ----------------------------------------------------
        # Local import
        # ----------------------------------------------------
        #
        # The registry/RenderSystem layer must not know about
        # individual graphics item implementations.
        #
        # The renderer is the correct architectural boundary
        # for this dependency.
        # ----------------------------------------------------

        from ui.items.bus_item import BusItem

        # ----------------------------------------------------
        # Validate the supplied model object at the renderer
        # boundary.
        #
        # We intentionally use attribute validation rather than
        # importing the concrete Bus model here.
        #
        # This keeps the renderer decoupled from the Core model
        # package structure.
        # ----------------------------------------------------

        required_attributes = (
            "id",
            "x",
            "y",
        )

        for attribute in required_attributes:

            if not hasattr(element, attribute):
                raise TypeError(
                    "BusRenderer expected a bus-like model "
                    f"object containing '{attribute}'"
                )

        # ----------------------------------------------------
        # Create the graphical item.
        # ----------------------------------------------------

        item = BusItem(
            element,
            controller,
        )

        return item


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "BusRenderer",
]
```
