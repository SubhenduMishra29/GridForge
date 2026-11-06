from __future__ import annotations

from core.application.application import Application
from core.application.command_manager import CommandManager
from core.application.results import ApplicationResult


class FakeCommandManager(CommandManager):
    def __init__(self) -> None:
        pass

    def undo(self):
        return ApplicationResult.success_result(message="undo")

    def redo(self):
        return ApplicationResult.success_result(message="redo")

    def can_undo(self):
        return True

    def can_redo(self):
        return False

    def undo_count(self):
        return 2

    def redo_count(self):
        return 3

    def undo_commands(self):
        return ()

    def redo_commands(self):
        return ()

    def clear_history(self):
        return "cleared"


def test_application_exposes_command_history_through_canonical_facade():
    command_manager = FakeCommandManager()
    application = Application(command_manager=command_manager)

    assert application.can_undo() is True
    assert application.can_redo() is False
    assert application.undo_count() == 2
    assert application.redo_count() == 3
    assert application.undo_commands() == ()
    assert application.redo_commands() == ()
    application.clear_history()
