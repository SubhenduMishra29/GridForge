# GridForge V2 — SLD solar tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class SolarTool(ModelPlacementTool):
    TOOL_ID = "solar"
    MODEL_NAME = "Solar"

__all__ = ["SolarTool"]
