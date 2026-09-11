# ============================================================
# File: ui/core/controller.py
# GridForge V2 — UI Controller
# Author: Subhendu Mishra
# ============================================================
"""UI coordination controller for GridForge V2.

The Controller owns presentation/interaction coordination only. Core
authority, command execution, transactions, and history remain behind the
headless ``core.application.Application`` boundary.
"""

from __future__ import annotations

from typing import Any

from core.application import Application
from ui.core.qt import QObject, Signal


class Controller(QObject):
    """Coordinate UI state while delegating mutation/history to Application."""

    tool_changed = Signal(object, object)
    state_changed = Signal()
    project_changed = Signal(object)
    reset_requested = Signal()

    _SIGNAL_NAMES = frozenset(
        {
            "tool_changed",
            "state_changed",
            "project_changed",
            "reset_requested",
        }
    )

    def __init__(
        self,
        application: Application | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        if application is not None and not isinstance(application, Application):
            raise TypeError("application must be a core.application.Application.")
        self.application = application
        self._tool_id: str | None = None
        self._project: Any | None = None
        self._disposed = False
        self._subscriptions: dict[str, list[Any]] = {
            signal_name: [] for signal_name in self._SIGNAL_NAMES
        }

    def get_application(self) -> Application | None:
        """Return the configured Application boundary."""
        return self.application

    def set_application(self, application: Application | None) -> None:
        """Set the Application boundary used for mutation/history delegation."""
        self._ensure_active()
        if application is not None and not isinstance(application, Application):
            raise TypeError("application must be a core.application.Application.")
        if self.application is application:
            return
        self.application = application
        self.state_changed.emit()

    @property
    def tool_id(self) -> str | None:
        return self._tool_id

    def get_tool_id(self) -> str | None:
        return self._tool_id

    def get_current_tool_id(self) -> str | None:
        return self._tool_id

    def set_tool(self, tool_id: str | None) -> None:
        self._ensure_active()
        if tool_id is not None:
            if not isinstance(tool_id, str):
                raise TypeError("tool_id must be a string or None.")
            tool_id = tool_id.strip()
            if not tool_id:
                raise ValueError("tool_id must not be empty.")

        previous_tool_id = self._tool_id
        if previous_tool_id == tool_id:
            return
        self._tool_id = tool_id
        self.tool_changed.emit(tool_id, previous_tool_id)
        self.state_changed.emit()

    def clear_tool(self) -> None:
        self.set_tool(None)

    @property
    def project(self) -> Any | None:
        return self._project

    def get_project(self) -> Any | None:
        return self._project

    def set_project(self, project: Any | None) -> None:
        self._ensure_active()
        if self._project is project:
            return
        self._project = project
        self.project_changed.emit(project)
        self.state_changed.emit()

    def execute_command(self, command: Any) -> Any:
        """Delegate command execution to Application; Controller never owns Core authority."""
        application = self._require_application()
        if command is None:
            raise ValueError("command must not be None.")
        result = application.execute(command)
        self.state_changed.emit()
        return result

    def undo(self) -> Any:
        """Delegate undo to Application."""
        result = self._require_application().undo()
        self.state_changed.emit()
        return result

    def redo(self) -> Any:
        """Delegate redo to Application."""
        result = self._require_application().redo()
        self.state_changed.emit()
        return result

    def can_undo(self) -> bool:
        return self._require_application().can_undo()

    def can_redo(self) -> bool:
        return self._require_application().can_redo()

    def undo_count(self) -> int:
        return self._require_application().undo_count()

    def redo_count(self) -> int:
        return self._require_application().redo_count()

    def get_undo_commands(self) -> tuple:
        return self._require_application().undo_commands()

    def get_redo_commands(self) -> tuple:
        return self._require_application().redo_commands()

    def get_undo_name(self) -> str | None:
        commands = self.get_undo_commands()
        if not commands:
            return None
        return getattr(commands[-1], "name", None)

    def get_redo_name(self) -> str | None:
        commands = self.get_redo_commands()
        if not commands:
            return None
        return getattr(commands[-1], "name", None)

    def clear_history(self) -> None:
        self._require_application().clear_history()
        self.state_changed.emit()

    def clear_redo(self) -> None:
        # Application owns history. There is deliberately no UI-side redo store.
        self.clear_history()

    def reset_command_history(self) -> None:
        self.clear_history()

    def get_command_state(self) -> dict[str, Any]:
        application = self._require_application()
        return {
            "can_undo": application.can_undo(),
            "can_redo": application.can_redo(),
            "undo_count": application.undo_count(),
            "redo_count": application.redo_count(),
        }

    def reset_state(self) -> None:
        self._ensure_active()
        previous_tool_id = self._tool_id
        had_project = self._project is not None
        self._tool_id = None
        self._project = None

        if previous_tool_id is not None:
            self.tool_changed.emit(None, previous_tool_id)
        if had_project:
            self.project_changed.emit(None)
        self.reset_requested.emit()
        self.state_changed.emit()

    def subscribe(self, signal_name: str, callback: Any) -> None:
        self._ensure_active()
        self._validate_subscription(signal_name, callback)
        callbacks = self._subscriptions[signal_name]
        if callback in callbacks:
            return
        getattr(self, signal_name).connect(callback)
        callbacks.append(callback)

    def unsubscribe(self, signal_name: str, callback: Any) -> None:
        self._ensure_active()
        self._validate_subscription(signal_name, callback)
        callbacks = self._subscriptions[signal_name]
        if callback not in callbacks:
            return
        signal = getattr(self, signal_name)
        try:
            signal.disconnect(callback)
        except (RuntimeError, TypeError):
            pass
        finally:
            if callback in callbacks:
                callbacks.remove(callback)

    @classmethod
    def _validate_subscription(cls, signal_name: str, callback: Any) -> None:
        if not isinstance(signal_name, str):
            raise TypeError("signal_name must be a string.")
        if signal_name not in cls._SIGNAL_NAMES:
            raise ValueError(f"Unknown Controller signal: {signal_name!r}")
        if not callable(callback):
            raise TypeError("callback must be callable.")

    def get_state(self) -> dict[str, Any]:
        return {
            "tool_id": self._tool_id,
            "has_application": self.application is not None,
            "has_project": self._project is not None,
            "disposed": self._disposed,
        }

    def dispose(self) -> None:
        if self._disposed:
            return
        for signal_name, callbacks in self._subscriptions.items():
            signal = getattr(self, signal_name)
            for callback in tuple(callbacks):
                try:
                    signal.disconnect(callback)
                except (RuntimeError, TypeError):
                    pass
            callbacks.clear()
        self._tool_id = None
        self._project = None
        self.application = None
        self._disposed = True

    def _require_application(self) -> Application:
        self._ensure_active()
        if self.application is None:
            raise RuntimeError("Application is required for mutation/history operations.")
        return self.application

    def _ensure_active(self) -> None:
        if self._disposed:
            raise RuntimeError("Controller has been disposed.")


__all__ = ["Controller"]
