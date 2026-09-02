# GridForge V2 — SLD reactor tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class ReactorTool(ModelPlacementTool):
    TOOL_ID = "reactor"
    MODEL_NAME = "Reactor"

__all__ = ["ReactorTool"]
