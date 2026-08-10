```python
# ============================================================
# File: ui/core/controller.py
# GridForge UI Controller
# ============================================================
#
# PURPOSE
# -------
# The Controller is the coordination layer between the GridForge
# domain model and the UI systems.
#
# It manages APPLICATION STATE and DISPATCHES EVENTS.
#
#
# ARCHITECTURE
# ------------
#
#                         Controller
#                             │
#             ┌───────────────┼───────────────┐
#             │               │               │
#             ▼               ▼               ▼
#          Model         ToolRegistry    UI Subscribers
#                             │
#                             ▼
#                       Active Tool
#
#
# The Controller does NOT:
#
#     - draw graphics
#     - handle mouse events
#     - create QGraphicsItems
#     - calculate electrical results
#     - modify the Qt scene directly
#     - import individual tools
#     - import individual renderers
#
#
# The Controller DOES:
#
#     - hold the application model reference
#     - maintain active tool state
#     - maintain persistent selection state
#     - publish application events
#     - provide a stable coordination API
#
#
# GOLDEN RULE
# -----------
# UI components communicate through the Controller instead of
# directly manipulating unrelated UI components.
#
# ============================================================

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set


class Controller:
    """
    Central coordination controller for the GridForge UI.

    The Controller is deliberately lightweight.

    It does not contain rendering logic or mouse-event logic.
    Those responsibilities belong to dedicated UI systems.

    Parameters
    ----------
    model:
        GridForge domain/application model.

    tool_registry:
        Optional runtime ToolRegistry.

        The registry is injected rather than imported here so
        the Controller remains independent of concrete tools.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        model: Any,
        tool_registry: Optional[Any] = None,
    ) -> None:
        """
        Initialize the GridForge controller.
        """

        # ----------------------------------------------------
        # Domain model
        # ----------------------------------------------------
        #
        # The Controller holds a reference to the model but does
        # not own the model's internal implementation.
        # ----------------------------------------------------

        self.model = model

        # ----------------------------------------------------
        # Runtime tool registry
        # ----------------------------------------------------
        #
        # This is injected during application initialization.
        #
        # The Controller therefore does not need to know which
        # concrete tools exist.
        # ----------------------------------------------------

        self.tool_registry = tool_registry

        # ----------------------------------------------------
        # Event subscribers
        # ----------------------------------------------------
        #
        # Mapping:
        #
        #     event_name -> callbacks
        #
        # Example:
        #
        #     "selection_changed"
        #     "model_changed"
        #     "tool_changed"
        # ----------------------------------------------------

        self._subscribers: Dict[
            str,
            List[Callable[..., Any]],
        ] = {}

        # ----------------------------------------------------
        # Active tool
        # ----------------------------------------------------
        #
        # Store the tool ID as the persistent application state.
        #
        # The actual tool instance is obtained from ToolRegistry.
        # ----------------------------------------------------

        self.current_tool_id: Optional[str] = None

        # ----------------------------------------------------
        # Persistent selection state
        # ----------------------------------------------------
        #
        # IMPORTANT:
        #
        # Selection stores MODEL IDs.
        #
        # It never stores QGraphicsItem objects.
        #
        # This keeps selection independent from the graphics
        # scene and allows the scene to be rebuilt safely.
        # ----------------------------------------------------

        self.selected_ids: Set[str] = set()

    # ========================================================
    # EVENT SYSTEM
    # ========================================================

    def subscribe(
        self,
        event_name: str,
        callback: Callable[..., Any],
    ) -> Callable[..., Any]:
        """
        Subscribe a callback to an application event.

        Parameters
        ----------
        event_name:
            Name of the event.

        callback:
            Callable invoked when the event is published.

        Returns
        -------
        callable
            The callback that was registered.

        Example
        -------

            controller.subscribe(
                "selection_changed",
                update_selection
            )
        """

        if not isinstance(event_name, str) or not event_name.strip():
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

        # ----------------------------------------------------
        # Prevent accidental duplicate subscriptions.
        # ----------------------------------------------------

        if callback not in subscribers:
            subscribers.append(callback)

        return callback

    # --------------------------------------------------------

    def unsubscribe(
        self,
        event_name: str,
        callback: Callable[..., Any],
    ) -> bool:
        """
        Remove a callback from an event.

        Returns
        -------
        bool
            True if the callback was removed.
            False if it was not subscribed.
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

    # --------------------------------------------------------

    def notify(
        self,
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Publish an application event.

        All registered callbacks receive the supplied arguments.

        Example:

            controller.notify(
                "tool_changed",
                "line"
            )

        Notes
        -----
        The Controller does not know what the subscribers do.

        This is the key property that keeps the UI modular.
        """

        callbacks = list(
            self._subscribers.get(
                event_name,
                [],
            )
        )

        for callback in callbacks:
            callback(*args, **kwargs)

    # ========================================================
    # TOOL MANAGEMENT
    # ========================================================

    def set_tool(
        self,
        tool_id: str,
    ) -> None:
        """
        Set the currently active interaction tool.

        Parameters
        ----------
        tool_id:
            Registered tool identifier.

        Example:

            controller.set_tool("line")

        The Controller stores only the ID.

        The actual tool instance remains owned by ToolRegistry.
        """

        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string"
            )

        tool_id = tool_id.strip()

        # ----------------------------------------------------
        # If a registry is available, verify the tool exists.
        #
        # This catches configuration errors early.
        # ----------------------------------------------------

        if self.tool_registry is not None:

            if not self.tool_registry.contains(tool_id):
                raise KeyError(
                    f"Tool '{tool_id}' is not registered"
                )

        # ----------------------------------------------------
        # Avoid unnecessary state changes.
        # ----------------------------------------------------

        if self.current_tool_id == tool_id:
            return

        self.current_tool_id = tool_id

        # ----------------------------------------------------
        # Notify interested UI systems.
        # ----------------------------------------------------

        self.notify(
            "tool_changed",
            tool_id,
        )

    # --------------------------------------------------------

    def get_current_tool(self) -> Optional[Any]:
        """
        Return the active tool instance.

        Returns
        -------
        object | None
            Active tool instance.

        Notes
        -----
        The Controller stores the tool ID.
        ToolRegistry owns the actual instance.
        """

        if (
            self.tool_registry is None
            or self.current_tool_id is None
        ):
            return None

        return self.tool_registry.get(
            self.current_tool_id
        )

    # --------------------------------------------------------

    def get_current_tool_id(self) -> Optional[str]:
        """
        Return the ID of the currently active tool.
        """

        return self.current_tool_id

    # ========================================================
    # SELECTION MANAGEMENT
    # ========================================================

    def select(
        self,
        obj_id: str,
        multi: bool = False,
    ) -> None:
        """
        Select an object by model ID.

        Parameters
        ----------
        obj_id:
            Model object identifier.

        multi:
            If False:
                Replace the current selection.

            If True:
                Add/toggle the object in the existing selection.

        Notes
        -----
        Selection is model-ID based.

        QGraphicsItems must never be stored here.
        """

        if not isinstance(obj_id, str) or not obj_id.strip():
            raise ValueError(
                "obj_id must be a non-empty string"
            )

        # ----------------------------------------------------
        # Single-selection mode
        # ----------------------------------------------------

        if not multi:
            self.selected_ids.clear()

        # ----------------------------------------------------
        # Toggle selection
        # ----------------------------------------------------

        if obj_id in self.selected_ids:
            self.selected_ids.remove(obj_id)
        else:
            self.selected_ids.add(obj_id)

        # ----------------------------------------------------
        # Notify UI systems.
        # ----------------------------------------------------

        self.notify(
            "selection_changed",
            self.selected_ids.copy(),
        )

    # --------------------------------------------------------

    def add_to_selection(
        self,
        obj_id: str,
    ) -> None:
        """
        Add an object to the current selection without toggling
        an already-selected object.
        """

        if not isinstance(obj_id, str) or not obj_id.strip():
            raise ValueError(
                "obj_id must be a non-empty string"
            )

        if obj_id in self.selected_ids:
            return

        self.selected_ids.add(obj_id)

        self.notify(
            "selection_changed",
            self.selected_ids.copy(),
        )

    # --------------------------------------------------------

    def remove_from_selection(
        self,
        obj_id: str,
    ) -> None:
        """
        Remove an object from the current selection.
        """

        if obj_id not in self.selected_ids:
            return

        self.selected_ids.remove(obj_id)

        self.notify(
            "selection_changed",
            self.selected_ids.copy(),
        )

    # --------------------------------------------------------

    def clear_selection(self) -> None:
        """
        Clear the complete current selection.
        """

        if not self.selected_ids:
            return

        self.selected_ids.clear()

        self.notify(
            "selection_changed",
            set(),
        )

    # --------------------------------------------------------

    def is_selected(
        self,
        obj_id: str,
    ) -> bool:
        """
        Return True when the object ID is selected.
        """

        return obj_id in self.selected_ids

    # --------------------------------------------------------

    def get_selection(self) -> Set[str]:
        """
        Return a copy of the current selection.

        A copy is returned so external systems cannot directly
        corrupt Controller state.
        """

        return self.selected_ids.copy()

    # ========================================================
    # MODEL CHANGE NOTIFICATION
    # ========================================================

    def model_changed(self) -> None:
        """
        Notify the UI that the domain model has changed.

        Tools should call this after a successful model
        modification.

        Example:

            graph.add_line(...)
            controller.model_changed()

        The Controller does not perform rendering itself.
        RenderSystem or other subscribers respond to the event.
        """

        self.notify(
            "model_changed",
            self.model,
        )

    # ========================================================
    # GENERIC STATE NOTIFICATION
    # ========================================================

    def state_changed(
        self,
        state_name: str,
        value: Any = None,
    ) -> None:
        """
        Publish a generic state-change event.

        This provides a controlled extension point for future
        UI state without turning Controller into a collection
        of unrelated setter methods.
        """

        self.notify(
            "state_changed",
            state_name,
            value,
        )

    # ========================================================
    # DEBUG / INTROSPECTION
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

    # ========================================================
    # DEBUG REPRESENTATION
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
```
