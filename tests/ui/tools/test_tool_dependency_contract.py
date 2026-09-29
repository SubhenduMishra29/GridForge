# ============================================================
# File: tests/ui/tools/test_tool_dependency_contract.py
# GridForge V2 — Tool Dependency Contract Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import inspect

from ui.core.tool_manager import ToolManager
from ui.canvas.grid_scene import GridScene
from ui.canvas.preview_layer import PreviewLayer
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.equipment.symbol.built_in_symbol_catalogue import register_builtin_symbols
from ui.tools.breaker_tool import BreakerTool
from ui.tools.bus_tool import BusTool
from ui.tools.default_tool_registry import create_default_tool_factories
from ui.tools.transformer_tool import TransformerTool


class FakeController:
    pass


class FakeApplication:
    pass


class FakeSelectionManager:
    pass


class FakeSnapSystem:
    pass


def _dependencies(qapp):
    symbols = SymbolRegistry()
    register_builtin_symbols(symbols)
    return {
        "controller": FakeController(),
        "application": FakeApplication(),
        "selection_manager": FakeSelectionManager(),
        "snap_system": FakeSnapSystem(),
        "preview_layer": PreviewLayer(scene=GridScene()),
        "symbol_registry": symbols,
        "equipment_registry": EquipmentRegistry.create_default(),
    }


def test_default_registry_uses_application_not_command_manager():
    signature = inspect.signature(create_default_tool_factories)
    assert "application" in signature.parameters
    assert "command_manager" not in signature.parameters


def test_default_bus_factory_constructs_with_application(qapp):
    dependencies = _dependencies(qapp)
    factories = create_default_tool_factories(controller=dependencies["controller"], application=dependencies["application"], selection_manager=dependencies["selection_manager"], snap_system=dependencies["snap_system"], preview_layer=dependencies["preview_layer"], symbol_registry=dependencies["symbol_registry"])

    tool = factories["bus"]()
    assert isinstance(tool, BusTool)
    assert tool.application is dependencies["application"]


def test_default_factories_construct_model_placement_tools_without_command_manager(qapp):
    dependencies = _dependencies(qapp)
    factories = create_default_tool_factories(controller=dependencies["controller"], application=dependencies["application"], selection_manager=dependencies["selection_manager"], snap_system=dependencies["snap_system"], preview_layer=dependencies["preview_layer"], symbol_registry=dependencies["symbol_registry"])

    transformer = factories["transformer"]()
    breaker = factories["breaker"]()

    assert isinstance(transformer, TransformerTool)
    assert isinstance(breaker, BreakerTool)
    assert transformer.application is dependencies["application"]
    assert transformer.controller is dependencies["controller"]
    assert transformer.selection_manager is dependencies["selection_manager"]
    assert transformer.snap_system is dependencies["snap_system"]
    assert breaker.application is dependencies["application"]
    assert breaker.controller is dependencies["controller"]
    assert breaker.selection_manager is dependencies["selection_manager"]
    assert breaker.snap_system is dependencies["snap_system"]
    assert "command_manager" not in transformer.get_state()
    assert "command_manager" not in breaker.get_state()


def test_tool_manager_constructs_registered_tool_with_application(qapp):
    dependencies = _dependencies(qapp)
    manager = ToolManager(controller=dependencies["controller"], application=dependencies["application"], selection_manager=dependencies["selection_manager"], snap_system=dependencies["snap_system"], preview_layer=dependencies["preview_layer"], equipment_registry=dependencies["equipment_registry"])

    created = []

    def factory(**dependencies):
        created.append(dependencies)
        return type("Tool", (), {"activate": lambda self, **kwargs: None, "deactivate": lambda self: None, "dispose": lambda self: None})()

    manager.register_tool("test", factory)
    manager.activate("test")

    assert len(created) == 1
    assert created[0]["controller"] is manager.controller
    assert created[0]["application"] is manager.application
    assert created[0]["selection_manager"] is manager.selection_manager
    assert created[0]["snap_system"] is manager.snap_system
