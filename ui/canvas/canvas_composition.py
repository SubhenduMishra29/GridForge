# ============================================================
# File: ui/canvas/canvas_composition.py
# GridForge V2 — Canvas Composition
# Author: Subhendu Mishra
# ============================================================
"""GridForge V2 application-owned Canvas composition boundary."""

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
from ui.core.controller import Controller
from ui.core.qt import QWidget
from ui.core.selection_manager import SelectionManager
from ui.core.snap_system import SnapSystem
from ui.core.tool_manager import ToolManager
from ui.tools.default_tool_registry import create_default_tool_factories


@dataclass(frozen=True)
class CanvasCompositionPreparation:
    """Canvas services that must exist before ToolManager construction."""

    selection_manager: SelectionManager
    grid_system: GridSystem
    scene: GridScene
    snap_system: SnapSystem


@dataclass(frozen=True)
class CanvasComposition:
    """Fully composed Canvas viewport and interaction services."""

    view: GraphicsView
    scene: GridScene
    selection_manager: SelectionManager
    grid_system: GridSystem
    interaction_manager: InteractionManager
    navigation_controller: NavigationController
    coordinate_system: CoordinateSystem
    snap_system: SnapSystem
    preview_layer: PreviewLayer

    @property
    def widget(self) -> QWidget:
        return self.view


class CanvasComposer:
    """Application-level constructor for the Canvas service graph."""

    def prepare(
        self,
        *,
        controller: Controller,
    ) -> CanvasCompositionPreparation:
        """Create the shared Canvas interaction dependencies.

        ToolManager requires SelectionManager and SnapSystem at construction
        time, while SnapSystem itself depends on the Canvas grid and scene.
        Preparation makes that dependency ordering explicit without creating a
        second Canvas service graph.
        """
        if controller is None:
            raise ValueError("controller must not be None.")

        selection_manager = SelectionManager()
        grid_system = GridSystem()
        scene = GridScene()
        snap_system = SnapSystem(
            controller=controller,
            grid_system=grid_system,
            scene=scene,
        )

        return CanvasCompositionPreparation(
            selection_manager=selection_manager,
            grid_system=grid_system,
            scene=scene,
            snap_system=snap_system,
        )

    def compose(
        self,
        *,
        controller: Controller,
        tool_manager: ToolManager,
        parent: Optional[QWidget] = None,
        preparation: CanvasCompositionPreparation | None = None,
    ) -> CanvasComposition:
        """Construct and wire one complete Canvas service graph."""
        if controller is None:
            raise ValueError("controller must not be None.")
        if tool_manager is None:
            raise ValueError("tool_manager must not be None.")
        if preparation is None:
            preparation = self.prepare(controller=controller)

        selection_manager = preparation.selection_manager
        grid_system = preparation.grid_system
        scene = preparation.scene
        snap_system = preparation.snap_system

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
        selection_manager.set_scene(scene)

        tool_manager.register_tools(
            create_default_tool_factories(
                controller=controller,
                application=tool_manager.application,
                selection_manager=selection_manager,
                snap_system=snap_system,
            )
        )

        return CanvasComposition(
            view=view,
            scene=scene,
            selection_manager=selection_manager,
            grid_system=grid_system,
            interaction_manager=interaction_manager,
            navigation_controller=navigation_controller,
            coordinate_system=coordinate_system,
            snap_system=snap_system,
            preview_layer=preview_layer,
        )


__all__ = [
    "CanvasCompositionPreparation",
    "CanvasComposition",
    "CanvasComposer",
]
