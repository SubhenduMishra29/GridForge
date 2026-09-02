"""
GridForge V2
===========

File:
    ui/canvas/canvas_composition.py

Purpose:
    Application-owned composition boundary for the Canvas subsystem.

Author:
    Subhendu Mishra

Architectural role:
    Compose existing Canvas services without making Canvas, plugins, or
    Qt graphics items authoritative owners of electrical truth.

This module deliberately does not introduce a second renderer framework.
Existing renderer contracts remain authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ui.canvas.coordinate_system import CoordinateSystem
from ui.canvas.grid_scene import GridScene
from ui.canvas.grid_system import GridSystem
from ui.canvas.graphics_view import GraphicsView
from ui.canvas.interaction_manager import InteractionManager
from ui.canvas.navigation_controller import NavigationController
from ui.canvas.preview_layer import PreviewLayer
from ui.canvas.render_system import RenderSystem
from ui.core.controller import Controller
from ui.core.qt import QWidget
from ui.core.renderer_registry import RendererRegistry
from ui.core.selection_manager import SelectionManager
from ui.core.snap_system import SnapSystem
from ui.core.tool_manager import ToolManager


@dataclass(frozen=True)
class CanvasComposition:
    """Fully composed Canvas services and their authoritative viewport."""

    view: GraphicsView
    scene: GridScene
    selection_manager: SelectionManager
    renderer_registry: RendererRegistry
    render_system: RenderSystem
    grid_system: GridSystem
    interaction_manager: InteractionManager
    navigation_controller: NavigationController
    coordinate_system: CoordinateSystem
    snap_system: SnapSystem
    preview_layer: PreviewLayer

    @property
    def widget(self) -> QWidget:
        """Return the composed Canvas widget."""
        return self.view


class CanvasComposer:
    """Application-level constructor for the existing Canvas services."""

    def compose(
        self,
        *,
        controller: Controller,
        tool_manager: ToolManager,
        parent: Optional[QWidget] = None,
    ) -> CanvasComposition:
        """Construct and wire one complete Canvas service graph."""
        if controller is None:
            raise ValueError("controller must not be None.")
        if tool_manager is None:
            raise ValueError("tool_manager must not be None.")

        selection_manager = SelectionManager(controller=controller)
        renderer_registry = RendererRegistry()
        grid_system = GridSystem()
        scene = GridScene()

        # GraphicsView is initially a viewport shell. Services requiring
        # the actual view are composed immediately afterward and then bound
        # through the explicit Canvas composition seam.
        view = GraphicsView(
            controller=controller,
            tool_manager=tool_manager,
            scene=scene,
            parent=parent,
        )

        coordinate_system = CoordinateSystem(
            view=view,
            grid_system=grid_system,
        )
        snap_system = SnapSystem(
            controller=controller,
            grid_system=grid_system,
            scene=scene,
        )
        preview_layer = PreviewLayer(scene=scene)
        interaction_manager = InteractionManager(
            view=view,
            controller=controller,
            tool_manager=tool_manager,
            coordinate_system=coordinate_system,
            snap_system=snap_system,
            preview_layer=preview_layer,
            selection_manager=selection_manager,
        )
        navigation_controller = NavigationController(view=view)

        view.bind_services(
            interaction_manager=interaction_manager,
            navigation_controller=navigation_controller,
        )

        render_system = RenderSystem(
            scene=scene,
            controller=controller,
            renderer_registry=renderer_registry,
            grid_system=grid_system,
            selection_manager=selection_manager,
        )

        selection_manager.set_scene(scene)

        return CanvasComposition(
            view=view,
            scene=scene,
            selection_manager=selection_manager,
            renderer_registry=renderer_registry,
            render_system=render_system,
            grid_system=grid_system,
            interaction_manager=interaction_manager,
            navigation_controller=navigation_controller,
            coordinate_system=coordinate_system,
            snap_system=snap_system,
            preview_layer=preview_layer,
        )


__all__ = ["CanvasComposition", "CanvasComposer"]
