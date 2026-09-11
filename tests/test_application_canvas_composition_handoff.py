"""GridForge V2 application/bootstrap Canvas composition tests."""

import inspect

from main import build_application


def test_application_bootstrap_hands_canvas_composition_to_plugin() -> None:
    source = inspect.getsource(build_application)
    assert "CanvasComposer" in source
    assert "canvas_composer.prepare" in source
    assert "canvas_composition" in source
    assert "set_composition" in source
    assert source.index("CanvasComposer") < source.index("initialize_all")
    assert source.index("set_composition") < source.index("initialize_all")


def test_application_bootstrap_binds_controller_to_canonical_application() -> None:
    source = inspect.getsource(build_application)
    assert "Controller(" in source
    assert "application=gridforge_application" in source
    assert "controller.gridforge_application" not in source


def test_application_bootstrap_constructs_tool_manager_with_canvas_dependencies() -> None:
    source = inspect.getsource(build_application)
    assert "ToolManager(" in source
    assert "application=gridforge_application" in source
    assert "selection_manager=canvas_preparation.selection_manager" in source
    assert "snap_system=canvas_preparation.snap_system" in source


def test_application_bootstrap_uses_current_canvas_composer_contract() -> None:
    from ui.canvas.canvas_composition import CanvasComposer

    signature = inspect.signature(CanvasComposer.compose)
    assert "command_manager" not in signature.parameters
    assert "preparation" in signature.parameters
    source = inspect.getsource(CanvasComposer.compose)
    assert "create_default_tool_factories" in source
    assert "command_manager" not in source


def test_application_bootstrap_has_no_legacy_ui_command_manager_path() -> None:
    source = inspect.getsource(build_application)
    assert "UICommandManager" not in source
    assert "command_manager" not in source


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
