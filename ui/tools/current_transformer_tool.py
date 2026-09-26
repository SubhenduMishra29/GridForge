# GridForge V2 — SLD current-transformer tool. Author: Subhendu Mishra
from core.application.commands.measurement_commands import CreateCurrentTransformerCommand
from .model_placement_tool import ModelPlacementTool


class CurrentTransformerTool(ModelPlacementTool):
    TOOL_ID = "current_transformer"
    MODEL_NAME = "Current Transformer"
    COMMAND_CLASS = CreateCurrentTransformerCommand
    ID_FIELD = "transformer_id"
    SYMBOL_ID = "current_transformer"


__all__ = ["CurrentTransformerTool"]
