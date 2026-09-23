# GridForge V2 — SLD grid tool. Author: Subhendu Mishra
from core.application.commands.model_commands import CreateGridCommand
from .model_placement_tool import ModelPlacementTool
class GridTool(ModelPlacementTool):
    TOOL_ID="grid"; MODEL_NAME="Grid"; COMMAND_CLASS=CreateGridCommand
    ID_FIELD="grid_id"; ENDPOINT_FIELDS=("endpoint",)
__all__=["GridTool"]
