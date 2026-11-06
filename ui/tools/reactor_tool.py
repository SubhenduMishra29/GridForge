# GridForge V2 — SLD reactor tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool
class ReactorTool(ModelPlacementTool):
    TOOL_ID = "reactor"
    MODEL_NAME = "Reactor"
    SYMBOL_ID = "reactor"
    SYMBOL_ID="reactor"
__all__=["ReactorTool"]
