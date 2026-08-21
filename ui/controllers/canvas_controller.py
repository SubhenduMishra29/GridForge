# ============================================================
# File: ui/controllers/canvas_controller.py
# GridForge V2 — Canvas Controller
# ============================================================
"""
Canvas Controller for GridForge V2.

Architecture
------------

                    MainWindow / Application
                             │
                             ▼
                     CanvasController
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
       GraphicsView   SelectionManager   RenderSystem
             │
             ├── InteractionManager
             └── NavigationController

Purpose
-------
CanvasController is the orchestration boundary for the
GridForge SLD canvas.

It coordinates existing canvas services. It does not implement
rendering, interaction, navigation, selection, snapping, tools,
or electrical-network logic.

Responsibilities
----------------
CanvasController:

    - own the composition relationship between canvas services;
    - expose the GraphicsView;
    - expose the canvas scene;
    - expose InteractionManager;
    - expose NavigationController;
    - expose SelectionManager;
    - expose RenderSystem;
    - request rendering through RenderSystem;
    - request graphical removal through RenderSystem;
    - synchronize graphical selection;
    - delegate navigation operations;
    - reset transient canvas state;
    - provide canvas diagnostics;
    - manage canvas-service lifecycle.

CanvasController does NOT:

    - own Core model state;
    - mutate Core model objects directly;
    - implement tools;
    - own tool lifecycle;
    - implement snapping;
    - implement selection ownership;
    - implement navigation algorithms;
    - implement rendering algorithms;
    - calculate electrical quantities;
    - validate electrical topology;
    - create Core objects;
    - maintain a second model state.

Authority
---------
Core/Application state remains authoritative.

The canvas is a graphical projection:

    Core/Application State
             │
             ▼
       CanvasController
             │
       ┌─────┴────────────┐
       ▼                  ▼
   RenderSystem     SelectionManager
       │                  │
       ▼                  ▼
 QGraphicsItems      Graphical State

Interaction remains owned by InteractionManager.

Navigation remains owned by NavigationController.

Tool ownership remains outside CanvasController and is
provided to GraphicsView during composition.

Qt Architecture
----------------
All Qt classes are imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.canvas.graphics_view import GraphicsView
from ui.canvas.render_system import RenderSystem
from ui.core.selection_manager import SelectionManager


class CanvasController:
    """
    Thin orchestration controller for the GridForge canvas.

    Parameters
    ----------
    controller:
        Authoritative application/UI controller.

    tool_manager:
        Application-owned ToolManager.

        GraphicsView requires this dependency for interaction
        forwarding. CanvasController does not create or own it.

    selection_manager:
        Optional application/canvas SelectionManager.

    graphics_view:
        Optional pre-created GraphicsView.

        When omitted, CanvasController creates one using the
        supplied controller and tool_manager.

    render_system:
        Optional pre-created RenderSystem.

        When omitted, CanvasController creates one for the
        GraphicsView scene.

    renderer_registry:
        RendererRegistry required when CanvasController creates
        a RenderSystem.

    grid_system:
        Optional GridSystem passed to a newly-created
        RenderSystem.

    parent:
        Optional Qt parent for a newly-created GraphicsView.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        tool_manager: Any,
        selection_manager: Optional[
            SelectionManager
        ] = None,
        graphics_view: Optional[
            GraphicsView
        ] = None,
        render_system: Optional[
            RenderSystem
        ] = None,
        renderer_registry: Any = None,
        grid_system: Any = None,
        parent: Optional[Any] = None,
    ) -> None:

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        if tool_manager is None:
            raise ValueError(
                "tool_manager must not be None."
            )

        self.controller = controller
        self.tool_manager = tool_manager

        # ----------------------------------------------------
        # Graphics view
        # ----------------------------------------------------

        if graphics_view is None:
            graphics_view = GraphicsView(
                controller=controller,
                tool_manager=tool_manager,
                parent=parent,
            )

        if not isinstance(
            graphics_view,
            GraphicsView,
        ):
            raise TypeError(
                "graphics_view must be a GraphicsView."
            )

        self.graphics_view = graphics_view

        # ----------------------------------------------------
        # Scene
        # ----------------------------------------------------

        self.scene = graphics_view.scene()

        if self.scene is None:
            raise RuntimeError(
                "GraphicsView must provide a QGraphicsScene."
            )

        # ----------------------------------------------------
        # Selection
        # ----------------------------------------------------

        if selection_manager is None:
            selection_manager = SelectionManager(
                controller,
                scene=self.scene,
            )

        if not isinstance(
            selection_manager,
            SelectionManager,
        ):
            raise TypeError(
                "selection_manager must be a "
                "SelectionManager."
            )

        self.selection_manager = selection_manager

        self.selection_manager.set_scene(
            self.scene
        )

        # ----------------------------------------------------
        # Rendering
        # ----------------------------------------------------

        if render_system is None:
            if renderer_registry is None:
                renderer_registry = (
                    self._get_renderer_registry_from_controller()
                )

            if renderer_registry is None:
                raise ValueError(
                    "renderer_registry must be provided when "
                    "render_system is not supplied."
                )

            render_system = RenderSystem(
                scene=self.scene,
                controller=controller,
                renderer_registry=renderer_registry,
                grid_system=grid_system,
                selection_manager=selection_manager,
            )

        if not isinstance(
            render_system,
            RenderSystem,
        ):
            raise TypeError(
                "render_system must be a RenderSystem."
            )

        self.render_system = render_system

        # Ensure the RenderSystem observes the same
        # SelectionManager used by CanvasController.
        self.render_system.set_selection_manager(
            self.selection_manager
        )

        self._disposed = False

    # ========================================================
    # VIEW ACCESS
    # ========================================================

    def get_view(
        self,
    ) -> GraphicsView:
        """
        Return the canvas GraphicsView.
        """

        self._ensure_active()

        return self.graphics_view

    @property
    def view(
        self,
    ) -> GraphicsView:
        """
        Read-only convenience access to GraphicsView.
        """

        return self.get_view()

    # ========================================================
    # SCENE ACCESS
    # ========================================================

    def get_scene(
        self,
    ) -> Any:
        """
        Return the GraphicsView-owned QGraphicsScene.
        """

        self._ensure_active()

        return self.scene

    # ========================================================
    # INTERACTION ACCESS
    # ========================================================

    def get_interaction_manager(
        self,
    ) -> Any:
        """
        Return the InteractionManager owned by GraphicsView.

        InteractionManager remains responsible for interaction
        and tool dispatch.
        """

        self._ensure_active()

        return self.graphics_view.interaction_manager

    # ========================================================
    # NAVIGATION ACCESS
    # ========================================================

    def get_navigation_controller(
        self,
    ) -> Any:
        """
        Return the NavigationController owned by GraphicsView.
        """

        self._ensure_active()

        return self.graphics_view.navigation_controller

    # ========================================================
    # SELECTION ACCESS
    # ========================================================

    def get_selection_manager(
        self,
    ) -> SelectionManager:
        """
        Return the canvas SelectionManager.
        """

        self._ensure_active()

        return self.selection_manager

    # ========================================================
    # RENDER SYSTEM ACCESS
    # ========================================================

    def get_render_system(
        self,
    ) -> RenderSystem:
        """
        Return the canvas RenderSystem.
        """

        self._ensure_active()

        return self.render_system

    # ========================================================
    # RENDERING
    # ========================================================

    def render(
        self,
        model: Any,
    ) -> tuple[Any, ...]:
        """
        Render one authoritative model element.

        Rendering is delegated entirely to RenderSystem.

        RenderSystem owns:

            model → renderer resolution
            renderer → graphics-item creation
            scene projection bookkeeping

        CanvasController performs no renderer lookup itself.
        """

        self._ensure_active()

        if model is None:
            raise ValueError(
                "model must not be None."
            )

        return self.render_system.render_object(
            model
        )

    # --------------------------------------------------------

    def render_all(
        self,
        models: Iterable[Any],
    ) -> tuple[tuple[Any, ...], ...]:
        """
        Render multiple authoritative model elements.

        Each element is delegated independently to RenderSystem.
        """

        self._ensure_active()

        if models is None:
            raise ValueError(
                "models must not be None."
            )

        result = []

        for model in models:
            result.append(
                self.render(
                    model
                )
            )

        self.render_system.sync_selection()

        return tuple(
            result
        )

    # --------------------------------------------------------

    def refresh(
        self,
        models: Optional[
            Iterable[Any]
        ] = None,
    ) -> None:
        """
        Rebuild the complete canvas projection.

        When models is omitted, RenderSystem obtains the
        authoritative objects from the application controller.
        """

        self._ensure_active()

        self.render_system.refresh(
            models
        )

    # --------------------------------------------------------

    def remove(
        self,
        model: Any,
    ) -> bool:
        """
        Remove the graphical projection of one authoritative
        model element.

        The underlying Core/application object is never removed.

        RenderSystem owns projection bookkeeping and graphical
        removal.
        """

        self._ensure_active()

        if model is None:
            raise ValueError(
                "model must not be None."
            )

        return self.render_system.remove_object(
            model
        )

    # ========================================================
    # SELECTION SYNCHRONIZATION
    # ========================================================

    def sync_selection(
        self,
    ) -> None:
        """
        Synchronize graphical selection from authoritative
        application selection.
        """

        self._ensure_active()

        self.selection_manager.sync_graphics(
            scene=self.scene
        )

    # --------------------------------------------------------

    def clear_graphical_selection(
        self,
    ) -> None:
        """
        Clear graphical selection only.

        Authoritative application selection is untouched.
        """

        self._ensure_active()

        self.selection_manager.reset_graphics(
            scene=self.scene
        )

    # ========================================================
    # NAVIGATION
    # ========================================================

    def zoom_in(
        self,
        steps: int = 1,
    ) -> None:
        """
        Delegate zoom-in to NavigationController.
        """

        self._ensure_active()

        self.get_navigation_controller().zoom_in(
            steps
        )

    # --------------------------------------------------------

    def zoom_out(
        self,
        steps: int = 1,
    ) -> None:
        """
        Delegate zoom-out to NavigationController.
        """

        self._ensure_active()

        self.get_navigation_controller().zoom_out(
            steps
        )

    # --------------------------------------------------------

    def reset_view(
        self,
    ) -> None:
        """
        Delegate viewport reset to NavigationController.
        """

        self._ensure_active()

        self.get_navigation_controller().reset()

    # --------------------------------------------------------

    def fit_content(
        self,
        margin: float = 50.0,
    ) -> None:
        """
        Delegate content fitting to NavigationController.
        """

        self._ensure_active()

        self.get_navigation_controller().fit_content(
            margin
        )

    # --------------------------------------------------------

    def pan_left(
        self,
    ) -> None:
        """
        Delegate left panning to NavigationController.
        """

        self._ensure_active()

        self.get_navigation_controller().pan_left()

    # --------------------------------------------------------

    def pan_right(
        self,
    ) -> None:
        """
        Delegate right panning to NavigationController.
        """

        self._ensure_active()

        self.get_navigation_controller().pan_right()

    # --------------------------------------------------------

    def pan_up(
        self,
    ) -> None:
        """
        Delegate upward panning to NavigationController.
        """

        self._ensure_active()

        self.get_navigation_controller().pan_up()

    # --------------------------------------------------------

    def pan_down(
        self,
    ) -> None:
        """
        Delegate downward panning to NavigationController.
        """

        self._ensure_active()

        self.get_navigation_controller().pan_down()

    # ========================================================
    # CANVAS RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset transient canvas state.

        Core/application state is untouched.

        Authoritative application selection is untouched.
        """

        self._ensure_active()

        self.render_system.clear()

        self.clear_graphical_selection()

    # ========================================================
    # SCENE REPLACEMENT
    # ========================================================

    def attach_scene(
        self,
        scene: Any,
    ) -> None:
        """
        Attach an externally managed QGraphicsScene.

        The existing RenderSystem projection is cleared before
        the scene is replaced.

        The SelectionManager and RenderSystem are synchronized
        with the new scene.

        Existing graphical items are not migrated.
        """

        self._ensure_active()

        if scene is None:
            raise ValueError(
                "scene must not be None."
            )

        current_scene = self.graphics_view.scene()

        if scene is current_scene:
            self.scene = scene

            self.selection_manager.set_scene(
                scene
            )

            return

        self.render_system.clear()

        self.graphics_view.setScene(
            scene
        )

        self.scene = scene

        self.render_system.scene = scene

        self.selection_manager.set_scene(
            scene
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of the canvas subsystem.
        """

        if self._disposed:
            return {
                "disposed": True,
            }

        return {
            "disposed": False,
            "scene_item_count": len(
                self.scene.items()
            ),
            "selection": (
                self.selection_manager.get_state()
            ),
            "graphics_view": (
                self._get_service_state(
                    self.graphics_view
                )
            ),
            "render_system": (
                self._get_service_state(
                    self.render_system
                )
            ),
        }

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose canvas infrastructure.

        Does not dispose the authoritative application
        Controller or ToolManager.
        """

        if self._disposed:
            return

        self.render_system.clear()

        dispose = getattr(
            self.render_system,
            "dispose",
            None,
        )

        if callable(dispose):
            dispose()

        self._disposed = True

    # ========================================================
    # ACTIVE STATE
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure the controller has not been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "CanvasController has been disposed."
            )

    # ========================================================
    # CONTROLLER SERVICES
    # ========================================================

    def _get_renderer_registry_from_controller(
        self,
    ) -> Any:
        """
        Resolve the application's RendererRegistry.

        This is only used when CanvasController must construct
        a RenderSystem.

        No renderer lookup occurs here.
        """

        registry = getattr(
            self.controller,
            "renderer_registry",
            None,
        )

        if registry is not None:
            return registry

        getter = getattr(
            self.controller,
            "get_renderer_registry",
            None,
        )

        if callable(getter):
            registry = getter()

        return registry

    # ========================================================
    # DIAGNOSTIC HELPER
    # ========================================================

    @staticmethod
    def _get_service_state(
        service: Any,
    ) -> Any:
        """
        Obtain optional diagnostic state without requiring every
        canvas service to expose the same diagnostic interface.
        """

        getter = getattr(
            service,
            "get_state",
            None,
        )

        if callable(getter):
            return getter()

        return {
            "type": type(service).__name__,
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        if self._disposed:
            return (
                "CanvasController("
                "disposed=True"
                ")"
            )

        return (
            "CanvasController("
            f"items={len(self.scene.items())}, "
            f"selected="
            f"{len(self.selection_manager.selected_ids)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "CanvasController",
]
