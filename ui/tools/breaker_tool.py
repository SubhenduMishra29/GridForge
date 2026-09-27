# GridForge V2 — SLD breaker tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool
class BreakerTool(ModelPlacementTool):
    TOOL_ID = "breaker"
    MODEL_NAME = "Breaker"
    SYMBOL_ID = "breaker"
__all__=["BreakerTool"]
