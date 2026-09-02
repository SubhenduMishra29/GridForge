# GridForge V2 — SLD CVT tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class CVTTool(ModelPlacementTool):
    TOOL_ID = "cvt"
    MODEL_NAME = "CVT"

__all__ = ["CVTTool"]
