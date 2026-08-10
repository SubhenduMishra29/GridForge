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
# Every GridForge renderer must provide:
#
#     create_item(element, controller)
#
# The RenderSystem therefore does not need to know whether the
# element is a Bus, Line, Transformer, Generator, Load, etc.
#
#
# RESPONSIBILITIES
# ----------------
#
# LineRenderer:
#
#     - accepts a Line model object
#     - provides the LineItem implementation
#     - passes the Controller to the graphical item
#
#
# IT DOES NOT:
# ------------
#
#     - modify the Line model
#     - calculate power flow
#     - perform topology operations
#     - handle mouse interaction
#     - manage snapping
#     - manage scene lifecycle
#
#
# MODEL ACCESS
# ------------
#
# A Line contains references to its endpoint buses through:
#
#     line.from_bus
#     line.to_bus
#
# LineItem is responsible for resolving the corresponding
# graphical positions using the model.
#
#
# AUTO REGISTRATION
# -----------------
#
# The renderer exposes:
#
#     model_type = Line
#
# This metadata is intentionally kept on the renderer class.
#
# The future renderer auto-loader will use this information to
# discover:
#
#     Line → LineRenderer
#
# without requiring RenderSystem to import this class.
#
# ============================================================

from __future__ import annotations

from typing import Any

from core.models.line import Line


class LineRenderer:
    """
    Renderer responsible for converting a Line model object
    into a LineItem graphics object.
    """

    # ========================================================
    # RENDERER REGISTRATION METADATA
    # ========================================================
    #
    # RendererRegistry/auto-loader uses this attribute to
    # determine which model class this renderer handles.
    #
    # Example:
    #
    #     Line → LineRenderer
    #
    # ========================================================

    model_type = Line

    # ========================================================
    # ITEM CREATION
    # ========================================================

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
            Line model instance.

        controller:
            GridForge Controller.

            The Controller provides access to the complete model
            and application state.

        Returns
        -------
        LineItem
            Graphics representation of the Line.

        Raises
        ------
        TypeError
            If the supplied object is not a Line instance.

        Notes
        -----
        The renderer does not modify the supplied Line.
        """

        # ----------------------------------------------------
        # Validate model type.
        #
        # Unlike BusRenderer, the Line class is imported here
        # because model_type registration requires the actual
        # class object.
        # ----------------------------------------------------

        if not isinstance(element, Line):
            raise TypeError(
                "LineRenderer expected a Line model object, "
                f"got {type(element).__name__}"
            )

        # ----------------------------------------------------
        # Local import of the graphics implementation.
        #
        # RenderSystem must remain completely unaware of
        # LineItem.
        #
        # LineRenderer is the correct architectural boundary
        # for this dependency.
        # ----------------------------------------------------

        from ui.items.line_item import LineItem

        # ----------------------------------------------------
        # Access the complete application model.
        #
        # LineItem needs the model to resolve:
        #
        #     line.from_bus
        #     line.to_bus
        #
        # into actual Bus objects and their coordinates.
        # ----------------------------------------------------

        model = controller.model

        # ----------------------------------------------------
        # Create the graphical item.
        # ----------------------------------------------------

        item = LineItem(
            element,
            model,
        )

        # ----------------------------------------------------
        # Optional Controller injection.
        #
        # This is useful if LineItem later needs to communicate
        # with Controller for:
        #
        #     - selection
        #     - inspection
        #     - context menus
        #     - topology interaction
        #
        # We do not require it today.
        # ----------------------------------------------------

        if hasattr(item, "set_controller"):
            item.set_controller(controller)

        return item


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "LineRenderer",
]
```
