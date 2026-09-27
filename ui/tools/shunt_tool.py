# GridForge V2 — SLD shunt tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool
class ShuntTool(ModelPlacementTool):
    TOOL_ID = "shunt"
    MODEL_NAME = "Shunt"
    SYMBOL_ID = "shunt"
    SYMBOL_ID="shunt"
__all__=["ShuntTool"]
