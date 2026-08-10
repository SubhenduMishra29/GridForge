"""
Controller

Location:
---------
ui/core/controller.py

Purpose:
--------
Acts as the central coordination layer between:
- UI (tools, interaction manager)
- Model (data layer)
- Systems (rendering, selection, etc.)

This follows a lightweight event-driven architecture.

Core Responsibilities:
----------------------
1. Store application-wide state (current tool, selection)
2. Provide event system (publish/subscribe)
3. Act as the single source of truth for selection
4. Coordinate updates between model and UI

Design Philosophy:
------------------
- Controller does NOT render
- Controller does NOT handle raw UI events
- Controller ONLY manages state + dispatches events
"""


class Controller:
    def __init__(self, model):
        """
        Initialize controller with application model.

        Parameters:
        -----------
        model : object
            Your domain model (contains graph, buses, lines, etc.)
        """

        self.model = model

        # ------------------------------------------------------
        # Event system
        # ------------------------------------------------------
        # event_name -> list of callbacks
        self._subscribers = {}

        # ------------------------------------------------------
        # Tool state
        # ------------------------------------------------------
        self.current_tool = None

        # ------------------------------------------------------
        # Selection state (PERSISTENT)
        # ------------------------------------------------------
        # Stores IDs (NOT QGraphicsItems)
        self.selected_ids = set()

    # ==========================================================
    # EVENT SYSTEM (PUB/SUB)
    # ==========================================================

    def subscribe(self, event_name: str, callback):
        """
        Subscribe to an event.

        Parameters:
        -----------
        event_name : str
        callback : callable
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []

        self._subscribers[event_name].append(callback)

    # ----------------------------------------------------------

    def notify(self, event_name: str, *args, **kwargs):
        """
        Notify all listeners of an event.

        Example:
        --------
        self.notify("model_changed")
        """
        for callback in self._subscribers.get(event_name, []):
            callback(*args, **kwargs)

    # ==========================================================
    # TOOL MANAGEMENT
    # ==========================================================

    def set_tool(self, tool_id: str):
        """
        Set the active interaction tool.

        Triggered by:
        - Toolbar clicks

        Effects:
        --------
        - Updates current tool
        - Notifies InteractionManager
        """
        self.current_tool = tool_id
        print(f"[Controller] Tool set: {tool_id}")

        self.notify("tool_changed", tool_id)

    # ==========================================================
    # SELECTION MANAGEMENT (MODEL-DRIVEN)
    # ==========================================================

    def select(self, obj_id: str, multi: bool = False):
        """
        Select or toggle an object by ID.

        Parameters:
        -----------
        obj_id : str
            ID of bus or line

        multi : bool
            If True → multi-select mode (Ctrl/Shift)
            If False → replace selection
        """

        if not multi:
            self.selected_ids.clear()

        # Toggle behavior
        if obj_id in self.selected_ids:
            self.selected_ids.remove(obj_id)
        else:
            self.selected_ids.add(obj_id)

        print(f"[Controller] Selected IDs: {self.selected_ids}")

        # Notify UI to update selection visuals
        self.notify("selection_changed")

    # ----------------------------------------------------------

    def clear_selection(self):
        """
        Clear all selections.
        """
        if not self.selected_ids:
            return

        self.selected_ids.clear()

        print("[Controller] Selection cleared")

        self.notify("selection_changed")
