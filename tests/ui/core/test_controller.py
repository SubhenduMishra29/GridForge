# ============================================================
# File: tests/ui/core/test_controller.py
# GridForge V2 — Controller Tests
# ============================================================
"""
Tests for ui.core.controller.Controller.

Coverage
--------
- initialization and Core access
- tool request state
- tool_changed notifications
- selection ownership and mutation
- project context
- command dispatch
- undo / redo
- reset_state
- subscription / unsubscription
- diagnostics
- disposal and lifecycle protection
- validation and failure contracts

These tests intentionally validate Controller as an application/UI
coordination boundary. They do not test concrete tools, rendering,
Canvas behavior, or Core implementation details.
"""

from __future__ import annotations

from typing import Any

import pytest

from ui.core.controller import Controller
from ui.core.qt import QCoreApplication


# ============================================================
# QT APPLICATION FIXTURE
# ============================================================


@pytest.fixture(scope="session")
def qapp() -> QCoreApplication:
    """
    Provide the minimal Qt application required by QObject.
    """

    app = QCoreApplication.instance()

    if app is None:
        app = QCoreApplication([])

    return app


@pytest.fixture
def controller(qapp: QCoreApplication) -> Controller:
    """
    Provide a fresh Controller.
    """

    return Controller()


# ============================================================
# TEST DOUBLES
# ============================================================


class CommandCore:
    """
    Core double exposing the direct command API.
    """

    def __init__(self) -> None:
        self.commands: list[Any] = []
        self.undo_count = 0
        self.redo_count = 0

    def execute_command(self, command: Any) -> str:
        self.commands.append(command)
        return "executed"

    def undo(self) -> str:
        self.undo_count += 1
        return "undone"

    def redo(self) -> str:
        self.redo_count += 1
        return "redone"


class CommandManager:
    """
    Command-manager double used for fallback API tests.
    """

    def __init__(self) -> None:
        self.commands: list[Any] = []
        self.undo_count = 0
        self.redo_count = 0

    def execute(self, command: Any) -> str:
        self.commands.append(command)
        return "executed-by-manager"

    def undo(self) -> str:
        self.undo_count += 1
        return "undone-by-manager"

    def redo(self) -> str:
        self.redo_count += 1
        return "redone-by-manager"


class ManagerCore:
    """
    Core double exposing command_manager only.
    """

    def __init__(self) -> None:
        self.command_manager = CommandManager()


class InvalidCommandCore:
    """
    Core double exposing none of the supported command APIs.
    """

    pass


# ============================================================
# INITIALIZATION / CORE
# ============================================================


def test_controller_initializes_without_core(
    controller: Controller,
) -> None:

    assert controller.core is None
    assert controller.get_core() is None


def test_controller_stores_core_without_taking_ownership(
    qapp: QCoreApplication,
) -> None:

    core = object()

    controller = Controller(core=core)

    assert controller.core is core
    assert controller.get_core() is core


def test_set_core_replaces_core(
    controller: Controller,
) -> None:

    first_core = object()
    second_core = object()

    controller.set_core(first_core)
    controller.set_core(second_core)

    assert controller.core is second_core


def test_set_core_accepts_none(
    controller: Controller,
) -> None:

    controller.set_core(object())
    controller.set_core(None)

    assert controller.core is None


def test_set_core_emits_state_changed(
    controller: Controller,
) -> None:

    events: list[str] = []

    controller.subscribe(
        "state_changed",
        lambda: events.append("state"),
    )

    controller.set_core(object())

    assert events == ["state"]


# ============================================================
# TOOL REQUEST STATE
# ============================================================


def test_initial_tool_id_is_none(
    controller: Controller,
) -> None:

    assert controller.tool_id is None
    assert controller.get_tool_id() is None


def test_set_tool_updates_tool_id(
    controller: Controller,
) -> None:

    controller.set_tool("bus")

    assert controller.tool_id == "bus"
    assert controller.get_tool_id() == "bus"


