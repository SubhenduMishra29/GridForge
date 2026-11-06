# ============================================================
# GridForge V2
# Author: Subhendu Mishra
# ============================================================
# File:
#     ui/tools/bus_tool.py
#
# Purpose:
#     SLD bus-placement interaction tool.
# ============================================================

from __future__ import annotations

from .model_placement_tool import ModelPlacementTool


class BusTool(ModelPlacementTool):
    """Bus placement through the canonical generic draft lifecycle."""

    TOOL_ID = "bus"
    MODEL_NAME = "Bus"
    SYMBOL_ID = "bus"


__all__ = ["BusTool"]
