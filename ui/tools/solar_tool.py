# GridForge V2 — SLD solar tool. Author: Subhendu Mishra
from core.application.commands.solar_commands import CreateSolarCommand
from .model_placement_tool import ModelPlacementTool
class SolarTool(ModelPlacementTool):
    TOOL_ID="solar"; MODEL_NAME="Solar"; COMMAND_CLASS=CreateSolarCommand
    ID_FIELD="solar_id"; ENDPOINT_FIELDS=("endpoint",)
__all__=["SolarTool"]
