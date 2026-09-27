# GridForge V2 — SLD shunt tool. Author: Subhendu Mishra
from core.application.commands.model_commands import CreateShuntCommand
from .model_placement_tool import ModelPlacementTool
class ShuntTool(ModelPlacementTool):
    SYMBOL_ID="shunt"
__all__=["ShuntTool"]
