# GridForge V2 — SLD motor tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class MotorTool(ModelPlacementTool):
    TOOL_ID = "motor"
    MODEL_NAME = "Motor"

__all__ = ["MotorTool"]
