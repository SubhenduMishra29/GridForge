# ============================================================
# File: ui/controllers/command_controller.py
# GridForge V2 — UI Command Controller
# ============================================================
"""
UI Command Controller for GridForge V2.

Architecture
------------

    UI Action / Toolbar / Menu
                │
                ▼
       CommandController
                │
                ▼
          CommandManager
                │
                ▼
            Command
                │
                ▼
        Application Controller
                │
                ▼
               Core

Purpose
-------
CommandController is the UI orchestration boundary for
command execution.

The UI submits commands through this controller rather than
implementing command history, undo/redo, or Core mutation.

CommandManager remains authoritative for:

    - command execution;
    - command history;
    - undo;
    - redo;
    - command grouping;
    - command lifecycle.

The Core remains authoritative for validation and mutation.

Successful Core mutations remain responsible for producing
authoritative domain events.

Responsibilities
----------------
CommandController:

    - execute commands;
    - undo;
    - redo;
    - expose command-history state;
    - clear history when explicitly requested by application
      lifecycle code;
    - provide diagnostics.

CommandController does NOT:

    - implement commands;
    - mutate Core directly;
    - maintain a second history;
    - decide whether a command is valid;
    - create domain events;
    - modify project revision directly;
    - implement undo/redo semantics;
    - perform Qt operations.

Qt Architecture
---------------
This module intentionally contains no Qt dependency.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.command_manager import CommandManager


class CommandController:
    """
    Thin UI orchestration adapter around CommandManager.

    CommandManager remains the sole owner of command history and
    command execution semantics.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        command_manager: CommandManager,
    ) -> None:
        """
        Initialize the CommandController.

        Parameters
        ----------
        command_manager:
            Existing GridForge CommandManager.

        The manager is not copied or replaced.
        """

        if command_manager is None:
            raise ValueError(
                "command_manager must not be None."
            )

        if not isinstance(
            command_manager,
            CommandManager,
        ):
            raise TypeError(
                "command_manager must be a CommandManager."
            )

        self.command_manager = command_manager

        self._disposed = False

    # ========================================================
    # MANAGER ACCESS
    # ========================================================

    def get_command_manager(
        self,
    ) -> CommandManager:
        """
        Return the underlying CommandManager.
        """

        self._ensure_active()

        return self.command_manager

    # ========================================================
    # EXECUTION
    # ========================================================

    def execute(
        self,
        command: Any,
    ) -> Any:
        """
        Execute a command through CommandManager.

        Parameters
        ----------
        command:
            Command instance implementing the GridForge command
            contract.

        Returns
        -------
        Any
            Result returned by CommandManager.

        Notes
        -----
        Validation and Core mutation are not performed here.
        """

        self._ensure_active()

        if command is None:
            raise ValueError(
                "command must not be None."
            )

        execute = getattr(
            self.command_manager,
            "execute",
            None,
        )

        if not callable(execute):
            raise TypeError(
                "CommandManager must provide execute()."
            )

        return execute(
            command
        )

    # --------------------------------------------------------

    def execute_command(
        self,
        command: Any,
    ) -> Any:
        """
        Explicit alias for execute().
        """

        return self.execute(
            command
        )

    # ========================================================
    # UNDO
    # ========================================================

    def undo(
        self,
    ) -> Any:
        """
        Undo the most recent successful command.

        Undo semantics remain entirely owned by CommandManager.
        """

        self._ensure_active()

        undo = getattr(
            self.command_manager,
            "undo",
            None,
        )

        if not callable(undo):
            raise TypeError(
                "CommandManager must provide undo()."
            )

        return undo()

    # ========================================================
    # REDO
    # ========================================================

    def redo(
        self,
    ) -> Any:
        """
        Redo the most recently undone command.
        """

        self._ensure_active()

        redo = getattr(
            self.command_manager,
            "redo",
            None,
        )

        if not callable(redo):
            raise TypeError(
                "CommandManager must provide redo()."
            )

        return redo()

    # ========================================================
    # CAN UNDO
    # ========================================================

    def can_undo(
        self,
    ) -> bool:
        """
        Return whether an undo operation is currently possible.
        """

        self._ensure_active()

        method = getattr(
            self.command_manager,
            "can_undo",
            None,
        )

        if callable(method):
            return bool(
                method()
            )

        value = getattr(
            self.command_manager,
            "can_undo",
            None,
        )

        if isinstance(
            value,
            bool,
        ):
            return value

        history = getattr(
            self.command_manager,
            "undo_stack",
            None,
        )

        if history is not None:
            try:
                return bool(
                    len(history)
                )
            except TypeError:
                pass

        return False

    # ========================================================
    # CAN REDO
    # ========================================================

    def can_redo(
        self,
    ) -> bool:
        """
        Return whether a redo operation is currently possible.
        """

        self._ensure_active()

        method = getattr(
            self.command_manager,
            "can_redo",
            None,
        )

        if callable(method):
            return bool(
                method()
            )

        value = getattr(
            self.command_manager,
            "can_redo",
            None,
        )

        if isinstance(
            value,
            bool,
        ):
            return value

        history = getattr(
            self.command_manager,
            "redo_stack",
            None,
        )

        if history is not None:
            try:
                return bool(
                    len(history)
                )
            except TypeError:
                pass

        return False

    # ========================================================
    # HISTORY
    # ========================================================

    def history(
        self,
    ) -> tuple[Any, ...]:
        """
        Return the current command history when exposed by
        CommandManager.

        A tuple is returned so callers cannot mutate manager
        history directly.
        """

        self._ensure_active()

        manager = self.command_manager

        getter = getattr(
            manager,
            "get_history",
            None,
        )

        if callable(getter):
            value = getter()

            if value is None:
                return ()

            return tuple(
                value
            )

        value = getattr(
            manager,
            "history",
            None,
        )

        if value is None:
            return ()

        return tuple(
            value
        )

    # --------------------------------------------------------

    def get_history(
        self,
    ) -> tuple[Any, ...]:
        """
        Return the current command history.
        """

        return self.history()

    # --------------------------------------------------------

    def history_count(
        self,
    ) -> int:
        """
        Return the number of commands currently in history.
        """

        return len(
            self.history()
        )

    # ========================================================
    # CURRENT COMMAND
    # ========================================================

    def current_command(
        self,
    ) -> Optional[Any]:
        """
        Return the currently exposed command, if the manager
        provides such a concept.
        """

        self._ensure_active()

        getter = getattr(
            self.command_manager,
            "get_current_command",
            None,
        )

        if callable(getter):
            return getter()

        value = getattr(
            self.command_manager,
            "current_command",
            None,
        )

        return value

    # ========================================================
    # GROUPING
    # ========================================================

    def begin_group(
        self,
        name: Optional[str] = None,
    ) -> Any:
        """
        Begin a command group when supported by CommandManager.

        Grouping is optional infrastructure and is not
        reimplemented here.
        """

        self._ensure_active()

        method = getattr(
            self.command_manager,
            "begin_group",
            None,
        )

        if not callable(method):
            raise NotImplementedError(
                "CommandManager does not support command groups."
            )

        if name is None:
            return method()

        return method(
            name
        )

    # --------------------------------------------------------

    def end_group(
        self,
    ) -> Any:
        """
        End the active command group.
        """

        self._ensure_active()

        method = getattr(
            self.command_manager,
            "end_group",
            None,
        )

        if not callable(method):
            raise NotImplementedError(
                "CommandManager does not support command groups."
            )

        return method()

    # ========================================================
    # CLEAR HISTORY
    # ========================================================

    def clear_history(
        self,
    ) -> Any:
        """
        Clear command history through CommandManager.

        This operation is intended for explicit application
        lifecycle boundaries such as opening a new project.

        It does not alter Core state directly.
        """

        self._ensure_active()

        method = getattr(
            self.command_manager,
            "clear_history",
            None,
        )

        if not callable(method):
            method = getattr(
                self.command_manager,
                "clear",
                None,
            )

        if not callable(method):
            raise TypeError(
                "CommandManager must provide "
                "clear_history() or clear()."
            )

        return method()

    # ========================================================
    # HISTORY INDEX / POSITION
    # ========================================================

    def history_index(
        self,
    ) -> Optional[int]:
        """
        Return the current history position when exposed by
        CommandManager.

        Returns None when the manager does not expose such state.
        """

        self._ensure_active()

        getter = getattr(
            self.command_manager,
            "get_history_index",
            None,
        )

        if callable(getter):
            value = getter()

            if value is None:
                return None

            return int(
                value
            )

        value = getattr(
            self.command_manager,
            "history_index",
            None,
        )

        if value is None:
            return None

        return int(
            value
        )

    # ========================================================
    # COMMAND DESCRIPTION
    # ========================================================

    def describe(
        self,
        command: Any,
    ) -> str:
        """
        Return a command description when supported.

        This method does not construct a description from the
        command's class name because presentation semantics
        belong to the command contract.
        """

        self._ensure_active()

        if command is None:
            raise ValueError(
                "command must not be None."
            )

        method = getattr(
            self.command_manager,
            "describe",
            None,
        )

        if callable(method):
            return str(
                method(
                    command
                )
            )

        description = getattr(
            command,
            "description",
            None,
        )

        if description is not None:
            return str(
                description
            )

        name = getattr(
            command,
            "name",
            None,
        )

        if name is not None:
            return str(
                name
            )

        return type(
            command
        ).__name__

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic command-controller snapshot.

        CommandManager remains authoritative.
        """

        if self._disposed:
            return {
                "disposed": True,
            }

        manager_state: Any = None

        getter = getattr(
            self.command_manager,
            "get_state",
            None,
        )

        if callable(getter):
            manager_state = getter()

        return {
            "disposed": False,
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo(),
            "history_count": self.history_count(),
            "history_index": self.history_index(),
            "manager_state": manager_state,
        }

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose this UI adapter.

        CommandManager is not disposed because it is owned by
        the application composition layer.
        """

        if self._disposed:
            return

        self._disposed = True

    # ========================================================
    # ACTIVE STATE
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure this controller has not been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "CommandController has been disposed."
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        if self._disposed:
            return (
                "CommandController("
                "disposed=True"
                ")"
            )

        return (
            "CommandController("
            f"history={self.history_count()}, "
            f"can_undo={self.can_undo()}, "
            f"can_redo={self.can_redo()}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "CommandController",
]
