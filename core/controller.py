"""
Application Controller

Location:
---------
core/controller.py

Purpose:
--------
This is the central coordination layer of the application.

It manages:
- Application state (e.g., active tool)
- Communication between UI components (via events)

It does NOT:
--------------
- Create UI elements
- Import UI modules
- Contain rendering logic

Think of this as:
→ The "brain" of the application (lightweight version)

Future Direction:
-----------------
This controller includes a simple event system.
Later, this will evolve into a dedicated event bus system.
"""


from typing import Optional, Callable, Dict, List


class Controller:
    """
    Central application controller.

    Keeps track of global state and notifies interested parts
    of the application when something changes.
    """

    def __init__(self):
        # --------------------------------------------------------------
        # Application State
        # --------------------------------------------------------------

        # Stores the currently active tool (e.g., "select", "line", etc.)
        self._active_tool: Optional[str] = None

        # --------------------------------------------------------------
        # Event Subscribers
        # --------------------------------------------------------------

        # Dictionary of event_name -> list of callback functions
        # Example:
        # {
        #     "tool_changed": [func1, func2]
        # }
        self._subscribers: Dict[str, List[Callable]] = {}

    # ==============================================================
    # TOOL MANAGEMENT
    # ==============================================================

    def set_tool(self, tool_id: str):
        """
        Set the currently active tool.

        Called by UI elements (e.g., toolbar buttons).

        Args:
            tool_id (str): Identifier of the selected tool
        """

        # Avoid unnecessary updates
        if self._active_tool == tool_id:
            return

        # Update state
        self._active_tool = tool_id

        print(f"[Controller] Active tool set to: {tool_id}")

        # Notify all listeners that the tool has changed
        self._emit("tool_changed", tool_id)

    def get_active_tool(self) -> Optional[str]:
        """
        Get the currently active tool.

        Returns:
            str or None
        """
        return self._active_tool

    # ==============================================================
    # EVENT SYSTEM (LIGHTWEIGHT)
    # ==============================================================

    def subscribe(self, event_name: str, callback: Callable):
        """
        Register a callback for a specific event.

        Example:
            controller.subscribe("tool_changed", my_function)

        Args:
            event_name (str): Name of the event
            callback (Callable): Function to call when event is triggered
        """

        if event_name not in self._subscribers:
            self._subscribers[event_name] = []

        self._subscribers[event_name].append(callback)

    def _emit(self, event_name: str, *args, **kwargs):
        """
        Trigger an event and notify all subscribers.

        This is an internal method and should not be called directly
        from outside the controller.

        Args:
            event_name (str): Name of the event
            *args, **kwargs: Data passed to subscribers
        """

        for callback in self._subscribers.get(event_name, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[Controller] Error in '{event_name}' handler: {e}")
