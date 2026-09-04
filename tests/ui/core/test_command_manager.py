# ============================================================
# File: tests/ui/core/test_command_manager.py
# GridForge V2 — UI Command Manager Tests
# ============================================================

from __future__ import annotations

import inspect

import pytest

from ui.core.command_manager import CommandManager


class FakeApplication:
    def __init__(self) -> None:
        self.executed = []
        self.result = object()

    def execute(self, command):
        self.executed.append(command)
        return self.result


def test_ui_command_manager_forwards_to_application_without_core_access():
    application = FakeApplication()
    manager = CommandManager(application=application)
    command = object()

    assert manager.execute(command) is application.result
    assert application.executed == [command]
    assert manager.get_application() is application


def test_ui_command_manager_does_not_require_controller_or_core_command_manager():
    application = FakeApplication()

    manager = CommandManager(application=application)

    assert not hasattr(manager, "controller")
    source = inspect.getsource(CommandManager)
    assert "core.command_manager" not in source
    assert "Core.command_manager" not in source


def test_ui_command_manager_rejects_missing_application():
    with pytest.raises(ValueError, match="application"):
        CommandManager(application=None)


def test_ui_command_manager_requires_application_execute():
    with pytest.raises(TypeError, match="execute"):
        CommandManager(application=object())
