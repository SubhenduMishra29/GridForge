# ============================================================
# File: ui/tools/transformer_tool.py
# GridForge V2 — Transformer Placement Tool
# Author: Subhendu Mishra
# ============================================================
"""Position-first Transformer placement through the canonical creation contract."""

from .model_placement_tool import ModelPlacementTool


class TransformerTool(ModelPlacementTool):
    TOOL_ID = "transformer"
    MODEL_NAME = "Transformer"
    SYMBOL_ID = "transformer"


__all__ = ["TransformerTool"]
