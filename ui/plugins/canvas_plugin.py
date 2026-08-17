"""
GridForge V2
============

File:
    ui/plugins/canvas_plugin.py

Purpose
-------
Composition plugin responsible for creating and exposing the primary
GridForge canvas.

Architectural role
------------------
CanvasPlugin is a UI composition plugin.

It:
    - creates the GridForge GridView;
    - exposes the GridView and its scene;
    - establishes the Qt parent/lifetime boundary;
    - provides the canvas component to the UI composition layer.

It does NOT:
    - own project state;
    - own network topology;
    - modify Core directly;
    - perform electrical calculations;
    - implement tool behavior;
    - own tool lifecycle;
    - create ToolManager;
    - create InteractionManager;
    - create NavigationController;
    - register tools;
    - register renderers;
    - maintain a second canvas state model.

Canvas ownership
----------------
GridView is the authoritative canvas viewport.

GridView owns:
    - its QGraphicsScene;
    - its InteractionManager;
    - its NavigationController;
    - Qt input routing.

CanvasPlugin owns only the composition relationship and plugin
lifecycle bookkeeping.

Qt boundary
-----------
All Qt imports pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ui.core.qt import (
    QGraphicsScene,
    QGraphicsView,
    QObject,
    QWidget,
)

from ui.canvas.graphics_view import GridView
from ui.plugins.plugin_context import PluginContext


# ============================================================
# CANVAS PLUGIN CONTEXT
# ============================================================


@dataclass(slots=True)
class CanvasPluginContext:
    """
    Narrow dependency context used by CanvasPlugin.

    The context contains references only.

    CanvasPlugin does not construct application services.

    ``controller`` is mandatory for actual GridView creation because
    GridView requires the application/UI controller as its authoritative
    coordination dependency.
    """

    parent: Optional[QWidget] = None

    controller: Any = None


# ============================================================
# CANVAS PLUGIN
# ============================================================


class CanvasPlugin(QObject):
    """
    Composition plugin for the primary GridForge canvas.

    GridView is the actual canvas component.

    The plugin does not duplicate state already owned by GridView,
    InteractionManager, NavigationController, ToolManager, Controller,
    or Core.
    """

    plugin_id = "canvas"
    plugin_name = "Canvas"
    plugin_version = "1.0"
    plugin_description = (
        "Primary GridForge graphical canvas composition."
    )

    plugin_dependencies: tuple[str, ...] = ()
    plugin_optional = False

    def __init__(
        self,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        Construct an uninitialized CanvasPlugin.

        Application dependencies are supplied during initialize().
        """

        super().__init__(
            parent
        )

        self._context: Optional[
            CanvasPluginContext
        ] = None

        self._view: Optional[
            GridView
        ] = None

        self._initialized = False

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def context(self) -> Optional[CanvasPluginContext]:
        """Return the current canvas plugin context."""

        return self._context

    @property
    def view(self) -> Optional[GridView]:
        """Return the GridForge canvas view."""

        return self._view

    @property
    def widget(self) -> Optional[QWidget]:
        """Return the canvas widget."""

        return self._view

    @property
    def scene(self) -> Optional[QGraphicsScene]:
        """
        Return the scene owned by GridView.

        CanvasPlugin does not own or replace this scene.
        """

        if self._view is None:
            return None

        return self._view.scene()

    @property
    def interaction_manager(self) -> Any:
        """
        Return GridView's interaction manager.

        The interaction manager is created and owned by GridView.
        """

        if self._view is None:
            return None

        return getattr(
            self._view,
            "interaction_manager",
            None,
        )

    @property
    def navigation_controller(self) -> Any:
        """
        Return GridView's navigation controller.

        NavigationController is created and owned by GridView.
        """

        if self._view is None:
            return None

        return getattr(
            self._view,
            "navigation_controller",
            None,
        )

    @property
    def initialized(self) -> bool:
        """Return whether the plugin has been initialized."""

        return self._initialized

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: Any,
    ) -> QWidget:
        """
        Initialize the canvas composition.

        The shared PluginContext is normalized into the narrower
        CanvasPluginContext.

        Initialization is idempotent.
        """

        if self._initialized:
            if self._view is None:
                raise RuntimeError(
                    "CanvasPlugin is initialized without a GridView."
                )

            return self._view

        self._context = self._coerce_context(
            context
        )

        self._validate_context()

        self._create_canvas()

        self._initialized = True

        if self._view is None:
            raise RuntimeError(
                "CanvasPlugin initialization produced no GridView."
            )

        return self._view

    def shutdown(self) -> None:
        """
        Shut down the plugin.

        Application services are not destroyed.

        GridView lifetime remains governed by Qt ownership. The plugin
        releases its reference to the composed widget.
        """

        if not self._initialized:
            return

        self._view = None
        self._context = None
        self._initialized = False

    # ========================================================
    # CONTEXT
    # ========================================================

    @staticmethod
    def _coerce_context(
        context: Any,
    ) -> CanvasPluginContext:
        """
        Normalize the shared PluginContext into the canvas context.

        A concrete CanvasPluginContext may also be supplied directly.
        """

        if isinstance(
            context,
            CanvasPluginContext,
        ):
            return context

        if not isinstance(
            context,
            PluginContext,
        ):
            raise TypeError(
                (
                    "CanvasPlugin.initialize() requires "
                    "PluginContext or CanvasPluginContext."
                )
            )

        return CanvasPluginContext(
            parent=(
                context.parent
                or context.main_window
            ),
            controller=context.controller,
        )

    def _validate_context(self) -> None:
        """
        Validate the dependencies required to construct GridView.
        """

        if self._context is None:
            raise RuntimeError(
                "CanvasPlugin context has not been initialized."
            )

        if self._context.controller is None:
            raise RuntimeError(
                (
                    "CanvasPlugin requires a controller. "
                    "GridView cannot be created without one."
                )
            )

    # ========================================================
    # CANVAS CREATION
    # ========================================================

    def _create_canvas(self) -> None:
        """
        Create the authoritative GridForge GridView.

        GridView itself creates and owns:
            - QGraphicsScene
            - InteractionManager
            - NavigationController

        CanvasPlugin therefore does not construct or replace any of
        those objects.
        """

        if self._context is None:
            raise RuntimeError(
                "CanvasPlugin context is unavailable."
            )

        if self._view is not None:
            raise RuntimeError(
                "CanvasPlugin already contains a GridView."
            )

        self._view = GridView(
            controller=self._context.controller,
            parent=self._context.parent,
        )

        if not isinstance(
            self._view,
            GridView,
        ):
            raise TypeError(
                "GridView construction returned an invalid object."
            )

    # ========================================================
    # CANVAS ACCESS
    # ========================================================

    def require_view(self) -> GridView:
        """
        Return the initialized GridView.

        Raises
        ------
        RuntimeError
            If the plugin has not been initialized.
        """

        if self._view is None:
            raise RuntimeError(
                "CanvasPlugin has not been initialized."
            )

        return self._view

    def require_scene(self) -> QGraphicsScene:
        """
        Return the scene owned by GridView.
        """

        scene = self.require_view().scene()

        if scene is None:
            raise RuntimeError(
                "GridView does not currently have a scene."
            )

        return scene

    # ========================================================
    # CANVAS OPERATIONS
    # ========================================================

    def refresh(self) -> None:
        """
        Request a visual refresh of the canvas.

        This is a presentation operation only.
        """

        view = self._view

        if view is None:
            return

        view.viewport().update()

        update = getattr(
            view,
            "update",
            None,
        )

        if callable(update):
            update()

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def canvas_available(self) -> bool:
        """Return whether the GridView exists."""

        return self._view is not None

    def scene_available(self) -> bool:
        """Return whether GridView has a scene."""

        return (
            self._view is not None
            and self._view.scene() is not None
        )


# ============================================================
# FACTORY
# ============================================================


def create_canvas_plugin(
    parent: Optional[QObject] = None,
) -> CanvasPlugin:
    """
    Create an uninitialized CanvasPlugin.

    Application/UI context is supplied during initialize().
    """

    return CanvasPlugin(
        parent=parent,
    )


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "CanvasPluginContext",
    "CanvasPlugin",
    "create_canvas_plugin",
]
