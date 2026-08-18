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
CommandManager is the UI-facing command boundary.

It does NOT own command execution state or command history.

All authoritative command execution and history operations are
delegated to the Controller.

The Controller remains the only UI/application boundary through
which the UI command layer reaches Core.

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
    - application/UI state;
    - the public command-history boundary.

UI CommandManager owns only:

    - UI-facing command dispatch;
    - validation of the Controller command boundary;
    - delegation;
    - command diagnostics;
    - convenience methods for UI consumers.

The UI CommandManager does NOT:

    - own command history;
    - store Command objects;
    - execute Command objects directly;
    - access Core directly;
    - access Core.command_manager directly;
    - mutate Core state;
    - implement commands;
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

Canonical state queries
-----------------------

    command_manager.can_undo()
                │
                ▼
    controller.can_undo()
                │
                ▼
    core.command_manager.can_undo()

The same pattern applies to:

    - can_redo()
    - undo_count()
    - redo_count()
    - get_undo_commands()
    - get_redo_commands()
    - get_undo_name()
    - get_redo_name()
    - clear_history()
    - clear_redo()
    - reset()
    - get_command_state()

Command contract
----------------
Commands are opaque to the UI CommandManager.

The UI CommandManager does not inspect or invoke command
internals. Commands are forwarded unchanged to the Controller,
which delegates authoritative execution to Core.command_manager.

Composite commands are treated identically to ordinary commands.

Command execution, undo semantics, redo semantics, grouping,
coalescing, and history ownership remain responsibilities of
the authoritative Core command layer.

