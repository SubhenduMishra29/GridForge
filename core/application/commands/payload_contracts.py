"""Backward-compatible command imports.

Command payload contracts are canonical in ``model_commands``. This module is
kept only for callers that imported the corrected contract names from the
former compatibility location; it performs no monkey-patching and owns no
independent command definitions.
"""

from .model_commands import (
    CreateCableCommand,
    CreateDisconnectorCommand,
    CreateSwitchCommand,
    UpdateCableCommand,
    UpdateDisconnectorCommand,
    UpdateGeneratorCommand,
    UpdateShuntCommand,
    UpdateSwitchCommand,
)

__all__ = [
    "CreateCableCommand",
    "UpdateCableCommand",
    "CreateSwitchCommand",
    "UpdateSwitchCommand",
    "CreateDisconnectorCommand",
    "UpdateDisconnectorCommand",
    "UpdateGeneratorCommand",
    "UpdateShuntCommand",
]
