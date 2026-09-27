# ============================================================
# File: ui/tools/synchronous_machine_tool.py
# GridForge V2 — SLD Synchronous Machine Tool
# Author: Subhendu Mishra
# ============================================================

from core.application.commands.synchronous_machine_commands import CreateSynchronousMachineCommand

from .model_placement_tool import ModelPlacementTool


class SynchronousMachineTool(ModelPlacementTool):
    """SLD placement tool for Synchronous Machine equipment."""

    TOOL_ID = "synchronous_machine"
    MODEL_NAME = "Synchronous Machine"
    SYMBOL_ID = "synchronous_machine"


__all__ = ["SynchronousMachineTool"]
