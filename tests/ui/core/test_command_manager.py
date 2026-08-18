# ============================================================
# File: tests/ui/core/test_command_manager.py
# GridForge V2 — UI Command Manager Tests
# ============================================================

from __future__ import annotations

import pytest

from ui.core.command_manager import CommandManager


# ============================================================
# TEST DOUBLES
# ============================================================


class FakeController:
    """
    Minimal Controller double implementing the complete public
    command boundary required by CommandManager.
    """

    def __init__(self) -> None:
        self.execute_calls = []
        self.undo_calls = 0
        self.redo_calls = 0

        self._can_undo = False
        self._can_redo = False

        self._undo_count = 0
        self._redo_count = 0

        self._undo_commands = ()
        self._redo_commands = ()

        self._undo_name = None
        self._redo_name = None

        self.clear_history_calls = 0
        self.clear_redo_calls = 0
        self.reset_command_history_calls = 0

        self.command_state = {
            "undo_count": 0,
            "redo_count": 0,
            "can_undo": False,
            "can_redo": False,
        }

    # --------------------------------------------------------
    # Command execution
    # --------------------------------------------------------

    def execute_command(self, command):
        self.execute_calls.append(command)
        return f"executed:{command}"

    def undo(self):
        self.undo_calls += 1
        return "undo-result"

    def redo(self):
        self.redo_calls += 1
        return "redo-result"

    # --------------------------------------------------------
    # Availability
    # --------------------------------------------------------

    def can_undo(self):
        return self._can_undo

    def can_redo(self):
        return self._can_redo

    # --------------------------------------------------------
    # Counts
    # --------------------------------------------------------

    def undo_count(self):
        return self._undo_count

    def redo_count(self):
        return self._redo_count

    # --------------------------------------------------------
    # History
    # --------------------------------------------------------

    def get_undo_commands(self):
        return self._undo_commands

    def get_redo_commands(self):
        return self._redo_commands

    # --------------------------------------------------------
    # Names
    # --------------------------------------------------------

    def get_undo_name(self):
        return self._undo_name

    def get_redo_name(self):
        return self._redo_name

    # --------------------------------------------------------
    # History mutation
    # --------------------------------------------------------

    def clear_history(self):
        self.clear_history_calls += 1
        return "history-cleared"

    def clear_redo(self):
        self.clear_redo_calls += 1
        return "redo-cleared"

    def reset_command_history(self):
        self.reset_command_history_calls += 1
        return "history-reset"

    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    def get_command_state(self):
        return self.command_state


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def controller():
    return FakeController()


@pytest.fixture
def command_manager(controller):
    return CommandManager(controller)


# ============================================================
# INITIALIZATION
# ============================================================


def test_command_manager_accepts_controller(controller):
    manager = CommandManager(controller)

    assert manager.controller is controller


def test_command_manager_rejects_none_controller():
    with pytest.raises(
        ValueError,
        match="controller must not be None",
    ):
        CommandManager(None)


@pytest.mark.parametrize(
    "missing_method",
    [
        "execute_command",
        "undo",
        "redo",
        "can_undo",
        "can_redo",
        "undo_count",
        "redo_count",
        "get_undo_commands",
        "get_redo_commands",
        "get_undo_name",
        "get_redo_name",
        "clear_history",
        "clear_redo",
        "reset_command_history",
        "get_command_state",
    ],
)
def test_command_manager_rejects_controller_missing_required_method(
    controller,
    missing_method,
):
    delattr(controller, missing_method)

    with pytest.raises(
        TypeError,
        match=rf"{missing_method}\(\)",
    ):
        CommandManager(controller)


# ============================================================
# CONTROLLER METHOD ACCESS
# ============================================================


def test_get_controller_method_returns_public_method(
    command_manager,
    controller,
):
    method = command_manager._get_controller_method(
        "execute_command"
    )

    assert method is controller.execute_command


