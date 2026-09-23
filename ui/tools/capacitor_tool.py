# GridForge V2 — SLD capacitor tool. Author: Subhendu Mishra
from core.application.commands.capacitor_commands import CreateCapacitorCommand
from .model_placement_tool import ModelPlacementTool
class CapacitorTool(ModelPlacementTool):
    TOOL_ID="capacitor"; MODEL_NAME="Capacitor"; COMMAND_CLASS=CreateCapacitorCommand
    ID_FIELD="capacitor_id"; ENDPOINT_FIELDS=("endpoint",)
__all__=["CapacitorTool"]
