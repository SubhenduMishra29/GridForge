"""
GridForge V2
============

File:
    tests/ui/canvas/test_graphics_view_binding.py

Purpose:
    Define the explicit post-construction Canvas service binding seam.

Author:
    Subhendu Mishra
"""

import inspect

from ui.canvas.graphics_view import GraphicsView


def test_graphics_view_exposes_explicit_service_binding() -> None:
    """GraphicsView must expose a composition-only service binding seam."""
    parameters = inspect.signature(GraphicsView.bind_services).parameters

    assert "interaction_manager" in parameters
    assert "navigation_controller" in parameters


def test_graphics_view_constructor_does_not_require_cyclic_services() -> None:
    """The viewport can be created before view-dependent services exist."""
    parameters = inspect.signature(GraphicsView.__init__).parameters

    assert parameters["interaction_manager"].default is None
    assert parameters["navigation_controller"].default is None
