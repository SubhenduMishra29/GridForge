# GridForge V2 — SLD current-transformer tool. Author: Subhendu Mishra
from core.application.commands.measurement_commands import CreateCurrentTransformerCommand
from .model_placement_tool import ModelPlacementTool
class CurrentTransformerTool(ModelPlacementTool):
    TOOL_ID="current_transformer"; MODEL_NAME="Current Transformer"; COMMAND_CLASS=CreateCurrentTransformerCommand
    ID_FIELD="transformer_id"; ENDPOINT_FIELDS=("p1_endpoint","p2_endpoint","s1_endpoint","s2_endpoint")
    ENDPOINT_ROLE_MAP={"P1":"p1_endpoint","P2":"p2_endpoint","S1":"s1_endpoint","S2":"s2_endpoint"}
__all__=["CurrentTransformerTool"]
