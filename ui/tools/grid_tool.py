# GridForge V2 — SLD grid tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class GridTool(ModelPlacementTool):
    TOOL_ID = "grid"
    MODEL_NAME = "Grid"

__all__ = ["GridTool"]
