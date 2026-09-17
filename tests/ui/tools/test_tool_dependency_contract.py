# ============================================================
# File: tests/ui/tools/test_tool_dependency_contract.py
# GridForge V2 — Tool Dependency Contract Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import inspect

from ui.core.tool_manager import ToolManager
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


def _dependencies():
    return {
        "controller": FakeController(),
        "application": FakeApplication(),
        "selection_manager": FakeSelectionManager(),
        "snap_system": FakeSnapSystem(),
    }


def test_default_registry_uses_application_not_command_manager():
    signature = inspect.signature(create_default_tool_factories)
    assert "application" in signature.parameters
    assert "command_manager" not in signature.parameters


def test_default_bus_factory_constructs_with_application():
    dependencies = _dependencies()
    factories = create_default_tool_factories(**dependencies)

    tool = factories["bus"]()
    assert isinstance(tool, BusTool)
    assert tool.application is dependencies["application"]


def test_default_factories_construct_model_placement_tools_without_command_manager():
    dependencies = _dependencies()
    factories = create_default_tool_factories(**dependencies)

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
    assert transformer.get_state()["has_command_manager"] is False
    assert breaker.get_state()["has_command_manager"] is False


def test_tool_manager_constructs_registered_tool_with_application():
    dependencies = _dependencies()
    manager = ToolManager(**dependencies)

    created = []

    def factory(**dependencies):
        created.append(dependencies)
        return object()

    manager.register_tool("test", factory)
    manager.activate("test")

    assert created == [
        {
            "controller": manager.controller,
            "application": manager.application,
            "selection_manager": manager.selection_manager,
            "snap_system": manager.snap_system,
        }
    ]
