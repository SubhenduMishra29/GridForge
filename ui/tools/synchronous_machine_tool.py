# GridForge V2 — SLD synchronous-machine tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class SynchronousMachineTool(ModelPlacementTool):
    TOOL_ID = "synchronous_machine"
    MODEL_NAME = "Synchronous Machine"

__all__ = ["SynchronousMachineTool"]
