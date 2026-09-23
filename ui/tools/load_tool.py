# GridForge V2 — SLD load tool. Author: Subhendu Mishra
from core.application.commands.model_commands import CreateLoadCommand
from .model_placement_tool import ModelPlacementTool
class LoadTool(ModelPlacementTool):
    TOOL_ID="load"; MODEL_NAME="Load"; COMMAND_CLASS=CreateLoadCommand
    ID_FIELD="load_id"; ENDPOINT_FIELDS=("endpoint",)
__all__=["LoadTool"]
