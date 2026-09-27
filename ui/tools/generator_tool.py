# GridForge V2 — SLD generator tool. Author: Subhendu Mishra
from core.application.commands.model_commands import CreateGeneratorCommand
from .model_placement_tool import ModelPlacementTool
class GeneratorTool(ModelPlacementTool):
    SYMBOL_ID="generator"
__all__=["GeneratorTool"]
