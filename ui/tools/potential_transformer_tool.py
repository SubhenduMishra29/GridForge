# GridForge V2 — SLD potential-transformer tool. Author: Subhendu Mishra
from core.application.commands.pt_commands import CreatePTCommand
from .model_placement_tool import ModelPlacementTool


class PotentialTransformerTool(ModelPlacementTool):
    TOOL_ID = "potential_transformer"
    MODEL_NAME = "Potential Transformer"
    SYMBOL_ID = "potential_transformer"


__all__ = ["PotentialTransformerTool"]
