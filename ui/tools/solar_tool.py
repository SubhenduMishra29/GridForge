# ============================================================
# File: ui/tools/solar_tool.py
# GridForge V2 — SLD Solar Tool
# Author: Subhendu Mishra
# ============================================================

from core.application.commands.solar_commands import CreateSolarCommand

from .model_placement_tool import ModelPlacementTool


class SolarTool(ModelPlacementTool):
    """SLD placement tool for Solar equipment."""

    TOOL_ID = "solar"
    MODEL_NAME = "Solar"
    SYMBOL_ID = "solar"


__all__ = ["SolarTool"]
