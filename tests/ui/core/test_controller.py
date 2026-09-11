# ============================================================
# File: tests/ui/core/test_controller.py
# GridForge V2 — Controller Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from core.application import Application
from ui.core.controller import Controller


def application_double() -> tuple[Application, dict[str, int], list[object]]:
    application = object.__new__(Application)
    counters = {"undo": 0, "redo": 0}
    executed: list[object] = []

    application.execute = lambda command: executed.append(command) or "executed"
    application.undo = lambda: counters.__setitem__("undo", counters["undo"] + 1) or "undo"
    application.redo = lambda: counters.__setitem__("redo", counters["redo"] + 1) or "redo"
    application.can_undo = lambda: True
    application.can_redo = lambda: False
    application.undo_count = lambda: 1
    application.redo_count = lambda: 0
    return application, counters, executed


def test_initial_state_has_application_but_no_core():
    application, _, _ = application_double()
    controller = Controller(application=application)

    try:
        assert controller.get_application() is application
        assert not hasattr(controller, "core")
        assert not hasattr(controller, "get_core")
        assert not hasattr(controller, "set_core")
        assert not hasattr(controller, "_core")
    finally:
        controller.dispose()


def test_tool_selection_is_ui_state():
    controller = Controller()
    events = []
    controller.subscribe("tool_changed", lambda new, old: events.append((new, old)))

    try:
        controller.set_tool("bus")
        controller.set_tool("line")
        controller.clear_tool()
        assert events == [("bus", None), ("line", "bus"), (None, "line")]
    finally:
        controller.dispose()


def test_project_context_is_ui_coordination_state():
    controller = Controller()
    project = object()

    try:
        controller.set_project(project)
        assert controller.get_project() is project
        controller.reset_state()
        assert controller.get_project() is None
    finally:
        controller.dispose()


def test_mutation_and_history_delegate_to_application():
    application, counters, executed = application_double()
    controller = Controller(application=application)

    try:
        assert controller.execute_command("command") == "executed"
        assert controller.undo() == "undo"
        assert controller.redo() == "redo"
        assert executed == ["command"]
        assert counters == {"undo": 1, "redo": 1}
        assert controller.can_undo() is True
        assert controller.can_redo() is False
        assert controller.undo_count() == 1
        assert controller.redo_count() == 0
        assert controller.get_command_state() == {
            "can_undo": True,
            "can_redo": False,
            "undo_count": 1,
            "redo_count": 0,
        }
    finally:
        controller.dispose()


def test_mutation_requires_application():
    controller = Controller()

    try:
        for operation in (
            lambda: controller.execute_command("command"),
            controller.undo,
            controller.redo,
        ):
            try:
                operation()
            except RuntimeError:
                continue
            raise AssertionError("operation must require Application")
    finally:
        controller.dispose()


def test_dispose_removes_application_reference():
    application, _, _ = application_double()
    controller = Controller(application=application)
    controller.dispose()
    assert controller.get_application() is None
