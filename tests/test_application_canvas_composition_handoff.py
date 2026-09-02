"""
GridForge V2
===========

File:
    tests/test_application_canvas_composition_handoff.py

Purpose:
    Define the application-bootstrap ownership contract for the Canvas
    composition handoff and enforce the unified SLD rendering boundary.

Author:
    Subhendu Mishra
"""

import inspect

from main import build_application


def test_application_bootstrap_hands_canvas_composition_to_plugin() -> None:
    """Bootstrap must compose Canvas before CanvasPlugin initialization."""
    source = inspect.getsource(build_application)

    assert "CanvasComposer" in source
    assert "canvas_composition" in source
    assert "set_composition" in source
    assert source.index("CanvasComposer") < source.index("initialize_all")
    assert source.index("set_composition") < source.index("initialize_all")


def test_canvas_composition_does_not_construct_legacy_renderer_stack() -> None:
    """Application composition must not activate the legacy renderer path."""
    from ui.canvas.canvas_composition import CanvasComposer

    source = inspect.getsource(CanvasComposer.compose)

    assert "RenderSystem" not in source
    assert "RendererRegistry" not in source


def test_default_tool_factories_do_not_depend_on_legacy_renderer_registry() -> None:
    """Tool construction must not require the retired renderer registry."""
    from ui.tools.default_tool_registry import create_default_tool_factories

    signature = inspect.signature(create_default_tool_factories)
    assert "renderer_registry" not in signature.parameters
