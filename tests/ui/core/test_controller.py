# ============================================================
# File: tests/ui/core/test_controller.py
# GridForge V2 — Controller Tests
# ============================================================

from __future__ import annotations

import pytest

from ui.core.controller import Controller


# ============================================================
# TEST DOUBLES
# ============================================================


class FakeCore:
    """Minimal Core double supporting direct command dispatch."""

    def __init__(self) -> None:
        self.executed = []
        self.undo_count = 0
        self.redo_count = 0

    def execute_command(self, command):
        self.executed.append(command)
        return f"executed:{command}"

    def undo(self):
        self.undo_count += 1
        return "undo-result"

    def redo(self):
        self.redo_count += 1
        return "redo-result"


class CommandManagerCore:
    """Core double exposing command_manager fallback."""

    class Manager:
        def __init__(self) -> None:
            self.executed = []
            self.undo_count = 0
            self.redo_count = 0

        def execute(self, command):
            self.executed.append(command)
            return f"manager-executed:{command}"

        def undo(self):
            self.undo_count += 1
            return "manager-undo"

        def redo(self):
            self.redo_count += 1
            return "manager-redo"

    def __init__(self) -> None:
        self.command_manager = self.Manager()


class InvalidCore:
    """Core double exposing none of the required command APIs."""


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def controller():
    controller = Controller()
    yield controller

    if not controller._disposed:
        controller.dispose()


# ============================================================
# INITIALIZATION
# ============================================================


def test_controller_initial_state(controller):
    assert controller.core is None
    assert controller.tool_id is None
    assert controller.selected_ids == ()
    assert controller.project is None

    state = controller.get_state()

    assert state == {
        "tool_id": None,
        "selected_ids": (),
        "selected_count": 0,
        "has_core": False,
        "has_project": False,
        "disposed": False,
    }


def test_controller_accepts_core():
    core = FakeCore()

    controller = Controller(core=core)

    try:
        assert controller.core is core
        assert controller.get_core() is core
    finally:
        controller.dispose()


# ============================================================
# CORE ACCESS
# ============================================================


def test_set_core_updates_core(controller):
    core = FakeCore()

    events = []
    controller.subscribe(
        "state_changed",
        lambda: events.append(True),
    )

    controller.set_core(core)

    assert controller.core is core
    assert controller.get_core() is core
    assert events == [True]


def test_set_core_can_clear_core(controller):
    core = FakeCore()

    controller.set_core(core)
    controller.set_core(None)

    assert controller.core is None


def test_set_core_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.set_core(FakeCore())


# ============================================================
# TOOL STATE
# ============================================================


def test_initial_tool_is_none(controller):
    assert controller.tool_id is None
    assert controller.get_tool_id() is None


def test_set_tool_updates_requested_tool(controller):
    controller.set_tool("bus")

    assert controller.tool_id == "bus"
    assert controller.get_tool_id() == "bus"


def test_set_tool_emits_tool_changed(controller):
    events = []

    controller.subscribe(
        "tool_changed",
        lambda new_id, previous_id: events.append(
            (new_id, previous_id)
        ),
    )

    controller.set_tool("bus")

    assert events == [
        ("bus", None),
    ]


def test_set_tool_emits_previous_tool_id(controller):
    events = []

    controller.subscribe(
        "tool_changed",
        lambda new_id, previous_id: events.append(
            (new_id, previous_id)
        ),
    )

    controller.set_tool("bus")
    controller.set_tool("line")

    assert events == [
        ("bus", None),
        ("line", "bus"),
    ]


def test_set_tool_emits_state_changed(controller):
    events = []

    controller.subscribe(
        "state_changed",
        lambda: events.append(True),
    )

    controller.set_tool("bus")

    assert events == [True]


def test_set_same_tool_does_not_emit(controller):
    tool_events = []
    state_events = []

    controller.subscribe(
        "tool_changed",
        lambda *args: tool_events.append(args),
    )

    controller.subscribe(
        "state_changed",
        lambda: state_events.append(True),
    )

    controller.set_tool("bus")
    controller.set_tool("bus")

    assert tool_events == [
        ("bus", None),
    ]

    assert state_events == [True]


