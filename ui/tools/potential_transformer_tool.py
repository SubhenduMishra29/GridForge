# GridForge V2 — SLD potential-transformer tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class PotentialTransformerTool(ModelPlacementTool):
    TOOL_ID = "potential_transformer"
    MODEL_NAME = "Potential Transformer"

__all__ = ["PotentialTransformerTool"]
