# ============================================================
# File: ui/canvas/canvas_composition.py
# GridForge V2 — Canvas Composition
# ============================================================
"""GridForge V2 application-owned Canvas composition boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ui.canvas.coordinate_system import CoordinateSystem
from ui.canvas.grid_scene import GridScene
from ui.canvas.grid_system import GridSystem
from ui.canvas.graphics_view import GraphicsView
from ui.canvas.interaction_manager import InteractionManager
from ui.canvas.mouse_event_adapter import MouseEventAdapter
from ui.canvas.navigation_controller import NavigationController
from ui.canvas.preview_layer import PreviewLayer
from ui.core.controller import Controller
from ui.core.qt import QWidget
from ui.core.selection_manager import SelectionManager
from ui.core.snap_system import SnapSystem
from ui.core.tool_manager import ToolManager
from ui.projection.selection_projection_coordinator import SelectionProjectionCoordinator
from ui.tools.default_tool_registry import create_default_tool_factories


@dataclass(frozen=True)
class CanvasCompositionPreparation:
    """Canvas services that must exist before ToolManager construction."""

    selection_manager: SelectionManager
    grid_system: GridSystem
    scene: GridScene
    snap_system: SnapSystem


@dataclass
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
    application: Any
    selection_projection: SelectionProjectionCoordinator | None = None

    @property
    def widget(self) -> QWidget:
        return self.view


class CanvasComposer:
    """Application-level constructor for the Canvas service graph."""

    def prepare(self, *, controller: Controller) -> CanvasCompositionPreparation:
        """Create the shared Canvas interaction dependencies."""
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
        preparation: CanvasCompositionPreparation,
        parent: Optional[QWidget] = None,
        properties_panel: Any = None,
    ) -> CanvasComposition:
        """Construct one complete Canvas service graph.

        The selection projection is intentionally deferred when the real
        PropertiesPanel presentation has not yet been composed. The normal
        application composition binds it before the Canvas is considered
        fully wired, so a coordinator is never constructed with a missing
        PropertiesPanel dependency.
        """
        if controller is None:
            raise ValueError("controller must not be None.")
        if tool_manager is None:
            raise ValueError("tool_manager must not be None.")
        if not isinstance(preparation, CanvasCompositionPreparation):
            raise TypeError("preparation must be CanvasCompositionPreparation.")

        application = tool_manager.application
        if application is None:
            raise ValueError("tool_manager must retain the canonical Application.")

        selection_manager = preparation.selection_manager
        grid_system = preparation.grid_system
        scene = preparation.scene
        snap_system = preparation.snap_system

        if tool_manager.selection_manager is not selection_manager:
            raise ValueError("ToolManager must use the prepared SelectionManager.")
        if tool_manager.snap_system is not snap_system:
            raise ValueError("ToolManager must use the prepared SnapSystem.")

        view = GraphicsView(
            controller=controller,
            tool_manager=tool_manager,
            scene=scene,
            parent=parent,
        )
        coordinate_system = CoordinateSystem(view=view, grid_system=grid_system)
        preview_layer = PreviewLayer(scene=scene)
        input_adapter = MouseEventAdapter(view=view, scene=scene)
        interaction_manager = InteractionManager(
            view=view,
            controller=controller,
            tool_manager=tool_manager,
            coordinate_system=coordinate_system,
            snap_system=snap_system,
            preview_layer=preview_layer,
            selection_manager=selection_manager,
            input_adapter=input_adapter,
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
                application=application,
                selection_manager=selection_manager,
                snap_system=snap_system,
            )
        )

        selection_projection = None
        if properties_panel is not None:
            selection_projection = SelectionProjectionCoordinator(
                selection_manager=selection_manager,
                application=application,
                properties_panel=properties_panel,
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
            application=application,
            selection_projection=selection_projection,
        )

    def bind_selection_projection(
        self,
        *,
        composition: CanvasComposition,
        properties_panel: Any,
    ) -> SelectionProjectionCoordinator:
        """Bind the real PropertiesPanel after panel plugin composition."""
        if not isinstance(composition, CanvasComposition):
            raise TypeError("composition must be CanvasComposition.")
        if properties_panel is None:
            raise ValueError("properties_panel must not be None.")
        if composition.selection_projection is not None:
            raise RuntimeError("Canvas selection projection is already bound.")

        coordinator = SelectionProjectionCoordinator(
            selection_manager=composition.selection_manager,
            application=composition.application,
            properties_panel=properties_panel,
        )
        composition.selection_projection = coordinator
        return coordinator


__all__ = [
    "CanvasCompositionPreparation",
    "CanvasComposition",
    "CanvasComposer",
]
