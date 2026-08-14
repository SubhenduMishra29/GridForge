# ============================================================
# File: ui/tools/__init__.py
# GridForge V2 — Tools Package
# ============================================================
"""
GridForge UI interaction tools.

This package contains concrete canvas interaction tools.

Built-in tools
--------------
    SelectTool
        Selection and movement interaction.

    BusTool
        Bus-placement interaction.

    LineTool
        Electrical line-creation interaction.

Registration
------------
Concrete tools register themselves with the centralized
ToolRegistry through their module-level registration decorators.

Importing this package therefore ensures that the built-in
tools are loaded and registered.

This package does NOT:

    - create tool instances;
    - manage the active tool;
    - route Qt events;
    - own ToolManager;
    - implement tool selection;
    - contain business logic.

ToolManager owns tool lifecycle and active-tool state.

Qt Architecture
---------------
No direct Qt imports are required here.
"""

from __future__ import annotations

from ui.tools.select_tool import SelectTool
from ui.tools.bus_tool import BusTool
from ui.tools.line_tool import LineTool


__all__ = [
    "SelectTool",
    "BusTool",
    "LineTool",
]
