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
    """Coordinate UI state while delegating mutation/history actions to Application."""

    tool_changed = Signal(object, object)
    state_changed = Signal()
    project_changed = Signal(object)
    reset_requested = Signal()

    _SIGNAL_NAMES = frozenset(
        {"tool_changed", "state_changed", "project_changed", "reset_requested"}
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
        self._tool_manager: Any | None = None
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

    def bind_tool_manager(self, tool_manager: Any) -> None:
        """Bind the authoritative ToolManager runtime state."""
        self._ensure_active()
        if tool_manager is None:
            raise ValueError("tool_manager must not be None.")
        if not callable(getattr(tool_manager, "activate", None)) or not callable(getattr(tool_manager, "deactivate", None)):
            raise TypeError("tool_manager must provide activate() and deactivate().")
        if self._tool_manager is not None and self._tool_manager is not tool_manager:
            raise RuntimeError("Controller is already bound to a different ToolManager.")
        self._tool_manager = tool_manager
        self.state_changed.emit()

    def _on_tool_manager_changed(self, tool_id: str | None, previous_tool_id: str | None) -> None:
        """Receive authoritative tool lifecycle changes from ToolManager."""
        self._ensure_active()
        if tool_id == previous_tool_id:
            return
        self.tool_changed.emit(tool_id, previous_tool_id)
        self.state_changed.emit()

    @property
    def tool_id(self) -> str | None:
        manager = self._tool_manager
        return None if manager is None else manager.active_tool_id

    def get_tool_id(self) -> str | None:
        return self.tool_id

    def get_current_tool_id(self) -> str | None:
        return self.tool_id

    def set_tool(self, tool_id: str | None) -> None:
        """Activate the canonical ToolManager tool."""
        self._ensure_active()
        manager = self._tool_manager
        if manager is None:
            raise RuntimeError("Controller requires the canonical ToolManager for tool activation.")
        manager.activate(tool_id)

    def clear_tool(self) -> None:
        self._ensure_active()
        manager = self._tool_manager
        if manager is None:
            raise RuntimeError("Controller requires the canonical ToolManager for tool deactivation.")
        manager.deactivate()

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
        """Delegate command execution to Application."""
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

    def get_command_state(self) -> dict[str, int | bool]:
        """Expose UI-relevant history state without exposing the history implementation."""
        application = self._require_application()
        return {
            "can_undo": application.can_undo(),
            "can_redo": application.can_redo(),
            "undo_count": application.undo_count(),
            "redo_count": application.redo_count(),
        }

    def reset_state(self) -> None:
        self._ensure_active()
        manager = self._tool_manager
        had_project = self._project is not None
        if manager is not None:
            manager.deactivate()
        self._project = None

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
            "tool_id": self.tool_id,
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
        self._tool_manager = None
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
