# GridForge V2 — SLD generator tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool
class GeneratorTool(ModelPlacementTool):
    TOOL_ID = "generator"
    MODEL_NAME = "Generator"
    SYMBOL_ID = "generator"
    SYMBOL_ID="generator"
__all__=["GeneratorTool"]
