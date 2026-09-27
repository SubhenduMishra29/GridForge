# ============================================================
# File: ui/tools/model_placement_tool.py
# GridForge V2 — Model Placement Tool
# Author: Subhendu Mishra
# ============================================================
"""Shared position-first placement behavior for concrete model tools."""

from __future__ import annotations

from typing import Any, Optional, Tuple
from uuid import uuid4

from .tool_base import ToolBase
from ui.canvas.symbol_preview_item import SymbolPreviewItem
from ui.creation.creation_context import CreationContext


class ModelPlacementTool(ToolBase):
    """Reusable UI-only placement interaction for concrete SLD model tools.

    Placement captures a canvas position and creates the immutable Application
    command. Electrical endpoint references are deliberately not acquired by
    this interaction; connectivity is a separate workflow.
    """

    MODEL_NAME = "Model"
    TOOL_ID = "model"
    SYMBOL_ID = ""
    COMMAND_CLASS = None
    ID_FIELD = "equipment_id"

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
        )
        self._position: Optional[Tuple[float, float]] = None
        self._preview_active = False
        self._preview_layer = preview_layer
        self._symbol_registry = symbol_registry
        self._creation_context: CreationContext | None = None

    def bind_creation_context(self, creation_context: CreationContext) -> None:
        if not isinstance(creation_context, CreationContext):
            raise TypeError("creation_context must be a CreationContext.")
        self._creation_context = creation_context

    def set_engineering_parameters(self, **parameters: Any) -> None:
        """Compatibility adapter into the canonical CreationDraft."""
        if not parameters:
            raise ValueError("Engineering parameters must not be empty.")
        self._require_creation_context().update_many(parameters)

    def _require_creation_context(self) -> CreationContext:
        if self._creation_context is None:
            raise RuntimeError("ModelPlacementTool is not bound to CreationContext.")
        return self._creation_context

    @property
    def tool_id(self) -> str:
        return self.TOOL_ID

    @property
    def name(self) -> str:
        return self.MODEL_NAME

    @property
    def description(self) -> str:
        return f"Place a {self.MODEL_NAME.lower()} on the SLD canvas."

    def on_activate(self) -> None:
        self._clear_state()

    def on_deactivate(self) -> None:
        self._clear_state()

    def on_mouse_press(self, event: Any) -> bool:
        self._ensure_active()
        position = self._snap_position(event)
        if position is None:
            return False
        self._position = position
        draft = self._require_creation_context().set_placement(position)
        self._preview_active = True
        self._show_preview(position)
        if not draft.validate_for_commit():
            return False
        command = self._build_command()
        self.execute_command(command)
        selector = getattr(self.selection_manager, "select_single", None)
        if callable(selector):
            selector(command.payload[self.ID_FIELD])
        self._require_creation_context().complete()
        self._clear_state()
        return True

    def on_mouse_move(self, event: Any) -> bool:
        self._ensure_active()
        position = self._snap_position(event)
        if position is None:
            return False
        self._position = position
        self._require_creation_context().set_placement(position)
        self._preview_active = True
        self._show_preview(position)
        return True

    def on_mouse_release(self, event: Any) -> bool:
        self._ensure_active()
        position = self._snap_position(event)
        if position is None:
            self._clear_state()
            return False
        self._position = position
        self._preview_active = True
        self._show_preview(position)
        return False

    def on_mouse_double_click(self, event: Any) -> bool:
        return self.on_mouse_press(event)

    def on_key_press(self, event: Any) -> bool:
        self._ensure_active()
        if self._is_escape_event(event):
            return self.on_cancel()
        return False

    def on_cancel(self) -> bool:
        self._ensure_active()
        had_state = self._preview_active or self._position is not None
        self._clear_state()
        return had_state

    def on_reset(self) -> None:
        self._ensure_active()
        self._clear_state()

    def _snap_result(self, event: Any) -> Any:
        scene_position = self.event_position(event)
        snap = getattr(self.get_snap_system(), "snap", None)
        if not callable(snap):
            raise TypeError("SnapSystem must provide snap().")
        result = snap(scene_position, allow_grid=True, allow_object=True)
        if getattr(result, "position", None) is None:
            return None
        return result

    def _snap_position(self, event: Any) -> Optional[Tuple[float, float]]:
        result = self._snap_result(event)
        position = getattr(result, "position", None) if result is not None else None
        if position is None:
            return None
        return self._position_tuple(position)

    def _show_preview(self, position: Tuple[float, float]) -> None:
        """Show a transient SymbolDefinition-driven equipment preview."""
        if self._preview_layer is None:
            return
        if self._symbol_registry is None:
            raise RuntimeError("Model placement requires the canonical SymbolRegistry for preview.")
        if not self.SYMBOL_ID:
            raise RuntimeError(f"{self.MODEL_NAME} has no canonical SYMBOL_ID.")
        definition = self._symbol_registry.require(self.SYMBOL_ID)
        item = SymbolPreviewItem(
            definition,
            position=position,
            rotation=0.0,
        )
        replace = getattr(self._preview_layer, "replace", None)
        if not callable(replace):
            raise TypeError("PreviewLayer must provide replace().")
        replace((item,))

    def _build_command(self) -> Any:
        command_class = self.COMMAND_CLASS
        if command_class is None:
            raise RuntimeError(f"{self.MODEL_NAME} tool has no Application command constructor.")
        draft = self._require_creation_context().require_draft()
        if not draft.validate_for_commit():
            raise RuntimeError(
                f"{self.MODEL_NAME} creation configuration is invalid: "
                + "; ".join(draft.validation_state.get("final", ()))
                + "; ".join(draft.validation_state.get("configuration", ()))
            )
        if self._position is None:
            raise RuntimeError(f"{self.MODEL_NAME} placement has no committed position.")
        payload = dict(draft.snapshot_values())
        payload[self.ID_FIELD] = f"{self.TOOL_ID}-{uuid4().hex}"
        payload["presentation_x"] = float(self._position[0])
        payload["presentation_y"] = float(self._position[1])
        return command_class(**payload)

    @staticmethod
    def _position_tuple(position: Any) -> Tuple[float, float]:
        if hasattr(position, "x") and hasattr(position, "y"):
            return float(position.x()), float(position.y())
        if isinstance(position, (tuple, list)) and len(position) >= 2:
            return float(position[0]), float(position[1])
        raise TypeError("SnapResult.position must provide x/y coordinates or a two-element position.")

    @staticmethod
    def _is_escape_event(event: Any) -> bool:
        if event is None:
            return False
        key = getattr(event, "key", None)
        if callable(key):
            key = key()
        if isinstance(event, dict):
            key = event.get("key", key)
        return key in ("Escape", "escape", 0x01000000)

    def _clear_state(self) -> None:
        self._position = None
        self._preview_active = False
        if self._preview_layer is not None:
            clear = getattr(self._preview_layer, "clear", None)
            if callable(clear):
                clear()

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state.update({
            "position": self._position,
            "preview_active": self._preview_active,
            "creation_active": self._creation_context is not None and self._creation_context.active,
        })
        return state


__all__ = ["ModelPlacementTool"]
