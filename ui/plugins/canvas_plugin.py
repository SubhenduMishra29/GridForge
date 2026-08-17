"""
GridForge V2
============

File:
    ui/plugins/canvas_plugin.py

Purpose
-------
Composition plugin responsible for creating and wiring the primary
GridForge canvas UI.

Architectural rules
-------------------
- The plugin owns canvas composition, not application state.
- The plugin must not perform electrical calculations.
- The plugin must not mutate Core directly.
- The plugin must not own authoritative project/network state.
- Canvas rendering remains delegated to the existing canvas/rendering
  subsystem.
- Tool interaction remains delegated to the ToolManager /
  InteractionManager layer.
- MainWindow remains thin and plugin-driven.
- ui.core.qt is the only Qt import boundary used here.
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


# ============================================================
# CANVAS PLUGIN CONTEXT
# ============================================================


@dataclass(slots=True)
class CanvasPluginContext:
    """
    Runtime dependencies required by CanvasPlugin.

    These are references to already-created application/UI services.
    CanvasPlugin does not create Core, domain, controller, tool, or
    rendering services.

    This context is intentionally narrower than the application-wide
    PluginContext. PluginManager may pass the shared PluginContext,
    which CanvasPlugin normalizes through ``_coerce_context()``.
    """

    parent: Optional[QWidget] = None

    scene: Optional[QGraphicsScene] = None

    view: Optional[QGraphicsView] = None

    canvas_controller: Any = None

    render_system: Any = None

    interaction_manager: Any = None

    tool_manager: Any = None


# ============================================================
# CANVAS PLUGIN
# ============================================================


class CanvasPlugin(QObject):
    """
    Composition plugin for the GridForge canvas.

    Responsibilities
    ----------------
    - create the primary canvas scene/view;
    - attach existing rendering services;
    - attach existing interaction services;
    - attach the existing tool system;
    - expose the composed canvas widget.

    Non-responsibilities
    --------------------
    - project state;
    - network topology;
    - electrical calculations;
    - commands;
    - undo/redo;
    - simulation state;
    - tool registration;
    - renderer registration.
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
        context: Any = None,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        Construct the canvas plugin.

        Construction does not create the canvas. Initialization remains
        an explicit lifecycle operation.
        """

        super().__init__(
            parent
        )

        self._context = self._coerce_context(
            context
        )

        self._scene: Optional[
            QGraphicsScene
        ] = None

        self._view: Optional[
            QGraphicsView
        ] = None

        self._widget: Optional[
            QWidget
        ] = None

        self._initialized = False

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def context(self) -> CanvasPluginContext:
        """Return the normalized canvas plugin context."""

        return self._context

    @property
    def scene(
        self,
    ) -> Optional[QGraphicsScene]:
        """Return the canvas scene."""

        return self._scene

    @property
    def view(
        self,
    ) -> Optional[QGraphicsView]:
        """Return the canvas view."""

        return self._view

    @property
    def widget(
        self,
    ) -> Optional[QWidget]:
        """Return the primary canvas widget."""

        return self._widget

    @property
    def initialized(self) -> bool:
        """Return whether the plugin is initialized."""

        return self._initialized

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: Any = None,
    ) -> QWidget:
        """
        Initialize the canvas composition.

        Initialization is idempotent. A second initialization returns
        the already-created canvas widget.
        """

        if self._initialized:
            if self._widget is None:
                raise RuntimeError(
                    "CanvasPlugin is initialized without a widget."
                )

            return self._widget

        if context is not None:
            self._context = self._coerce_context(
                context
            )

        self._create_canvas()

        self._wire_canvas()

        self._initialized = True

        if self._widget is None:
            raise RuntimeError(
                "CanvasPlugin initialization produced no widget."
            )

        return self._widget

    def shutdown(self) -> None:
        """
        Shut down the canvas composition.

        Application services and Core/domain objects are not destroyed.
        Qt ownership remains responsible for Qt object lifetime.
        """

        if not self._initialized:
            return

        self._disconnect_canvas()

        self._scene = None
        self._view = None
        self._widget = None

        self._initialized = False

    # ========================================================
    # CONTEXT
    # ========================================================

    @staticmethod
    def _coerce_context(
        context: Any,
    ) -> CanvasPluginContext:
        """
        Convert the shared application PluginContext or a
        CanvasPluginContext into the canvas-specific context.

        This keeps PluginManager independent of concrete plugin types.
        """

        if context is None:
            return CanvasPluginContext()

        if isinstance(
            context,
            CanvasPluginContext,
        ):
            return context

        return CanvasPluginContext(
            parent=getattr(
                context,
                "parent",
                None,
            ),
            scene=getattr(
                context,
                "scene",
                None,
            ),
            view=getattr(
                context,
                "view",
                None,
            ),
            canvas_controller=getattr(
                context,
                "canvas_controller",
                None,
            ),
            render_system=getattr(
                context,
                "render_system",
                None,
            ),
            interaction_manager=getattr(
                context,
                "interaction_manager",
                None,
            ),
            tool_manager=getattr(
                context,
                "tool_manager",
                None,
            ),
        )

    # ========================================================
    # CANVAS CREATION
    # ========================================================

    def _create_canvas(self) -> None:
        """
        Create or adopt the canvas scene and view.

        Injected objects are reused. Missing canvas objects are created
        locally because they are composition-owned UI objects rather
        than Core/application services.
        """

        scene = self._context.scene

        if scene is None:
            scene = QGraphicsScene(
                self._context.parent
            )

        self._scene = scene

        view = self._context.view

        if view is None:
            view = self._create_grid_view(
                scene
            )
        else:
            view.setScene(
                scene
            )

        self._view = view
        self._widget = view

    @staticmethod
    def _create_grid_view(
        scene: QGraphicsScene,
        parent: Optional[QWidget] = None,
    ) -> QGraphicsView:
        """
        Create the GridForge-specific graphics view.

        GridView is preferred because it contains GridForge canvas
        interaction/rendering behavior.

        The small constructor compatibility sequence allows the plugin
        to work with the established GridView constructor without
        embedding constructor knowledge elsewhere in the composition
        layer.
        """

        try:
            view = GridView(
                scene=scene,
                parent=parent,
            )
        except TypeError:
            try:
                view = GridView(
                    scene,
                    parent,
                )
            except TypeError:
                view = GridView(
                    parent
                )

                view.setScene(
                    scene
                )

        if not isinstance(
            view,
            QGraphicsView,
        ):
            raise TypeError(
                "GridView must inherit from QGraphicsView."
            )

        return view

    # ========================================================
    # WIRING
    # ========================================================

    def _wire_canvas(self) -> None:
        """
        Attach existing canvas-related services.

        The plugin performs composition only. Service implementations
        remain responsible for their own behavior.
        """

        self._wire_render_system()
        self._wire_interaction_manager()
        self._wire_tool_manager()
        self._wire_canvas_controller()

    def _wire_render_system(self) -> None:
        """Attach the rendering system to the canvas."""

        render_system = self._context.render_system

        if render_system is None:
            return

        self._invoke_optional(
            render_system,
            (
                "set_view",
                "set_canvas_view",
                "attach_view",
            ),
            self._view,
        )

        self._invoke_optional(
            render_system,
            (
                "set_scene",
                "set_canvas_scene",
                "attach_scene",
            ),
            self._scene,
        )

    def _wire_interaction_manager(self) -> None:
        """Attach the interaction manager to the canvas."""

        interaction_manager = (
            self._context.interaction_manager
        )

        if interaction_manager is None:
            return

        self._invoke_optional(
            interaction_manager,
            (
                "set_view",
                "set_canvas_view",
                "attach_view",
            ),
            self._view,
        )

        self._invoke_optional(
            interaction_manager,
            (
                "set_scene",
                "set_canvas_scene",
                "attach_scene",
            ),
            self._scene,
        )

    def _wire_tool_manager(self) -> None:
        """Attach the existing tool manager to the canvas."""

        tool_manager = self._context.tool_manager

        if tool_manager is None:
            return

        self._invoke_optional(
            tool_manager,
            (
                "set_view",
                "set_canvas_view",
                "attach_view",
            ),
            self._view,
        )

        self._invoke_optional(
            tool_manager,
            (
                "set_scene",
                "set_canvas_scene",
                "attach_scene",
            ),
            self._scene,
        )

    def _wire_canvas_controller(self) -> None:
        """Attach the canvas controller where supported."""

        controller = (
            self._context.canvas_controller
        )

        if controller is None:
            return

        self._invoke_optional(
            controller,
            (
                "set_view",
                "set_canvas_view",
                "attach_view",
            ),
            self._view,
        )

        self._invoke_optional(
            controller,
            (
                "set_scene",
                "set_canvas_scene",
                "attach_scene",
            ),
            self._scene,
        )

    # ========================================================
    # DISCONNECT
    # ========================================================

    def _disconnect_canvas(self) -> None:
        """
        Detach plugin-owned canvas connections.

        The underlying services remain alive and owned by their
        respective application layers.
        """

        services = (
            self._context.render_system,
            self._context.interaction_manager,
            self._context.tool_manager,
            self._context.canvas_controller,
        )

        for service in services:
            if service is None:
                continue

            self._invoke_optional(
                service,
                (
                    "detach_view",
                    "remove_view",
                    "clear_view",
                ),
                self._view,
            )

            self._invoke_optional(
                service,
                (
                    "detach_scene",
                    "remove_scene",
                    "clear_scene",
                ),
                self._scene,
            )

    # ========================================================
    # PUBLIC CANVAS OPERATIONS
    # ========================================================

    def set_scene(
        self,
        scene: QGraphicsScene,
    ) -> None:
        """
        Replace the canvas scene.

        The caller remains responsible for scene ownership.
        """

        if not isinstance(
            scene,
            QGraphicsScene,
        ):
            raise TypeError(
                "scene must be QGraphicsScene."
            )

        if self._scene is scene:
            return

        self._disconnect_scene_connections()

        self._scene = scene

        if self._view is not None:
            self._view.setScene(
                scene
            )

        if self._initialized:
            self._wire_canvas()

    def set_view(
        self,
        view: QGraphicsView,
    ) -> None:
        """
        Replace the canvas view.

        The Qt parent hierarchy remains responsible for widget
        ownership.
        """

        if not isinstance(
            view,
            QGraphicsView,
        ):
            raise TypeError(
                "view must be QGraphicsView."
            )

        if self._view is view:
            return

        self._disconnect_view_connections()

        self._view = view
        self._widget = view

        if self._scene is not None:
            view.setScene(
                self._scene
            )

        if self._initialized:
            self._wire_canvas()

    def refresh(self) -> None:
        """
        Request a visual refresh.

        No Core calculation or domain mutation occurs here.
        """

        render_system = self._context.render_system

        if render_system is not None:
            self._invoke_optional(
                render_system,
                (
                    "refresh",
                    "request_refresh",
                    "render",
                    "update",
                ),
            )

        if self._view is not None:
            self._view.viewport().update()

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def canvas_available(self) -> bool:
        """Return whether a canvas view exists."""

        return self._view is not None

    def scene_available(self) -> bool:
        """Return whether a canvas scene exists."""

        return self._scene is not None

    # ========================================================
    # DISCONNECT HELPERS
    # ========================================================

    def _disconnect_view_connections(self) -> None:
        """Detach services from the current canvas view."""

        services = (
            self._context.render_system,
            self._context.interaction_manager,
            self._context.tool_manager,
            self._context.canvas_controller,
        )

        for service in services:
            if service is None:
                continue

            self._invoke_optional(
                service,
                (
                    "detach_view",
                    "remove_view",
                    "clear_view",
                ),
                self._view,
            )

    def _disconnect_scene_connections(self) -> None:
        """Detach services from the current canvas scene."""

        services = (
            self._context.render_system,
            self._context.interaction_manager,
            self._context.tool_manager,
            self._context.canvas_controller,
        )

        for service in services:
            if service is None:
                continue

            self._invoke_optional(
                service,
                (
                    "detach_scene",
                    "remove_scene",
                    "clear_scene",
                ),
                self._scene,
            )

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    @staticmethod
    def _invoke_optional(
        target: Any,
        method_names: tuple[str, ...],
        *args: Any,
    ) -> bool:
        """
        Invoke the first supported capability method.

        Exceptions raised by an existing method are deliberately not
        swallowed. They represent actual integration failures.
        """

        for method_name in method_names:
            method = getattr(
                target,
                method_name,
                None,
            )

            if callable(method):
                method(*args)
                return True

        return False


# ============================================================
# FACTORY
# ============================================================


def create_canvas_plugin(
    context: Any = None,
    parent: Optional[QObject] = None,
) -> CanvasPlugin:
    """
    Create a CanvasPlugin.

    Creation does not initialize the plugin.
    """

    return CanvasPlugin(
        context=context,
        parent=parent,
    )


__all__ = [
    "CanvasPluginContext",
    "CanvasPlugin",
    "create_canvas_plugin",
]
