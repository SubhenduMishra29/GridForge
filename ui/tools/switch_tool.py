# GridForge V2 — SLD switch tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class SwitchTool(ModelPlacementTool):
    TOOL_ID = "switch"
    MODEL_NAME = "Switch"

__all__ = ["SwitchTool"]