def test_set_tool_emits_tool_changed_with_previous_id(
    controller: Controller,
) -> None:

    events: list[tuple[Any, Any]] = []

    controller.subscribe(
        "tool_changed",
        lambda new, previous: events.append(
            (new, previous)
        ),
    )

    controller.set_tool("bus")
    controller.set_tool("line")

    assert events == [
        ("bus", None),
        ("line", "bus"),
    ]


def test_set_tool_emits_state_changed(
    controller: Controller,
) -> None:

    events: list[str] = []

    controller.subscribe(
        "state_changed",
        lambda: events.append("state"),
    )

    controller.set_tool("bus")

    assert events == ["state"]


def test_setting_same_tool_is_noop(
    controller: Controller,
) -> None:

    tool_events: list[Any] = []
    state_events: list[Any] = []

    controller.subscribe(
        "tool_changed",
        lambda *args: tool_events.append(args),
    )

    controller.subscribe(
        "state_changed",
        lambda: state_events.append(True),
    )

    controller.set_tool("bus")
    tool_events.clear()
    state_events.clear()

    controller.set_tool("bus")

    assert tool_events == []
    assert state_events == []
    assert controller.tool_id == "bus"


def test_clear_tool_clears_requested_tool(
    controller: Controller,
) -> None:

    controller.set_tool("bus")
    controller.clear_tool()

    assert controller.tool_id is None


def test_clear_tool_emits_previous_tool(
    controller: Controller,
) -> None:

    events: list[tuple[Any, Any]] = []

    controller.subscribe(
        "tool_changed",
        lambda new, previous: events.append(
            (new, previous)
        ),
    )

    controller.set_tool("bus")
    controller.clear_tool()

    assert events[-1] == (None, "bus")


def test_set_tool_strips_whitespace(
    controller: Controller,
) -> None:

    controller.set_tool("  bus  ")

    assert controller.tool_id == "bus"


def test_set_tool_rejects_non_string(
    controller: Controller,
) -> None:

    with pytest.raises(
        TypeError,
        match="tool_id must be a string or None",
    ):
        controller.set_tool(123)


def test_set_tool_rejects_empty_string(
    controller: Controller,
) -> None:

    with pytest.raises(
        ValueError,
        match="tool_id must not be empty",
    ):
        controller.set_tool("   ")


# ============================================================
# SELECTION
# ============================================================


def test_initial_selection_is_empty(
    controller: Controller,
) -> None:

    assert controller.selected_ids == ()
    assert controller.get_selected_ids() == ()
    assert controller.has_selection() is False


def test_select_replaces_selection_by_default(
    controller: Controller,
) -> None:

    controller.select("bus-1")
    controller.select("bus-2")

    assert controller.selected_ids == ("bus-2",)


def test_select_multi_adds_to_selection(
    controller: Controller,
) -> None:

    controller.select("bus-1")
    controller.select("bus-2", multi=True)

    assert controller.selected_ids == (
        "bus-1",
        "bus-2",
    )


def test_select_multi_does_not_duplicate(
    controller: Controller,
) -> None:

    controller.select("bus-1")
    controller.select("bus-1", multi=True)

    assert controller.selected_ids == ("bus-1",)


def test_select_same_single_object_is_noop(
    controller: Controller,
) -> None:

    events: list[Any] = []

    controller.subscribe(
        "selection_changed",
        lambda value: events.append(value),
    )

    controller.select("bus-1")
    events.clear()

    controller.select("bus-1")

    assert events == []


def test_select_emits_selection_changed(
    controller: Controller,
) -> None:

    events: list[tuple[Any, ...]] = []

    controller.subscribe(
        "selection_changed",
        lambda value: events.append(value),
    )

    controller.select("bus-1")

    assert events == [
        ("bus-1",)
    ]


def test_select_emits_state_changed(
    controller: Controller,
) -> None:

    events: list[bool] = []

    controller.subscribe(
        "state_changed",
        lambda: events.append(True),
    )

    controller.select("bus-1")

    assert events == [True]


