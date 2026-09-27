# GridForge V2 — SLD capacitor tool. Author: Subhendu Mishra
from core.application.commands.capacitor_commands import CreateCapacitorCommand
from .model_placement_tool import ModelPlacementTool
class CapacitorTool(ModelPlacementTool):
    SYMBOL_ID="capacitor"
__all__=["CapacitorTool"]
