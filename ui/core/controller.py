"""
GridForge V2 — UI Controller
============================

File:
    ui/core/controller.py

Purpose
-------
Provides the central coordination state for the GridForge UI.

The Controller sits between UI systems and the authoritative
GridForge application/domain layer.

It owns UI coordination state such as:

    - active tool identifier
    - persistent selection identifiers
    - UI-level event subscriptions

It does not own domain state and does not perform domain
mutations.

Architectural Contract
----------------------
1. The Core/domain model remains authoritative.
2. The Controller does not perform electrical calculations.
3. The Controller does not directly mutate the domain model.
4. The Controller does not render graphics.
5. The Controller does not handle Qt input events.
6. The Controller does not instantiate concrete tools.
7. Tool instances remain owned by ToolRegistry.
8. Selection is stored using model object IDs only.
9. The Controller contains no Qt dependency.
10. UI event notification is distinct from authoritative
    domain events.
11. Core mutations must occur through the established
    command/application boundary.

Dependency Direction
--------------------
    UI Input
       |
       v
    InteractionManager / Tool
       |
       v
    Application / Command Boundary
       |
       v
    GridForge Core

    Controller
       |
       +---- active tool ID
       |
       +---- selection state
       |
       +---- UI coordination events
       |
       +---- injected service references
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set


class Controller:
    """
    Central UI coordination controller.

    The Controller deliberately contains only UI coordination
    state. It is not the authoritative application/domain
    controller.
    """

    def __init__(
        self,
        model: Any,
        tool_registry: Optional[Any] = None,
    ) -> None:
        """
        Initialize the UI Controller.

        Parameters
        ----------
        model:
            Reference to the authoritative GridForge model or
            application-facing model context.

        tool_registry:
            Optional injected ToolRegistry.

            The Controller does not import, construct, or own
            concrete tool implementations.
        """

        self.model = model
        self.tool_registry = tool_registry

        # ----------------------------------------------------
        # UI-level event subscribers
        # ----------------------------------------------------

        self._subscribers: Dict[
            str,
            List[Callable[..., Any]],
        ] = {}

        # ----------------------------------------------------
        # Active tool
        # ----------------------------------------------------
        #
        # Only the registered tool identifier is stored here.
        #
        # Example:
        #
        #     "select"
        #     "bus"
        #     "line"
        #
        # The concrete instance belongs to ToolRegistry.
        # ----------------------------------------------------

        self.current_tool_id: Optional[str] = None

        # ----------------------------------------------------
        # Persistent logical selection
        # ----------------------------------------------------
        #
        # Only authoritative model object IDs are stored.
        #
        # Graphics objects must never be stored here.
        # ----------------------------------------------------

        self.selected_ids: Set[str] = set()

    # ========================================================
    # UI EVENT SYSTEM
    # ========================================================

    def subscribe(
        self,
        event_name: str,
        callback: Callable[..., Any],
    ) -> Callable[..., Any]:
        """
        Subscribe a callback to a UI coordination event.
        """

        if (
            not isinstance(event_name, str)
            or not event_name.strip()
        ):
            raise ValueError(
                "event_name must be a non-empty string"
            )

        if not callable(callback):
            raise TypeError(
                "callback must be callable"
            )

        subscribers = self._subscribers.setdefault(
            event_name,
            [],
        )

        if callback not in subscribers:
            subscribers.append(callback)

        return callback

    def unsubscribe(
        self,
        event_name: str,
        callback: Callable[..., Any],
    ) -> bool:
        """
        Remove a callback from a UI coordination event.

        Returns
        -------
        bool
            True if the callback was removed.
            False if it was not registered.
        """

        subscribers = self._subscribers.get(event_name)

        if not subscribers:
            return False

        if callback not in subscribers:
            return False

        subscribers.remove(callback)

        if not subscribers:
            del self._subscribers[event_name]

        return True

    def notify(
        self,
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Notify all subscribers of a UI coordination event.

        Subscriber iteration uses a snapshot so callbacks may
        safely subscribe or unsubscribe during notification.
        """

        callbacks = list(
            self._subscribers.get(
                event_name,
                [],
            )
        )

        for callback in callbacks:
            callback(
                *args,
                **kwargs,
            )

    # ========================================================
    # TOOL MANAGEMENT
    # ========================================================

    def set_tool(
        self,
        tool_id: str,
    ) -> None:
        """
        Set the active interaction tool.

        The Controller stores only the tool identifier.
        ToolRegistry owns the actual tool instance.
        """

        if (
            not isinstance(tool_id, str)
            or not tool_id.strip()
        ):
            raise ValueError(
                "tool_id must be a non-empty string"
            )

        tool_id = tool_id.strip()

        if self.tool_registry is not None:
            if not self.tool_registry.contains(tool_id):
                raise KeyError(
                    f"Tool '{tool_id}' is not registered"
                )

        if self.current_tool_id == tool_id:
            return

        previous_tool_id = self.current_tool_id
        self.current_tool_id = tool_id

        self.notify(
            "tool_changed",
            tool_id,
            previous_tool_id,
        )

    def clear_tool(self) -> None:
        """
        Clear the active interaction tool.
        """

        if self.current_tool_id is None:
            return

        previous_tool_id = self.current_tool_id
        self.current_tool_id = None

        self.notify(
            "tool_changed",
            None,
            previous_tool_id,
        )

    def get_current_tool_id(self) -> Optional[str]:
        """
        Return the active tool identifier.
        """

        return self.current_tool_id

    def get_current_tool(self) -> Optional[Any]:
        """
        Return the active tool instance from ToolRegistry.

        The Controller never creates or owns the tool.
        """

        if (
            self.tool_registry is None
            or self.current_tool_id is None
        ):
            return None

        return self.tool_registry.get(
            self.current_tool_id
        )

    # ========================================================
    # SELECTION MANAGEMENT
    # ========================================================

    @staticmethod
    def _validate_object_id(obj_id: str) -> str:
        """
        Validate and normalize a model object identifier.
        """

        if (
            not isinstance(obj_id, str)
            or not obj_id.strip()
        ):
            raise ValueError(
                "obj_id must be a non-empty string"
            )

        return obj_id.strip()

    def select(
        self,
        obj_id: str,
        multi: bool = False,
    ) -> None:
        """
        Select an object.

        Parameters
        ----------
        obj_id:
            Authoritative model object ID.

        multi:
            False:
                Replace the current selection with obj_id.

            True:
                Toggle obj_id in the current selection.
        """

        obj_id = self._validate_object_id(obj_id)

        if multi:
            if obj_id in self.selected_ids:
                self.selected_ids.remove(obj_id)
            else:
                self.selected_ids.add(obj_id)

        else:
            if (
                len(self.selected_ids) == 1
                and obj_id in self.selected_ids
            ):
                return

            self.selected_ids.clear()
            self.selected_ids.add(obj_id)

        self.notify(
            "selection_changed",
            self.selected_ids.copy(),
        )

    def add_to_selection(
        self,
        obj_id: str,
    ) -> None:
        """
        Add an object to the current selection.

        This operation is idempotent.
        """

        obj_id = self._validate_object_id(obj_id)

        if obj_id in self.selected_ids:
            return

        self.selected_ids.add(obj_id)

        self.notify(
            "selection_changed",
            self.selected_ids.copy(),
        )

    def remove_from_selection(
        self,
        obj_id: str,
    ) -> None:
        """
        Remove an object from the current selection.
        """

        obj_id = self._validate_object_id(obj_id)

        if obj_id not in self.selected_ids:
            return

        self.selected_ids.remove(obj_id)

        self.notify(
            "selection_changed",
            self.selected_ids.copy(),
        )

    def clear_selection(self) -> None:
        """
        Clear the current selection.
        """

        if not self.selected_ids:
            return

        self.selected_ids.clear()

        self.notify(
            "selection_changed",
            set(),
        )

    def is_selected(
        self,
        obj_id: str,
    ) -> bool:
        """
        Return whether an object is currently selected.
        """

        obj_id = self._validate_object_id(obj_id)

        return obj_id in self.selected_ids

    def get_selection(self) -> Set[str]:
        """
        Return a copy of the current logical selection.
        """

        return self.selected_ids.copy()

    # ========================================================
    # MODEL/UI SYNCHRONIZATION
    # ========================================================

    def model_changed(self) -> None:
        """
        Notify UI subscribers that the authoritative model
        state has changed.

        This method does not mutate the model.

        The authoritative application/core event mechanism
        remains responsible for determining that a domain
        mutation occurred.
        """

        self.notify(
            "model_changed",
            self.model,
        )

    # ========================================================
    # GENERIC UI STATE
    # ========================================================

    def state_changed(
        self,
        state_name: str,
        value: Any = None,
    ) -> None:
        """
        Publish a UI/application-state notification.

        This is intended for coordination state that does not
        warrant a dedicated Controller method.
        """

        if (
            not isinstance(state_name, str)
            or not state_name.strip()
        ):
            raise ValueError(
                "state_name must be a non-empty string"
            )

        self.notify(
            "state_changed",
            state_name.strip(),
            value,
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def subscriber_count(
        self,
        event_name: str,
    ) -> int:
        """
        Return the number of subscribers for an event.
        """

        return len(
            self._subscribers.get(
                event_name,
                [],
            )
        )

    def get_state(self) -> Dict[str, Any]:
        """
        Return a diagnostic snapshot of Controller state.

        The returned structure is detached from internal
        mutable selection state.
        """

        return {
            "current_tool_id": self.current_tool_id,
            "selected_ids": self.selected_ids.copy(),
            "events": list(self._subscribers.keys()),
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "Controller("
            f"tool={self.current_tool_id!r}, "
            f"selected={len(self.selected_ids)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "Controller",
]
