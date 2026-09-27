# GridForge V2 — SLD load tool. Author: Subhendu Mishra
from core.application.commands.model_commands import CreateLoadCommand
from .model_placement_tool import ModelPlacementTool
class LoadTool(ModelPlacementTool):
    SYMBOL_ID="load"
__all__=["LoadTool"]