def test_select_many_replaces_selection(
    controller: Controller,
) -> None:

    controller.select("old")

    controller.select_many(
        ["bus-1", "bus-2", "bus-3"]
    )

    assert controller.selected_ids == (
        "bus-1",
        "bus-2",
        "bus-3",
    )


def test_select_many_removes_duplicates(
    controller: Controller,
) -> None:

    controller.select_many(
        [
            "bus-1",
            "bus-2",
            "bus-1",
            "bus-3",
            "bus-2",
        ]
    )

    assert controller.selected_ids == (
        "bus-1",
        "bus-2",
        "bus-3",
    )


def test_select_many_multi_adds_without_duplicates(
    controller: Controller,
) -> None:

    controller.select("bus-1")

    controller.select_many(
        [
            "bus-2",
            "bus-3",
            "bus-2",
        ],
        multi=True,
    )

    assert controller.selected_ids == (
        "bus-1",
        "bus-2",
        "bus-3",
    )


def test_select_many_same_selection_is_noop(
    controller: Controller,
) -> None:

    controller.select_many(
        ["bus-1", "bus-2"]
    )

    events: list[Any] = []

    controller.subscribe(
        "selection_changed",
        lambda value: events.append(value),
    )

    controller.select_many(
        ["bus-1", "bus-2"]
    )

    assert events == []


def test_toggle_selection_adds_object(
    controller: Controller,
) -> None:

    controller.toggle_selection("bus-1")

    assert controller.selected_ids == ("bus-1",)


def test_toggle_selection_removes_object(
    controller: Controller,
) -> None:

    controller.select("bus-1")

    controller.toggle_selection("bus-1")

    assert controller.selected_ids == ()


def test_remove_from_selection_removes_object(
    controller: Controller,
) -> None:

    controller.select_many(
        ["bus-1", "bus-2"]
    )

    controller.remove_from_selection("bus-1")

    assert controller.selected_ids == ("bus-2",)


def test_remove_non_selected_object_is_noop(
    controller: Controller,
) -> None:

    controller.select("bus-1")

    controller.remove_from_selection("bus-2")

    assert controller.selected_ids == ("bus-1",)


def test_remove_none_is_noop(
    controller: Controller,
) -> None:

    controller.select("bus-1")

    controller.remove_from_selection(None)

    assert controller.selected_ids == ("bus-1",)


def test_clear_selection(
    controller: Controller,
) -> None:

    controller.select_many(
        ["bus-1", "bus-2"]
    )

    controller.clear_selection()

    assert controller.selected_ids == ()
    assert controller.has_selection() is False


def test_clear_empty_selection_is_noop(
    controller: Controller,
) -> None:

    events: list[Any] = []

    controller.subscribe(
        "selection_changed",
        lambda value: events.append(value),
    )

    controller.clear_selection()

    assert events == []


def test_selected_ids_is_immutable_snapshot(
    controller: Controller,
) -> None:

    controller.select_many(
        ["bus-1", "bus-2"]
    )

    selected = controller.selected_ids

    assert isinstance(selected, tuple)

    with pytest.raises(
        AttributeError
    ):
        selected.append("bus-3")  # type: ignore[attr-defined]

    assert controller.selected_ids == (
        "bus-1",
        "bus-2",
    )


def test_is_selected(
    controller: Controller,
) -> None:

    controller.select("bus-1")

    assert controller.is_selected("bus-1") is True
    assert controller.is_selected("bus-2") is False
    assert controller.is_selected(None) is False


def test_select_rejects_none(
    controller: Controller,
) -> None:

    with pytest.raises(
        ValueError,
        match="object_id must not be None",
    ):
        controller.select(None)


def test_select_rejects_invalid_multi(
    controller: Controller,
) -> None:

    with pytest.raises(
        TypeError,
        match="multi must be a bool",
    ):
        controller.select(
            "bus-1",
            multi=1,  # type: ignore[arg-type]
        )


