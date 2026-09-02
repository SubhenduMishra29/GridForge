# GridForge V2 — SLD shunt tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class ShuntTool(ModelPlacementTool):
    TOOL_ID = "shunt"
    MODEL_NAME = "Shunt"

__all__ = ["ShuntTool"]
