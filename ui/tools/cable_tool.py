# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/tools/cable_tool.py
#
# Purpose:
#     SLD cable-placement interaction tool.
#
# Architectural Role:
#     CableTool captures placement intent only. Persistent Core
#     mutation must be performed by a confirmed Application command.
#
# Author:
#     Subhendu Mishra
# ============================================================

from __future__ import annotations

from typing import Any

from .transformer_tool import TransformerTool


class CableTool(TransformerTool):
    """SLD cable-placement scaffold using the established tool boundary."""

    TOOL_ID = "cable"

    @property
    def name(self) -> str:
        return "Cable"

    @property
    def description(self) -> str:
        return "Place a cable on the SLD canvas."

    @staticmethod
    def _require_transformer_command_boundary() -> None:
        raise RuntimeError(
            "Cable placement requires a confirmed Core cable-creation command. "
            "No CreateCable command is currently exposed by the GridForge Core API."
        )


__all__ = ["CableTool"]