def test_clear_tool_clears_requested_tool(controller):
    controller.set_tool("bus")

    events = []

    controller.subscribe(
        "tool_changed",
        lambda new_id, previous_id: events.append(
            (new_id, previous_id)
        ),
    )

    controller.clear_tool()

    assert controller.tool_id is None
    assert events == [
        (None, "bus"),
    ]


def test_clear_tool_when_already_clear_is_noop(controller):
    events = []

    controller.subscribe(
        "tool_changed",
        lambda *args: events.append(args),
    )

    controller.clear_tool()

    assert controller.tool_id is None
    assert events == []


def test_set_tool_rejects_non_string(controller):
    with pytest.raises(TypeError):
        controller.set_tool(123)


def test_set_tool_rejects_empty_string(controller):
    with pytest.raises(ValueError):
        controller.set_tool("")


def test_set_tool_rejects_whitespace_string(controller):
    with pytest.raises(ValueError):
        controller.set_tool("   ")


def test_set_tool_strips_identifier(controller):
    controller.set_tool("  bus  ")

    assert controller.tool_id == "bus"


# ============================================================
# SELECTION
# ============================================================


def test_initial_selection_is_empty(controller):
    assert controller.selected_ids == ()
    assert controller.get_selected_ids() == ()
    assert controller.has_selection() is False


def test_select_replaces_selection_by_default(controller):
    controller.select("bus-1")
    controller.select("bus-2")

    assert controller.selected_ids == ("bus-2",)


def test_select_multi_adds_to_selection(controller):
    controller.select("bus-1")
    controller.select("bus-2", multi=True)

    assert controller.selected_ids == (
        "bus-1",
        "bus-2",
    )


def test_select_multi_does_not_duplicate(controller):
    controller.select("bus-1")
    controller.select("bus-1", multi=True)

    assert controller.selected_ids == ("bus-1",)


def test_select_same_single_object_is_noop(controller):
    selection_events = []
    state_events = []

    controller.subscribe(
        "selection_changed",
        lambda value: selection_events.append(value),
    )

    controller.subscribe(
        "state_changed",
        lambda: state_events.append(True),
    )

    controller.select("bus-1")
    controller.select("bus-1")

    assert selection_events == [
        ("bus-1",),
    ]

    assert state_events == [True]


def test_selected_ids_is_immutable_snapshot(controller):
    controller.select("bus-1")

    selected = controller.selected_ids

    assert isinstance(selected, tuple)

    with pytest.raises(AttributeError):
        selected.append("bus-2")


def test_selection_changed_emits_tuple(controller):
    events = []

    controller.subscribe(
        "selection_changed",
        lambda value: events.append(value),
    )

    controller.select("bus-1")

    assert events == [
        ("bus-1",),
    ]

    assert isinstance(events[0], tuple)


def test_select_rejects_none(controller):
    with pytest.raises(ValueError):
        controller.select(None)


def test_select_rejects_non_boolean_multi(controller):
    with pytest.raises(TypeError):
        controller.select("bus-1", multi=1)


# ============================================================
# SELECT MANY
# ============================================================


def test_select_many_replaces_selection(controller):
    controller.select("old")

    controller.select_many(
        [
            "bus-1",
            "bus-2",
            "bus-3",
        ]
    )

    assert controller.selected_ids == (
        "bus-1",
        "bus-2",
        "bus-3",
    )


def test_select_many_removes_duplicates_preserving_order(
    controller,
):
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
    controller,
):
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


def test_select_many_multi_unchanged_is_noop(controller):
    controller.select_many(
        [
            "bus-1",
            "bus-2",
        ]
    )

    selection_events = []

    controller.subscribe(
        "selection_changed",
        lambda value: selection_events.append(value),
    )

    controller.select_many(
        [
            "bus-1",
            "bus-2",
            "bus-1",
        ],
        multi=True,
    )

    assert selection_events == []


def test_select_many_rejects_none(controller):
    with pytest.raises(ValueError):
        controller.select_many(None)


def test_select_many_rejects_non_boolean_multi(controller):
    with pytest.raises(TypeError):
        controller.select_many(
            ["bus-1"],
            multi=1,
        )


def test_select_many_rejects_none_inside_iterable(controller):
    with pytest.raises(ValueError):
        controller.select_many(
            ["bus-1", None]
        )


def test_select_many_accepts_generator(controller):
    controller.select_many(
        (value for value in ["bus-1", "bus-2"])
    )

    assert controller.selected_ids == (
        "bus-1",
        "bus-2",
    )


