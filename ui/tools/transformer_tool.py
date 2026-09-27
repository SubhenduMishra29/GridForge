# ============================================================
# File: ui/tools/transformer_tool.py
# GridForge V2 — Transformer Placement Tool
# Author: Subhendu Mishra
# ============================================================
"""SLD transformer placement using the canonical CreationDraft."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from core.application.commands.model_commands import CreateTransformerCommand
from core.model.transformer import ImpedanceBasis

from .model_placement_tool import ModelPlacementTool


class TransformerTool(ModelPlacementTool):
    """Position-first transformer placement with explicit engineering input."""

    TOOL_ID = "transformer"
    MODEL_NAME = "Transformer"
    SYMBOL_ID = "transformer"
    COMMAND_CLASS = CreateTransformerCommand
    ID_FIELD = "transformer_id"

    def _build_command(self) -> Any:
        draft = self._require_creation_context().require_draft()
        if not draft.validate_for_commit():
            raise RuntimeError(
                "Transformer creation draft is invalid: "
                + "; ".join(draft.validation_state.get("configuration", ()))
            )
        if self._position is None:
            raise RuntimeError("Transformer placement has no committed position.")
        parameters = draft.snapshot_values()
        return CreateTransformerCommand(
            transformer_id=f"{self.TOOL_ID}-{uuid4().hex}",
            presentation_x=float(self._position[0]),
            presentation_y=float(self._position[1]),
            endpoint_from=None,
            endpoint_to=None,
            r=float(parameters["r"]),
            x=float(parameters["x"]),
            b=float(parameters.get("b", 0.0)),
            impedance_basis=self._normalize_impedance_basis(parameters["impedance_basis"]),
            impedance_base_mva=(
                None if parameters.get("impedance_base_mva") is None
                else float(parameters["impedance_base_mva"])
            ),
            impedance_base_voltage_kv=float(parameters["impedance_base_voltage_kv"]),
            tap=float(parameters.get("tap", 1.0)),
            shift=float(parameters.get("shift", 0.0)),
            name=str(parameters.get("name", "")),
            rate_mva=(
                None if parameters.get("rate_mva") is None
                else float(parameters["rate_mva"])
            ),
        )

    @staticmethod
    def _normalize_impedance_basis(value: Any) -> ImpedanceBasis:
        if isinstance(value, ImpedanceBasis):
            return value
        try:
            return ImpedanceBasis(str(value).strip().lower())
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Transformer impedance_basis must be 'pu' or 'engineering'."
            ) from exc


__all__ = ["TransformerTool"]
