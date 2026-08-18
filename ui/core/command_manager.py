# ============================================================
# File: ui/core/command_manager.py
# GridForge V2 — UI Command Manager
# ============================================================
"""
UI-facing command dispatch facade for GridForge V2.

Architecture
------------

    UI / Tool / Panel / Toolbar
                │
                ▼
       UI CommandManager
                │
                ▼
           Controller
                │
                ▼
      Core.command_manager
                │
                ▼
             Command
                │
                ▼
              Core
                │
                ▼
         Domain Events


Purpose
-------
CommandManager provides the UI-facing command boundary.

It delegates all authoritative command execution and command
history operations to Controller, which delegates them to the
authoritative Core.command_manager.

This class therefore contains NO independent command history.

Authoritative ownership
-----------------------
Core.command_manager owns:

    - command execution;
    - undo history;
    - redo history;
    - undo/redo transitions;
    - command-history semantics.

Controller owns:

    - command dispatch coordination;
    - access to Core;
    - application/UI state.

UI CommandManager owns only:

    - UI-facing command dispatch convenience;
    - validation of the Controller boundary;
    - command-manager diagnostics;
    - delegation to Controller.

The UI CommandManager does NOT:

    - own command history;
    - store Command objects;
    - execute Command objects directly;
    - call Core directly;
    - mutate Core state;
    - implement individual commands;
    - implement undo semantics;
    - implement redo semantics;
    - implement grouping/coalescing;
    - maintain application state;
    - maintain project state;
    - manage tools;
    - manage canvas state;
    - perform rendering;
    - perform selection;
    - perform navigation;
    - perform snapping;
    - perform electrical calculations.

Canonical execution
-------------------

    command_manager.execute(command)
                │
                ▼
    controller.execute_command(command)
                │
                ▼
    core.command_manager.execute(command)

Canonical undo
--------------

    command_manager.undo()
                │
                ▼
    controller.undo()
                │
                ▼
    core.command_manager.undo()

Canonical redo
--------------

    command_manager.redo()
                │
                ▼
    controller.redo()
                │
                ▼
    core.command_manager.redo()


Command contract
----------------
Commands remain responsible for implementing:

    execute(controller)
    undo(controller)

The UI CommandManager does not inspect command internals.

Composite commands remain ordinary commands.

Grouping/coalescing remains the responsibility of the command
layer.

Qt
--
This module is completely Qt-independent.
"""

from __future__ import annotations

from typing import Any, Optional


