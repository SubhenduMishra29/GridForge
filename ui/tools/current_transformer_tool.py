# GridForge V2 — SLD current-transformer tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class CurrentTransformerTool(ModelPlacementTool):
    TOOL_ID = "current_transformer"
    MODEL_NAME = "Current Transformer"

__all__ = ["CurrentTransformerTool"]
