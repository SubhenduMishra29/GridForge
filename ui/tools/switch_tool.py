# GridForge V2 — SLD switch tool. Author: Subhendu Mishra
from core.application.commands.model_commands import CreateSwitchCommand
from .model_placement_tool import ModelPlacementTool
class SwitchTool(ModelPlacementTool):
    TOOL_ID="switch"; MODEL_NAME="Switch"; COMMAND_CLASS=CreateSwitchCommand
    ID_FIELD="switch_id"; SYMBOL_ID="switch"
__all__=["SwitchTool"]
