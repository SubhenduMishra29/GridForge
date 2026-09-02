# GridForge V2 — SLD load tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class LoadTool(ModelPlacementTool):
    TOOL_ID = "load"
    MODEL_NAME = "Load"

__all__ = ["LoadTool"]
