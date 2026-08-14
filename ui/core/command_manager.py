# ============================================================
# File: ui/core/command_manager.py
# GridForge V2 — UI Command Manager
# ============================================================
"""
Central UI command-routing boundary for GridForge V2.

Purpose
-------
CommandManager provides the UI-facing boundary for executing
application commands.

Architecture
------------

    UI / Tool
        │
        ▼
    CommandManager
        │
        ▼
    Command
        │
        ▼
    Controller
        │
        ▼
      Core
        │
        ▼
   Domain Events

CommandManager is deliberately independent of Qt.

Responsibilities
----------------
CommandManager:

    - receives command objects from UI/application code;
    - validates the command interface;
    - executes commands through the Controller;
    - tracks command history;
    - supports undo/redo;
    - clears redo history after a new successful command;
    - provides command diagnostics;
    - provides a single UI-facing command execution boundary.

CommandManager does NOT:

    - implement domain/model mutations;
    - directly modify Core state;
    - implement individual command behavior;
    - contain tool logic;
    - contain canvas logic;
    - contain selection logic;
    - contain navigation logic;
    - create QGraphicsItems;
    - perform electrical calculations;
    - own Controller application state.

Command Architecture
--------------------
The canonical GridForge V2 command contract is:

    Command
        execute(controller)
        undo(controller)

Commands represent user/application intent.

Controller/Core remain authoritative for validation and
mutation.

Successful Core mutations generate authoritative domain
events.

Failed commands must not enter history.

Undo/redo execute through the normal command/Core pathway.

Undo/redo do not rewind the project revision.

CommandManager therefore stores command history, but does not
store a second copy of application state.

History Ownership
-----------------
CommandManager owns:

    - undo history;
    - redo history.

Controller owns:

    - application state;
    - Core interaction;
    - project revision;
    - domain events.

CommandManager never attempts to reconstruct application state
from its own history.

Composite Commands
------------------
A CompositeCommand may implement the same Command interface.

CommandManager treats it as a normal command and does not need
to know its internal structure.

Command Grouping
----------------
Grouping/coalescing is optional and must be implemented by the
command layer itself.

CommandManager does not infer grouping semantics.

Qt Architecture
---------------
This module is intentionally Qt-independent.

No direct PySide6/PyQt imports are permitted.

The command layer is usable from:

    - Canvas tools
    - Panels
    - Toolbar actions
    - Menus
    - Keyboard shortcuts
    - Future automation/API layers
"""

from __future__ import annotations

from typing import Any, Optional


