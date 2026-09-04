# ============================================================
# File: ui/core/controller.py
# GridForge V2 — UI Controller
# ============================================================
"""
Central application/UI controller for GridForge V2.

Controller owns application-level coordination state such as the
requested tool identifier and project/application context. It does
not own user selection; UI-Core SelectionManager is the sole selection
authority.

Core command execution/history remains a legacy compatibility boundary
for this controller and is intentionally unchanged by the selection
migration.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QObject, Signal


class Controller(QObject):
    """Central GridForge UI/application controller.

    Selection is owned exclusively by ``ui.core.SelectionManager``.
    This Controller intentionally contains no selection state or
    selection signal.
    """

    # ========================================================
    # SIGNALS
    # ========================================================

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

    # ========================================================
    # COMMAND CONTRACT
    # ========================================================

    _COMMAND_MANAGER_METHODS = (
        "execute",
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
        "reset",
        "get_state",
    )

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        core: Optional[Any] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._core = core
        self._tool_id: Optional[str] = None
        self._project: Optional[Any] = None
        self._disposed = False
        self._subscriptions: dict[str, list[Any]] = {
            signal_name: [] for signal_name in self._SIGNAL_NAMES
        }

    # ========================================================
    # CORE ACCESS
    # ========================================================

    @property
    def core(self) -> Optional[Any]:
        return self._core

    def get_core(self) -> Optional[Any]:
        return self._core

    def set_core(self, core: Optional[Any]) -> None:
        self._ensure_active()
        if self._core is core:
            return
        self._core = core
        self.state_changed.emit()

    # ========================================================
    # TOOL REQUEST STATE
    # ========================================================

    @property
    def tool_id(self) -> Optional[str]:
        return self._tool_id

    def get_tool_id(self) -> Optional[str]:
        return self._tool_id

    def get_current_tool_id(self) -> Optional[str]:
        return self._tool_id

    def set_tool(self, tool_id: Optional[str]) -> None:
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

    # ========================================================
    # PROJECT CONTEXT
    # ========================================================

    @property
    def project(self) -> Optional[Any]:
        return self._project

    def get_project(self) -> Optional[Any]:
        return self._project

    def set_project(self, project: Optional[Any]) -> None:
        self._ensure_active()
        if self._project is project:
            return
        self._project = project
        self.project_changed.emit(project)
        self.state_changed.emit()

    # ========================================================
    # CORE COMMAND BOUNDARY
    # ========================================================

    def _get_command_manager(self) -> Any:
        self._ensure_active()
        core = self._core
        if core is None:
            raise RuntimeError("Cannot access command manager without a Core.")
        command_manager = getattr(core, "command_manager", None)
        if command_manager is None:
            raise TypeError("Core must provide command_manager.")
        return command_manager

    def _get_command_manager_method(self, method_name: str) -> Any:
        if method_name not in self._COMMAND_MANAGER_METHODS:
            raise ValueError(f"Unknown command-manager method: {method_name!r}")
        method = getattr(self._get_command_manager(), method_name, None)
        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                f"{method_name}()."
            )
        return method

    def execute_command(self, command: Any) -> Any:
        self._ensure_active()
        if command is None:
            raise ValueError("command must not be None.")
        result = self._get_command_manager_method("execute")(command)
        self.state_changed.emit()
        return result

    # ========================================================
    # UNDO / REDO
    # ========================================================

    def undo(self) -> Any:
        self._ensure_active()
        result = self._get_command_manager_method("undo")()
        self.state_changed.emit()
        return result

    def redo(self) -> Any:
        self._ensure_active()
        result = self._get_command_manager_method("redo")()
        self.state_changed.emit()
        return result

    # ========================================================
    # COMMAND AVAILABILITY
    # ========================================================

    def can_undo(self) -> bool:
        result = self._get_command_manager_method("can_undo")()
        if not isinstance(result, bool):
            raise TypeError("Core.command_manager.can_undo() must return a bool.")
        return result

    def can_redo(self) -> bool:
        result = self._get_command_manager_method("can_redo")()
        if not isinstance(result, bool):
            raise TypeError("Core.command_manager.can_redo() must return a bool.")
        return result

    # ========================================================
    # COMMAND HISTORY COUNTS
    # ========================================================

    def undo_count(self) -> int:
        result = self._get_command_manager_method("undo_count")()
        if isinstance(result, bool) or not isinstance(result, int):
            raise TypeError("Core.command_manager.undo_count() must return an integer.")
        return result

    def redo_count(self) -> int:
        result = self._get_command_manager_method("redo_count")()
        if isinstance(result, bool) or not isinstance(result, int):
            raise TypeError("Core.command_manager.redo_count() must return an integer.")
        return result

    # ========================================================
    # COMMAND HISTORY ACCESS
    # ========================================================

    def get_undo_commands(self) -> tuple[Any, ...]:
        try:
            return tuple(self._get_command_manager_method("get_undo_commands")())
        except TypeError as exc:
            raise TypeError(
                "Core.command_manager.get_undo_commands() must return an iterable."
            ) from exc

    def get_redo_commands(self) -> tuple[Any, ...]:
        try:
            return tuple(self._get_command_manager_method("get_redo_commands")())
        except TypeError as exc:
            raise TypeError(
                "Core.command_manager.get_redo_commands() must return an iterable."
            ) from exc

    # ========================================================
    # COMMAND HISTORY LABELS
    # ========================================================

    def get_undo_name(self) -> Optional[str]:
        result = self._get_command_manager_method("get_undo_name")()
        if result is not None and not isinstance(result, str):
            raise TypeError(
                "Core.command_manager.get_undo_name() must return a string or None."
            )
        return result

    def get_redo_name(self) -> Optional[str]:
        result = self._get_command_manager_method("get_redo_name")()
        if result is not None and not isinstance(result, str):
            raise TypeError(
                "Core.command_manager.get_redo_name() must return a string or None."
            )
        return result

    # ========================================================
    # COMMAND HISTORY MANAGEMENT
    # ========================================================

    def clear_history(self) -> Any:
        result = self._get_command_manager_method("clear_history")()
        self.state_changed.emit()
        return result

    def clear_redo(self) -> Any:
        result = self._get_command_manager_method("clear_redo")()
        self.state_changed.emit()
        return result

    def reset_command_history(self) -> Any:
        result = self._get_command_manager_method("reset")()
        self.state_changed.emit()
        return result

    # ========================================================
    # COMMAND STATE
    # ========================================================

    def get_command_state(self) -> dict[str, Any]:
        state = self._get_command_manager_method("get_state")()
        if not isinstance(state, dict):
            raise TypeError(
                "Core.command_manager.get_state() must return a dictionary."
            )
        return dict(state)

    # ========================================================
    # CONTROLLER STATE RESET
    # ========================================================

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

    # ========================================================
    # SUBSCRIPTION API
    # ========================================================

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

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(self) -> dict[str, Any]:
        return {
            "tool_id": self._tool_id,
            "has_core": self._core is not None,
            "has_project": self._project is not None,
            "disposed": self._disposed,
        }

    def __repr__(self) -> str:
        return (
            "Controller("
            f"tool={self._tool_id!r}, "
            f"core={self._core is not None}, "
            f"disposed={self._disposed}"
            ")"
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

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
        self._disposed = True

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    def _ensure_active(self) -> None:
        if self._disposed:
            raise RuntimeError("Controller has been disposed.")


__all__ = ["Controller"]
