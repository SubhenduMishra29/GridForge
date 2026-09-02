# GridForge V2 — SLD battery tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class BatteryTool(ModelPlacementTool):
    TOOL_ID = "battery"
    MODEL_NAME = "Battery"

__all__ = ["BatteryTool"]
