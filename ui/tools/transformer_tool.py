# ============================================================
# File: ui/tools/transformer_tool.py
# GridForge V2 — Transformer Placement Tool
# Author: Subhendu Mishra
# ============================================================
"""SLD transformer placement as a position-first equipment workflow."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from core.application.commands.model_commands import CreateTransformerCommand
from core.model.transformer import ImpedanceBasis

from .model_placement_tool import ModelPlacementTool


class TransformerTool(ModelPlacementTool):
    """Place a Transformer first; establish electrical connectivity separately.

    Transformer impedance reference data remains explicit engineering input.
    Endpoint references are intentionally absent from the placement interaction
    and may be supplied later by the dedicated connection workflow.
    """

    TOOL_ID = "transformer"
    MODEL_NAME = "Transformer"
    SYMBOL_ID = "transformer"
    COMMAND_CLASS = CreateTransformerCommand
    ID_FIELD = "transformer_id"

    def __init__(
        self,
        controller: Any,
        application: Any,
        selection_manager: Any,
        snap_system: Any,
        preview_layer: Any = None,
        symbol_registry: Any = None,
    ) -> None:
        super().__init__(
            controller=controller,
            application=application,
            selection_manager=selection_manager,
            snap_system=snap_system,
            preview_layer=preview_layer,
            symbol_registry=symbol_registry,
        )
        self._engineering_parameters: dict[str, Any] = {}

    def set_engineering_parameters(self, **parameters: Any) -> None:
        """Store explicit Transformer engineering input and complete a pending placement."""
        if not parameters:
            raise ValueError("Transformer engineering parameters must not be empty.")
        self._engineering_parameters = dict(parameters)
        if self._position is not None and self._has_complete_engineering_parameters():
            self.execute_command(self._build_command())
            self._clear_state()

    def on_mouse_press(self, event: Any) -> bool:
        """Capture placement even when engineering input is configured afterward."""
        self._ensure_active()
        position = self._snap_position(event)
        if position is None:
            return False
        self._position = position
        self._preview_active = True
        self._show_preview(position)
        if self._has_complete_engineering_parameters():
            self.execute_command(self._build_command())
            self._clear_state()
        return True

    def _has_complete_engineering_parameters(self) -> bool:
        parameters = self._engineering_parameters
        required = ("r", "x", "impedance_basis", "impedance_base_voltage_kv")
        if any(name not in parameters or parameters[name] is None for name in required):
            return False
        return (
            parameters.get("impedance_base_mva") is not None
            or parameters.get("rate_mva") is not None
        )

    def _build_command(self) -> Any:
        """Build a position-first Transformer command with explicit engineering basis."""
        parameters = self._engineering_parameters
        required = (
            "r",
            "x",
            "impedance_basis",
            "impedance_base_voltage_kv",
        )
        missing = [name for name in required if name not in parameters]
        if missing:
            raise RuntimeError(
                "Transformer engineering parameters are incomplete: "
                + ", ".join(missing)
            )

        if (
            parameters.get("impedance_base_mva") is None
            and parameters.get("rate_mva") is None
        ):
            raise RuntimeError(
                "Transformer engineering parameters require an explicit "
                "impedance_base_mva or rate_mva."
            )

        if self._position is None:
            raise RuntimeError("Transformer placement has no committed position.")

        return CreateTransformerCommand(
            transformer_id=f"{self.TOOL_ID}-{uuid4().hex}",
            presentation_x=float(self._position[0]),
            presentation_y=float(self._position[1]),
            endpoint_from=None,
            endpoint_to=None,
            r=float(parameters["r"]),
            x=float(parameters["x"]),
            b=float(parameters.get("b", 0.0)),
            impedance_basis=self._normalize_impedance_basis(
                parameters["impedance_basis"]
            ),
            impedance_base_mva=(
                None
                if parameters.get("impedance_base_mva") is None
                else float(parameters["impedance_base_mva"])
            ),
            impedance_base_voltage_kv=float(
                parameters["impedance_base_voltage_kv"]
            ),
            tap=float(parameters.get("tap", 1.0)),
            shift=float(parameters.get("shift", 0.0)),
            name=str(parameters.get("name", "")),
            rate_mva=(
                None
                if parameters.get("rate_mva") is None
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
