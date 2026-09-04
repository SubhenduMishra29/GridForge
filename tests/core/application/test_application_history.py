from __future__ import annotations

from core.application.application import Application
from core.application.command_manager import CommandManager


class FakeCommandManager(CommandManager):
    def __init__(self) -> None:
        pass

    def undo(self):
        return "undo-result"

    def redo(self):
        return "redo-result"

    def can_undo(self):
        return True

    def can_redo(self):
        return False

    def undo_count(self):
        return 2

    def redo_count(self):
        return 3

    def undo_commands(self):
        return ("u1", "u2")

    def redo_commands(self):
        return ("r1", "r2", "r3")

    def clear_history(self):
        return "cleared"


def test_application_exposes_command_history_through_canonical_facade():
    command_manager = FakeCommandManager()
    application = Application(command_manager=command_manager)

    assert application.undo() == "undo-result"
    assert application.redo() == "redo-result"
    assert application.can_undo() is True
    assert application.can_redo() is False
    assert application.undo_count() == 2
    assert application.redo_count() == 3
    assert application.undo_commands() == ("u1", "u2")
    assert application.redo_commands() == ("r1", "r2", "r3")
    assert application.clear_history() == "cleared"