def test_select_many_rejects_none_iterable(
    controller: Controller,
) -> None:

    with pytest.raises(
        ValueError,
        match="object_ids must not be None",
    ):
        controller.select_many(None)  # type: ignore[arg-type]


def test_select_many_rejects_none_member(
    controller: Controller,
) -> None:

    with pytest.raises(
        ValueError,
        match="object_ids must not contain None",
    ):
        controller.select_many(
            ["bus-1", None]
        )


# ============================================================
# PROJECT CONTEXT
# ============================================================


def test_initial_project_is_none(
    controller: Controller,
) -> None:

    assert controller.project is None
    assert controller.get_project() is None


def test_set_project(
    controller: Controller,
) -> None:

    project = object()

    controller.set_project(project)

    assert controller.project is project
    assert controller.get_project() is project


def test_set_project_emits_project_changed(
    controller: Controller,
) -> None:

    events: list[Any] = []

    controller.subscribe(
        "project_changed",
        lambda project: events.append(project),
    )

    project = object()

    controller.set_project(project)

    assert events == [project]


def test_set_same_project_is_noop(
    controller: Controller,
) -> None:

    project = object()

    controller.set_project(project)

    events: list[Any] = []

    controller.subscribe(
        "project_changed",
        lambda value: events.append(value),
    )

    controller.set_project(project)

    assert events == []


def test_set_project_emits_state_changed(
    controller: Controller,
) -> None:

    events: list[bool] = []

    controller.subscribe(
        "state_changed",
        lambda: events.append(True),
    )

    controller.set_project(object())

    assert events == [True]


# ============================================================
# COMMAND DISPATCH
# ============================================================


def test_execute_command_uses_core_direct_api(
    qapp: QCoreApplication,
) -> None:

    core = CommandCore()
    controller = Controller(core=core)

    command = object()

    result = controller.execute_command(command)

    assert result == "executed"
    assert core.commands == [command]


def test_execute_command_uses_command_manager_fallback(
    qapp: QCoreApplication,
) -> None:

    core = ManagerCore()
    controller = Controller(core=core)

    command = object()

    result = controller.execute_command(command)

    assert result == "executed-by-manager"
    assert core.command_manager.commands == [command]


def test_execute_command_prefers_direct_core_api(
    qapp: QCoreApplication,
) -> None:

    core = CommandCore()
    core.command_manager = CommandManager()

    controller = Controller(core=core)

    controller.execute_command("command")

    assert core.commands == ["command"]
    assert core.command_manager.commands == []


def test_execute_command_emits_state_changed(
    qapp: QCoreApplication,
) -> None:

    controller = Controller(
        core=CommandCore()
    )

    events: list[bool] = []

    controller.subscribe(
        "state_changed",
        lambda: events.append(True),
    )

    controller.execute_command("command")

    assert events == [True]


def test_execute_command_requires_core(
    controller: Controller,
) -> None:

    with pytest.raises(
        RuntimeError,
        match="without a Core",
    ):
        controller.execute_command("command")


def test_execute_command_rejects_none(
    controller: Controller,
) -> None:

    with pytest.raises(
        ValueError,
        match="command must not be None",
    ):
        controller.execute_command(None)


def test_execute_command_rejects_invalid_core(
    qapp: QCoreApplication,
) -> None:

    controller = Controller(
        core=InvalidCommandCore()
    )

    with pytest.raises(
        TypeError,
        match="Core must provide execute_command",
    ):
        controller.execute_command("command")


# ============================================================
# UNDO / REDO
# ============================================================


def test_undo_uses_direct_core_api(
    qapp: QCoreApplication,
) -> None:

    core = CommandCore()
    controller = Controller(core=core)

    assert controller.undo() == "undone"
    assert core.undo_count == 1


