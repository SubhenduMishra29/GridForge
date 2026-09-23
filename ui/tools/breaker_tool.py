# GridForge V2 — SLD breaker tool. Author: Subhendu Mishra
from core.application.commands.breaker_commands import CreateBreakerCommand
from .model_placement_tool import ModelPlacementTool
class BreakerTool(ModelPlacementTool):
    TOOL_ID="breaker"; MODEL_NAME="Breaker"; COMMAND_CLASS=CreateBreakerCommand
    ID_FIELD="breaker_id"; ENDPOINT_FIELDS=("endpoint_from","endpoint_to")
__all__=["BreakerTool"]
