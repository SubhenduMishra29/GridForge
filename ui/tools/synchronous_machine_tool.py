# GridForge V2 — SLD synchronous-machine tool. Author: Subhendu Mishra
from core.application.commands.synchronous_machine_commands import CreateSynchronousMachineCommand
from .model_placement_tool import ModelPlacementTool
class SynchronousMachineTool(ModelPlacementTool):
    TOOL_ID="synchronous_machine"; MODEL_NAME="Synchronous Machine"; COMMAND_CLASS=CreateSynchronousMachineCommand
    ID_FIELD="synchronous_machine_id"; ENDPOINT_FIELDS=("endpoint",)
__all__=["SynchronousMachineTool"]
