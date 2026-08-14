# ============================================================
# File: ui/renderers/line_renderer.py
# GridForge Line Renderer
# ============================================================
#
# PURPOSE
# -------
# Converts a Core Line model object into its graphical
# representation used by the GridForge canvas.
#
#
# ARCHITECTURE
# ------------
#
#                  Core Line Model
#                         │
#                         ▼
#                   LineRenderer
#                         │
#                         ▼
#                      LineItem
#                         │
#                         ▼
#                  QGraphicsScene
#
#
# RENDERER CONTRACT
# -----------------
#
# Every GridForge renderer provides:
#
#     create_item(element, controller)
#
# RenderSystem therefore remains independent of concrete
# graphical item implementations.
#
#
# RESPONSIBILITIES
# ----------------
#
# LineRenderer:
#
#     - accepts a Line model object
#     - creates the corresponding LineItem
#     - passes the application Controller to the graphical item
#
#
# IT DOES NOT:
# ------------
#
#     - modify the Line model
#     - calculate power flow
#     - perform topology operations
#     - handle mouse interaction
#     - perform snapping
#     - manage selection state
#     - manage scene lifecycle
#
#
# REGISTRATION
# ------------
#
# The renderer is registered through RendererRegistry.
#
# RendererLoader is responsible for importing this module.
# Importing the module therefore activates registration.
#
# ============================================================

from __future__ import annotations

from typing import Any

from ui.core.renderer_registry import register_renderer


@register_renderer("line")
class LineRenderer:
    """
    Renderer responsible for converting a Line model object
    into a LineItem graphics object.

    The renderer contains no persistent UI state.
    """

    @staticmethod
    def create_item(
        element: Any,
        controller: Any,
    ) -> Any:
        """
        Create the graphical representation of a Line.

        Parameters
        ----------
        element:
            GridForge Line model object.

        controller:
            GridForge application Controller.

            The controller is passed to the graphical item
            according to the established renderer/item contract.

        Returns
        -------
        Any
            The LineItem representing the supplied Line.

        Notes
        -----
        The renderer does not modify the supplied model object.

        LineItem is imported locally so that the renderer
        registry and RenderSystem remain independent of concrete
        graphics-item implementations.
        """

        from ui.items.line_item import LineItem

        return LineItem(
            element,
            controller,
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "LineRenderer",
]
