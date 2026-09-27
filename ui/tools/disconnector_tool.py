# GridForge V2 — SLD disconnector tool. Author: Subhendu Mishra
from core.application.commands.model_commands import CreateDisconnectorCommand
from .model_placement_tool import ModelPlacementTool
class DisconnectorTool(ModelPlacementTool):
    TOOL_ID="disconnector"; MODEL_NAME="Disconnector"; COMMAND_CLASS=CreateDisconnectorCommand
    ID_FIELD="disconnector_id"; SYMBOL_ID="disconnector"
    
__all__=["DisconnectorTool"]
