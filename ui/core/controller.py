# ============================================================
# File: ui/core/controller.py
# GridForge V2 — UI Controller
# ============================================================
"""
Central application/UI controller for GridForge V2.

Architecture
------------

    UI / Tool / Panel / Toolbar
              │
              ▼
         Controller
              │
       ┌──────┴──────────────┐
       ▼                     ▼
 Application State     Core.command_manager
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
Controller is the central UI/application coordination boundary.

It bridges UI-facing application state and the authoritative
GridForge Core.

Controller owns:

    - application-level tool-selection intent;
    - persistent application selection;
    - project/application context;
    - access to Core;
    - command dispatch coordination;
    - public command-history delegation;
    - public UI state notifications;
    - Controller-owned signal subscriptions;
    - Controller lifecycle.

Controller does NOT own:

    - concrete tools;
    - ToolManager;
    - tool activation/deactivation;
    - input event processing;
    - rendering;
    - canvas state;
    - snapping;
    - navigation;
    - coordinate conversion;
    - electrical calculations;
    - domain/model state;
    - command objects;
    - command history;
    - undo/redo state.

Authoritative Ownership
-----------------------

Core owns domain/model state.

Core.command_manager owns:

    - command execution;
    - command history;
    - undo history;
    - redo history;
    - undo/redo transitions;
    - command-history semantics.

Controller does not duplicate any of those responsibilities.

Controller only exposes the public application boundary required
by the UI.

Command Architecture
---------------------

Canonical command execution:

    UI CommandManager
            │
            ▼
    Controller.execute_command()
            │
            ▼
    Core.command_manager.execute()
            │
            ▼
          Command
            │
            ▼
           Core
            │
            ▼
      Domain Events


Canonical undo:

    UI CommandManager
            │
            ▼
    Controller.undo()
            │
            ▼
    Core.command_manager.undo()


Canonical redo:

    UI CommandManager
            │
            ▼
    Controller.redo()
            │
            ▼
    Core.command_manager.redo()


Canonical command-state queries:

    UI CommandManager
            │
            ▼
    Controller.can_undo()
            │
            ▼
    Core.command_manager.can_undo()


The same delegation model applies to:

    - can_redo()
    - undo_count()
    - redo_count()
    - get_undo_commands()
    - get_redo_commands()
    - get_undo_name()
    - get_redo_name()
    - clear_history()
    - clear_redo()
    - reset_command_history()
    - get_command_state()

Controller never accesses Core.command_manager from the UI
facade directly. The UI CommandManager communicates only with
the public Controller command boundary.

Tool Selection
--------------

Controller stores the requested tool identifier.

    Controller.set_tool("bus")
            │
            ▼
       tool_changed("bus", previous)
            │
            ▼
       ToolManager
            │
            ▼
       Tool lifecycle

Controller never calls ToolManager directly.

The stored tool ID represents requested application intent, not
active tool lifecycle state.

Selection
---------

Controller owns persistent application selection.

Graphics selection is a UI projection of this application
selection.

Controller does not manipulate GraphicsItems directly.

Project Context
---------------

Controller may retain an externally owned project/application
context.

Controller does not duplicate project/domain state.

Qt
--

All Qt dependencies are imported through ui.core.qt.

This module contains no direct PySide6/PyQt imports.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import QObject, Signal


class Controller(QObject):
    """
    Central GridForge UI/application controller.

    Controller is the authoritative UI/application coordination
    boundary.

    It owns application-level transient state and delegates all
    Core operations through explicit public boundaries.

    Concrete tool lifecycle belongs to ToolManager.

    Domain state belongs to Core.

    Command execution and command history belong exclusively to
    Core.command_manager.
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
        Initialize the Controller.

        Parameters
        ----------
        core:
            Optional externally owned authoritative GridForge Core.

        parent:
            Optional Qt parent.

        Notes
        -----
        Controller does not take ownership of Core.

        No ToolManager, CommandManager, Renderer, Canvas or
        domain object is constructed here.
        """

        super().__init__(parent)

        # ----------------------------------------------------
        # Authoritative Core reference.
        #
        # Core remains externally owned.
        # ----------------------------------------------------

        self._core = core

        # ----------------------------------------------------
        # Requested application-level tool.
        #
        # This is intent only.
        #
        # ToolManager owns actual tool lifecycle.
        # ----------------------------------------------------

        self._tool_id: Optional[str] = None

        # ----------------------------------------------------
        # Persistent application selection.
        #
        # Selection is application/UI state, not duplicated
        # Core domain state.
        # ----------------------------------------------------

        self._selected_ids: list[Any] = []

        # ----------------------------------------------------
        # Current project/application context.
        #
        # The object itself remains externally owned.
        # ----------------------------------------------------

        self._project: Optional[Any] = None

        # ----------------------------------------------------
        # Lifecycle state.
        # ----------------------------------------------------

        self._disposed = False

        # ----------------------------------------------------
        # Controller-owned signal subscription registry.
        #
        # This tracks only callbacks registered through
        # Controller.subscribe().
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
        """
        Return the associated Core.

        Core remains externally owned.
        """

        return self._core

    # --------------------------------------------------------

    def get_core(self) -> Optional[Any]:
        """
        Return the associated Core.
        """

        return self._core

    # --------------------------------------------------------

    def set_core(
        self,
        core: Optional[Any],
    ) -> None:
        """
        Attach or replace the associated Core.

        The Controller does not copy or inspect Core state.

        Parameters
        ----------
        core:
            New externally owned Core, or None.

        Notes
        -----
        Replacing Core does not alter Controller-owned
        selection/tool/project state.

        Core command history remains owned by whichever Core
        instance is currently attached.
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

        This is requested state, not active ToolManager state.
        """

        return self._tool_id

    # --------------------------------------------------------

    def get_tool_id(self) -> Optional[str]:
        """
        Return the currently requested tool identifier.
        """

        return self._tool_id

    # --------------------------------------------------------

    def set_tool(
        self,
        tool_id: Optional[str],
    ) -> None:
        """
        Request an application-level tool.

        Parameters
        ----------
        tool_id:
            Stable tool identifier, or None to clear the request.

        Notes
        -----
        Controller does not construct or activate tools.

        ToolManager observes tool_changed().
        """

        self._ensure_active()

        if tool_id is not None:

            if not isinstance(
                tool_id,
                str,
            ):
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
        """
        Clear the current application-level tool request.
        """

        self.set_tool(None)

    # ========================================================
    # SELECTION
    # ========================================================

    @property
    def selected_ids(self) -> tuple[Any, ...]:
        """
        Return an immutable snapshot of application selection.
        """

        return tuple(
            self._selected_ids
        )

    # --------------------------------------------------------

    def get_selected_ids(
        self,
    ) -> tuple[Any, ...]:
        """
        Return the current application selection.
        """

        return self.selected_ids

    # --------------------------------------------------------

    def has_selection(self) -> bool:
        """
        Return True when at least one object is selected.
        """

        return bool(
            self._selected_ids
        )

    # --------------------------------------------------------

    def is_selected(
        self,
        object_id: Any,
    ) -> bool:
        """
        Return whether an object is selected.

        None is never considered selected.
        """

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

        Parameters
        ----------
        object_id:
            Stable application object identifier.

        multi:
            False:
                replace current selection.

            True:
                add to current selection.
        """

        self._ensure_active()

        if object_id is None:
            raise ValueError(
                "object_id must not be None."
            )

        if not isinstance(
            multi,
            bool,
        ):
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

        Parameters
        ----------
        object_ids:
            Iterable of object identifiers.

        multi:
            False:
                replace current selection.

            True:
                add to current selection.
        """

        self._ensure_active()

        if object_ids is None:
            raise ValueError(
                "object_ids must not be None."
            )

        if not isinstance(
            multi,
            bool,
        ):
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
                ids.append(
                    object_id
                )

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
        """
        Toggle an object in application selection.
        """

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
        """
        Remove an object from application selection.

        Missing IDs are ignored.
        """

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
        """
        Clear application selection.
        """

        self._ensure_active()

        if not self._selected_ids:
            return

        self._selected_ids.clear()

        self._emit_selection_changed()

    # --------------------------------------------------------

    def _emit_selection_changed(self) -> None:
        """
        Emit canonical selection/state notifications.
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
        """
        Return the current project/application context.
        """

        return self._project

    # --------------------------------------------------------

    def get_project(self) -> Optional[Any]:
        """
        Return the current project/application context.
        """

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
    # COMMAND MANAGER ACCESS
    # ========================================================

    def _get_command_manager(self) -> Any:
        """
        Return Core's authoritative command manager.

        This is the only internal route from Controller to the
        Core command manager.

        Controller does not own the returned object.
        """

        self._ensure_active()

        core = self._core

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

    # --------------------------------------------------------

    def _get_command_manager_method(
        self,
        method_name: str,
    ) -> Any:
        """
        Return a validated method from Core.command_manager.

        Controller centralizes the Core command-boundary lookup so
        public methods remain thin delegation methods.
        """

        command_manager = (
            self._get_command_manager()
        )

        method = getattr(
            command_manager,
            method_name,
            None,
        )

        if not callable(method):
            raise TypeError(
                "Core.command_manager must provide "
                f"{method_name}()."
            )

        return method

    # ========================================================
    # COMMAND EXECUTION
    # ========================================================

    def execute_command(
        self,
        command: Any,
    ) -> Any:
        """
        Execute a command through Core.command_manager.

        Canonical flow:

            Controller.execute_command(command)
                    │
                    ▼
            Core.command_manager.execute(command)
                    │
                    ▼
                  Command
                    │
                    ▼
                   Core

        Controller never calls command.execute() directly.

        Command validation remains the responsibility of the
        authoritative Core command manager.
        """

        self._ensure_active()

        if command is None:
            raise ValueError(
                "command must not be None."
            )

        execute = self._get_command_manager_method(
            "execute"
        )

        result = execute(
            command
        )

        self.state_changed.emit()

        return result

    # ========================================================
    # UNDO / REDO
    # ========================================================

    def undo(
        self,
    ) -> Any:
        """
        Undo through Core.command_manager.

        History transitions are owned exclusively by Core.
        """

        self._ensure_active()

        undo = self._get_command_manager_method(
            "undo"
        )

        result = undo()

        self.state_changed.emit()

        return result

    # --------------------------------------------------------

    def redo(
        self,
    ) -> Any:
        """
        Redo through Core.command_manager.

        History transitions are owned exclusively by Core.
        """

        self._ensure_active()

        redo = self._get_command_manager_method(
            "redo"
        )

        result = redo()

        self.state_changed.emit()

        return result

    # ========================================================
    # COMMAND AVAILABILITY
    # ========================================================

    def can_undo(
        self,
    ) -> bool:
        """
        Return whether Core has an available undo operation.
        """

        method = self._get_command_manager_method(
            "can_undo"
        )

        return bool(
            method()
        )

    # --------------------------------------------------------

    def can_redo(
        self,
    ) -> bool:
        """
        Return whether Core has an available redo operation.
        """

        method = self._get_command_manager_method(
            "can_redo"
        )

        return bool(
            method()
        )

    # ========================================================
    # COMMAND HISTORY COUNTS
    # ========================================================

    def undo_count(
        self,
    ) -> int:
        """
        Return the authoritative undo-history count.
        """

        method = self._get_command_manager_method(
            "undo_count"
        )

        result = method()

        if isinstance(
            result,
            bool,
        ) or not isinstance(
            result,
            int,
        ):
            raise TypeError(
                "Core.command_manager.undo_count() "
                "must return an integer."
            )

        return result

    # --------------------------------------------------------

    def redo_count(
        self,
    ) -> int:
        """
        Return the authoritative redo-history count.
        """

        method = self._get_command_manager_method(
            "redo_count"
        )

        result = method()

        if isinstance(
            result,
            bool,
        ) or not isinstance(
            result,
            int,
        ):
            raise TypeError(
                "Core.command_manager.redo_count() "
                "must return an integer."
            )

        return result

    # ========================================================
    # COMMAND HISTORY ACCESS
    # ========================================================

    def get_undo_commands(
        self,
    ) -> tuple[Any, ...]:
        """
        Return an immutable snapshot of Core undo history.

        Controller does not retain the returned commands.
        """

        method = self._get_command_manager_method(
            "get_undo_commands"
        )

        result = method()

        try:
            return tuple(
                result
            )
        except TypeError as exc:
            raise TypeError(
                "Core.command_manager.get_undo_commands() "
                "must return an iterable."
            ) from exc

    # --------------------------------------------------------

    def get_redo_commands(
        self,
    ) -> tuple[Any, ...]:
        """
        Return an immutable snapshot of Core redo history.

        Controller does not retain the returned commands.
        """

        method = self._get_command_manager_method(
            "get_redo_commands"
        )

        result = method()

        try:
            return tuple(
                result
            )
        except TypeError as exc:
            raise TypeError(
                "Core.command_manager.get_redo_commands() "
                "must return an iterable."
            ) from exc

    # ========================================================
    # COMMAND HISTORY LABELS
    # ========================================================

    def get_undo_name(
        self,
    ) -> Optional[str]:
        """
        Return the display name of the next undo operation.
        """

        method = self._get_command_manager_method(
            "get_undo_name"
        )

        result = method()

        if (
            result is not None
            and not isinstance(
                result,
                str,
            )
        ):
            raise TypeError(
                "Core.command_manager.get_undo_name() "
                "must return a string or None."
            )

        return result

    # --------------------------------------------------------

    def get_redo_name(
        self,
    ) -> Optional[str]:
        """
        Return the display name of the next redo operation.
        """

        method = self._get_command_manager_method(
            "get_redo_name"
        )

        result = method()

        if (
            result is not None
            and not isinstance(
                result,
                str,
            )
        ):
            raise TypeError(
                "Core.command_manager.get_redo_name() "
                "must return a string or None."
            )

        return result

    # ========================================================
    # COMMAND HISTORY MANAGEMENT
    # ========================================================

    def clear_history(
        self,
    ) -> Any:
        """
        Clear Core command history.

        This affects command history only.

        Controller application state and Core domain state are
        not directly reset by this method.
        """

        method = self._get_command_manager_method(
            "clear_history"
        )

        result = method()

        self.state_changed.emit()

        return result

    # --------------------------------------------------------

    def clear_redo(
        self,
    ) -> Any:
        """
        Clear Core redo history only.
        """

        method = self._get_command_manager_method(
            "clear_redo"
        )

        result = method()

        self.state_changed.emit()

        return result

    # --------------------------------------------------------

    def reset_command_history(
        self,
    ) -> Any:
        """
        Reset Core command-history state.

        This is intentionally distinct from reset_state().

        reset_command_history():

            clears command history only.

        reset_state():

            resets Controller-owned application state only.

        Neither method implicitly resets the other layer.
        """

        method = self._get_command_manager_method(
            "reset"
        )

        result = method()

        self.state_changed.emit()

        return result

    # ========================================================
    # COMMAND STATE
    # ========================================================

    def get_command_state(
        self,
    ) -> dict[str, Any]:
        """
        Return the authoritative Core command-manager state.

        Core.command_manager owns the state.

        Controller returns a copied dictionary so the caller
        cannot mutate a dictionary owned by Core.
        """

        method = self._get_command_manager_method(
            "get_state"
        )

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

    # ========================================================
    # CONTROLLER STATE RESET
    # ========================================================

    def reset_state(self) -> None:
        """
        Reset Controller-owned transient application state.

        This method does NOT reset Core.

        This method does NOT clear command history.

        ToolManager observes the tool_changed() notification and
        remains responsible for actual tool lifecycle.
        """

        self._ensure_active()

        previous_tool_id = self._tool_id

        had_selection = bool(
            self._selected_ids
        )

        had_project = (
            self._project is not None
        )

        # ----------------------------------------------------
        # Reset Controller-owned state.
        # ----------------------------------------------------

        self._tool_id = None
        self._selected_ids.clear()
        self._project = None

        # ----------------------------------------------------
        # Notify tool lifecycle boundary.
        # ----------------------------------------------------

        if previous_tool_id is not None:

            self.tool_changed.emit(
                None,
                previous_tool_id,
            )

        # ----------------------------------------------------
        # Notify selection boundary.
        # ----------------------------------------------------

        if had_selection:

            self.selection_changed.emit(
                self.selected_ids
            )

        # ----------------------------------------------------
        # Notify project boundary.
        # ----------------------------------------------------

        if had_project:

            self.project_changed.emit(
                None
            )

        # ----------------------------------------------------
        # Explicit reset notification.
        # ----------------------------------------------------

        self.reset_requested.emit()

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
        Subscribe to a public Controller signal.

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

        except (
            RuntimeError,
            TypeError,
        ):
            # Qt may report that the callback is already
            # disconnected.
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
        """
        Validate a Controller signal subscription.
        """

        if not isinstance(
            signal_name,
            str,
        ):
            raise TypeError(
                "signal_name must be a string."
            )

        if signal_name not in cls._SIGNAL_NAMES:
            raise ValueError(
                "Unknown Controller signal: "
                f"{signal_name!r}"
            )

        if not callable(callback):
            raise TypeError(
                "callback must be callable."
            )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of Controller-owned state.

        This method does not expose mutable internal collections.

        Command-manager state is deliberately not duplicated here.

        Use get_command_state() for command-history diagnostics.
        """

        return {
            "tool_id": self._tool_id,
            "selected_ids": self.selected_ids,
            "selected_count": len(
                self._selected_ids
            ),
            "has_selection": bool(
                self._selected_ids
            ),
            "has_core": self._core is not None,
            "has_project": self._project is not None,
            "disposed": self._disposed,
        }

    # --------------------------------------------------------

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

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

    def dispose(
        self,
    ) -> None:
        """
        Dispose the Controller.

        Controller does not own Core.

        Registered Controller subscriptions are disconnected.

        Core is not reset, disposed, or otherwise mutated.
        """

        if self._disposed:
            return

        # ----------------------------------------------------
        # Disconnect callbacks registered through subscribe().
        # ----------------------------------------------------

        for (
            signal_name,
            callbacks,
        ) in self._subscriptions.items():

            signal = getattr(
                self,
                signal_name,
            )

            for callback in tuple(
                callbacks
            ):

                try:
                    signal.disconnect(
                        callback
                    )

                except (
                    RuntimeError,
                    TypeError,
                ):
                    pass

            callbacks.clear()

        # ----------------------------------------------------
        # Clear Controller-owned state.
        # ----------------------------------------------------

        self._tool_id = None
        self._selected_ids.clear()
        self._project = None

        # ----------------------------------------------------
        # Core remains externally owned.
        #
        # Do not dispose, reset, or mutate Core.
        # ----------------------------------------------------

        self._disposed = True

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure the Controller has not been disposed.
        """

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