def test_redo_uses_direct_core_api(
    qapp: QCoreApplication,
) -> None:

    core = CommandCore()
    controller = Controller(core=core)

    assert controller.redo() == "redone"
    assert core.redo_count == 1


def test_undo_uses_command_manager_fallback(
    qapp: QCoreApplication,
) -> None:

    core = ManagerCore()
    controller = Controller(core=core)

    assert controller.undo() == "undone-by-manager"
    assert core.command_manager.undo_count == 1


def test_redo_uses_command_manager_fallback(
    qapp: QCoreApplication,
) -> None:

    core = ManagerCore()
    controller = Controller(core=core)

    assert controller.redo() == "redone-by-manager"
    assert core.command_manager.redo_count == 1


def test_undo_requires_core(
    controller: Controller,
) -> None:

    with pytest.raises(
        RuntimeError,
        match="Cannot undo without a Core",
    ):
        controller.undo()


def test_redo_requires_core(
    controller: Controller,
) -> None:

    with pytest.raises(
        RuntimeError,
        match="Cannot redo without a Core",
    ):
        controller.redo()


def test_undo_rejects_invalid_core(
    qapp: QCoreApplication,
) -> None:

    controller = Controller(
        core=InvalidCommandCore()
    )

    with pytest.raises(
        TypeError,
        match="Core must provide undo",
    ):
        controller.undo()


def test_redo_rejects_invalid_core(
    qapp: QCoreApplication,
) -> None:

    controller = Controller(
        core=InvalidCommandCore()
    )

    with pytest.raises(
        TypeError,
        match="Core must provide redo",
    ):
        controller.redo()


# ============================================================
# RESET
# ============================================================


def test_reset_state_clears_controller_owned_state(
    controller: Controller,
) -> None:

    controller.set_tool("bus")
    controller.select_many(
        ["bus-1", "bus-2"]
    )

    project = object()
    controller.set_project(project)

    controller.reset_state()

    assert controller.tool_id is None
    assert controller.selected_ids == ()
    assert controller.project is None


def test_reset_state_emits_tool_changed_when_tool_exists(
    controller: Controller,
) -> None:

    events: list[tuple[Any, Any]] = []

    controller.set_tool("bus")

    controller.subscribe(
        "tool_changed",
        lambda new, previous: events.append(
            (new, previous)
        ),
    )

    controller.reset_state()

    assert events == [
        (None, "bus")
    ]


def test_reset_state_emits_selection_changed(
    controller: Controller,
) -> None:

    controller.select("bus-1")

    events: list[Any] = []

    controller.subscribe(
        "selection_changed",
        lambda value: events.append(value),
    )

    controller.reset_state()

    assert events == [()]


def test_reset_state_emits_reset_requested(
    controller: Controller,
) -> None:

    events: list[bool] = []

    controller.subscribe(
        "reset_requested",
        lambda: events.append(True),
    )

    controller.reset_state()

    assert events == [True]


def test_reset_state_emits_state_changed(
    controller: Controller,
) -> None:

    events: list[bool] = []

    controller.subscribe(
        "state_changed",
        lambda: events.append(True),
    )

    controller.reset_state()

    assert events == [True]


def test_reset_state_does_not_mutate_core(
    qapp: QCoreApplication,
) -> None:

    core = object()
    controller = Controller(core=core)

    controller.set_tool("bus")
    controller.select("bus-1")
    controller.set_project(object())

    controller.reset_state()

    assert controller.core is core


def test_reset_state_without_tool_does_not_emit_tool_changed(
    controller: Controller,
) -> None:

    events: list[Any] = []

    controller.subscribe(
        "tool_changed",
        lambda *args: events.append(args),
    )

    controller.reset_state()

    assert events == []


# ============================================================
# SUBSCRIPTION API
# ============================================================


