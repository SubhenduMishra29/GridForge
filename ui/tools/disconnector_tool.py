# GridForge V2 — SLD disconnector tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class DisconnectorTool(ModelPlacementTool):
    TOOL_ID = "disconnector"
    MODEL_NAME = "Disconnector"

__all__ = ["DisconnectorTool"]
