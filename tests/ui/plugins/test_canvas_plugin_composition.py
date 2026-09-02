"""
GridForge V2
===========

File:
    tests/ui/plugins/test_canvas_plugin_composition.py

Purpose:
    Define the CanvasPlugin boundary for consuming an application-composed
    CanvasComposition without constructing Canvas services itself.

Author:
    Subhendu Mishra
"""

from unittest.mock import MagicMock

from ui.canvas.canvas_composition import CanvasComposition
from ui.plugins.canvas_plugin import CanvasPlugin


def test_canvas_plugin_accepts_precomposed_canvas() -> None:
    """CanvasPlugin must accept an application-owned CanvasComposition."""
    composition = CanvasComposition(
        view=MagicMock(),
        scene=MagicMock(),
        selection_manager=MagicMock(),
        renderer_registry=MagicMock(),
        render_system=MagicMock(),
        grid_system=MagicMock(),
        interaction_manager=MagicMock(),
        navigation_controller=MagicMock(),
        coordinate_system=MagicMock(),
        snap_system=MagicMock(),
        preview_layer=MagicMock(),
    )

    plugin = CanvasPlugin()

    plugin.set_composition(composition)

    assert plugin.composition is composition
