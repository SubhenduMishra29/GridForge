# GridForge V2 — SLD disconnector tool. Author: Subhendu Mishra
from core.application.commands.model_commands import CreateDisconnectorCommand
from .model_placement_tool import ModelPlacementTool
class DisconnectorTool(ModelPlacementTool):
    TOOL_ID="disconnector"; MODEL_NAME="Disconnector"; COMMAND_CLASS=CreateDisconnectorCommand
    ID_FIELD="disconnector_id"; ENDPOINT_FIELDS=("endpoint_from","endpoint_to")
    COMMAND_DEFAULTS={"voltage_kv":1.0,"rated_current_a":1.0}
__all__=["DisconnectorTool"]
