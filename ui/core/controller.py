```python
# ============================================================
# File: ui/core/controller.py
# GridForge V2 — UI Controller
# ============================================================
"""
Central application/UI controller for GridForge V2.

Controller is the UI/application coordination boundary.

Ownership
---------

Controller owns:

    - application-level tool-selection intent;
    - authoritative application selection;
    - project/application context;
    - access to Core;
    - command dispatch coordination;
    - public UI state notifications.

Controller does NOT:

    - own concrete tools;
    - activate/deactivate tools;
    - process input events;
    - render graphics;
    - perform snapping;
    - perform navigation;
    - perform coordinate conversion;
    - perform electrical calculations;
    - duplicate Core domain state.

Tool selection
--------------

Controller stores the requested tool identifier.

Canonical flow:

    Controller.set_tool("bus")
            |
            v
    tool_changed("bus", previous)
            |
            v
       ToolManager
            |
            v
      tool lifecycle

Controller never calls ToolManager directly.

Selection
---------

Controller owns persistent application selection.

Graphics selection is a projection of this state.

Core
----

Core remains authoritative for domain/model state.

Controller provides access to Core and coordinates UI-side
operations through the Core command boundary.

Qt
--

All Qt dependencies are imported through ui.core.qt.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import QObject, Signal


class Controller(QObject):
    """
    Central GridForge UI/application controller.

    The Controller is independent of Canvas, Tools, Renderers,
    and GraphicsItems.

    Concrete tool lifecycle belongs to ToolManager.
    """

    # ========================================================
    # SIGNALS
    # ========================================================

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

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        core: Optional[Any] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        Initialize Controller.

        Controller does not take ownership of Core.
        """

        super().__init__(parent)

        self._core = core

        # Application-level requested tool.
        self._tool_id: Optional[str] = None

        # Authoritative application selection.
        self._selected_ids: list[Any] = []

        # External project/application context.
        self._project: Optional[Any] = None

        # Controller lifecycle.
        self._disposed = False

        # ----------------------------------------------------
        # Track subscriptions explicitly.
        #
        # This gives Controller deterministic cleanup and
        # prevents duplicate registrations.
        # ----------------------------------------------------

        self._subscriptions: dict[
            str,
            list[Any],
        ] = {
            signal_name: []
            for signal_name in self._SIGNAL_NAMES
        }

    # ========================================================
    # CORE ACCESS
    # ========================================================

    @property
    def core(self) -> Optional[Any]:
        """Return the associated Core object."""
        return self._core

    # --------------------------------------------------------

    def get_core(self) -> Optional[Any]:
        """Return the associated Core object."""
        return self._core

    # --------------------------------------------------------

    def set_core(
        self,
        core: Optional[Any],
    ) -> None:
        """
        Attach or replace the Core object.

        Controller does not inspect or duplicate Core state.
        """

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
        """
        Return the currently requested application-level tool ID.

        This is requested application state, not active tool
        lifecycle state.
        """

        return self._tool_id

    # --------------------------------------------------------

    def get_tool_id(self) -> Optional[str]:
        """Return the currently requested tool identifier."""
        return self._tool_id

    # --------------------------------------------------------

    def set_tool(
        self,
        tool_id: Optional[str],
    ) -> None:
        """
        Request an application-level tool.

        None clears the current tool request.

        Controller does not construct or activate tools.
        """

        self._ensure_active()

        if tool_id is not None:

            if not isinstance(tool_id, str):
                raise TypeError(
                    "tool_id must be a string or None."
                )

            tool_id = tool_id.strip()

            if not tool_id:
                raise ValueError(
                    "tool_id must not be empty."
                )

        previous_tool_id = self._tool_id

        if previous_tool_id == tool_id:
            return

        self._tool_id = tool_id

        self.tool_changed.emit(
            tool_id,
            previous_tool_id,
        )

        self.state_changed.emit()

    # --------------------------------------------------------

    def clear_tool(self) -> None:
        """Clear the current application-level tool request."""
        self.set_tool(None)

    # ========================================================
    # SELECTION
    # ========================================================

    @property
    def selected_ids(self) -> tuple[Any, ...]:
        """
        Return an immutable snapshot of application selection.
        """

        return tuple(self._selected_ids)

    # --------------------------------------------------------

    def get_selected_ids(
        self,
    ) -> tuple[Any, ...]:
        """Return the authoritative application selection."""
        return self.selected_ids

    # --------------------------------------------------------

    def has_selection(self) -> bool:
        """Return whether at least one object is selected."""
        return bool(self._selected_ids)

    # --------------------------------------------------------

    def is_selected(
        self,
        object_id: Any,
    ) -> bool:
        """Return whether an object is selected."""

        if object_id is None:
            return False

        return object_id in self._selected_ids

    # --------------------------------------------------------

    def select(
        self,
        object_id: Any,
        multi: bool = False,
    ) -> None:
        """
        Select an application object.

        multi=False replaces the selection.

        multi=True adds to the selection.
        """

        self._ensure_active()

        if object_id is None:
            raise ValueError(
                "object_id must not be None."
            )

        if not isinstance(multi, bool):
            raise TypeError(
                "multi must be a bool."
            )

        if multi:

            if object_id in self._selected_ids:
                return

            self._selected_ids.append(
                object_id
            )

        else:

            if (
                len(self._selected_ids) == 1
                and self._selected_ids[0] == object_id
            ):
                return

            self._selected_ids = [
                object_id
            ]

        self._emit_selection_changed()

    # --------------------------------------------------------

    def select_many(
        self,
        object_ids: Iterable[Any],
        multi: bool = False,
    ) -> None:
        """
        Select multiple application objects.

        Duplicate IDs are removed while preserving input order.
        """

        self._ensure_active()

        if object_ids is None:
            raise ValueError(
                "object_ids must not be None."
            )

        if not isinstance(multi, bool):
            raise TypeError(
                "multi must be a bool."
            )

        ids: list[Any] = []

        for object_id in object_ids:

            if object_id is None:
                raise ValueError(
                    "object_ids must not contain None."
                )

            if object_id not in ids:
                ids.append(object_id)

        if multi:

            changed = False

            for object_id in ids:

                if object_id not in self._selected_ids:

                    self._selected_ids.append(
                        object_id
                    )

                    changed = True

            if not changed:
                return

        else:

            if self._selected_ids == ids:
                return

            self._selected_ids = ids

        self._emit_selection_changed()

    # --------------------------------------------------------

    def toggle_selection(
        self,
        object_id: Any,
    ) -> None:
        """Toggle an object in the authoritative selection."""

        self._ensure_active()

        if object_id is None:
            raise ValueError(
                "object_id must not be None."
            )

        if object_id in self._selected_ids:

            self._selected_ids.remove(
                object_id
            )

        else:

            self._selected_ids.append(
                object_id
            )

        self._emit_selection_changed()

    # --------------------------------------------------------

    def remove_from_selection(
        self,
        object_id: Any,
    ) -> None:
        """Remove an object from the authoritative selection."""

        self._ensure_active()

        if object_id is None:
            return

        if object_id not in self._selected_ids:
            return

        self._selected_ids.remove(
            object_id
        )

        self._emit_selection_changed()

    # --------------------------------------------------------

    def clear_selection(self) -> None:
        """Clear the authoritative application selection."""

        self._ensure_active()

        if not self._selected_ids:
            return

        self._selected_ids.clear()

        self._emit_selection_changed()

    # --------------------------------------------------------

    def _emit_selection_changed(self) -> None:
        """
        Emit the canonical selection and state notifications.
        """

        self.selection_changed.emit(
            self.selected_ids
        )

        self.state_changed.emit()

    # ========================================================
    # PROJECT CONTEXT
    # ========================================================

    @property
    def project(self) -> Optional[Any]:
        """Return the current project/application context."""
        return self._project

    # --------------------------------------------------------

    def get_project(self) -> Optional[Any]:
        """Return the current project/application context."""
        return self._project

    # --------------------------------------------------------

    def set_project(
        self,
        project: Optional[Any],
    ) -> None:
        """
        Set the current project/application context.

        Controller does not duplicate project domain state.
        """

        self._ensure_active()

        if self._project is project:
            return

        self._project = project

        self.project_changed.emit(
            project
        )

        self.state_changed.emit()

    # ========================================================
    # COMMAND DISPATCH
    # ========================================================

    def execute_command(
        self,
        command: Any,
    ) -> Any:
        """
        Execute a command through the Core command boundary.
        """

        self._ensure_active()

        if command is None:
            raise ValueError(
                "command must not be None."
            )

        core = self._core

        if core is None:
            raise RuntimeError(
                "Cannot execute command without a Core."
            )

        execute = getattr(
            core,
            "execute_command",
            None,
        )

        if callable(execute):

            result = execute(command)

            self.state_changed.emit()

            return result

        command_manager = getattr(
            core,
            "command_manager",
            None,
        )

        execute = getattr(
            command_manager,
            "execute",
            None,
        )

        if callable(execute):

            result = execute(command)

            self.state_changed.emit()

            return result

        raise TypeError(
            "Core must provide execute_command() "
            "or command_manager.execute()."
        )

    # ========================================================
    # UNDO / REDO
    # ========================================================

    def undo(self) -> Any:
        """Request an undo operation through Core."""

        self._ensure_active()

        core = self._core

        if core is None:
            raise RuntimeError(
                "Cannot undo without a Core."
            )

        undo = getattr(
            core,
            "undo",
            None,
        )

        if callable(undo):

            result = undo()

            self.state_changed.emit()

            return result

        command_manager = getattr(
            core,
            "command_manager",
            None,
        )

        undo = getattr(
            command_manager,
            "undo",
            None,
        )

        if callable(undo):

            result = undo()

            self.state_changed.emit()

            return result

        raise TypeError(
            "Core must provide undo() "
            "or command_manager.undo()."
        )

    # --------------------------------------------------------

    def redo(self) -> Any:
        """Request a redo operation through Core."""

        self._ensure_active()

        core = self._core

        if core is None:
            raise RuntimeError(
                "Cannot redo without a Core."
            )

        redo = getattr(
            core,
            "redo",
            None,
        )

        if callable(redo):

            result = redo()

            self.state_changed.emit()

            return result

        command_manager = getattr(
            core,
            "command_manager",
            None,
        )

        redo = getattr(
            command_manager,
            "redo",
            None,
        )

        if callable(redo):

            result = redo()

            self.state_changed.emit()

            return result

        raise TypeError(
            "Core must provide redo() "
            "or command_manager.redo()."
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset_state(self) -> None:
        """
        Reset Controller-owned transient application state.

        Core is not modified.

        ToolManager observes tool_changed(None, previous_tool)
        and owns the actual tool lifecycle transition.
        """

        self._ensure_active()

        previous_tool_id = self._tool_id
        had_selection = bool(self._selected_ids)
        had_project = self._project is not None

        self._tool_id = None
        self._selected_ids.clear()
        self._project = None

        changed = False

        if previous_tool_id is not None:

            self.tool_changed.emit(
                None,
                previous_tool_id,
            )

            changed = True

        if had_selection:

            self.selection_changed.emit(
                self.selected_ids
            )

            changed = True

        if had_project:
            self.project_changed.emit(
                None
            )

            changed = True

        self.reset_requested.emit()

        # Reset itself is an application state transition even
        # when Controller-owned state was already empty.
        self.state_changed.emit()

    # ========================================================
    # SUBSCRIPTION API
    # ========================================================

    def subscribe(
        self,
        signal_name: str,
        callback: Any,
    ) -> None:
        """
        Subscribe to one of the Controller's public signals.

        Duplicate subscriptions are ignored.
        """

        self._ensure_active()

        self._validate_subscription(
            signal_name,
            callback,
        )

        callbacks = self._subscriptions[
            signal_name
        ]

        if callback in callbacks:
            return

        signal = getattr(
            self,
            signal_name,
        )

        signal.connect(
            callback
        )

        callbacks.append(
            callback
        )

    # --------------------------------------------------------

    def unsubscribe(
        self,
        signal_name: str,
        callback: Any,
    ) -> None:
        """
        Remove a Controller signal subscription.

        Missing subscriptions are ignored.
        """

        self._ensure_active()

        self._validate_subscription(
            signal_name,
            callback,
        )

        callbacks = self._subscriptions[
            signal_name
        ]

        if callback not in callbacks:
            return

        signal = getattr(
            self,
            signal_name,
        )

        try:
            signal.disconnect(
                callback
            )
        except (RuntimeError, TypeError):
            # Qt may report an already-disconnected callback.
            pass
        finally:
            if callback in callbacks:
                callbacks.remove(
                    callback
                )

    # --------------------------------------------------------

    @classmethod
    def _validate_subscription(
        cls,
        signal_name: str,
        callback: Any,
    ) -> None:
        """Validate a public Controller subscription."""

        if not isinstance(
            signal_name,
            str,
        ):
            raise TypeError(
                "signal_name must be a string."
            )

        if signal_name not in cls._SIGNAL_NAMES:
            raise ValueError(
                f"Unknown Controller signal: "
                f"{signal_name!r}"
            )

        if not callable(callback):
            raise TypeError(
                "callback must be callable."
            )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(self) -> dict[str, Any]:
        """Return a diagnostic snapshot of Controller state."""

        return {
            "tool_id": self._tool_id,
            "selected_ids": self.selected_ids,
            "selected_count": len(
                self._selected_ids
            ),
            "has_core": self._core is not None,
            "has_project": self._project is not None,
            "disposed": self._disposed,
        }

    # --------------------------------------------------------

    def __repr__(self) -> str:
        """Return a concise diagnostic representation."""

        return (
            "Controller("
            f"tool={self._tool_id!r}, "
            f"selected={len(self._selected_ids)}, "
            f"core={self._core is not None}, "
            f"disposed={self._disposed}"
            ")"
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(self) -> None:
        """
        Dispose the Controller.

        Controller does not own Core.

        All Controller-owned subscriptions are disconnected
        before the Controller is marked disposed.
        """

        if self._disposed:
            return

        # ----------------------------------------------------
        # Disconnect registered callbacks first.
        # ----------------------------------------------------

        for signal_name, callbacks in self._subscriptions.items():

            signal = getattr(
                self,
                signal_name,
            )

            for callback in tuple(callbacks):

                try:
                    signal.disconnect(
                        callback
                    )
                except (RuntimeError, TypeError):
                    pass

            callbacks.clear()

        # ----------------------------------------------------
        # Clear Controller-owned state.
        # ----------------------------------------------------

        self._tool_id = None
        self._selected_ids.clear()
        self._project = None

        # Core is external and therefore deliberately retained
        # as a non-owned reference until object destruction.
        #
        # No Core mutation occurs here.

        self._disposed = True

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    def _ensure_active(self) -> None:
        """Ensure the Controller has not been disposed."""

        if self._disposed:
            raise RuntimeError(
                "Controller has been disposed."
            )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "Controller",
]
```
