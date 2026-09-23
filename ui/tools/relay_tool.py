# GridForge V2 — SLD relay tool. Author: Subhendu Mishra
from core.application.commands.relay_commands import CreateRelayCommand
from .model_placement_tool import ModelPlacementTool
class RelayTool(ModelPlacementTool):
    TOOL_ID="relay"; MODEL_NAME="Relay"; COMMAND_CLASS=CreateRelayCommand
    ID_FIELD="relay_id"; COMMAND_DEFAULTS={"relay_type":"overcurrent"}
__all__=["RelayTool"]
