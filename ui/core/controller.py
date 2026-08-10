```python
# ============================================================
# File: ui/core/controller.py
# GridForge UI Controller
# ============================================================
#
# PURPOSE
# -------
# Central coordination layer between:
#
#     Domain Model
#          │
#          ▼
#      Controller
#          │
#     ┌────┼───────────────┐
#     ▼    ▼               ▼
#  Tools Selection     UI Systems
#
#
# RESPONSIBILITIES
# ----------------
#
# Controller:
#
# - stores the application model reference
# - stores the active tool ID
# - provides access to the registered active tool
# - maintains persistent selection state
# - publishes application events
# - provides a stable coordination API
#
#
# CONTROLLER DOES NOT:
# -------------------
#
# - handle mouse events
# - render graphics
# - create QGraphicsItems
# - modify QGraphicsScene
# - import concrete tools
# - import renderers
# - perform electrical calculations
#
#
# TOOL ARCHITECTURE
# -----------------
#
# Controller stores:
#
#     current_tool_id = "line"
#
# ToolRegistry stores:
#
#     "line" -> LineTool instance
#
# InteractionManager obtains:
#
#     controller.get_current_tool()
#
#
# Therefore:
#
#     Controller
#          │
#          │ tool ID
#          ▼
#     ToolRegistry
#          │
#          │ tool instance
#          ▼
#     InteractionManager
#          │
#          ▼
#     Active Tool
#
#
# ============================================================

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
)


class Controller:
    """
    Central coordination controller for the GridForge UI.

    The Controller is deliberately lightweight.

    It manages application state and publishes events,
    while specialized systems perform the actual work.
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
        Initialize the GridForge Controller.

        Parameters
        ----------
        model:
            GridForge domain/application model.

        tool_registry:
            Optional ToolRegistry instance.

            The registry is injected rather than imported,
            keeping the Controller independent from concrete
            tool implementations.
        """

        # ----------------------------------------------------
        # DOMAIN MODEL
        # ----------------------------------------------------

        self.model = model

        # ----------------------------------------------------
        # TOOL REGISTRY
        # ----------------------------------------------------
        #
        # The Controller does not create tools.
        #
        # It only keeps a reference to the registry so that
        # systems such as InteractionManager can obtain the
        # currently active tool through the Controller.
        # ----------------------------------------------------

        self.tool_registry = tool_registry

        # ----------------------------------------------------
        # EVENT SYSTEM
        # ----------------------------------------------------
        #
        # Structure:
        #
        # {
        #     "tool_changed": [
        #         callback1,
        #         callback2
        #     ],
        #
        #     "model_changed": [
        #         callback1
        #     ]
        # }
        # ----------------------------------------------------

        self._subscribers: Dict[
            str,
            List[Callable[..., Any]],
        ] = {}

        # ----------------------------------------------------
        # ACTIVE TOOL
        # ----------------------------------------------------
        #
        # IMPORTANT:
        #
        # Only the identifier is stored here.
        #
        # Example:
        #
        #     "select"
        #     "bus"
        #     "line"
        #
        # The actual tool instance belongs to ToolRegistry.
        # ----------------------------------------------------

        self.current_tool_id: Optional[str] = None

        # ----------------------------------------------------
        # PERSISTENT SELECTION
        # ----------------------------------------------------
        #
        # Stores MODEL IDs only.
        #
        # Never store:
        #
        #     QGraphicsItem
        #     QGraphicsObject
        #     QWidget
        #
        # This allows RenderSystem to safely rebuild the
        # graphics scene without losing logical selection.
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
            Callable that receives the event notification.

        Returns
        -------
        callable
            The registered callback.
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

        # ----------------------------------------------------
        # Prevent duplicate subscriptions.
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
            True if removed.
            False if it was not registered.
        """

        subscribers = self._subscribers.get(
            event_name
        )

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
        Publish an event to all subscribers.

        Example
        -------
        controller.notify(
            "model_changed",
            model
        )
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

        The Controller stores only the tool ID.

        The actual tool instance remains inside ToolRegistry.

        Example
        -------
        controller.set_tool("line")
        """

        if (
            not isinstance(tool_id, str)
            or not tool_id.strip()
        ):
            raise ValueError(
                "tool_id must be a non-empty string"
            )

        tool_id = tool_id.strip()

        # ----------------------------------------------------
        # Validate registration when a registry is available.
        #
        # ToolRegistry must provide:
        #
        #     contains(tool_id)
        #
        # ----------------------------------------------------

        if self.tool_registry is not None:

            if not self.tool_registry.contains(
                tool_id
            ):
                raise KeyError(
                    f"Tool '{tool_id}' is not registered"
                )

        # ----------------------------------------------------
        # Ignore redundant tool changes.
        # ----------------------------------------------------

        if self.current_tool_id == tool_id:
            return

        # ----------------------------------------------------
        # Update state.
        # ----------------------------------------------------

        self.current_tool_id = tool_id

        print(
            f"[Controller] Tool set: {tool_id}"
        )

        # ----------------------------------------------------
        # Notify InteractionManager.
        # ----------------------------------------------------

        self.notify(
            "tool_changed",
            tool_id,
        )

    # --------------------------------------------------------

    def clear_tool(self) -> None:
        """
        Clear the currently active tool.

        This publishes:

            tool_changed(None)

        so InteractionManager can clear its transient
        interaction state and preview graphics.
        """

        if self.current_tool_id is None:
            return

        previous_tool = (
            self.current_tool_id
        )

        self.current_tool_id = None

        print(
            "[Controller] Tool cleared: "
            f"{previous_tool}"
        )

        self.notify(
            "tool_changed",
            None,
        )

    # --------------------------------------------------------

    def get_current_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the active tool ID.

        Returns
        -------
        str | None
        """

        return self.current_tool_id

    # --------------------------------------------------------

    def get_current_tool(
        self,
    ) -> Optional[Any]:
        """
        Return the active tool instance.

        The Controller does not create the instance.

        ToolRegistry owns the actual tool object.

        Returns
        -------
        object | None
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

    def select(
        self,
        obj_id: str,
        multi: bool = False,
    ) -> None:
        """
        Select or toggle an object.

        Parameters
        ----------
        obj_id:
            Model object ID.

        multi:
            False:
                Replace current selection.

            True:
                Toggle the object in the current selection.
        """

        if (
            not isinstance(obj_id, str)
            or not obj_id.strip()
        ):
            raise ValueError(
                "obj_id must be a non-empty string"
            )

        obj_id = obj_id.strip()

        # ----------------------------------------------------
        # Single-selection mode.
        # ----------------------------------------------------

        if not multi:
            self.selected_ids.clear()

        # ----------------------------------------------------
        # Toggle selection.
        # ----------------------------------------------------

        if obj_id in self.selected_ids:
            self.selected_ids.remove(
                obj_id
            )
        else:
            self.selected_ids.add(
                obj_id
            )

        # ----------------------------------------------------
        # Notify UI.
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
        Add an object to the current selection.

        Unlike select(..., multi=True), this method does not
        toggle an already-selected object.
        """

        if (
            not isinstance(obj_id, str)
            or not obj_id.strip()
        ):
            raise ValueError(
                "obj_id must be a non-empty string"
            )

        obj_id = obj_id.strip()

        if obj_id in self.selected_ids:
            return

        self.selected_ids.add(
            obj_id
        )

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

        self.selected_ids.remove(
            obj_id
        )

        self.notify(
            "selection_changed",
            self.selected_ids.copy(),
        )

    # --------------------------------------------------------

    def clear_selection(
        self,
    ) -> None:
        """
        Clear all selected objects.
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
        Return True if the object is selected.
        """

        return obj_id in self.selected_ids

    # --------------------------------------------------------

    def get_selection(
        self,
    ) -> Set[str]:
        """
        Return a copy of the current selection.
        """

        return self.selected_ids.copy()

    # ========================================================
    # MODEL CHANGE NOTIFICATION
    # ========================================================

    def model_changed(
        self,
    ) -> None:
        """
        Notify UI systems that the domain model changed.

        The Controller does not render the change.

        RenderSystem and other subscribers decide what
        action is required.
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
        Publish a generic application-state change.

        This provides an extension point for future UI state.
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

    # --------------------------------------------------------

    def get_state(
        self,
    ) -> Dict[str, Any]:
        """
        Return a diagnostic snapshot of Controller state.
        """

        return {
            "current_tool_id": (
                self.current_tool_id
            ),
            "selected_ids": (
                self.selected_ids.copy()
            ),
            "events": list(
                self._subscribers.keys()
            ),
        }

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "Controller("
            f"tool={self.current_tool_id!r}, "
            f"selected="
            f"{len(self.selected_ids)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "Controller",
]
```