# ============================================================
# SELECTION QUERIES
# ============================================================


def test_is_selected(controller):
    controller.select("bus-1")

    assert controller.is_selected("bus-1") is True
    assert controller.is_selected("bus-2") is False


def test_is_selected_none_is_false(controller):
    assert controller.is_selected(None) is False


def test_has_selection(controller):
    assert controller.has_selection() is False

    controller.select("bus-1")

    assert controller.has_selection() is True


# ============================================================
# TOGGLE SELECTION
# ============================================================


def test_toggle_selection_adds_unselected_object(controller):
    controller.toggle_selection("bus-1")

    assert controller.selected_ids == ("bus-1",)


def test_toggle_selection_removes_selected_object(controller):
    controller.select("bus-1")

    controller.toggle_selection("bus-1")

    assert controller.selected_ids == ()


def test_toggle_selection_rejects_none(controller):
    with pytest.raises(ValueError):
        controller.toggle_selection(None)


# ============================================================
# REMOVE / CLEAR SELECTION
# ============================================================


def test_remove_from_selection(controller):
    controller.select_many(
        [
            "bus-1",
            "bus-2",
        ]
    )

    controller.remove_from_selection("bus-1")

    assert controller.selected_ids == ("bus-2",)


def test_remove_unselected_object_is_noop(controller):
    controller.select("bus-1")

    events = []

    controller.subscribe(
        "selection_changed",
        lambda value: events.append(value),
    )

    controller.remove_from_selection("bus-2")

    assert controller.selected_ids == ("bus-1",)
    assert events == []


def test_remove_none_is_noop(controller):
    controller.select("bus-1")

    controller.remove_from_selection(None)

    assert controller.selected_ids == ("bus-1",)


def test_clear_selection(controller):
    controller.select_many(
        [
            "bus-1",
            "bus-2",
        ]
    )

    controller.clear_selection()

    assert controller.selected_ids == ()
    assert controller.has_selection() is False


def test_clear_empty_selection_is_noop(controller):
    events = []

    controller.subscribe(
        "selection_changed",
        lambda value: events.append(value),
    )

    controller.clear_selection()

    assert events == []


# ============================================================
# PROJECT CONTEXT
# ============================================================


def test_project_initially_none(controller):
    assert controller.project is None
    assert controller.get_project() is None


def test_set_project(controller):
    project = object()

    events = []

    controller.subscribe(
        "project_changed",
        lambda value: events.append(value),
    )

    controller.set_project(project)

    assert controller.project is project
    assert controller.get_project() is project
    assert events == [project]


def test_set_project_emits_state_changed(controller):
    events = []

    controller.subscribe(
        "state_changed",
        lambda: events.append(True),
    )

    controller.set_project(object())

    assert events == [True]


def test_set_same_project_is_noop(controller):
    project = object()

    controller.set_project(project)

    events = []

    controller.subscribe(
        "project_changed",
        lambda value: events.append(value),
    )

    controller.set_project(project)

    assert events == []


# ============================================================
# COMMAND DISPATCH
# ============================================================


def test_execute_command_uses_core_execute_command(controller):
    core = FakeCore()
    controller.set_core(core)

    result = controller.execute_command("cmd")

    assert result == "executed:cmd"
    assert core.executed == ["cmd"]


def test_execute_command_emits_state_changed(controller):
    core = FakeCore()
    controller.set_core(core)

    events = []

    controller.subscribe(
        "state_changed",
        lambda: events.append(True),
    )

    controller.execute_command("cmd")

    assert events == [True]


def test_execute_command_uses_command_manager_fallback(
    controller,
):
    core = CommandManagerCore()
    controller.set_core(core)

    result = controller.execute_command("cmd")

    assert result == "manager-executed:cmd"
    assert core.command_manager.executed == ["cmd"]


def test_execute_command_rejects_none(controller):
    controller.set_core(FakeCore())

    with pytest.raises(ValueError):
        controller.execute_command(None)


def test_execute_command_without_core_fails(controller):
    with pytest.raises(RuntimeError):
        controller.execute_command("cmd")


def test_execute_command_rejects_invalid_core_boundary(
    controller,
):
    controller.set_core(InvalidCore())

    with pytest.raises(TypeError):
        controller.execute_command("cmd")


