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
from ui.canvas.grid_system import GridSystem
from ui.canvas.graphics_view import GraphicsView
from ui.canvas.interaction_manager import InteractionManager
from ui.canvas.navigation_controller import NavigationController
from ui.canvas.preview_layer import PreviewLayer
from ui.core.qt import QWidget
from ui.core.selection_manager import SelectionManager
from ui.core.snap_system import SnapSystem
from ui.core.controller import Controller
from ui.core.renderer_registry import RendererRegistry
from ui.canvas.render_system import RenderSystem
from ui.core.tool_manager import ToolManager


@dataclass(frozen=True)
class CanvasComposition:
    """Fully composed Canvas services and their authoritative viewport."""

    view: GraphicsView
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

    @property
    def scene(self):
        """Return the scene exposed by the authoritative Canvas view."""

        scene = self.view.scene()
        if scene is None:
            raise RuntimeError("Canvas view does not currently have a scene.")
        return scene


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

        selection_manager = SelectionManager(controller=controller)
        renderer_registry = RendererRegistry()
        grid_system = GridSystem()
        coordinate_system = CoordinateSystem()
        snap_system = SnapSystem(
            coordinate_system=coordinate_system,
            grid_system=grid_system,
        )
        preview_layer = PreviewLayer()

        view = GraphicsView(
            controller=controller,
            tool_manager=tool_manager,
            parent=parent,
        )
        scene = view.scene()
        if scene is None:
            raise RuntimeError("GraphicsView did not create a scene.")

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
        render_system = RenderSystem(
            renderer_registry=renderer_registry,
            scene=scene,
            controller=controller,
            grid_system=grid_system,
            selection_manager=selection_manager,
        )

        selection_manager.set_scene(scene)
        render_system.set_scene(scene)

        # The view currently creates these two services internally. Keep the
        # explicit composition references here until GraphicsView is migrated
        # to pure dependency injection in a later, separately verified step.
        return CanvasComposition(
            view=view,
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
