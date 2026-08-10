"""
Tool Registry

Location:
---------
ui/core/tool_registry.py

Purpose:
--------
Stores and manages tool instances.

This acts as the central access point for all interaction tools.
"""

class ToolRegistry:
    """
    Holds tool instances mapped by tool_id.
    """

    def __init__(self):
        # Mapping: tool_id -> tool instance
        self._tools = {}

    # ==========================================================
    # REGISTRATION
    # ==========================================================

    def register(self, tool_id: str, tool_instance):
        """
        Register a tool instance.

        Parameters:
        -----------
        tool_id : str
            Unique identifier (e.g., "select", "line")

        tool_instance : object
            Tool implementation
        """
        self._tools[tool_id] = tool_instance
        print(f"[ToolRegistry] Registered tool: {tool_id}")

    # ==========================================================
    # ACCESS
    # ==========================================================

    def get(self, tool_id: str):
        """
        Retrieve a tool by ID.
        """
        return self._tools.get(tool_id)

    def list_tools(self):
        """
        Returns all registered tools.
        """
        return list(self._tools.keys())
