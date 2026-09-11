# ============================================================
# File: tests/ui/tools/test_tool_dependency_contract.py
# GridForge V2 — Tool Dependency Contract Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import inspect

from ui.core.tool_manager import ToolManager
from ui.tools.bus_tool import BusTool
from ui.tools.default_tool_registry import create_default_tool_factories


class FakeController:
    pass


class FakeApplication:
    pass


class FakeSelectionManager:
    pass


class FakeSnapSystem:
    pass


def test_default_registry_uses_application_not_command_manager():
    signature = inspect.signature(create_default_tool_factories)
    assert "application" in signature.parameters
    assert "command_manager" not in signature.parameters


def test_default_bus_factory_constructs_with_application():
    factories = create_default_tool_factories(
        controller=FakeController(),
        application=FakeApplication(),
        selection_manager=FakeSelectionManager(),
        snap_system=FakeSnapSystem(),
    )

    tool = factories["bus"]()
    assert isinstance(tool, BusTool)
    assert tool.application.__class__ is FakeApplication


def test_tool_manager_constructs_registered_tool_with_application():
    application = FakeApplication()
    controller = FakeController()
    manager = ToolManager(
        controller=controller,
        application=application,
        selection_manager=FakeSelectionManager(),
        snap_system=FakeSnapSystem(),
    )

    created = []

    def factory(**dependencies):
        created.append(dependencies)
        return object()

    manager.register_tool("test", factory)
    manager.activate("test")

    assert created == [
        {
            "controller": controller,
            "application": application,
            "selection_manager": manager.selection_manager,
            "snap_system": manager.snap_system,
        }
    ]
