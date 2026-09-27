# GridForge V2 — SLD reactor tool. Author: Subhendu Mishra
from core.application.commands.reactor_commands import CreateReactorCommand
from .model_placement_tool import ModelPlacementTool
class ReactorTool(ModelPlacementTool):
    TOOL_ID="reactor"; MODEL_NAME="Reactor"; COMMAND_CLASS=CreateReactorCommand
    ID_FIELD="reactor_id"
    SYMBOL_ID="reactor"
__all__=["ReactorTool"]
