# ============================================================
# File: ui/controllers/canvas_controller.py
# GridForge V2 — Canvas Controller
# ============================================================
"""
Canvas Controller for GridForge V2.

CanvasController is a legacy presentation orchestration boundary
for the SLD canvas. The active canvas composition is owned by
CanvasComposer; when this compatibility controller is used, it
consumes the UI-Core SelectionManager as the sole selection
authority.

Selection authority
-------------------
SelectionManager owns transient UI selection state.
CanvasController only coordinates graphical projection and does
not read or write Controller selection state.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.canvas.graphics_view import GraphicsView
from ui.canvas.render_system import RenderSystem
from ui.core.selection_manager import SelectionManager


class CanvasController:
    """Thin legacy orchestration controller for the SLD canvas."""

    def __init__(
        self,
        controller: Any,
        tool_manager: Any,
        selection_manager: Optional[SelectionManager] = None,
        graphics_view: Optional[GraphicsView] = None,
        render_system: Optional[RenderSystem] = None,
        renderer_registry: Any = None,
        grid_system: Any = None,
        parent: Optional[Any] = None,
    ) -> None:
        if controller is None:
            raise ValueError("controller must not be None.")
        if tool_manager is None:
            raise ValueError("tool_manager must not be None.")

        self.controller = controller
        self.tool_manager = tool_manager

        if graphics_view is None:
            graphics_view = GraphicsView(
                controller=controller,
                tool_manager=tool_manager,
                parent=parent,
            )
        if not isinstance(graphics_view, GraphicsView):
            raise TypeError("graphics_view must be a GraphicsView.")

        self.graphics_view = graphics_view
        scene = graphics_view.graphics_scene
        if scene is None:
            raise RuntimeError("GraphicsView must provide a graphics_scene.")
        self.scene = scene

        if selection_manager is None:
            selection_manager = SelectionManager(scene=scene)
        if not isinstance(selection_manager, SelectionManager):
            raise TypeError("selection_manager must be a SelectionManager.")

        self.selection_manager = selection_manager
        self.selection_manager.set_scene(scene)

        if render_system is None:
            if renderer_registry is None:
                renderer_registry = self._get_renderer_registry()
            if renderer_registry is None:
                raise ValueError(
                    "renderer_registry must be provided when render_system is not supplied."
                )
            render_system = RenderSystem(
                scene=scene,
                controller=controller,
                renderer_registry=renderer_registry,
                grid_system=grid_system,
                selection_manager=selection_manager,
            )
        if not isinstance(render_system, RenderSystem):
            raise TypeError("render_system must be a RenderSystem.")

        self.render_system = render_system
        self.render_system.set_selection_manager(self.selection_manager)
        self._disposed = False

    @property
    def disposed(self) -> bool:
        return self._disposed

    def get_view(self) -> GraphicsView:
        self._ensure_active()
        return self.graphics_view

    @property
    def view(self) -> GraphicsView:
        return self.get_view()

    def get_scene(self) -> Any:
        self._ensure_active()
        return self.scene

    def get_interaction_manager(self) -> Any:
        self._ensure_active()
        return self.graphics_view.interaction_manager

    def get_navigation_controller(self) -> Any:
        self._ensure_active()
        return self.graphics_view.navigation_controller

    def get_selection_manager(self) -> SelectionManager:
        self._ensure_active()
        return self.selection_manager

    def get_render_system(self) -> RenderSystem:
        self._ensure_active()
        return self.render_system

    def render(self, model: Any) -> tuple[Any, ...]:
        self._ensure_active()
        if model is None:
            raise ValueError("model must not be None.")
        return self.render_system.render_object(model)

    def render_all(self, models: Iterable[Any]) -> tuple[tuple[Any, ...], ...]:
        self._ensure_active()
        if models is None:
            raise ValueError("models must not be None.")
        result = tuple(self.render(model) for model in models)
        self.render_system.sync_selection()
        return result

    def refresh(self, models: Optional[Iterable[Any]] = None) -> None:
        self._ensure_active()
        self.render_system.refresh(models)

    def remove(self, model: Any) -> bool:
        self._ensure_active()
        if model is None:
            raise ValueError("model must not be None.")
        return self.render_system.remove_object(model)

    def sync_selection(self) -> None:
        """Project SelectionManager state onto the canvas graphics."""
        self._ensure_active()
        self.selection_manager.sync_graphics(scene=self.scene)

    def clear_graphical_selection(self) -> None:
        """Clear graphical selection without changing SelectionManager state."""
        self._ensure_active()
        self.selection_manager.reset_graphics(scene=self.scene)

    def clear_selection(self) -> None:
        """Clear authoritative UI selection through SelectionManager."""
        self._ensure_active()
        self.selection_manager.clear()
        self.selection_manager.sync_graphics(scene=self.scene)

    def zoom_in(self, steps: int = 1) -> None:
        self._ensure_active()
        self.get_navigation_controller().zoom_in(steps)

    def zoom_out(self, steps: int = 1) -> None:
        self._ensure_active()
        self.get_navigation_controller().zoom_out(steps)

    def reset_view(self) -> None:
        self._ensure_active()
        self.get_navigation_controller().reset_view()

    def fit_content(self, margin: float = 50.0) -> None:
        self._ensure_active()
        self.get_navigation_controller().fit_content(margin)

    def get_zoom_level(self) -> float:
        self._ensure_active()
        return self.get_navigation_controller().get_zoom_level()

    def set_zoom_level(self, level: float) -> None:
        self._ensure_active()
        self.get_navigation_controller().set_zoom_level(level)

    def get_transform(self) -> Any:
        self._ensure_active()
        return self.get_navigation_controller().get_transform()

    def set_transform(self, transform: Any) -> None:
        self._ensure_active()
        self.get_navigation_controller().set_transform(transform)

    def handle_wheel(self, event: Any) -> bool:
        self._ensure_active()
        return self.get_navigation_controller().handle_wheel(event)

    def reset(self) -> None:
        self._ensure_active()
        self.render_system.clear()
        self.selection_manager.reset_graphics(scene=self.scene)
        self.get_navigation_controller().reset_view()

    def get_state(self) -> dict[str, Any]:
        if self._disposed:
            return {"disposed": True}
        return {
            "disposed": False,
            "scene_item_count": len(self.scene.items()),
            "selection": self.selection_manager.get_state(),
            "render_system": self._get_service_state(self.render_system),
            "navigation": self._get_service_state(self.get_navigation_controller()),
        }

    def dispose(self) -> None:
        if self._disposed:
            return
        self.render_system.clear()
        self._disposed = True

    def _ensure_active(self) -> None:
        if self._disposed:
            raise RuntimeError("CanvasController has been disposed.")

    def _get_renderer_registry(self) -> Any:
        registry = getattr(self.controller, "renderer_registry", None)
        if registry is not None:
            return registry
        getter = getattr(self.controller, "get_renderer_registry", None)
        if callable(getter):
            return getter()
        return None

    @staticmethod
    def _get_service_state(service: Any) -> dict[str, Any]:
        getter = getattr(service, "get_state", None)
        if callable(getter):
            state = getter()
            if isinstance(state, dict):
                return state
        return {"type": type(service).__name__}

    def __repr__(self) -> str:
        if self._disposed:
            return "CanvasController(disposed=True)"
        return (
            "CanvasController("
            f"scene_items={len(self.scene.items())}, "
            f"selected={len(self.selection_manager.selected_ids)}"
            ")"
        )


__all__ = ["CanvasController"]