class CommandManager:
    """
    UI-facing command dispatch facade.

    The authoritative CommandManager remains owned by Core.

    This class intentionally contains no command history of its
    own and does not duplicate Core command state.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
    ) -> None:
        """
        Initialize the UI command facade.

        Parameters
        ----------
        controller:
            Authoritative GridForge Controller.

        Notes
        -----
        The Controller remains externally owned.

        No command history is created here.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        self.controller = controller

    # ========================================================
    # COMMAND MANAGER ACCESS
    # ========================================================

    def _get_core_command_manager(
        self,
    ) -> Any:
        """
        Return the authoritative Core command manager.

        The UI CommandManager never stores or owns this object.
        """

        core = getattr(
            self.controller,
            "core",
            None,
        )

        if core is None:
            raise RuntimeError(
                "Cannot access command manager without a Core."
            )

        command_manager = getattr(
            core,
            "command_manager",
            None,
        )

        if command_manager is None:
            raise TypeError(
                "Core must provide command_manager."
            )

        return command_manager

    # ========================================================
    # EXECUTION
    # ========================================================

    def execute(
        self,
        command: Any,
    ) -> Any:
        """
        Execute a command through the canonical Controller path.

        Canonical flow:

            UI CommandManager
                ↓
            Controller.execute_command()
                ↓
            Core.command_manager.execute()

        The authoritative Core command manager owns history
        semantics.
        """

        if command is None:
            raise ValueError(
                "command must not be None."
            )

        execute = getattr(
            self.controller,
            "execute_command",
            None,
        )

        if not callable(execute):
            raise TypeError(
                "Controller must provide execute_command()."
            )

        return execute(
            command
        )

    # ========================================================
    # UNDO
    # ========================================================

    def undo(
        self,
    ) -> Any:
        """
        Undo through the canonical Controller/Core pathway.

        History mutation is performed exclusively by
        Core.command_manager.
        """

        undo = getattr(
            self.controller,
            "undo",
            None,
        )

        if not callable(undo):
            raise TypeError(
                "Controller must provide undo()."
            )

        return undo()

    # ========================================================
    # REDO
    # ========================================================

    def redo(
        self,
    ) -> Any:
        """
        Redo through the canonical Controller/Core pathway.

        History mutation is performed exclusively by
        Core.command_manager.
        """

        redo = getattr(
            self.controller,
            "redo",
            None,
        )

        if not callable(redo):
            raise TypeError(
                "Controller must provide redo()."
            )

        return redo()

    # ========================================================
    # AVAILABILITY
    # ========================================================

    def can_undo(
        self,
    ) -> bool:
        """
        Return whether an undo operation is available.

        The authoritative state comes from Core.command_manager.
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "can_undo",
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                "can_undo()."
            )

        return bool(
            method()
        )

    # --------------------------------------------------------

    def can_redo(
        self,
    ) -> bool:
        """
        Return whether a redo operation is available.

        The authoritative state comes from Core.command_manager.
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "can_redo",
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                "can_redo()."
            )

        return bool(
            method()
        )

    # ========================================================
    # HISTORY COUNTS
    # ========================================================

    def undo_count(
        self,
    ) -> int:
        """
        Return the authoritative undo-history count.
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "undo_count",
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                "undo_count()."
            )

        return int(
            method()
        )

    # --------------------------------------------------------

    def redo_count(
        self,
    ) -> int:
        """
        Return the authoritative redo-history count.
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "redo_count",
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                "redo_count()."
            )

        return int(
            method()
        )

    # ========================================================
    # HISTORY ACCESS
    # ========================================================

    def get_undo_commands(
        self,
    ) -> tuple[Any, ...]:
        """
        Return the authoritative undo-history snapshot.

        The UI facade does not maintain its own collection.
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "get_undo_commands",
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                "get_undo_commands()."
            )

        result = method()

        return tuple(
            result
        )

    # --------------------------------------------------------

    def get_redo_commands(
        self,
    ) -> tuple[Any, ...]:
        """
        Return the authoritative redo-history snapshot.
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "get_redo_commands",
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                "get_redo_commands()."
            )

        result = method()

        return tuple(
            result
        )

    # ========================================================
    # COMMAND LABELS
    # ========================================================

    def get_undo_name(
        self,
    ) -> Optional[str]:
        """
        Return the authoritative display name of the next
        undo operation.
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "get_undo_name",
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                "get_undo_name()."
            )

        return method()

    # --------------------------------------------------------

    def get_redo_name(
        self,
    ) -> Optional[str]:
        """
        Return the authoritative display name of the next
        redo operation.
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "get_redo_name",
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                "get_redo_name()."
            )

        return method()

    # ========================================================
    # HISTORY MANAGEMENT
    # ========================================================

    def clear_history(
        self,
    ) -> Any:
        """
        Clear authoritative command history.

        This delegates to Core.command_manager.

        It does not modify application/domain state directly.
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "clear_history",
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                "clear_history()."
            )

        return method()

    # --------------------------------------------------------

    def clear_redo(
        self,
    ) -> Any:
        """
        Clear authoritative redo history.
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "clear_redo",
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                "clear_redo()."
            )

        return method()

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> Any:
        """
        Reset authoritative command-history state.

        Delegates to Core.command_manager.reset() when available.

        This method does not reset Controller state.
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "reset",
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                "reset()."
            )

        return method()

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic command-manager state.

        The returned state originates from the authoritative
        Core command manager.

        A small fallback state is provided only when the Core
        command manager does not expose get_state().
        """

        command_manager = (
            self._get_core_command_manager()
        )

        method = getattr(
            command_manager,
            "get_state",
            None,
        )

        if callable(method):
            state = method()

            if not isinstance(
                state,
                dict,
            ):
                raise TypeError(
                    "Core.command_manager.get_state() "
                    "must return a dictionary."
                )

            return dict(
                state
            )

        return {
            "undo_count": self.undo_count(),
            "redo_count": self.redo_count(),
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo(),
            "undo_name": self.get_undo_name(),
            "redo_name": self.get_redo_name(),
        }

    # ========================================================
    # CONTROLLER ACCESS
    # ========================================================

    def get_controller(
        self,
    ) -> Any:
        """
        Return the associated Controller.

        The Controller remains externally owned.
        """

        return self.controller

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.

        The representation queries authoritative Core history
        state rather than maintaining local history.
        """

        try:
            undo_count = self.undo_count()
        except (RuntimeError, TypeError):
            undo_count = "?"

        try:
            redo_count = self.redo_count()
        except (RuntimeError, TypeError):
            redo_count = "?"

        return (
            "CommandManager("
            f"undo={undo_count}, "
            f"redo={redo_count}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "CommandManager",
]
