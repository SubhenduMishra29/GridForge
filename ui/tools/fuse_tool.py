# GridForge V2 — SLD fuse tool. Author: Subhendu Mishra
from core.application.commands.model_commands import CreateFuseCommand
from .model_placement_tool import ModelPlacementTool
class FuseTool(ModelPlacementTool):
    TOOL_ID="fuse"; MODEL_NAME="Fuse"; COMMAND_CLASS=CreateFuseCommand
    ID_FIELD="fuse_id"; ENDPOINT_FIELDS=("endpoint_from","endpoint_to")
__all__=["FuseTool"]
