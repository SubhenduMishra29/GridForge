# ============================================================
# File: ui/controllers/canvas_controller.py
# GridForge V2 — Canvas Controller
# ============================================================
"""
Canvas Controller for GridForge V2.

Architecture
------------

                    MainWindow / Plugin
                           │
                           ▼
                   CanvasController
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       GraphicsView   SelectionManager  Renderers
             │
             ├── InteractionManager
             └── NavigationController

Purpose
-------
CanvasController is the UI orchestration boundary for the
canvas.

It coordinates already-existing canvas services. It does not
become a second application controller and does not implement
canvas subsystems itself.

Responsibilities
----------------
CanvasController:

    - attach and expose the GraphicsView;
    - coordinate canvas lifecycle;
    - coordinate scene synchronization;
    - provide stable access to canvas services;
    - request rendering of authoritative objects;
    - request graphical removal of objects;
    - synchronize graphical selection;
    - expose navigation operations;
    - reset transient canvas state;
    - provide canvas diagnostics.

CanvasController does NOT:

    - own Core model state;
    - mutate Core model objects directly;
    - implement tools;
    - implement snapping;
    - implement selection ownership;
    - implement navigation algorithms;
    - implement rendering algorithms;
    - calculate electrical quantities;
    - validate electrical topology;
    - create Core objects;
    - maintain a second scene/model state.

Authority
---------
Core/Application state remains authoritative.

The canvas is a graphical projection:

    Core/Application State
             │
             ▼
       CanvasController
             │
       ┌─────┴─────┐
       ▼           ▼
   Renderers   SelectionManager
       │           │
       ▼           ▼
    QGraphicsItems

Tool interaction remains owned by InteractionManager and the
active Tool.

Navigation remains owned by NavigationController.

Selection ownership remains with the application's
Controller.selected_ids and is accessed through
SelectionManager.

Qt Architecture
---------------
All Qt classes must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.canvas.graphics_view import GraphicsView
from ui.core.selection_manager import SelectionManager


class CanvasController:
    """
    UI orchestration controller for the GridForge canvas.

    The class deliberately remains thin. It coordinates existing
    UI services instead of reproducing their responsibilities.

    Parameters
    ----------
    controller:
        Authoritative GridForge application/Core controller.

    selection_manager:
        Optional SelectionManager.

        When omitted, a SelectionManager is created for the
        canvas scene after GraphicsView initialization.

    graphics_view:
        Optional pre-created GraphicsView.

        When omitted, CanvasController creates one.

    parent:
        Optional Qt parent for a newly-created GraphicsView.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        selection_manager: Optional[
            SelectionManager
        ] = None,
        graphics_view: Optional[
            GraphicsView
        ] = None,
        parent: Optional[Any] = None,
    ) -> None:

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        self.controller = controller

        # ----------------------------------------------------
        # Graphics view
        # ----------------------------------------------------

        if graphics_view is None:
            graphics_view = GraphicsView(
                controller,
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
        # Selection
        # ----------------------------------------------------

        if selection_manager is None:
            selection_manager = SelectionManager(
                controller,
                scene=graphics_view.get_scene(),
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

        # ----------------------------------------------------
        # Ensure selection manager observes the canvas scene.
        #
        # This does not alter authoritative selection state.
        # ----------------------------------------------------

        self.selection_manager.set_scene(
            self.graphics_view.get_scene()
        )

        # ----------------------------------------------------
        # Lifecycle state
        # ----------------------------------------------------

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

    # --------------------------------------------------------

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
        Return the canvas QGraphicsScene.
        """

        self._ensure_active()

        return self.graphics_view.get_scene()

    # ========================================================
    # INTERACTION ACCESS
    # ========================================================

    def get_interaction_manager(
        self,
    ) -> Any:
        """
        Return the canvas InteractionManager.

        Tool lifecycle remains owned by InteractionManager.
        """

        self._ensure_active()

        return (
            self.graphics_view
            .get_interaction_manager()
        )

    # ========================================================
    # NAVIGATION ACCESS
    # ========================================================

    def get_navigation_controller(
        self,
    ) -> Any:
        """
        Return the canvas NavigationController.
        """

        self._ensure_active()

        return (
            self.graphics_view
            .get_navigation_controller()
        )

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
    # RENDERING
    # ========================================================

    def render(
        self,
        model: Any,
    ) -> Any:
        """
        Render one authoritative application/Core object.

        Renderer resolution is delegated to RendererRegistry.

        The CanvasController does not contain a concrete
        model-type-to-renderer mapping.
        """

        self._ensure_active()

        if model is None:
            raise ValueError(
                "model must not be None."
            )

        registry = self._get_renderer_registry()

        renderer = self._resolve_renderer(
            registry,
            model,
        )

        return self._render_with_renderer(
            renderer,
            model,
        )

    # --------------------------------------------------------

    def render_all(
        self,
        models: Iterable[Any],
    ) -> tuple[Any, ...]:
        """
        Render a collection of authoritative objects.

        Each object is resolved through RendererRegistry.

        Existing graphical projections are updated by the
        responsible renderer.
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

        return tuple(
            result
        )

    # --------------------------------------------------------

    def remove(
        self,
        object_id: Any,
    ) -> bool:
        """
        Remove the graphical projection of object_id.

        The underlying Core/application object is not removed.

        Renderer resolution is delegated to RendererRegistry.
        """

        self._ensure_active()

        if object_id is None:
            raise ValueError(
                "object_id must not be None."
            )

        registry = self._get_renderer_registry()

        renderer = self._resolve_renderer_for_id(
            registry,
            object_id,
        )

        if renderer is None:
            return False

        remove = getattr(
            renderer,
            "remove",
            None,
        )

        if not callable(remove):
            raise TypeError(
                "renderer must provide remove()."
            )

        return bool(
            remove(
                object_id
            )
        )

    # ========================================================
    # SELECTION SYNCHRONIZATION
    # ========================================================

    def sync_selection(
        self,
    ) -> None:
        """
        Synchronize graphical selection from authoritative
        Controller.selected_ids.
        """

        self._ensure_active()

        self.selection_manager.sync_graphics(
            self.get_scene()
        )

    # --------------------------------------------------------

    def clear_graphical_selection(
        self,
    ) -> None:
        """
        Clear only graphical selection state.

        Authoritative application selection is not modified.
        """

        self._ensure_active()

        self.selection_manager.reset_graphics(
            self.get_scene()
        )

    # ========================================================
    # NAVIGATION
    # ========================================================

    def zoom_in(
        self,
        steps: int = 1,
    ) -> None:
        """
        Request canvas zoom-in through NavigationController.
        """

        self._ensure_active()

        self.graphics_view.zoom_in(
            steps
        )

    # --------------------------------------------------------

    def zoom_out(
        self,
        steps: int = 1,
    ) -> None:
        """
        Request canvas zoom-out through NavigationController.
        """

        self._ensure_active()

        self.graphics_view.zoom_out(
            steps
        )

    # --------------------------------------------------------

    def reset_view(
        self,
    ) -> None:
        """
        Reset canvas navigation.
        """

        self._ensure_active()

        self.graphics_view.reset_view()

    # --------------------------------------------------------

    def fit_content(
        self,
        margin: float = 50.0,
    ) -> None:
        """
        Fit graphical scene content into the viewport.
        """

        self._ensure_active()

        self.graphics_view.fit_content(
            margin
        )

    # --------------------------------------------------------

    def pan_left(
        self,
    ) -> None:
        """
        Pan the canvas left.
        """

        self._ensure_active()

        self.get_navigation_controller().pan_left()

    # --------------------------------------------------------

    def pan_right(
        self,
    ) -> None:
        """
        Pan the canvas right.
        """

        self._ensure_active()

        self.get_navigation_controller().pan_right()

    # --------------------------------------------------------

    def pan_up(
        self,
    ) -> None:
        """
        Pan the canvas upward.
        """

        self._ensure_active()

        self.get_navigation_controller().pan_up()

    # --------------------------------------------------------

    def pan_down(
        self,
    ) -> None:
        """
        Pan the canvas downward.
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

        This operation does not modify Core model state and does
        not clear authoritative application selection.
        """

        self._ensure_active()

        self.graphics_view.reset_canvas()

        self.selection_manager.reset_graphics(
            self.get_scene()
        )

    # ========================================================
    # SCENE REPLACEMENT
    # ========================================================

    def attach_scene(
        self,
        scene: Any,
    ) -> None:
        """
        Attach an externally managed scene to the canvas.

        The GraphicsView remains the viewport owner.

        SelectionManager is updated to observe the new scene.

        Existing graphical items are not migrated automatically.
        """

        self._ensure_active()

        if scene is None:
            raise ValueError(
                "scene must not be None."
            )

        current_scene = (
            self.graphics_view.get_scene()
        )

        if scene is current_scene:
            self.selection_manager.set_scene(
                scene
            )
            return

        self.graphics_view.setScene(
            scene
        )

        self.selection_manager.set_scene(
            scene
        )

    # ========================================================
    # RENDERER REGISTRY
    # ========================================================

    def _get_renderer_registry(
        self,
    ) -> Any:
        """
        Obtain the application's RendererRegistry.

        The registry is application infrastructure and is
        therefore resolved from the authoritative controller.

        Supported controller contracts are:

            controller.renderer_registry

        or:

            controller.get_renderer_registry()
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

        if registry is None:
            raise TypeError(
                "controller must provide "
                "renderer_registry or "
                "get_renderer_registry()."
            )

        return registry

    # ========================================================
    # RENDERER RESOLUTION
    # ========================================================

    @staticmethod
    def _resolve_renderer(
        registry: Any,
        model: Any,
    ) -> Any:
        """
        Resolve the renderer responsible for model.

        The method supports the canonical registry contract while
        remaining independent of concrete renderer classes.
        """

        resolve = getattr(
            registry,
            "resolve",
            None,
        )

        if callable(resolve):
            renderer = resolve(
                model
            )

            if renderer is None:
                raise LookupError(
                    "No renderer registered for "
                    f"model type "
                    f"{type(model).__name__}."
                )

            return renderer

        get_renderer = getattr(
            registry,
            "get_renderer",
            None,
        )

        if callable(get_renderer):
            renderer = get_renderer(
                model
            )

            if renderer is None:
                raise LookupError(
                    "No renderer registered for "
                    f"model type "
                    f"{type(model).__name__}."
                )

            return renderer

        raise TypeError(
            "RendererRegistry must provide "
            "resolve() or get_renderer()."
        )

    # --------------------------------------------------------

    @staticmethod
    def _render_with_renderer(
        renderer: Any,
        model: Any,
    ) -> Any:
        """
        Invoke the renderer's canonical render contract.
        """

        render = getattr(
            renderer,
            "render",
            None,
        )

        if not callable(render):
            raise TypeError(
                "renderer must provide render()."
            )

        return render(
            model
        )

    # --------------------------------------------------------

    @staticmethod
    def _resolve_renderer_for_id(
        registry: Any,
        object_id: Any,
    ) -> Optional[Any]:
        """
        Resolve a renderer for an object identifier when the
        registry provides such a lookup.

        A renderer registry that cannot resolve by ID returns
        None rather than guessing a renderer.
        """

        resolver = getattr(
            registry,
            "resolve_for_id",
            None,
        )

        if callable(resolver):
            return resolver(
                object_id
            )

        get_renderer = getattr(
            registry,
            "get_renderer_for_id",
            None,
        )

        if callable(get_renderer):
            return get_renderer(
                object_id
            )

        # ----------------------------------------------------
        # The controller deliberately does not inspect renderer
        # internals or guess based on object ID.
        # ----------------------------------------------------

        return None

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

        scene = self.get_scene()

        return {
            "disposed": False,
            "scene_item_count": len(
                scene.items()
            ),
            "selection": (
                self.selection_manager.get_state()
            ),
            "graphics_view": (
                self.graphics_view.get_state()
            ),
        }

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose transient canvas infrastructure.

        This does not modify Core/application state.

        The CanvasController does not dispose the authoritative
        application Controller.
        """

        if self._disposed:
            return

        if self.graphics_view is not None:
            self.graphics_view.dispose()

        self._disposed = True

    # ========================================================
    # ACTIVE STATE
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure the canvas controller has not been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "CanvasController has been disposed."
            )

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

        scene = self.get_scene()

        return (
            "CanvasController("
            f"items={len(scene.items())}, "
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
