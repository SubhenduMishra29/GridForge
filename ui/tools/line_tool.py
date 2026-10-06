# ============================================================
# File: ui/tools/line_tool.py
# GridForge V2 — Line Placement Tool
# Author: Subhendu Mishra
# ============================================================
"""Position-first Line placement through the canonical draft lifecycle."""

from .model_placement_tool import ModelPlacementTool


class LineTool(ModelPlacementTool):
    """Thin specialization of the canonical position-first placement tool."""

    TOOL_ID = "line"
    MODEL_NAME = "Line"
    SYMBOL_ID = "line"


__all__ = ["LineTool"]
