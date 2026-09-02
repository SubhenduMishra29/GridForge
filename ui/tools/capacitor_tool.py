# GridForge V2 — SLD capacitor tool. Author: Subhendu Mishra
from .model_placement_tool import ModelPlacementTool

class CapacitorTool(ModelPlacementTool):
    TOOL_ID = "capacitor"
    MODEL_NAME = "Capacitor"

__all__ = ["CapacitorTool"]
