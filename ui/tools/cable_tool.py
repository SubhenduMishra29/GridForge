# ============================================================
# File: ui/tools/cable_tool.py
# GridForge V2 — Cable Placement Tool
# Author: Subhendu Mishra
# ============================================================
"""Position-first Cable placement through the canonical draft lifecycle."""

from .model_placement_tool import ModelPlacementTool


class CableTool(ModelPlacementTool):
    """Thin specialization of the canonical position-first placement tool."""

    TOOL_ID = "cable"
    MODEL_NAME = "Cable"
    SYMBOL_ID = "cable"


__all__ = ["CableTool"]
