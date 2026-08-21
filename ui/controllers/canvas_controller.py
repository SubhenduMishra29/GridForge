# ============================================================
# File: ui/controllers/canvas_controller.py
# GridForge V2 — Canvas Controller
# ============================================================
"""
Canvas Controller for GridForge V2.

CanvasController is the orchestration boundary for the SLD
canvas. It coordinates existing canvas services without
duplicating their responsibilities.

Architecture
------------

    Application Controller
             │
             ▼
      CanvasController
             │
       ┌─────┼───────────────┐
       ▼     ▼               ▼
   GraphicsView        RenderSystem
       │                   │
       ├── Interaction     ├── RendererRegistry
       │                   ├── Renderers
       └── Navigation      └── Graphics Items
             │
             ▼
      SelectionManager
             │
             ▼
    Controller.selected_ids

Responsibilities
----------------
CanvasController:

    - compose the canvas services;
    - expose GraphicsView;
    - expose the canvas scene;
    - expose InteractionManager;
    - expose NavigationController;
    - expose SelectionManager;
    - expose RenderSystem;
    - delegate rendering;
    - delegate graphical removal;
    - delegate navigation;
    - synchronize graphical selection;
    - reset transient canvas state;
    - provide diagnostics;
    - manage its own lifecycle.

CanvasController does NOT:

    - own Core model state;
    - modify Core model objects;
    - implement rendering;
    - resolve renderers directly;
    - implement navigation;
    - implement interaction;
    - implement tools;
    - own ToolManager lifecycle;
    - implement selection ownership;
    - perform snapping;
    - validate electrical topology;
    - perform electrical calculations;
    - create domain objects.

Authority
---------
Application/Core state remains authoritative.

The canvas is a graphical projection of that state.

Rendering is delegated to RenderSystem.

Selection authority remains Controller.selected_ids.

Navigation mechanics remain owned by NavigationController.

Interaction mechanics remain owned by InteractionManager.

Qt Architecture
---------------
Qt classes are obtained through the existing canvas/core
boundaries. CanvasController itself does not import PySide6
or PyQt directly.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.canvas.graphics_view import GraphicsView
from ui.canvas.render_system import RenderSystem
from ui.core.selection_manager import SelectionManager


class CanvasController:
    """
    Thin orchestration controller for the GridForge SLD canvas.
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
        """
        Initialize the canvas controller.

        Parameters
        ----------
        controller:
            Authoritative application/UI controller.

        tool_manager:
            Existing application-owned ToolManager.

        selection_manager:
            Optional SelectionManager. When omitted, one is
            created for the canvas scene.

        graphics_view:
            Optional pre-created GraphicsView.

        render_system:
            Optional pre-created RenderSystem.

        renderer_registry:
            RendererRegistry used when RenderSystem must be
            created by CanvasController.

        grid_system:
            Optional GridSystem passed to RenderSystem.

        parent:
            Optional parent for a newly-created GraphicsView.
        """

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
        # GraphicsView
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

        # GraphicsView owns this scene.
        scene = graphics_view.graphics_scene

        if scene is None:
            raise RuntimeError(
                "GraphicsView must provide a graphics_scene."
            )

        self.scene = scene

        # ----------------------------------------------------
        # SelectionManager
        # ----------------------------------------------------

        if selection_manager is None:
            selection_manager = SelectionManager(
                controller=controller,
                scene=scene,
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
            scene
        )

        # ----------------------------------------------------
        # RenderSystem
        # ----------------------------------------------------

        if render_system is None:

            if renderer_registry is None:
                renderer_registry = (
                    self._get_renderer_registry()
                )

            if renderer_registry is None:
                raise ValueError(
                    "renderer_registry must be provided "
                    "when render_system is not supplied."
                )

            render_system = RenderSystem(
                scene=scene,
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

        self.render_system.set_selection_manager(
            self.selection_manager
        )

        self._disposed = False

    # ========================================================
    # STATE
    # ========================================================

    @property
    def disposed(
        self,
    ) -> bool:
        """
        Return whether the CanvasController has been disposed.
        """

        return self._disposed

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
        Return the authoritative GraphicsView scene.
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
        Return GraphicsView's InteractionManager.
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
        Return GraphicsView's NavigationController.
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

        Renderer lookup and graphics-item creation remain
        entirely inside RenderSystem.
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
        """

        self._ensure_active()

        if models is None:
            raise ValueError(
                "models must not be None."
            )

        result: list[tuple[Any, ...]] = []

        for model in models:
            result.append(
                self.render(
                    model
                )
            )

        self.render_system.sync_selection()

        return tuple(result)

    # --------------------------------------------------------

    def refresh(
        self,
        models: Optional[
            Iterable[Any]
        ] = None,
    ) -> None:
        """
        Rebuild the complete canvas projection.

        RenderSystem owns the actual refresh operation.
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
        Remove the graphical projection of an authoritative
        model element.

        This does not remove the application/Core object.
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
    # SELECTION
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

        Controller.selected_ids is untouched.
        """

        self._ensure_active()

        self.selection_manager.reset_graphics(
            scene=self.scene
        )

    # --------------------------------------------------------

    def clear_selection(
        self,
    ) -> None:
        """
        Clear authoritative application selection through
        SelectionManager.

        This is intentionally separate from
        clear_graphical_selection().
        """

        self._ensure_active()

        self.selection_manager.clear()

        self.selection_manager.sync_graphics(
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
        Reset the viewport transform and navigation state.
        """

        self._ensure_active()

        self.get_navigation_controller().reset_view()

    # --------------------------------------------------------

    def fit_content(
        self,
        margin: float = 50.0,
    ) -> None:
        """
        Fit canvas content into the viewport.
        """

        self._ensure_active()

        self.get_navigation_controller().fit_content(
            margin
        )

    # --------------------------------------------------------

    def get_zoom_level(
        self,
    ) -> float:
        """
        Return the current navigation zoom level.
        """

        self._ensure_active()

        return self.get_navigation_controller().get_zoom_level()

    # --------------------------------------------------------

    def set_zoom_level(
        self,
        level: float,
    ) -> None:
        """
        Set the navigation zoom level.
        """

        self._ensure_active()

        self.get_navigation_controller().set_zoom_level(
            level
        )

    # --------------------------------------------------------

    def get_transform(
        self,
    ) -> Any:
        """
        Return the current viewport transform.
        """

        self._ensure_active()

        return self.get_navigation_controller().get_transform()

    # --------------------------------------------------------

    def set_transform(
        self,
        transform: Any,
    ) -> None:
        """
        Set the viewport transform through
        NavigationController.
        """

        self._ensure_active()

        self.get_navigation_controller().set_transform(
            transform
        )

    # --------------------------------------------------------

    def handle_wheel(
        self,
        event: Any,
    ) -> bool:
        """
        Delegate wheel navigation to NavigationController.
        """

        self._ensure_active()

        return self.get_navigation_controller().handle_wheel(
            event
        )

    # ========================================================
    # CANVAS RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset transient canvas state.

        This clears graphical projections and graphical
        selection only. It does not modify Core/application
        model state or authoritative selection.
        """

        self._ensure_active()

        self.render_system.clear()

        self.selection_manager.reset_graphics(
            scene=self.scene
        )

        self.get_navigation_controller().reset_view()

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot.

        No authoritative application state is duplicated.
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
            "render_system": (
                self._get_service_state(
                    self.render_system
                )
            ),
            "navigation": (
                self._get_service_state(
                    self.get_navigation_controller()
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
        Dispose CanvasController-owned canvas state.

        Controller and ToolManager remain application-owned and
        are therefore not disposed here.
        """

        if self._disposed:
            return

        self.render_system.clear()

        self._disposed = True

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Raise if the controller has been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "CanvasController has been disposed."
            )

    # --------------------------------------------------------

    def _get_renderer_registry(
        self,
    ) -> Any:
        """
        Resolve the application's RendererRegistry.

        This is composition-time dependency discovery only.

        CanvasController never uses RendererRegistry directly
        for model rendering.
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
            return getter()

        return None

    # --------------------------------------------------------

    @staticmethod
    def _get_service_state(
        service: Any,
    ) -> dict[str, Any]:
        """
        Obtain optional diagnostics from a canvas service.
        """

        getter = getattr(
            service,
            "get_state",
            None,
        )

        if callable(getter):
            state = getter()

            if isinstance(
                state,
                dict,
            ):
                return state

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
            f"scene_items={len(self.scene.items())}, "
            f"selected={len(self.selection_manager.selected_ids)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "CanvasController",
]
