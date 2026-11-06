# ============================================================
# File: ui/tools/fuse_tool.py
# GridForge V2 — SLD Fuse Tool
# Author: Subhendu Mishra
# ============================================================

from core.application.commands.model_commands import CreateFuseCommand

from .model_placement_tool import ModelPlacementTool


class FuseTool(ModelPlacementTool):
    """SLD placement tool for Fuse equipment."""

    TOOL_ID = "fuse"
    MODEL_NAME = "Fuse"
    SYMBOL_ID = "fuse"


__all__ = ["FuseTool"]
