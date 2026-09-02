# GridForge V2 — SLD fuse tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class FuseTool(ModelPlacementTool):
    TOOL_ID = "fuse"
    MODEL_NAME = "Fuse"

__all__ = ["FuseTool"]
