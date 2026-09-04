"""GridForge V2 application/bootstrap Canvas composition tests."""

import inspect

from main import build_application


def test_application_bootstrap_hands_canvas_composition_to_plugin() -> None:
    source = inspect.getsource(build_application)
    assert "CanvasComposer" in source
    assert "canvas_composition" in source
    assert "set_composition" in source
    assert source.index("CanvasComposer") < source.index("initialize_all")
    assert source.index("set_composition") < source.index("initialize_all")


def test_application_bootstrap_injects_render_system_for_composed_canvas_scene() -> None:
    source = inspect.getsource(build_application)
    assert "SLDCanvasRenderSystem" in source
    assert "canvas_composition.scene" in source
    assert "sld_canvas_render_system" in source
    assert source.index("SLDCanvasRenderSystem") < source.index("initialize_all")


def test_canvas_composition_requires_and_forwards_ui_command_manager() -> None:
    from ui.canvas.canvas_composition import CanvasComposer

    signature = inspect.signature(CanvasComposer.compose)
    assert "command_manager" in signature.parameters
    source = inspect.getsource(CanvasComposer.compose)
    assert "command_manager=command_manager" in source
    assert "command_manager=None" not in source


def test_application_bootstrap_creates_one_ui_command_facade_for_canvas_tools() -> None:
    source = inspect.getsource(build_application)
    assert "UICommandManager" in source
    assert "command_manager = UICommandManager" in source
    assert "command_manager=command_manager" in source


def test_canvas_composition_does_not_construct_legacy_renderer_stack() -> None:
    from ui.canvas.canvas_composition import CanvasComposer

    source = inspect.getsource(CanvasComposer.compose)
    assert "RenderSystem" not in source
    assert "RendererRegistry" not in source


def test_default_tool_factories_do_not_depend_on_legacy_renderer_registry() -> None:
    from ui.tools.default_tool_registry import create_default_tool_factories

    signature = inspect.signature(create_default_tool_factories)
    assert "renderer_registry" not in signature.parameters


def test_tool_base_has_no_legacy_renderer_registry_contract() -> None:
    from ui.tools.tool_base import ToolBase

    signature = inspect.signature(ToolBase.__init__)
    assert "renderer_registry" not in signature.parameters
    assert not hasattr(ToolBase, "get_renderer_registry")
