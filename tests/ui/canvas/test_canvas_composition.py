"""
GridForge V2
============

File:
    tests/ui/canvas/test_canvas_composition.py

Purpose:
    Define the Canvas composition ownership contract.

Author:
    Subhendu Mishra
"""

from ui.canvas.canvas_composition import CanvasComposer
from ui.canvas.grid_scene import GridScene
from ui.core.controller import Controller
from ui.core.tool_manager import ToolManager


def test_canvas_composer_uses_one_shared_scene_and_service_instances() -> None:
    """CanvasComposer must compose services once and share the Canvas scene."""
    controller = Controller()
    tool_manager = ToolManager(controller=controller)

    composition = CanvasComposer().compose(
        controller=controller,
        tool_manager=tool_manager,
    )

    assert isinstance(composition.scene, GridScene)
    assert composition.view.scene() is composition.scene
    assert composition.render_system.scene is composition.scene
    assert composition.selection_manager.scene is composition.scene
    assert composition.interaction_manager.view is composition.view
    assert composition.navigation_controller.view is composition.view
    assert composition.coordinate_system.view is composition.view
    assert composition.snap_system.scene is composition.scene