Qt
--
This module is completely Qt-independent.
"""

from __future__ import annotations

from typing import Any, Optional


class CommandManager:
    """
    UI-facing command dispatch facade.

    This object intentionally contains no independent command
    history.

    The authoritative command manager remains owned by Core and
    is accessed exclusively through the public Controller
    command boundary.
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

        Raises
        ------
        ValueError
            If controller is None.

        TypeError
            If the Controller does not expose the required
            command-boundary interface.

        Notes
        -----
        The Controller remains externally owned.

        No command history or command state is created here.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        self._validate_controller(
            controller
        )

        self.controller = controller

    # ========================================================
    # CONTROLLER VALIDATION
    # ========================================================

    @staticmethod
    def _validate_controller(
        controller: Any,
    ) -> None:
        """
        Validate the required public Controller command API.

        The UI CommandManager deliberately depends on the public
        Controller boundary rather than inspecting Core.

        Required Controller methods:

            execute_command()
            undo()
            redo()
            can_undo()
            can_redo()
            undo_count()
            redo_count()
            get_undo_commands()
            get_redo_commands()
            get_undo_name()
            get_redo_name()
            clear_history()
            clear_redo()
            reset_command_history()
            get_command_state()
        """

        required_methods = (
            "execute_command",
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
            "reset_command_history",
            "get_command_state",
        )

        for method_name in required_methods:

            method = getattr(
                controller,
                method_name,
                None,
            )

            if not callable(method):
                raise TypeError(
                    "Controller must provide "
                    f"public command-boundary method "
                    f"{method_name}()."
                )

    # ========================================================
    # CONTROLLER METHOD ACCESS
    # ========================================================

    def _get_controller_method(
        self,
        method_name: str,
    ) -> Any:
        """
        Return a validated public Controller method.

        This helper centralizes boundary validation.

        No private Controller members and no Core members are
        accessed by the UI CommandManager.
        """

        method = getattr(
            self.controller,
            method_name,
            None,
        )

        if not callable(method):
            raise TypeError(
                "Controller must provide "
                f"{method_name}()."
            )

        return method

    # ========================================================
    # EXECUTION
    # ========================================================

    def execute(
        self,
        command: Any,
    ) -> Any:
        """
        Execute a command through the canonical Controller path.

        Flow:

            UI CommandManager
                ↓
            Controller.execute_command()
                ↓
            Core.command_manager.execute()

        The UI CommandManager performs no command execution
        itself.
        """

        if command is None:
            raise ValueError(
                "command must not be None."
            )

        execute = self._get_controller_method(
            "execute_command"
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
        Undo through the canonical Controller path.

        Flow:

            UI CommandManager
                ↓
            Controller.undo()
                ↓
            Core.command_manager.undo()
        """

        undo = self._get_controller_method(
            "undo"
        )

        return undo()

    # ========================================================
    # REDO
    # ========================================================

    def redo(
        self,
    ) -> Any:
        """
        Redo through the canonical Controller path.

        Flow:

            UI CommandManager
                ↓
            Controller.redo()
                ↓
            Core.command_manager.redo()
        """

        redo = self._get_controller_method(
            "redo"
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

        The authoritative answer comes from Core through the
        Controller command boundary.

        The Controller contract requires an actual bool result.
        """

        method = self._get_controller_method(
            "can_undo"
        )

        result = method()

        if not isinstance(result, bool):
            raise TypeError(
                "Controller.can_undo() must return "
                "a boolean."
            )

        return result

    # --------------------------------------------------------

    def can_redo(
        self,
    ) -> bool:
        """
        Return whether a redo operation is available.

        The authoritative answer comes from Core through the
        Controller command boundary.

        The Controller contract requires an actual bool result.
        """

        method = self._get_controller_method(
            "can_redo"
        )

        result = method()

        if not isinstance(result, bool):
            raise TypeError(
                "Controller.can_redo() must return "
                "a boolean."
            )

        return result

    # ========================================================
    # HISTORY COUNTS
    # ========================================================

    def undo_count(
        self,
    ) -> int:
        """
        Return the authoritative undo-history count.
        """

        method = self._get_controller_method(
            "undo_count"
        )

        result = method()

        if isinstance(result, bool):
            raise TypeError(
                "Controller.undo_count() must return "
                "an integer."
            )

        if not isinstance(result, int):
            raise TypeError(
                "Controller.undo_count() must return "
                "an integer."
            )

        return result

    # --------------------------------------------------------

    def redo_count(
        self,
    ) -> int:
        """
        Return the authoritative redo-history count.
        """

        method = self._get_controller_method(
            "redo_count"
        )

        result = method()

        if isinstance(result, bool):
            raise TypeError(
                "Controller.redo_count() must return "
                "an integer."
            )

        if not isinstance(result, int):
            raise TypeError(
                "Controller.redo_count() must return "
                "an integer."
            )

        return result

    # ========================================================
    # HISTORY ACCESS
    # ========================================================

    def get_undo_commands(
        self,
    ) -> tuple[Any, ...]:
        """
        Return an immutable snapshot of authoritative undo
        history.

        The UI CommandManager does not retain the returned
        commands.
        """

        method = self._get_controller_method(
            "get_undo_commands"
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
        Return an immutable snapshot of authoritative redo
        history.

        The UI CommandManager does not retain the returned
        commands.
        """

        method = self._get_controller_method(
            "get_redo_commands"
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
        Return the display name of the next undo operation.
        """

        method = self._get_controller_method(
            "get_undo_name"
        )

        result = method()

        if result is not None and not isinstance(
            result,
            str,
        ):
            raise TypeError(
                "Controller.get_undo_name() must return "
                "a string or None."
            )

        return result

    # --------------------------------------------------------

    def get_redo_name(
        self,
    ) -> Optional[str]:
        """
        Return the display name of the next redo operation.
        """

        method = self._get_controller_method(
            "get_redo_name"
        )

        result = method()

        if result is not None and not isinstance(
            result,
            str,
        ):
            raise TypeError(
                "Controller.get_redo_name() must return "
                "a string or None."
            )

        return result

    # ========================================================
    # HISTORY MANAGEMENT
    # ========================================================

    def clear_history(
        self,
    ) -> Any:
        """
        Clear authoritative command history.

        Controller/Core state is not directly modified by this
        facade.
        """

        method = self._get_controller_method(
            "clear_history"
        )

        return method()

    # --------------------------------------------------------

    def clear_redo(
        self,
    ) -> Any:
        """
        Clear authoritative redo history.
        """

        method = self._get_controller_method(
            "clear_redo"
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

        This delegates to Controller.reset_command_history().

        It does not reset Controller application state.
        """

        method = self._get_controller_method(
            "reset_command_history"
        )

        return method()

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return the authoritative command-manager diagnostic
        state.

        The state originates from Core.command_manager through
        Controller.

        The returned dictionary is copied so callers cannot
        mutate a dictionary owned by another layer.
        """

        method = self._get_controller_method(
            "get_command_state"
        )

        state = method()

        if not isinstance(
            state,
            dict,
        ):
            raise TypeError(
                "Controller.get_command_state() must "
                "return a dictionary."
            )

        return dict(
            state
        )

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

        Representation uses the public Controller command
        boundary and does not inspect Core directly.
        """

        try:
            undo_count = self.undo_count()

        except (
            RuntimeError,
            TypeError,
        ):
            undo_count = "?"

        try:
            redo_count = self.redo_count()

        except (
            RuntimeError,
            TypeError,
        ):
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
