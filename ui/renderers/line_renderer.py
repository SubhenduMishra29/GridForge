# ============================================================
# File: ui/renderers/line_renderer.py
# GridForge Line Renderer
# ============================================================

"""
GridForge Line Renderer
=======================

Converts a Core Line model object into its graphical
representation used by the GridForge canvas.

Architecture
------------

    core.model.line.Line
            │
            ▼
       LineRenderer
            │
            ▼
         LineItem
            │
            ▼
      QGraphicsScene

The renderer:

    - declares the Core model type it renders;
    - creates the corresponding graphics item;
    - does not own persistent rendering state;
    - does not modify the Core model;
    - does not perform topology operations;
    - does not perform snapping;
    - does not handle tools;
    - does not manage selection;
    - does not manage scene lifecycle.

Renderer registration is performed by RendererLoader.

Qt dependencies belong to the graphics-item layer.
"""

from __future__ import annotations

from typing import Any

from core.model.line import Line


class LineRenderer:
    """
    Renderer for the GridForge Core Line model.

    Renderer instances contain no persistent rendering state.
    """

    # ========================================================
    # RENDERER CONTRACT
    # ========================================================

    model_type = Line

    # ========================================================
    # ITEM CREATION
    # ========================================================

    @staticmethod
    def create_item(
        element: Line,
        controller: Any,
    ) -> Any:
        """
        Create the graphical representation of a Line.

        Parameters
        ----------
        element:
            Core GridForge Line model object.

        controller:
            GridForge application Controller.

        Returns
        -------
        Any
            LineItem representing the supplied Line.

        Raises
        ------
        TypeError
            If element is not a Line instance.
        """

        if not isinstance(element, Line):
            raise TypeError(
                "LineRenderer.create_item() requires a "
                "core.model.line.Line instance."
            )

        # ----------------------------------------------------
        # Local import keeps the renderer layer independent
        # from concrete graphics-item imports during renderer
        # discovery.
        # ----------------------------------------------------

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
