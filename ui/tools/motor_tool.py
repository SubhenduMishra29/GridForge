# ============================================================
# File: ui/tools/motor_tool.py
# GridForge V2 — SLD Motor Tool
# Author: Subhendu Mishra
# ============================================================

from core.application.commands.motor_commands import CreateMotorCommand

from .model_placement_tool import ModelPlacementTool


class MotorTool(ModelPlacementTool):
    """SLD placement tool for Motor equipment."""

    TOOL_ID = "motor"
    MODEL_NAME = "Motor"
    SYMBOL_ID = "motor"


__all__ = ["MotorTool"]
