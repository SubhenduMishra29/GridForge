# ============================================================
# File: ui/tools/relay_tool.py
# GridForge V2 — SLD Relay Tool
# Author: Subhendu Mishra
# ============================================================
"""Relay placement through the canonical creation contract."""

from .model_placement_tool import ModelPlacementTool


class RelayTool(ModelPlacementTool):
    TOOL_ID = "relay"
    MODEL_NAME = "Relay"
    SYMBOL_ID = "relay"


__all__ = ["RelayTool"]
