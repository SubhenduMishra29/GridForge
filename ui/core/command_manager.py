# ============================================================
# File: ui/core/command_manager.py
# GridForge V2 — UI Command Manager
# ============================================================
"""UI-facing command dispatch facade over the headless Application.

The UI facade owns no command history and performs no domain mutation.
It forwards opaque Application Commands to the canonical Application
boundary. Command-state operations are forwarded only when explicitly
exposed by Application; no Core or Controller reach-through is used.
"""

from __future__ import annotations

from typing import Any


class CommandManager:
    """Thin UI command facade backed directly by ``Application``."""

    def __init__(self, application: Any) -> None:
        if application is None:
            raise ValueError("application must not be None.")

        execute = getattr(application, "execute", None)
        if not callable(execute):
            raise TypeError("application must provide execute().")

        self.application = application

    def execute(self, command: Any) -> Any:
        """Forward one opaque command to ``Application.execute()``."""
        if command is None:
            raise ValueError("command must not be None.")
        return self.application.execute(command)

    def _get_application_method(self, method_name: str) -> Any:
        method = getattr(self.application, method_name, None)
        if not callable(method):
            raise TypeError(
                "Application must provide "
                f"{method_name}() for this UI command operation."
            )
        return method

    def undo(self) -> Any:
        return self._get_application_method("undo")()

    def redo(self) -> Any:
        return self._get_application_method("redo")()

    def can_undo(self) -> bool:
        result = self._get_application_method("can_undo")()
        if not isinstance(result, bool):
            raise TypeError("Application.can_undo() must return a bool.")
        return result

    def can_redo(self) -> bool:
        result = self._get_application_method("can_redo")()
        if not isinstance(result, bool):
            raise TypeError("Application.can_redo() must return a bool.")
        return result

    def undo_count(self) -> int:
        result = self._get_application_method("undo_count")()
        if isinstance(result, bool) or not isinstance(result, int):
            raise TypeError("Application.undo_count() must return an integer.")
        return result

    def redo_count(self) -> int:
        result = self._get_application_method("redo_count")()
        if isinstance(result, bool) or not isinstance(result, int):
            raise TypeError("Application.redo_count() must return an integer.")
        return result

    def get_undo_commands(self) -> tuple[Any, ...]:
        return tuple(self._get_application_method("undo_commands")())

    def get_redo_commands(self) -> tuple[Any, ...]:
        return tuple(self._get_application_method("redo_commands")())

    def clear_history(self) -> Any:
        return self._get_application_method("clear_history")()

    def reset(self) -> Any:
        return self._get_application_method("reset")()

    def get_state(self) -> dict[str, Any]:
        state = self._get_application_method("get_command_state")()
        if not isinstance(state, dict):
            raise TypeError("Application.get_command_state() must return a dictionary.")
        return dict(state)

    def get_application(self) -> Any:
        return self.application

    def __repr__(self) -> str:
        try:
            undo_count = self.undo_count()
        except (RuntimeError, TypeError):
            undo_count = "?"

        try:
            redo_count = self.redo_count()
        except (RuntimeError, TypeError):
            redo_count = "?"

        return f"CommandManager(undo={undo_count}, redo={redo_count})"


__all__ = ["CommandManager"]
