"""
GridForge V2
============

File:
    ui/plugins/canvas_plugin.py

Purpose
-------
Canvas composition plugin for the GridForge SLD UI.

Architectural role
------------------
CanvasPlugin owns the lifecycle of the authoritative GraphicsView.

It does not create:
    - ToolManager
    - InteractionManager
    - NavigationController
    - Controller
    - RenderSystem

Those are application-owned dependencies supplied through
PluginContext.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QGraphicsScene,
    QWidget,
)

from ui.canvas.graphics_view import GraphicsView
from ui.plugins.plugin_context import PluginContext


class CanvasPlugin:
    """
    GridForge canvas composition plugin.

    CanvasPlugin creates exactly one authoritative GraphicsView.

    The GraphicsView receives its application-owned dependencies
    through PluginContext.
    """

    plugin_id = "canvas"

    def __init__(
        self,
        context: Optional[PluginContext] = None,
    ) -> None:
        self._context = context
        self._view: Optional[GraphicsView] = None
        self._initialized = False

    # ========================================================
    # CONTEXT
    # ========================================================

    @property
    def context(self) -> Optional[PluginContext]:
        """
        Return the current plugin context.
        """

        return self._context

    def set_context(
        self,
        context: PluginContext,
    ) -> None:
        """
        Supply the plugin dependency context.

        Context may only be replaced before initialization.
        """

        if not isinstance(
            context,
            PluginContext,
        ):
            raise TypeError(
                "context must be PluginContext."
            )

        if self._initialized:
            raise RuntimeError(
                "CanvasPlugin context cannot be changed "
                "after initialization."
            )

        self._context = context

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def initialize(
        self,
        context: Optional[PluginContext] = None,
    ) -> bool:
        """
        Initialize the canvas plugin.
        """

        if self._initialized:
            return True

        if context is not None:
            self.set_context(
                context
            )

        if self._context is None:
            raise RuntimeError(
                "CanvasPlugin requires a PluginContext."
            )

        self._validate_context()

        self._create_canvas()

        self._initialized = True

        return True

    # ========================================================
    # CONTEXT VALIDATION
    # ========================================================

    def _validate_context(
        self,
    ) -> None:
        """
        Validate all dependencies required by the canvas.
        """

        if self._context is None:
            raise RuntimeError(
                "CanvasPlugin context is unavailable."
            )

        if self._context.controller is None:
            raise RuntimeError(
                (
                    "CanvasPlugin requires a controller. "
                    "GraphicsView cannot be created without one."
                )
            )

        if self._context.tool_manager is None:
            raise RuntimeError(
                (
                    "CanvasPlugin requires a ToolManager. "
                    "GraphicsView cannot create InteractionManager "
                    "without one."
                )
            )

    # ========================================================
    # CANVAS CREATION
    # ========================================================

    def _create_canvas(
        self,
    ) -> None:
        """
        Create the authoritative GridForge GraphicsView.

        GraphicsView itself creates and owns:

            - QGraphicsScene
            - InteractionManager
            - NavigationController

        CanvasPlugin supplies the existing application-owned
        dependencies.
        """

        if self._context is None:
            raise RuntimeError(
                "CanvasPlugin context is unavailable."
            )

        if self._view is not None:
            raise RuntimeError(
                "CanvasPlugin already contains a GraphicsView."
            )

        controller = (
            self._context.controller
        )

        tool_manager = (
            self._context.tool_manager
        )

        if controller is None:
            raise RuntimeError(
                "CanvasPlugin controller is unavailable."
            )

        if tool_manager is None:
            raise RuntimeError(
                "CanvasPlugin ToolManager is unavailable."
            )

        self._view = GraphicsView(
            controller=controller,
            tool_manager=tool_manager,
            parent=self._context.parent,
        )

        if not isinstance(
            self._view,
            GraphicsView,
        ):
            raise TypeError(
                "GraphicsView construction returned "
                "an invalid object."
            )

    # ========================================================
    # CANVAS ACCESS
    # ========================================================

    @property
    def widget(
        self,
    ) -> Optional[QWidget]:
        """
        Return the canvas QWidget.

        ShellPlugin consumes this property during composition.
        """

        return self._view

    # --------------------------------------------------------

    def require_view(
        self,
    ) -> GraphicsView:
        """
        Return the initialized GraphicsView.
        """

        if self._view is None:
            raise RuntimeError(
                "CanvasPlugin has not been initialized."
            )

        return self._view

    # --------------------------------------------------------

    def require_scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the scene owned by GraphicsView.
        """

        scene = (
            self.require_view().scene()
        )

        if scene is None:
            raise RuntimeError(
                "GraphicsView does not currently "
                "have a scene."
            )

        return scene

    # ========================================================
    # STATE
    # ========================================================

    @property
    def initialized(
        self,
    ) -> bool:
        """
        Return whether the canvas plugin is initialized.
        """

        return self._initialized

    # ========================================================
    # SHUTDOWN
    # ========================================================

    def shutdown(
        self,
    ) -> None:
        """
        Shut down the canvas plugin.

        GraphicsView is a Qt child of the supplied parent and is
        therefore allowed to follow Qt ownership semantics.
        """

        if self._view is not None:
            self._view.setParent(None)
            self._view.deleteLater()

        self._view = None
        self._initialized = False


# ============================================================
# FACTORY
# ============================================================


def create_canvas_plugin(
    context: Optional[PluginContext] = None,
) -> CanvasPlugin:
    """
    Create a CanvasPlugin.

    No Qt canvas is constructed until initialize() is called.
    """

    return CanvasPlugin(
        context=context
    )


__all__ = [
    "CanvasPlugin",
    "create_canvas_plugin",
]

