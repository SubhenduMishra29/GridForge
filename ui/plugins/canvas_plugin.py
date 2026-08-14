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
- Tool interaction remains delegated to the ToolManager/
  InteractionManager layer.
- MainWindow remains thin and plugin-driven.
- PySide6 is the only Qt binding used by GridForge.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget

from ui.core.qt import QtWidgets
from ui.canvas.graphics_view import GridView


# ============================================================
# CANVAS PLUGIN CONTEXT
# ============================================================


@dataclass(slots=True)
class CanvasPluginContext:
    """
    Runtime dependencies supplied to CanvasPlugin.

    The context contains references to already-created application
    services. CanvasPlugin does not create Core/domain services.
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

    The plugin provides the canvas widget and wires existing canvas,
    rendering, and interaction services into that widget.

    It deliberately does not own:
        - project state
        - network topology
        - electrical calculations
        - commands
        - undo/redo history
        - simulation state
    """

    plugin_id = "canvas"
    plugin_name = "Canvas"
    plugin_version = "1.0"

    def __init__(
        self,
        context: Optional[CanvasPluginContext] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        self._context = (
            context
            or CanvasPluginContext()
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
        """Return the plugin context."""

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
        """Return the plugin's root widget."""

        return self._widget

    @property
    def initialized(self) -> bool:
        """Return whether the plugin has been initialized."""

        return self._initialized

    # ========================================================
    # PLUGIN LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: Optional[
            CanvasPluginContext
        ] = None,
    ) -> QWidget:
        """
        Initialize the canvas plugin.

        Initialization is idempotent. If the plugin has already been
        initialized, the existing root widget is returned.
        """

        if self._initialized:
            assert self._widget is not None
            return self._widget

        if context is not None:
            self._context = context

        self._create_canvas()

        self._wire_canvas()

        self._initialized = True

        assert self._widget is not None

        return self._widget

    def shutdown(self) -> None:
        """
        Disconnect plugin-owned references.

        The plugin does not delete application-owned services.
        Qt parent ownership remains responsible for widget lifetime.
        """

        self._disconnect_canvas()

        self._scene = None
        self._view = None
        self._widget = None

        self._initialized = False

    # ========================================================
    # CANVAS CREATION
    # ========================================================

    def _create_canvas(self) -> None:
        """
        Create the scene and GridView.

        Existing injected objects are reused rather than replaced.
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

    def _create_grid_view(
        self,
        scene: QGraphicsScene,
    ) -> QGraphicsView:
        """
        Create the GridForge-specific graphics view.

        GridView is preferred over a generic QGraphicsView because the
        GridForge canvas owns grid/coordinate interaction behavior.
        """

        try:
            view = GridView(
                scene=scene,
                parent=self._context.parent,
            )
        except TypeError:
            try:
                view = GridView(
                    scene,
                    self._context.parent,
                )
            except TypeError:
                view = GridView(
                    self._context.parent
                )
                view.setScene(
                    scene
                )

        return view

    # ========================================================
    # WIRING
    # ========================================================

    def _wire_canvas(self) -> None:
        """
        Wire existing rendering and interaction services.

        Services are intentionally treated through small capability
        checks so CanvasPlugin does not impose a concrete implementation
        hierarchy on the rest of the UI.
        """

        self._wire_render_system()

        self._wire_interaction_manager()

        self._wire_tool_manager()

        self._wire_canvas_controller()

    def _wire_render_system(self) -> None:
        """Attach the render system to the canvas where supported."""

        render_system = (
            self._context.render_system
        )

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
        """Attach the tool manager to the canvas interaction layer."""

        tool_manager = (
            self._context.tool_manager
        )

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
        Disconnect plugin-owned service references.

        Services are not destroyed by this method.
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

        Scene ownership remains with the caller.
        """

        if not isinstance(
            scene,
            QGraphicsScene,
        ):
            raise TypeError(
                "scene must be QGraphicsScene."
            )

        self._scene = scene

        if self._view is not None:
            self._view.setScene(
                scene
            )

        self._wire_render_system()
        self._wire_interaction_manager()
        self._wire_tool_manager()
        self._wire_canvas_controller()

    def set_view(
        self,
        view: QGraphicsView,
    ) -> None:
        """
        Replace the canvas view.

        View ownership remains with its Qt parent hierarchy.
        """

        if not isinstance(
            view,
            QGraphicsView,
        ):
            raise TypeError(
                "view must be QGraphicsView."
            )

        self._view = view

        if self._scene is not None:
            self._view.setScene(
                self._scene
            )

        self._widget = view

        self._wire_render_system()
        self._wire_interaction_manager()
        self._wire_tool_manager()
        self._wire_canvas_controller()

    def refresh(self) -> None:
        """
        Request a visual refresh through the rendering layer.

        No Core calculation is performed here.
        """

        render_system = (
            self._context.render_system
        )

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
        """Return whether a scene exists."""

        return self._scene is not None

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
        Invoke the first supported method.

        Returns True when a method was found and called.

        The helper deliberately does not swallow exceptions raised by
        an existing method implementation. Such exceptions indicate a
        genuine integration problem and must remain visible.
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
# PLUGIN FACTORY
# ============================================================


def create_canvas_plugin(
    context: Optional[
        CanvasPluginContext
    ] = None,
    parent: Optional[QObject] = None,
) -> CanvasPlugin:
    """
    Create a CanvasPlugin instance.

    Construction does not initialize the plugin. Plugin lifecycle
    remains explicit.
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
