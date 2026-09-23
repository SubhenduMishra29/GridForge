# GridForge V2 — SLD CVT tool. Author: Subhendu Mishra
from core.application.commands.measurement_commands import CreateCapacitiveVoltageTransformerCommand
from .model_placement_tool import ModelPlacementTool
class CVTTool(ModelPlacementTool):
    TOOL_ID="cvt"; MODEL_NAME="CVT"; COMMAND_CLASS=CreateCapacitiveVoltageTransformerCommand
    ID_FIELD="transformer_id"; ENDPOINT_FIELDS=("h1_endpoint","h2_endpoint","x1_endpoint","x2_endpoint")
    ENDPOINT_ROLE_MAP={"H1":"h1_endpoint","H2":"h2_endpoint","X1":"x1_endpoint","X2":"x2_endpoint"}
__all__=["CVTTool"]
