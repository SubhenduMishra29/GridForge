# ============================================================
# File: ui/core/controller.py
# GridForge V2 — UI Controller
# ============================================================
"""
Central application/UI controller for GridForge V2.

Purpose
-------
Controller is the application-facing coordination boundary of
the UI layer.

It provides stable UI contracts for:

    - application selection;
    - application-level tool requests;
    - UI state notifications;
    - Core access;
    - command execution;
    - project/application lifecycle coordination.

Controller does NOT:

    - own QGraphicsItems;
    - render the canvas;
    - implement tool behavior;
    - own concrete tool instances;
    - perform canvas navigation;
    - perform snapping;
    - perform coordinate conversion;
    - perform electrical calculations;
    - directly manipulate graphics;
    - duplicate Core domain state unnecessarily.

Architecture
------------

                    UI
                     │
                     ▼
                Controller
                /    |    \
               /     |     \
              ▼      ▼      ▼
        Selection   Tools   Commands
              │      │
              │      ▼
              │  ToolManager
              │
              ▼
        Application State
              │
              ▼
             Core

Tool selection
--------------
Controller stores only the requested application-level tool
identifier.

The canonical flow is:

    controller.set_tool("bus")
            │
            ▼
    tool_changed(new_id, previous_id)
            │
            ▼
       ToolManager
            │
            ▼
      lifecycle transition

Controller does NOT create, activate, deactivate, or cancel
concrete tool instances.

Selection
---------
Controller owns the authoritative persistent application
selection.

The canonical state is:

    controller.selected_ids

SelectionManager is an adapter around this state and delegates
selection mutations to Controller.

Graphics selection is only a projection of this state.

Core
----
The Core remains authoritative for domain/model state.

Controller provides access to the application Core and acts as
the UI-side coordination boundary.

Controller must not become a second domain model.

Qt architecture
---------------
All Qt dependencies pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import QObject, Signal


class Controller(QObject):
    """
    Central GridForge UI/application controller.

    The Controller is intentionally independent of Canvas,
    Tools, Renderers, and GraphicsItems.

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
            Optional GridForge Core/application model.

            The Controller does not take ownership of the Core.

        parent:
            Optional Qt parent.

        Notes
        -----
        The Controller owns application-level UI coordination
        state, not the domain model itself.
        """

        super().__init__(parent)

        self._core = core

        # ----------------------------------------------------
        # Application-level tool request.
        #
        # None means no tool has been requested.
        #
        # Controller stores the identifier only.
        # ----------------------------------------------------

        self._tool_id: Optional[str] = None

        # ----------------------------------------------------
        # Authoritative application selection.
        #
        # Controller owns this collection.
        #
        # A tuple is exposed publicly so callers cannot mutate
        # the internal collection accidentally.
        # ----------------------------------------------------

        self._selected_ids: list[Any] = []

        # ----------------------------------------------------
        # Optional project/application reference.
        #
        # This is a UI/application context reference and is not
        # a duplicate Core model.
        # ----------------------------------------------------

        self._project: Optional[Any] = None

        # ----------------------------------------------------
        # Lifecycle state.
        # ----------------------------------------------------

        self._disposed = False

    # ========================================================
    # CORE ACCESS
    # ========================================================

    @property
    def core(self) -> Optional[Any]:
        """
        Return the associated GridForge Core object.

        The Core remains owned by the application layer.
        """

        return self._core

    # --------------------------------------------------------

    def set_core(
        self,
        core: Optional[Any],
    ) -> None:
        """
        Attach or replace the Core application object.

        The Controller does not inspect or duplicate Core state.
        """

        self._ensure_active()

        self._core = core

        self.state_changed.emit()

    # --------------------------------------------------------

    def get_core(self) -> Optional[Any]:
        """
        Return the associated Core object.
        """

        return self._core

    # ========================================================
    # TOOL REQUEST STATE
    # ========================================================

    @property
    def tool_id(self) -> Optional[str]:
        """
        Return the currently requested application-level tool ID.

        This is a request/state identifier only.

        It is not a concrete tool instance.
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
            Tool identifier.

            None clears the current tool request.

        Notes
        -----
        Controller does not create or activate the tool.

        ToolManager is responsible for observing tool_changed()
        and performing the corresponding lifecycle transition.
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
        Return the authoritative application selection.

        A tuple snapshot is returned so callers cannot mutate
        Controller selection without going through the
        Controller API.
        """

        return tuple(
            self._selected_ids
        )

    # --------------------------------------------------------

    def get_selected_ids(
        self,
    ) -> tuple[Any, ...]:
        """
        Return the authoritative application selection.
        """

        return self.selected_ids

    # --------------------------------------------------------

    def has_selection(self) -> bool:
        """
        Return True when at least one application object is
        selected.
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
        Return whether an object ID is currently selected.
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
            Authoritative application/Core object identifier.

        multi:
            False:
                replace the current selection.

            True:
                add the object to the current selection.

        Notes
        -----
        Controller owns the persistent selection collection.

        SelectionManager delegates to this method.

        GraphicsItems are never modified directly here.
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

        self.selection_changed.emit(
            self.selected_ids
        )

        self.state_changed.emit()

    # --------------------------------------------------------

    def select_many(
        self,
        object_ids: Iterable[Any],
        multi: bool = False,
    ) -> None:
        """
        Select multiple application objects.

        Parameters
        ----------
        object_ids:
            Iterable of authoritative object IDs.

        multi:
            False:
                replace the current selection.

            True:
                add to the current selection.

        Duplicate IDs are removed while preserving input order.
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

        self.selection_changed.emit(
            self.selected_ids
        )

        self.state_changed.emit()

    # --------------------------------------------------------

    def toggle_selection(
        self,
        object_id: Any,
    ) -> None:
        """
        Toggle an object in the authoritative selection.

        This is an application-selection operation.

        Graphics interaction remains outside Controller.
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

        self.selection_changed.emit(
            self.selected_ids
        )

        self.state_changed.emit()

    # --------------------------------------------------------

    def remove_from_selection(
        self,
        object_id: Any,
    ) -> None:
        """
        Remove an object from the authoritative selection.
        """

        self._ensure_active()

        if object_id is None:
            return

        if object_id not in self._selected_ids:
            return

        self._selected_ids.remove(
            object_id
        )

        self.selection_changed.emit(
            self.selected_ids
        )

        self.state_changed.emit()

    # --------------------------------------------------------

    def clear_selection(self) -> None:
        """
        Clear the authoritative application selection.
        """

        self._ensure_active()

        if not self._selected_ids:
            return

        self._selected_ids.clear()

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
        Return the current application/project context.
        """

        return self._project

    # --------------------------------------------------------

    def get_project(self) -> Optional[Any]:
        """
        Return the current application/project context.
        """

        return self._project

    # --------------------------------------------------------

    def set_project(
        self,
        project: Optional[Any],
    ) -> None:
        """
        Set the current application/project context.

        The project is treated as an external application
        object. Controller does not duplicate its domain state.
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
        Execute an application command through the Core command
        boundary.

        The Controller does not implement command behavior.

        The associated application/Core object must provide one
        of the supported command-entry methods:

            execute_command(command)

        or:

            command_manager.execute(command)

        Returns
        -------
        Any
            Result returned by the command boundary.
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
            result = execute(
                command
            )

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
            result = execute(
                command
            )

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
        """
        Request an undo operation through the Core command
        boundary.
        """

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
        """
        Request a redo operation through the Core command
        boundary.
        """

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
    # GENERIC APPLICATION RESET
    # ========================================================

    def reset_state(self) -> None:
        """
        Reset Controller-owned transient application state.

        This does not reset or mutate the Core model.

        It:

            - clears selection;
            - clears the requested tool;
            - clears the project context.
        """

        self._ensure_active()

        previous_tool_id = self._tool_id

        self._tool_id = None
        self._selected_ids.clear()
        self._project = None

        if previous_tool_id is not None:

            self.tool_changed.emit(
                None,
                previous_tool_id,
            )

        self.selection_changed.emit(
            self.selected_ids
        )

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
        Subscribe a callback to a Controller signal.

        Parameters
        ----------
        signal_name:
            Public signal name.

        callback:
            Callable receiving the signal arguments.

        Supported signals
        -----------------
        tool_changed
        selection_changed
        state_changed
        project_changed
        reset_requested

        This method provides the stable subscription contract
        used by UI coordination services such as ToolManager.
        """

        self._ensure_active()

        if not isinstance(
            signal_name,
            str,
        ):
            raise TypeError(
                "signal_name must be a string."
            )

        if not callable(
            callback
        ):
            raise TypeError(
                "callback must be callable."
            )

        signal = getattr(
            self,
            signal_name,
            None,
        )

        if signal is None or not callable(
            getattr(
                signal,
                "connect",
                None,
            )
        ):
            raise ValueError(
                f"Unknown Controller signal: "
                f"{signal_name!r}"
            )

        signal.connect(
            callback
        )

    # --------------------------------------------------------

    def unsubscribe(
        self,
        signal_name: str,
        callback: Any,
    ) -> None:
        """
        Remove a callback from a Controller signal.

        Missing or already-disconnected callbacks are ignored
        where Qt permits safe disconnection.
        """

        self._ensure_active()

        if not isinstance(
            signal_name,
            str,
        ):
            raise TypeError(
                "signal_name must be a string."
            )

        if not callable(
            callback
        ):
            raise TypeError(
                "callback must be callable."
            )

        signal = getattr(
            self,
            signal_name,
            None,
        )

        if signal is None or not callable(
            getattr(
                signal,
                "disconnect",
                None,
            )
        ):
            raise ValueError(
                f"Unknown Controller signal: "
                f"{signal_name!r}"
            )

        try:
            signal.disconnect(
                callback
            )
        except (RuntimeError, TypeError):
            pass

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(self) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of Controller state.
        """

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
        """
        Return a concise diagnostic representation.
        """

        return (
            "Controller("
            f"tool={self._tool_id!r}, "
            f"selected="
            f"{len(self._selected_ids)}, "
            f"core="
            f"{self._core is not None}"
            ")"
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(self) -> None:
        """
        Dispose the Controller.

        Controller does not own the Core.

        Disposal clears Controller-owned application state and
        prevents further mutations.
        """

        if self._disposed:
            return

        self._tool_id = None
        self._selected_ids.clear()
        self._project = None

        self._disposed = True

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    def _ensure_active(self) -> None:
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
