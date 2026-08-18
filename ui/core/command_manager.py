# ============================================================
# File: ui/core/command_manager.py
# GridForge V2 — UI Command Manager
# ============================================================
"""
Central UI command-routing and history boundary for GridForge V2.

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


Purpose
-------
CommandManager is the single UI-facing boundary for command
execution and command history.

Commands represent application/user intent.

The Controller and Core remain authoritative for application
and domain state.

CommandManager owns only:

    - undo history;
    - redo history;
    - command execution coordination;
    - command-history diagnostics.

CommandManager does NOT own:

    - application state;
    - Core state;
    - project state;
    - domain state;
    - domain mutations;
    - command implementation;
    - tool lifecycle;
    - canvas state;
    - selection state;
    - navigation;
    - rendering;
    - snapping;
    - electrical calculations.

Canonical Command Contract
--------------------------
A command must provide:

    execute(controller)
    undo(controller)

The CommandManager passes the authoritative Controller to the
command.

CommandManager does not inspect command internals.

History Semantics
-----------------
New command:

    success
        -> undo history
        -> redo history cleared

    failure
        -> no history mutation
        -> existing redo history preserved

Undo:

    success
        -> command moves undo -> redo

    failure
        -> command remains in undo history
        -> redo history unchanged

Redo:

    success
        -> command moves redo -> undo

    failure
        -> command remains in redo history
        -> undo history unchanged

Undo/redo are executed through the normal command pathway:

    command.undo(controller)
    command.execute(controller)

CommandManager does not reconstruct application state from
history.

CommandManager does not rewind project revision.

Composite Commands
------------------
Composite commands implement the same Command interface and are
treated as ordinary commands.

CommandManager does not inspect or manage their internal
structure.

Grouping / Coalescing
---------------------
Optional grouping or coalescing belongs to the command layer.

CommandManager does not infer grouping semantics.

Qt
--
This module is completely Qt-independent.
"""

from __future__ import annotations

from typing import Any, Optional


