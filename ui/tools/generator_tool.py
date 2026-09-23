# GridForge V2 — SLD generator tool. Author: Subhendu Mishra
from core.application.commands.model_commands import CreateGeneratorCommand
from .model_placement_tool import ModelPlacementTool
class GeneratorTool(ModelPlacementTool):
    TOOL_ID="generator"; MODEL_NAME="Generator"; COMMAND_CLASS=CreateGeneratorCommand
    ID_FIELD="generator_id"; ENDPOINT_FIELDS=("endpoint",)
__all__=["GeneratorTool"]