# ============================================================
# UNDO / REDO
# ============================================================


def test_undo_uses_core_undo(controller):
    core = FakeCore()
    controller.set_core(core)

    result = controller.undo()

    assert result == "undo-result"
    assert core.undo_count == 1


def test_redo_uses_core_redo(controller):
    core = FakeCore()
    controller.set_core(core)

    result = controller.redo()

    assert result == "redo-result"
    assert core.redo_count == 1


def test_undo_uses_command_manager_fallback(controller):
    core = CommandManagerCore()
    controller.set_core(core)

    result = controller.undo()

    assert result == "manager-undo"
    assert core.command_manager.undo_count == 1


def test_redo_uses_command_manager_fallback(controller):
    core = CommandManagerCore()
    controller.set_core(core)

    result = controller.redo()

    assert result == "manager-redo"
    assert core.command_manager.redo_count == 1


def test_undo_without_core_fails(controller):
    with pytest.raises(RuntimeError):
        controller.undo()


def test_redo_without_core_fails(controller):
    with pytest.raises(RuntimeError):
        controller.redo()


def test_undo_invalid_core_boundary_fails(controller):
    controller.set_core(InvalidCore())

    with pytest.raises(TypeError):
        controller.undo()


def test_redo_invalid_core_boundary_fails(controller):
    controller.set_core(InvalidCore())

    with pytest.raises(TypeError):
        controller.redo()


# ============================================================
# SUBSCRIPTION API
# ============================================================


def test_subscribe_to_tool_changed(controller):
    events = []

    def callback(new_id, previous_id):
        events.append(
            (new_id, previous_id)
        )

    controller.subscribe(
        "tool_changed",
        callback,
    )

    controller.set_tool("bus")

    assert events == [
        ("bus", None),
    ]


def test_subscribe_to_selection_changed(controller):
    events = []

    controller.subscribe(
        "selection_changed",
        lambda value: events.append(value),
    )

    controller.select("bus-1")

    assert events == [
        ("bus-1",),
    ]


def test_subscribe_to_state_changed(controller):
    events = []

    controller.subscribe(
        "state_changed",
        lambda: events.append(True),
    )

    controller.set_tool("bus")

    assert events == [True]


def test_subscribe_to_project_changed(controller):
    events = []

    controller.subscribe(
        "project_changed",
        lambda project: events.append(project),
    )

    project = object()

    controller.set_project(project)

    assert events == [project]


def test_subscribe_to_reset_requested(controller):
    events = []

    controller.subscribe(
        "reset_requested",
        lambda: events.append(True),
    )

    controller.reset_state()

    assert events == [True]


def test_subscribe_rejects_non_string_signal_name(
    controller,
):
    with pytest.raises(TypeError):
        controller.subscribe(
            123,
            lambda: None,
        )


def test_subscribe_rejects_non_callable_callback(
    controller,
):
    with pytest.raises(TypeError):
        controller.subscribe(
            "state_changed",
            None,
        )


def test_subscribe_rejects_unknown_signal(controller):
    with pytest.raises(ValueError):
        controller.subscribe(
            "unknown_signal",
            lambda: None,
        )


def test_unsubscribe_removes_callback(controller):
    events = []

    def callback():
        events.append(True)

    controller.subscribe(
        "state_changed",
        callback,
    )

    controller.unsubscribe(
        "state_changed",
        callback,
    )

    controller.set_tool("bus")

    assert events == []


def test_unsubscribe_rejects_non_string_signal_name(
    controller,
):
    with pytest.raises(TypeError):
        controller.unsubscribe(
            123,
            lambda: None,
        )


def test_unsubscribe_rejects_non_callable_callback(
    controller,
):
    with pytest.raises(TypeError):
        controller.unsubscribe(
            "state_changed",
            None,
        )


def test_unsubscribe_rejects_unknown_signal(controller):
    with pytest.raises(ValueError):
        controller.unsubscribe(
            "unknown_signal",
            lambda: None,
        )


# ============================================================
# RESET
# ============================================================


def test_reset_state_clears_controller_state(controller):
    controller.set_tool("bus")
    controller.select_many(
        [
            "bus-1",
            "bus-2",
        ]
    )

    project = object()
    controller.set_project(project)

    controller.reset_state()

    assert controller.tool_id is None
    assert controller.selected_ids == ()
    assert controller.project is None