def test_get_controller_method_rejects_missing_method(
    command_manager,
):
    with pytest.raises(
        TypeError,
        match="missing_method",
    ):
        command_manager._get_controller_method(
            "missing_method"
        )


def test_get_controller_returns_controller(
    command_manager,
    controller,
):
    assert command_manager.get_controller() is controller


# ============================================================
# EXECUTION
# ============================================================


def test_execute_delegates_to_controller(
    command_manager,
    controller,
):
    command = object()

    result = command_manager.execute(command)

    assert result == f"executed:{command}"
    assert controller.execute_calls == [command]


def test_execute_passes_command_unchanged(
    command_manager,
    controller,
):
    command = object()

    command_manager.execute(command)

    assert controller.execute_calls[0] is command


def test_execute_rejects_none(
    command_manager,
):
    with pytest.raises(
        ValueError,
        match="command must not be None",
    ):
        command_manager.execute(None)


# ============================================================
# UNDO
# ============================================================


def test_undo_delegates_to_controller(
    command_manager,
    controller,
):
    result = command_manager.undo()

    assert result == "undo-result"
    assert controller.undo_calls == 1


def test_undo_does_not_create_local_history(
    command_manager,
    controller,
):
    command_manager.undo()

    assert not hasattr(
        command_manager,
        "_undo_history",
    )
    assert not hasattr(
        command_manager,
        "_redo_history",
    )


# ============================================================
# REDO
# ============================================================


def test_redo_delegates_to_controller(
    command_manager,
    controller,
):
    result = command_manager.redo()

    assert result == "redo-result"
    assert controller.redo_calls == 1


def test_redo_does_not_create_local_history(
    command_manager,
):
    command_manager.redo()

    assert not hasattr(
        command_manager,
        "_undo_history",
    )
    assert not hasattr(
        command_manager,
        "_redo_history",
    )


# ============================================================
# AVAILABILITY
# ============================================================


def test_can_undo_returns_controller_value(
    command_manager,
    controller,
):
    controller._can_undo = True

    assert command_manager.can_undo() is True


def test_can_undo_returns_false(
    command_manager,
    controller,
):
    controller._can_undo = False

    assert command_manager.can_undo() is False


@pytest.mark.parametrize(
    "invalid_value",
    [
        1,
        0,
        "true",
        "false",
        [],
        [True],
        None,
        object(),
    ],
)
def test_can_undo_rejects_non_boolean_result(
    command_manager,
    controller,
    invalid_value,
):
    controller.can_undo = lambda: invalid_value

    with pytest.raises(
        TypeError,
        match="Controller.can_undo\(\) must return a boolean",
    ):
        command_manager.can_undo()


def test_can_redo_returns_controller_value(
    command_manager,
    controller,
):
    controller._can_redo = True

    assert command_manager.can_redo() is True


def test_can_redo_returns_false(
    command_manager,
    controller,
):
    controller._can_redo = False

    assert command_manager.can_redo() is False


@pytest.mark.parametrize(
    "invalid_value",
    [
        1,
        0,
        "true",
        "false",
        [],
        [True],
        None,
        object(),
    ],
)
def test_can_redo_rejects_non_boolean_result(
    command_manager,
    controller,
    invalid_value,
):
    controller.can_redo = lambda: invalid_value

    with pytest.raises(
        TypeError,
        match="Controller.can_redo\(\) must return a boolean",
    ):
        command_manager.can_redo()


# ============================================================
# HISTORY COUNTS
# ============================================================


def test_undo_count_returns_integer(
    command_manager,
    controller,
):
    controller._undo_count = 7

    assert command_manager.undo_count() == 7


def test_redo_count_returns_integer(
    command_manager,
    controller,
):
    controller._redo_count = 4

    assert command_manager.redo_count() == 4


