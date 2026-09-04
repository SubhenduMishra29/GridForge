# NOTE: This file is retained with its existing UI coordination surface.
# Phase 7.1 makes the headless Application an explicit dependency so the
# composition root no longer mutates the Controller with a hidden runtime
# attribute. Command dispatch for the Bus slice is performed by the dedicated
# UI CommandManager facade and does not use Controller command infrastructure.

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import QObject, Signal


class Controller(QObject):
    """Central UI coordination state and externally supplied application context.

    Controller owns UI/application coordination state. The canonical mutation
    boundary for tools is the Application-backed UI CommandManager; Controller
    is not the command execution owner.
    """

    tool_changed = Signal(object, object)
    selection_changed = Signal(object)
    state_changed = Signal()
    project_changed = Signal(object)
    reset_requested = Signal()

    _SIGNAL_NAMES = frozenset(
        {
            "tool_changed",
            "selection_changed",
            "state_changed",
            "project_changed",
            "reset_requested",
        }
    )

    def __init__(
        self,
        core: Optional[Any] = None,
        parent: Optional[QObject] = None,
        application: Optional[Any] = None,
    ) -> None:
        super().__init__(parent)

        self._core = core
        self.application = application
        # Explicit compatibility name for existing UI callers. This is set
        # during construction rather than attached dynamically by main.py.
        self.gridforge_application = application

        self._tool_id: Optional[str] = None
        self._selected_ids: list[Any] = []
        self._project: Optional[Any] = None
        self._disposed = False
        self._subscriptions: dict[str, list[Any]] = {
            signal_name: [] for signal_name in self._SIGNAL_NAMES
        }

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

    def get_application(self) -> Optional[Any]:
        return self.application

    def set_application(self, application: Optional[Any]) -> None:
        self._ensure_active()
        if self.application is application:
            return
        self.application = application
        self.gridforge_application = application
        self.state_changed.emit()

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

    @property
    def selected_ids(self) -> tuple[Any, ...]:
        return tuple(self._selected_ids)

    def get_selected_ids(self) -> tuple[Any, ...]:
        return self.selected_ids

    def has_selection(self) -> bool:
        return bool(self._selected_ids)

    def is_selected(self, object_id: Any) -> bool:
        if object_id is None:
            return False
        return object_id in self._selected_ids

    def select(self, object_id: Any, multi: bool = False) -> None:
        self._ensure_active()
        if object_id is None:
            raise ValueError("object_id must not be None.")
        if not isinstance(multi, bool):
            raise TypeError("multi must be a bool.")
        if multi:
            if object_id in self._selected_ids:
                return
            self._selected_ids.append(object_id)
        else:
            if len(self._selected_ids) == 1 and self._selected_ids[0] == object_id:
                return
            self._selected_ids = [object_id]
        self._emit_selection_changed()

    def select_many(self, object_ids: Iterable[Any], multi: bool = False) -> None:
        self._ensure_active()
        if object_ids is None:
            raise ValueError("object_ids must not be None.")
        if not isinstance(multi, bool):
            raise TypeError("multi must be a bool.")
        ids: list[Any] = []
        for object_id in object_ids:
            if object_id is None:
                raise ValueError("object_ids must not contain None.")
            if object_id not in ids:
                ids.append(object_id)
        if multi:
            changed = False
            for object_id in ids:
                if object_id not in self._selected_ids:
                    self._selected_ids.append(object_id)
                    changed = True
            if not changed:
                return
        else:
            if self._selected_ids == ids:
                return
            self._selected_ids = ids
        self._emit_selection_changed()

    def toggle_selection(self, object_id: Any) -> None:
        self._ensure_active()
        if object_id is None:
            raise ValueError("object_id must not be None.")
        if object_id in self._selected_ids:
            self._selected_ids.remove(object_id)
        else:
            self._selected_ids.append(object_id)
        self._emit_selection_changed()

    def remove_from_selection(self, object_id: Any) -> None:
        self._ensure_active()
        if object_id is None or object_id not in self._selected_ids:
            return
        self._selected_ids.remove(object_id)
        self._emit_selection_changed()

    def clear_selection(self) -> None:
        self._ensure_active()
        if not self._selected_ids:
            return
        self._selected_ids.clear()
        self._emit_selection_changed()

    def _emit_selection_changed(self) -> None:
        self.selection_changed.emit(self.selected_ids)
        self.state_changed.emit()

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

    def dispose(self) -> None:
        if self._disposed:
            return
        self._subscriptions = {name: [] for name in self._SIGNAL_NAMES}
        self._selected_ids.clear()
        self._tool_id = None
        self._project = None
        self._disposed = True

    def is_disposed(self) -> bool:
        return self._disposed

    def _ensure_active(self) -> None:
        if self._disposed:
            raise RuntimeError("Controller has been disposed.")


__all__ = ["Controller"]