class CommandManager:
    """
    Central command execution and history manager.

    CommandManager is a UI/application service.

    It does not own application state and does not implement
    domain mutations.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        *,
        max_history: Optional[int] = None,
    ) -> None:
        """
        Initialize the CommandManager.

        Parameters
        ----------
        controller:
            GridForge application Controller.

        max_history:
            Optional maximum number of commands retained in
            undo history.

            None means unlimited history.

        Notes
        -----
        The Controller remains the authoritative application
        state owner.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        if (
            max_history is not None
            and (
                isinstance(max_history, bool)
                or not isinstance(max_history, int)
            )
        ):
            raise TypeError(
                "max_history must be an integer or None."
            )

        if (
            max_history is not None
            and max_history <= 0
        ):
            raise ValueError(
                "max_history must be greater than zero."
            )

        self.controller = controller
        self.max_history = max_history

        # ----------------------------------------------------
        # History
        # ----------------------------------------------------
        #
        # Lists contain Command instances only.
        #
        # CommandManager does not store snapshots of Core state.
        # ----------------------------------------------------

        self._undo_stack: list[Any] = []
        self._redo_stack: list[Any] = []

        self._executing = False

    # ========================================================
    # COMMAND VALIDATION
    # ========================================================

    @staticmethod
    def _validate_command(
        command: Any,
    ) -> None:
        """
        Validate the minimum Command protocol.

        A command must provide:

            execute(controller)
            undo(controller)
        """

        if command is None:
            raise ValueError(
                "command must not be None."
            )

        execute = getattr(
            command,
            "execute",
            None,
        )

        undo = getattr(
            command,
            "undo",
            None,
        )

        if not callable(execute):
            raise TypeError(
                "command must provide execute(controller)."
            )

        if not callable(undo):
            raise TypeError(
                "command must provide undo(controller)."
            )

    # ========================================================
    # EXECUTION
    # ========================================================

    def execute(
        self,
        command: Any,
    ) -> Any:
        """
        Execute a new command.

        Parameters
        ----------
        command:
            Command implementing execute(controller) and
            undo(controller).

        Returns
        -------
        Any
            Value returned by command.execute().

        History semantics
        -----------------
        A command enters undo history only when execution
        completes successfully.

        If execute() raises, the command is not added to
        history and the existing redo history is preserved.

        A successful new command invalidates redo history.
        """

        self._validate_command(
            command
        )

        if self._executing:
            raise RuntimeError(
                "CommandManager does not permit recursive "
                "command execution."
            )

        self._executing = True

        try:
            result = command.execute(
                self.controller
            )

        except Exception:
            # ------------------------------------------------
            # Failed commands do not enter history.
            #
            # Existing redo history remains untouched because
            # no new successful command was committed.
            # ------------------------------------------------
            raise

        finally:
            self._executing = False

        # ----------------------------------------------------
        # Successful command.
        # ----------------------------------------------------

        self._undo_stack.append(
            command
        )

        # ----------------------------------------------------
        # A new successful command invalidates redo history.
        # ----------------------------------------------------

        self._redo_stack.clear()

        self._enforce_history_limit()

        return result

    # ========================================================
    # UNDO
    # ========================================================

    def undo(self) -> Any:
        """
        Undo the most recent successful command.

        Undo is executed through the command's undo(controller)
        method.

        Returns
        -------
        Any
            Value returned by command.undo().

        Raises
        ------
        RuntimeError
            If no command is available for undo.

        Notes
        -----
        If undo fails, the command remains in the undo stack.

        A successful undo moves the command to the redo stack.
        """

        if not self._undo_stack:
            raise RuntimeError(
                "No command available for undo."
            )

        if self._executing:
            raise RuntimeError(
                "CommandManager does not permit recursive "
                "command execution."
            )

        command = self._undo_stack[-1]

        self._executing = True

        try:
            result = command.undo(
                self.controller
            )

        except Exception:
            # ------------------------------------------------
            # Failed undo does not alter history.
            # ------------------------------------------------
            raise

        finally:
            self._executing = False

        # ----------------------------------------------------
        # Undo succeeded.
        # ----------------------------------------------------

        self._undo_stack.pop()

        self._redo_stack.append(
            command
        )

        return result

    # ========================================================
    # REDO
    # ========================================================

    def redo(self) -> Any:
        """
        Redo the most recently undone command.

        Returns
        -------
        Any
            Value returned by command.execute().

        Raises
        ------
        RuntimeError
            If no command is available for redo.

        Notes
        -----
        Redo uses the normal command.execute(controller)
        pathway.

        If redo fails, the command remains in the redo stack.
        """

        if not self._redo_stack:
            raise RuntimeError(
                "No command available for redo."
            )

        if self._executing:
            raise RuntimeError(
                "CommandManager does not permit recursive "
                "command execution."
            )

        command = self._redo_stack[-1]

        self._executing = True

        try:
            result = command.execute(
                self.controller
            )

        except Exception:
            # ------------------------------------------------
            # Failed redo does not alter history.
            # ------------------------------------------------
            raise

        finally:
            self._executing = False

        # ----------------------------------------------------
        # Redo succeeded.
        # ----------------------------------------------------

        self._redo_stack.pop()

        self._undo_stack.append(
            command
        )

        self._enforce_history_limit()

        return result

    # ========================================================
    # HISTORY LIMIT
    # ========================================================

    def _enforce_history_limit(
        self,
    ) -> None:
        """
        Enforce the configured undo-history limit.

        The oldest undo entries are discarded first.

        Redo history is not modified here.
        """

        if self.max_history is None:
            return

        overflow = (
            len(self._undo_stack)
            - self.max_history
        )

        if overflow <= 0:
            return

        del self._undo_stack[
            :overflow
        ]

    # ========================================================
    # AVAILABILITY
    # ========================================================

    def can_undo(
        self,
    ) -> bool:
        """
        Return True when an undo operation is available.
        """

        return bool(
            self._undo_stack
        )

    # --------------------------------------------------------

    def can_redo(
        self,
    ) -> bool:
        """
        Return True when a redo operation is available.
        """

        return bool(
            self._redo_stack
        )

    # ========================================================
    # HISTORY ACCESS
    # ========================================================

    def undo_count(
        self,
    ) -> int:
        """
        Return the number of commands available for undo.
        """

        return len(
            self._undo_stack
        )

    # --------------------------------------------------------

    def redo_count(
        self,
    ) -> int:
        """
        Return the number of commands available for redo.
        """

        return len(
            self._redo_stack
        )

    # --------------------------------------------------------

    def get_undo_commands(
        self,
    ) -> tuple[Any, ...]:
        """
        Return a snapshot of the undo history.

        The returned tuple does not expose a mutable history
        collection.
        """

        return tuple(
            self._undo_stack
        )

    # --------------------------------------------------------

    def get_redo_commands(
        self,
    ) -> tuple[Any, ...]:
        """
        Return a snapshot of the redo history.
        """

        return tuple(
            self._redo_stack
        )

    # ========================================================
    # COMMAND LABELS
    # ========================================================

    @staticmethod
    def _command_name(
        command: Any,
    ) -> str:
        """
        Return a stable human-readable command name.

        Command implementations may optionally provide:

            name

        or:

            description

        Otherwise the class name is used.
        """

        name = getattr(
            command,
            "name",
            None,
        )

        if isinstance(
            name,
            str,
        ) and name.strip():

            return name.strip()

        description = getattr(
            command,
            "description",
            None,
        )

        if isinstance(
            description,
            str,
        ) and description.strip():

            return description.strip()

        return type(
            command
        ).__name__

    # --------------------------------------------------------

    def get_undo_name(
        self,
    ) -> Optional[str]:
        """
        Return the display name of the next undo operation.
        """

        if not self._undo_stack:
            return None

        return self._command_name(
            self._undo_stack[-1]
        )

    # --------------------------------------------------------

    def get_redo_name(
        self,
    ) -> Optional[str]:
        """
        Return the display name of the next redo operation.
        """

        if not self._redo_stack:
            return None

        return self._command_name(
            self._redo_stack[-1]
        )

    # ========================================================
    # HISTORY MANAGEMENT
    # ========================================================

    def clear_history(
        self,
    ) -> None:
        """
        Clear both undo and redo histories.

        This does not modify Controller/Core state.
        """

        self._undo_stack.clear()
        self._redo_stack.clear()

    # --------------------------------------------------------

    def clear_redo(
        self,
    ) -> None:
        """
        Clear redo history without modifying undo history.
        """

        self._redo_stack.clear()

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset command-history state.

        This is equivalent to clear_history().

        No Core or Controller state is modified.
        """

        self.clear_history()

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of command state.

        The command objects themselves are represented by their
        display names to avoid exposing mutable history lists.
        """

        return {
            "undo_count": len(
                self._undo_stack
            ),
            "redo_count": len(
                self._redo_stack
            ),
            "can_undo": bool(
                self._undo_stack
            ),
            "can_redo": bool(
                self._redo_stack
            ),
            "undo_name": (
                self.get_undo_name()
            ),
            "redo_name": (
                self.get_redo_name()
            ),
            "max_history": (
                self.max_history
            ),
            "executing": self._executing,
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "CommandManager("
            f"undo={len(self._undo_stack)}, "
            f"redo={len(self._redo_stack)}, "
            f"max_history="
            f"{self.max_history!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "CommandManager",
]
