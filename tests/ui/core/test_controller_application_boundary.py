# ============================================================
# File: tests/ui/core/test_controller_application_boundary.py
# GridForge V2 — Controller/Application Boundary Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import pytest

from ui.core.controller import Controller


class FakeApplication:
    def __init__(self) -> None:
        self.executed = []
        self.undo_calls = 0
        self.redo_calls = 0

    def execute(self, command):
        self.executed.append(command)
        return "executed"

    def undo(self):
        self.undo_calls += 1
        return "undo"

    def redo(self):
        self.redo_calls += 1
        return "redo"

    def can_undo(self):
        return self.undo_calls == 0

    def can_redo(self):
        return self.redo_calls == 0


def test_controller_has_no_core_dependency_or_accessor():
    controller = Controller(application=FakeApplication())

    try:
        assert not hasattr(controller, "core")
        assert not hasattr(controller, "get_core")
        assert not hasattr(controller, "set_core")
        assert not hasattr(controller, "_core")
    finally:
        controller.dispose()


def test_controller_delegates_command_execution_to_application():
    application = FakeApplication()
    controller = Controller(application=application)

    try:
        assert controller.execute_command("command") == "executed"
        assert application.executed == ["command"]
    finally:
        controller.dispose()


def test_controller_delegates_undo_and_redo_to_application():
    application = FakeApplication()
    controller = Controller(application=application)

    try:
        assert controller.undo() == "undo"
        assert controller.redo() == "redo"
        assert application.undo_calls == 1
        assert application.redo_calls == 1
    finally:
        controller.dispose()


def test_controller_requires_application_for_mutation_delegation():
    controller = Controller()

    try:
        with pytest.raises(RuntimeError):
            controller.execute_command("command")
        with pytest.raises(RuntimeError):
            controller.undo()
        with pytest.raises(RuntimeError):
            controller.redo()
    finally:
        controller.dispose()
