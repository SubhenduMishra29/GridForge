"""
Tools package

Purpose:
--------
Contains all interaction tools used by the editor.

Examples:
---------
- SelectTool
- BusTool
- LineTool

Important:
----------
Tools are auto-registered via decorators:
    @register_tool("tool_id")

Registration is triggered from:
    ui/core/__init__.py

So we DO NOT import tools here to avoid:
- circular dependencies
- duplicate side effects
"""

# Optional: explicit exports (not required)
__all__ = [
    "select_tool",
    "bus_tool",
    "line_tool",
]