class CommandManager:
    """
    Central UI/application command execution and history manager.

    Controller owns application state.

    CommandManager owns only command history and command
    execution coordination.
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
            Authoritative GridForge Controller passed to every
            command during execution and undo.

        max_history:
            Maximum number of commands retained in undo history.

            None:
                Unlimited history.

            Positive integer:
                Oldest undo entries are discarded when the
                configured limit is exceeded.

        Notes
        -----
        CommandManager does not take ownership of Controller.
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
        # Command history only.
        #
        # These collections contain Command objects.
        #
        # No application/domain state is duplicated here.
        # ----------------------------------------------------

        self._undo_stack: list[Any] = []
        self._redo_stack: list[Any] = []

        # ----------------------------------------------------
        # Prevent recursive command execution.
        #
        # This protects the command state machine from a command
        # attempting to execute/undo/redo another command
        # through the same manager while one operation is active.
        # ----------------------------------------------------

        self._executing = False

    # ========================================================
    # COMMAND VALIDATION
    # ========================================================

    @staticmethod
    def _validate_command(
        command: Any,
    ) -> None:
        """
        Validate the canonical Command protocol.

        Required interface:

            execute(controller)
            undo(controller)

        The manager intentionally does not require a concrete
        Command base class. Structural validation keeps the
        command layer decoupled.
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

        if not callable(execute):
            raise TypeError(
                "command must provide execute(controller)."
            )

        undo = getattr(
            command,
            "undo",
            None,
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

        Canonical flow:

            CommandManager
                |
                v
            command.execute(controller)

        A command enters undo history only after successful
        completion.

        Failed commands do not modify either history stack.

        A successful new command invalidates redo history.
        """

        self._validate_command(
            command
        )

        self._ensure_not_executing()

        self._executing = True

        try:
            result = command.execute(
                self.controller
            )

        except Exception:
            # ------------------------------------------------
            # Failed command:
            #
            # - do not add to undo history;
            # - preserve existing redo history.
            # ------------------------------------------------
            raise

        finally:
            self._executing = False

        # ----------------------------------------------------
        # Commit command to history only after successful
        # execution.
        # ----------------------------------------------------

        self._undo_stack.append(
            command
        )

        # ----------------------------------------------------
        # A successful new command invalidates redo history.
        # ----------------------------------------------------

        self._redo_stack.clear()

        self._enforce_history_limit()

        return result

    # ========================================================
    # UNDO
    # ========================================================

    def undo(
        self,
    ) -> Any:
        """
        Undo the most recent successfully executed command.

        Canonical flow:

            CommandManager
                |
                v
            command.undo(controller)

        History is modified only after successful undo.

        Failed undo leaves the command in the undo stack.
        """

        if not self._undo_stack:
            raise RuntimeError(
                "No command available for undo."
            )

        self._ensure_not_executing()

        command = self._undo_stack[-1]

        self._executing = True

        try:
            result = command.undo(
                self.controller
            )

        except Exception:
            # ------------------------------------------------
            # Failed undo:
            #
            # Command remains available for another undo
            # attempt. No history transition occurs.
            # ------------------------------------------------
            raise

        finally:
            self._executing = False

        # ----------------------------------------------------
        # Commit successful undo:
        #
        # undo -> redo
        # ----------------------------------------------------

        self._undo_stack.pop()

        self._redo_stack.append(
            command
        )

        return result

    # ========================================================
    # REDO
    # ========================================================

    def redo(
        self,
    ) -> Any:
        """
        Redo the most recently undone command.

        Redo uses the normal command execution pathway:

            command.execute(controller)

        History is modified only after successful execution.

        Failed redo leaves the command in the redo stack.
        """

        if not self._redo_stack:
            raise RuntimeError(
                "No command available for redo."
            )

        self._ensure_not_executing()

        command = self._redo_stack[-1]

        self._executing = True

        try:
            result = command.execute(
                self.controller
            )

        except Exception:
            # ------------------------------------------------
            # Failed redo:
            #
            # Command remains in redo history.
            # ------------------------------------------------
            raise

        finally:
            self._executing = False

        # ----------------------------------------------------
        # Commit successful redo:
        #
        # redo -> undo
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

        Only the oldest undo entries are discarded.

        Redo history is intentionally untouched.
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
    # HISTORY COUNTS
    # ========================================================

    def undo_count(
        self,
    ) -> int:
        """
        Return the number of commands currently available
        for undo.
        """

        return len(
            self._undo_stack
        )

    # --------------------------------------------------------

    def redo_count(
        self,
    ) -> int:
        """
        Return the number of commands currently available
        for redo.
        """

        return len(
            self._redo_stack
        )

    # ========================================================
    # HISTORY ACCESS
    # ========================================================

    def get_undo_commands(
        self,
    ) -> tuple[Any, ...]:
        """
        Return an immutable snapshot of undo history.

        The manager's internal list remains private.
        """

        return tuple(
            self._undo_stack
        )

    # --------------------------------------------------------

    def get_redo_commands(
        self,
    ) -> tuple[Any, ...]:
        """
        Return an immutable snapshot of redo history.
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

        Resolution order:

            1. command.name
            2. command.description
            3. command class name
        """

        name = getattr(
            command,
            "name",
            None,
        )

        if (
            isinstance(name, str)
            and name.strip()
        ):
            return name.strip()

        description = getattr(
            command,
            "description",
            None,
        )

        if (
            isinstance(description, str)
            and description.strip()
        ):
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

        Returns None when undo is unavailable.
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

        Returns None when redo is unavailable.
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

        Controller/Core state is not modified.
        """

        self._undo_stack.clear()
        self._redo_stack.clear()

    # --------------------------------------------------------

    def clear_redo(
        self,
    ) -> None:
        """
        Clear redo history only.

        Undo history is preserved.
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

        Equivalent to clear_history().

        Controller/Core state is not modified.
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

        Command objects themselves are represented only by
        their display names.
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
            "undo_name": self.get_undo_name(),
            "redo_name": self.get_redo_name(),
            "max_history": self.max_history,
            "executing": self._executing,
        }

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    def _ensure_not_executing(
        self,
    ) -> None:
        """
        Reject recursive command operations.

        A command must complete before another command-manager
        operation can begin.
        """

        if self._executing:
            raise RuntimeError(
                "CommandManager does not permit recursive "
                "command execution."
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

        return (
            "CommandManager("
            f"undo={len(self._undo_stack)}, "
            f"redo={len(self._redo_stack)}, "
            f"max_history={self.max_history!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "CommandManager",
]