@pytest.mark.parametrize(
    "invalid_value",
    [
        True,
        False,
        1.5,
        "1",
        None,
        [],
        object(),
    ],
)
def test_undo_count_rejects_invalid_result(
    command_manager,
    controller,
    invalid_value,
):
    controller.undo_count = lambda: invalid_value

    with pytest.raises(
        TypeError,
        match="Controller.undo_count\(\) must return an integer",
    ):
        command_manager.undo_count()


@pytest.mark.parametrize(
    "invalid_value",
    [
        True,
        False,
        1.5,
        "1",
        None,
        [],
        object(),
    ],
)
def test_redo_count_rejects_invalid_result(
    command_manager,
    controller,
    invalid_value,
):
    controller.redo_count = lambda: invalid_value

    with pytest.raises(
        TypeError,
        match="Controller.redo_count\(\) must return an integer",
    ):
        command_manager.redo_count()


# ============================================================
# HISTORY ACCESS
# ============================================================


def test_get_undo_commands_returns_tuple(
    command_manager,
    controller,
):
    command_a = object()
    command_b = object()

    controller._undo_commands = [
        command_a,
        command_b,
    ]

    result = command_manager.get_undo_commands()

    assert result == (
        command_a,
        command_b,
    )
    assert isinstance(result, tuple)


def test_get_redo_commands_returns_tuple(
    command_manager,
    controller,
):
    command_a = object()
    command_b = object()

    controller._redo_commands = [
        command_a,
        command_b,
    ]

    result = command_manager.get_redo_commands()

    assert result == (
        command_a,
        command_b,
    )
    assert isinstance(result, tuple)


def test_get_undo_commands_does_not_retain_controller_collection(
    command_manager,
    controller,
):
    commands = [object()]

    controller._undo_commands = commands

    result = command_manager.get_undo_commands()

    commands.append(object())

    assert len(result) == 1


def test_get_redo_commands_does_not_retain_controller_collection(
    command_manager,
    controller,
):
    commands = [object()]

    controller._redo_commands = commands

    result = command_manager.get_redo_commands()

    commands.append(object())

    assert len(result) == 1


# ============================================================
# COMMAND NAMES
# ============================================================


def test_get_undo_name_returns_string(
    command_manager,
    controller,
):
    controller._undo_name = "Delete Bus"

    assert command_manager.get_undo_name() == "Delete Bus"


def test_get_undo_name_returns_none(
    command_manager,
    controller,
):
    controller._undo_name = None

    assert command_manager.get_undo_name() is None


@pytest.mark.parametrize(
    "invalid_value",
    [
        1,
        True,
        [],
        {},
        object(),
    ],
)
def test_get_undo_name_rejects_invalid_result(
    command_manager,
    controller,
    invalid_value,
):
    controller.get_undo_name = lambda: invalid_value

    with pytest.raises(
        TypeError,
        match="Controller.get_undo_name\(\) must return a string or None",
    ):
        command_manager.get_undo_name()


def test_get_redo_name_returns_string(
    command_manager,
    controller,
):
    controller._redo_name = "Restore Bus"

    assert command_manager.get_redo_name() == "Restore Bus"


def test_get_redo_name_returns_none(
    command_manager,
    controller,
):
    controller._redo_name = None

    assert command_manager.get_redo_name() is None


@pytest.mark.parametrize(
    "invalid_value",
    [
        1,
        True,
        [],
        {},
        object(),
    ],
)
def test_get_redo_name_rejects_invalid_result(
    command_manager,
    controller,
    invalid_value,
):
    controller.get_redo_name = lambda: invalid_value

    with pytest.raises(
        TypeError,
        match="Controller.get_redo_name\(\) must return a string or None",
    ):
        command_manager.get_redo_name()


# ============================================================
# HISTORY MANAGEMENT
# ============================================================


def test_clear_history_delegates_to_controller(
    command_manager,
    controller,
):
    result = command_manager.clear_history()

    assert result == "history-cleared"
    assert controller.clear_history_calls == 1


