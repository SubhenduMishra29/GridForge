# GridForge V2 — SLD relay tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class RelayTool(ModelPlacementTool):
    TOOL_ID = "relay"
    MODEL_NAME = "Relay"

__all__ = ["RelayTool"]
