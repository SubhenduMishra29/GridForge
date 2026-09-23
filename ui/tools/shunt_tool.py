# GridForge V2 — SLD shunt tool. Author: Subhendu Mishra
from core.application.commands.model_commands import CreateShuntCommand
from .model_placement_tool import ModelPlacementTool
class ShuntTool(ModelPlacementTool):
    TOOL_ID="shunt"; MODEL_NAME="Shunt"; COMMAND_CLASS=CreateShuntCommand
    ID_FIELD="shunt_id"; ENDPOINT_FIELDS=("endpoint",)
__all__=["ShuntTool"]
