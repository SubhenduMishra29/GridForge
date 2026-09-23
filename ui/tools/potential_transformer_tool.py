# GridForge V2 — SLD potential-transformer tool. Author: Subhendu Mishra
from core.application.commands.pt_commands import CreatePTCommand
from .model_placement_tool import ModelPlacementTool
class PotentialTransformerTool(ModelPlacementTool):
    TOOL_ID="potential_transformer"; MODEL_NAME="Potential Transformer"; COMMAND_CLASS=CreatePTCommand
    ID_FIELD="pt_id"; ENDPOINT_FIELDS=("primary_a","primary_b","secondary_a","secondary_b")
__all__=["PotentialTransformerTool"]
