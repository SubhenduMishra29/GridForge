# GridForge V2 — SLD battery tool. Author: Subhendu Mishra
from core.application.commands.battery_commands import CreateBatteryCommand
from .model_placement_tool import ModelPlacementTool
class BatteryTool(ModelPlacementTool):
    TOOL_ID="battery"; MODEL_NAME="Battery"; COMMAND_CLASS=CreateBatteryCommand
    ID_FIELD="battery_id"; ENDPOINT_FIELDS=("endpoint",)
__all__=["BatteryTool"]
