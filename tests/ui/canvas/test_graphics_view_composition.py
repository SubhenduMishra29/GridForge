"""
GridForge V2
============

File:
    tests/ui/canvas/test_graphics_view_composition.py

Purpose:
    Define the Canvas viewport dependency-injection contract.

Author:
    Subhendu Mishra
"""

import inspect

from ui.canvas.graphics_view import GraphicsView


def test_graphics_view_accepts_composed_canvas_services() -> None:
    """GraphicsView must consume, not construct, Canvas services."""
    parameters = inspect.signature(GraphicsView.__init__).parameters

    assert "scene" in parameters
    assert "interaction_manager" in parameters
    assert "navigation_controller" in parameters