def test_clear_redo_delegates_to_controller(
    command_manager,
    controller,
):
    result = command_manager.clear_redo()

    assert result == "redo-cleared"
    assert controller.clear_redo_calls == 1


# ============================================================
# RESET
# ============================================================


def test_reset_delegates_to_reset_command_history(
    command_manager,
    controller,
):
    result = command_manager.reset()

    assert result == "history-reset"
    assert controller.reset_command_history_calls == 1


# ============================================================
# STATE
# ============================================================


def test_get_state_returns_dictionary(
    command_manager,
    controller,
):
    controller.command_state = {
        "undo_count": 2,
        "redo_count": 1,
        "can_undo": True,
        "can_redo": True,
    }

    result = command_manager.get_state()

    assert result == controller.command_state
    assert isinstance(result, dict)


def test_get_state_returns_copy(
    command_manager,
    controller,
):
    controller.command_state = {
        "undo_count": 2,
        "redo_count": 1,
    }

    result = command_manager.get_state()

    result["undo_count"] = 99

    assert controller.command_state["undo_count"] == 2


@pytest.mark.parametrize(
    "invalid_value",
    [
        None,
        [],
        (),
        "state",
        1,
        object(),
    ],
)
def test_get_state_rejects_non_dictionary_result(
    command_manager,
    controller,
    invalid_value,
):
    controller.get_command_state = lambda: invalid_value

    with pytest.raises(
        TypeError,
        match="Controller.get_command_state\(\) must return a dictionary",
    ):
        command_manager.get_state()


# ============================================================
# OWNERSHIP / ARCHITECTURAL BOUNDARY
# ============================================================


def test_command_manager_does_not_store_command_history(
    command_manager,
):
    assert not hasattr(
        command_manager,
        "_commands",
    )

    assert not hasattr(
        command_manager,
        "_undo_history",
    )

    assert not hasattr(
        command_manager,
        "_redo_history",
    )


def test_command_manager_does_not_store_core(
    command_manager,
):
    assert not hasattr(
        command_manager,
        "core",
    )

    assert not hasattr(
        command_manager,
        "_core",
    )


def test_command_manager_stores_controller_only(
    command_manager,
    controller,
):
    assert command_manager.controller is controller


def test_execute_does_not_invoke_command_directly(
    command_manager,
    controller,
):
    class CommandSpy:
        def __init__(self):
            self.execute_called = False

        def execute(self, *args, **kwargs):
            self.execute_called = True

    command = CommandSpy()

    command_manager.execute(command)

    assert command.execute_called is False
    assert controller.execute_calls == [command]


# ============================================================
# REPRESENTATION
# ============================================================


def test_repr_contains_command_history_counts(
    command_manager,
    controller,
):
    controller._undo_count = 3
    controller._redo_count = 2

    result = repr(command_manager)

    assert result == (
        "CommandManager("
        "undo=3, "
        "redo=2"
        ")"
    )


def test_repr_uses_question_mark_when_undo_count_fails(
    command_manager,
):
    command_manager.controller.undo_count = (
        lambda: (_ for _ in ()).throw(
            RuntimeError("unavailable")
        )
    )

    result = repr(command_manager)

    assert "undo=?" in result


def test_repr_uses_question_mark_when_redo_count_fails(
    command_manager,
):
    command_manager.controller.redo_count = (
        lambda: (_ for _ in ()).throw(
            TypeError("invalid")
        )
    )

    result = repr(command_manager)

    assert "redo=?" in result


# ============================================================
# QT INDEPENDENCE
# ============================================================


def test_command_manager_is_qt_independent():
    import ui.core.command_manager as module

    assert not hasattr(
        module,
        "QWidget",
    )

    assert not hasattr(
        module,
        "QObject",
    )

    assert not hasattr(
        module,
        "QGraphicsView",
    )


# ============================================================
# PUBLIC API
# ============================================================


def test_public_api_contains_command_manager():
    import ui.core.command_manager as module

    assert module.__all__ == [
        "CommandManager",
    ]