def test_subscribe_receives_signal(
    controller: Controller,
) -> None:

    events: list[tuple[Any, Any]] = []

    def callback(
        new_tool: Any,
        previous_tool: Any,
    ) -> None:
        events.append(
            (
                new_tool,
                previous_tool,
            )
        )

    controller.subscribe(
        "tool_changed",
        callback,
    )

    controller.set_tool("bus")

    assert events == [
        ("bus", None)
    ]


def test_unsubscribe_stops_callback(
    controller: Controller,
) -> None:

    events: list[Any] = []

    def callback(
        new_tool: Any,
        previous_tool: Any,
    ) -> None:
        events.append(
            (
                new_tool,
                previous_tool,
            )
        )

    controller.subscribe(
        "tool_changed",
        callback,
    )

    controller.set_tool("bus")

    controller.unsubscribe(
        "tool_changed",
        callback,
    )

    controller.set_tool("line")

    assert events == [
        ("bus", None)
    ]


def test_subscribe_rejects_non_string_signal_name(
    controller: Controller,
) -> None:

    with pytest.raises(
        TypeError,
        match="signal_name must be a string",
    ):
        controller.subscribe(
            123,  # type: ignore[arg-type]
            lambda: None,
        )


def test_subscribe_rejects_non_callable_callback(
    controller: Controller,
) -> None:

    with pytest.raises(
        TypeError,
        match="callback must be callable",
    ):
        controller.subscribe(
            "state_changed",
            None,  # type: ignore[arg-type]
        )


def test_subscribe_rejects_unknown_signal(
    controller: Controller,
) -> None:

    with pytest.raises(
        ValueError,
        match="Unknown Controller signal",
    ):
        controller.subscribe(
            "does_not_exist",
            lambda: None,
        )


def test_unsubscribe_rejects_non_string_signal_name(
    controller: Controller,
) -> None:

    with pytest.raises(
        TypeError,
        match="signal_name must be a string",
    ):
        controller.unsubscribe(
            123,  # type: ignore[arg-type]
            lambda: None,
        )


def test_unsubscribe_rejects_non_callable_callback(
    controller: Controller,
) -> None:

    with pytest.raises(
        TypeError,
        match="callback must be callable",
    ):
        controller.unsubscribe(
            "state_changed",
            None,  # type: ignore[arg-type]
        )


def test_unsubscribe_rejects_unknown_signal(
    controller: Controller,
) -> None:

    with pytest.raises(
        ValueError,
        match="Unknown Controller signal",
    ):
        controller.unsubscribe(
            "does_not_exist",
            lambda: None,
        )


def test_unsubscribe_missing_callback_is_safe(
    controller: Controller,
) -> None:

    callback = lambda: None

    controller.unsubscribe(
        "state_changed",
        callback,
    )


# ============================================================
# DIAGNOSTICS
# ============================================================


def test_get_state_initial(
    controller: Controller,
) -> None:

    state = controller.get_state()

    assert state == {
        "tool_id": None,
        "selected_ids": (),
        "selected_count": 0,
        "has_core": False,
        "has_project": False,
        "disposed": False,
    }


def test_get_state_reflects_controller_state(
    controller: Controller,
) -> None:

    controller.set_tool("bus")
    controller.select_many(
        ["bus-1", "bus-2"]
    )
    controller.set_core(object())
    controller.set_project(object())

    state = controller.get_state()

    assert state["tool_id"] == "bus"
    assert state["selected_ids"] == (
        "bus-1",
        "bus-2",
    )
    assert state["selected_count"] == 2
    assert state["has_core"] is True
    assert state["has_project"] is True
    assert state["disposed"] is False


def test_repr_contains_diagnostic_state(
    controller: Controller,
) -> None:

    controller.set_tool("bus")
    controller.select("bus-1")
    controller.set_core(object())

    representation = repr(controller)

    assert "Controller(" in representation
    assert "tool='bus'" in representation
    assert "selected=1" in representation
    assert "core=True" in representation


# ============================================================
# DISPOSAL
# ============================================================


