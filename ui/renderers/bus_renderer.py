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
# graphics/interaction state, not a renderer-registry concern.
#
#
# REGISTRATION
# ------------
#
# Renderer registration is performed through the renderer
# registry decorator.
#
# The renderer loader is responsible for importing this module.
# Importing the module therefore registers BusRenderer.
#
# The package initializer does not perform registration.
#
#
# Qt IMPORT RULE
# --------------
#
# This renderer does not directly depend on Qt.
# Any Qt dependency belongs to the graphical item layer.
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

from ui.core.renderer_registry import register_renderer


@register_renderer("bus")
class BusRenderer:
    """
    Renderer responsible for converting a Bus model object
    into a BusItem graphics object.

    The renderer contains no persistent UI state.

    Renderer instances may therefore be created whenever
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
        Create the graphical representation of a Bus.

        Parameters
        ----------
        element:
            GridForge Bus model object.

        controller:
            GridForge application controller passed to the
            graphical item when required by the established
            item/controller contract.

        Returns
        -------
        Any
            The BusItem representing the supplied Bus model.

        Notes
        -----
        BusItem is imported locally so that the renderer
        registry does not need to know about individual
        graphics-item implementations.
        """

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