def test_reset_state_emits_tool_changed_when_tool_exists(
    controller,
):
    tool_events = []

    controller.set_tool("bus")

    controller.subscribe(
        "tool_changed",
        lambda new_id, previous_id: tool_events.append(
            (new_id, previous_id)
        ),
    )

    controller.reset_state()

    assert tool_events == [
        (None, "bus"),
    ]


def test_reset_state_does_not_emit_tool_changed_when_no_tool(
    controller,
):
    events = []

    controller.subscribe(
        "tool_changed",
        lambda *args: events.append(args),
    )

    controller.reset_state()

    assert events == []


def test_reset_state_emits_selection_changed(controller):
    controller.select("bus-1")

    events = []

    controller.subscribe(
        "selection_changed",
        lambda value: events.append(value),
    )

    controller.reset_state()

    assert events == [()]


def test_reset_state_emits_reset_requested(controller):
    events = []

    controller.subscribe(
        "reset_requested",
        lambda: events.append(True),
    )

    controller.reset_state()

    assert events == [True]


def test_reset_state_does_not_mutate_core(controller):
    core = FakeCore()
    controller.set_core(core)

    controller.set_tool("bus")
    controller.select("bus-1")
    controller.set_project(object())

    controller.reset_state()

    assert controller.core is core
    assert core.executed == []


# ============================================================
# DIAGNOSTICS
# ============================================================


def test_get_state_reflects_current_state(controller):
    core = FakeCore()
    project = object()

    controller.set_core(core)
    controller.set_project(project)
    controller.set_tool("bus")
    controller.select_many(
        [
            "bus-1",
            "bus-2",
        ]
    )

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


def test_repr_contains_diagnostic_state(controller):
    core = FakeCore()

    controller.set_core(core)
    controller.set_tool("bus")
    controller.select_many(
        [
            "bus-1",
            "bus-2",
        ]
    )

    representation = repr(controller)

    assert "Controller(" in representation
    assert "tool='bus'" in representation
    assert "selected=2" in representation
    assert "core=True" in representation


# ============================================================
# DISPOSAL
# ============================================================


def test_dispose_clears_controller_owned_state(controller):
    controller.set_tool("bus")
    controller.select("bus-1")
    controller.set_project(object())

    controller.dispose()

    assert controller._tool_id is None
    assert controller._selected_ids == []
    assert controller._project is None
    assert controller._disposed is True


def test_dispose_does_not_dispose_core():
    core = FakeCore()

    controller = Controller(core=core)

    controller.dispose()

    assert controller.core is core


def test_dispose_is_idempotent(controller):
    controller.dispose()
    controller.dispose()

    assert controller._disposed is True


def test_mutation_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.set_tool("bus")


def test_selection_mutation_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.select("bus-1")


def test_select_many_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.select_many(["bus-1"])


def test_toggle_selection_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.toggle_selection("bus-1")


def test_remove_selection_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.remove_from_selection("bus-1")


def test_clear_selection_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.clear_selection()


def test_set_project_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.set_project(object())


def test_execute_command_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.execute_command("cmd")


def test_undo_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.undo()


def test_redo_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.redo()


def test_reset_state_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.reset_state()


def test_subscribe_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.subscribe(
            "state_changed",
            lambda: None,
        )


def test_unsubscribe_after_dispose_fails(controller):
    controller.dispose()

    with pytest.raises(RuntimeError):
        controller.unsubscribe(
            "state_changed",
            lambda: None,
        )


# ============================================================
# CONTROLLER / TOOL MANAGER CONTRACT
# ============================================================


def test_tool_changed_callback_receives_new_and_previous_ids(
    controller,
):
    received = []

    controller.subscribe(
        "tool_changed",
        lambda new_id, previous_id: received.append(
            (new_id, previous_id)
        ),
    )

    controller.set_tool("select")
    controller.set_tool("line")
    controller.clear_tool()

    assert received == [
        ("select", None),
        ("line", "select"),
        (None, "line"),
    ]


def test_controller_does_not_create_concrete_tools(
    controller,
):
    controller.set_tool("bus")

    assert controller.tool_id == "bus"

    # Controller stores only the requested identifier.
    assert not hasattr(controller, "_tool_instances")
    assert not hasattr(controller, "_active_tool")
    assert not hasattr(controller, "_active_tool_id")
