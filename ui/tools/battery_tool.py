# ============================================================
# File: ui/tools/battery_tool.py
# GridForge V2 — SLD battery placement tool
# Author: Subhendu Mishra
# ============================================================

from core.application.commands.battery_commands import CreateBatteryCommand

from .model_placement_tool import ModelPlacementTool


class BatteryTool(ModelPlacementTool):
    """SLD placement tool for Battery equipment."""


__all__ = ["BatteryTool"]
