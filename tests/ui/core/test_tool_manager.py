# ============================================================
# File: tests/ui/core/test_tool_manager.py
# GridForge V2 — ToolManager Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import pytest

from ui.core.tool_manager import ToolManager


class Tool:
    def __init__(self, **dependencies):
        self.dependencies = dependencies
        self.active = False
        self.disposed = False

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def cancel(self):
        return True

    def reset(self):
        pass

    def dispose(self):
        self.disposed = True


@pytest.fixture
def dependencies():
    return {
        "controller": object(),
        "application": object(),
        "selection_manager": object(),
        "snap_system": object(),
    }


def test_requires_canonical_application_dependencies(dependencies):
    manager = ToolManager(**dependencies)
    assert manager.application is dependencies["application"]
    assert manager.selection_manager is dependencies["selection_manager"]
    assert manager.snap_system is dependencies["snap_system"]


def test_rejects_missing_application(dependencies):
    dependencies.pop("application")
    with pytest.raises(TypeError):
        ToolManager(**dependencies)


def test_rejects_obsolete_command_manager_keyword(dependencies):
    dependencies["command_manager"] = object()
    with pytest.raises(TypeError):
        ToolManager(**dependencies)


def test_registered_tool_receives_one_canonical_dependency_contract(dependencies):
    manager = ToolManager(**dependencies)
    created = []

    def factory(**kwargs):
        created.append(kwargs)
        return Tool(**kwargs)

    manager.register_tool("test", factory)
    manager.activate("test")

    assert created == [dependencies]
    assert manager.get_current_tool().active is True


def test_failed_activation_restores_previous_tool(dependencies):
    manager = ToolManager(**dependencies)
    first = Tool()

    class FailingTool(Tool):
        def activate(self):
            raise RuntimeError("activation failure")

    manager.register_tool("first", lambda **_: first)
    manager.register_tool("second", lambda **_: FailingTool())
    manager.activate("first")

    with pytest.raises(RuntimeError, match="activation failure"):
        manager.activate("second")

    assert manager.get_current_tool() is first
    assert manager.get_current_tool_id() == "first"
    assert first.active is True


def test_manager_owns_tool_lifecycle(dependencies):
    manager = ToolManager(**dependencies)
    tool = Tool()
    manager.register_tool("test", lambda **_: tool)
    manager.activate("test")
    manager.dispose()

    assert tool.disposed is True
