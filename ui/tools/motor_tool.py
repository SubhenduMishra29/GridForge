# GridForge V2 — SLD motor tool. Author: Subhendu Mishra
from core.application.commands.motor_commands import CreateMotorCommand
from .model_placement_tool import ModelPlacementTool
class MotorTool(ModelPlacementTool):
    TOOL_ID="motor"; MODEL_NAME="Motor"; COMMAND_CLASS=CreateMotorCommand
    ID_FIELD="motor_id"; ENDPOINT_FIELDS=("endpoint",)
__all__=["MotorTool"]