def test_dispose_clears_controller_owned_state(
    controller: Controller,
) -> None:

    controller.set_tool("bus")
    controller.select("bus-1")
    controller.set_project(object())

    controller.dispose()

    state = controller.get_state()

    assert state["tool_id"] is None
    assert state["selected_ids"] == ()
    assert state["selected_count"] == 0
    assert state["has_project"] is False
    assert state["disposed"] is True


def test_dispose_does_not_destroy_core(
    qapp: QCoreApplication,
) -> None:

    core = object()
    controller = Controller(core=core)

    controller.dispose()

    assert controller.core is core


def test_dispose_is_idempotent(
    controller: Controller,
) -> None:

    controller.dispose()
    controller.dispose()

    assert controller.get_state()["disposed"] is True


@pytest.mark.parametrize(
    "operation",
    [
        "set_core",
        "set_tool",
        "select",
        "select_many",
        "toggle_selection",
        "remove_from_selection",
        "clear_selection",
        "set_project",
        "execute_command",
        "undo",
        "redo",
        "reset_state",
        "subscribe",
        "unsubscribe",
    ],
)
def test_disposed_controller_rejects_mutating_or_operational_api(
    controller: Controller,
    operation: str,
) -> None:

    controller.dispose()

    with pytest.raises(
        RuntimeError,
        match="Controller has been disposed",
    ):

        if operation == "set_core":
            controller.set_core(object())

        elif operation == "set_tool":
            controller.set_tool("bus")

        elif operation == "select":
            controller.select("bus-1")

        elif operation == "select_many":
            controller.select_many(["bus-1"])

        elif operation == "toggle_selection":
            controller.toggle_selection("bus-1")

        elif operation == "remove_from_selection":
            controller.remove_from_selection("bus-1")

        elif operation == "clear_selection":
            controller.clear_selection()

        elif operation == "set_project":
            controller.set_project(object())

        elif operation == "execute_command":
            controller.execute_command("command")

        elif operation == "undo":
            controller.undo()

        elif operation == "redo":
            controller.redo()

        elif operation == "reset_state":
            controller.reset_state()

        elif operation == "subscribe":
            controller.subscribe(
                "state_changed",
                lambda: None,
            )

        elif operation == "unsubscribe":
            controller.unsubscribe(
                "state_changed",
                lambda: None,
            )

        else:
            raise AssertionError(
                f"Unhandled operation: {operation}"
            )


def test_disposed_controller_still_exposes_read_only_state(
    controller: Controller,
) -> None:

    controller.set_tool("bus")
    controller.select("bus-1")
    controller.dispose()

    assert controller.tool_id is None
    assert controller.selected_ids == ()
    assert controller.project is None


# ============================================================
# SIGNAL ORDERING
# ============================================================


def test_set_tool_signal_order(
    controller: Controller,
) -> None:

    events: list[str] = []

    controller.subscribe(
        "tool_changed",
        lambda *_: events.append(
            "tool_changed"
        ),
    )

    controller.subscribe(
        "state_changed",
        lambda: events.append(
            "state_changed"
        ),
    )

    controller.set_tool("bus")

    assert events == [
        "tool_changed",
        "state_changed",
    ]


def test_selection_signal_order(
    controller: Controller,
) -> None:

    events: list[str] = []

    controller.subscribe(
        "selection_changed",
        lambda *_: events.append(
            "selection_changed"
        ),
    )

    controller.subscribe(
        "state_changed",
        lambda: events.append(
            "state_changed"
        ),
    )

    controller.select("bus-1")

    assert events == [
        "selection_changed",
        "state_changed",
    ]


def test_project_signal_order(
    controller: Controller,
) -> None:

    events: list[str] = []

    controller.subscribe(
        "project_changed",
        lambda *_: events.append(
            "project_changed"
        ),
    )

    controller.subscribe(
        "state_changed",
        lambda: events.append(
            "state_changed"
        ),
    )

    controller.set_project(object())

    assert events == [
        "project_changed",
        "state_changed",
    ]
