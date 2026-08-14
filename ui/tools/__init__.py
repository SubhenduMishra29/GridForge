# ============================================================
# File: ui/tools/__init__.py
# GridForge V2 — UI Tools Package
# ============================================================
"""
GridForge V2 UI Tools package.

The concrete tool set is intentionally frozen to exactly:

    SelectTool
    BusTool
    LineTool

Tools represent user interaction intent.

They do not own:

    - Core model state;
    - application command history;
    - rendering;
    - navigation;
    - selection authority;
    - electrical calculations.

Tool registration and lifecycle are handled by ToolManager.

Concrete tools are imported explicitly here so package-level
consumers have a stable public API.

No automatic plugin discovery is performed.
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
