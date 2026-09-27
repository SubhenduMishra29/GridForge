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
from ui.creation.command_factory import CreationCommandFactory
from core.model import EndpointReference, EquipmentType


class ModelPlacementTool(ToolBase):
    """Reusable UI-only placement interaction for concrete SLD model tools.

    Placement captures a canvas position and creates the immutable Application
    command. Required endpoint/terminal acquisition is definition-driven and
    remains transient until the final Application command is prepared.
    """

    MODEL_NAME = "Model"
    TOOL_ID = "model"
    SYMBOL_ID = ""

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
        draft = self._require_creation_context().require_draft()
        snap = self._snap_result(event)
        if snap is None:
            return False

        # First interaction establishes the presentation placement.  Required
        # terminal/topology acquisition is then performed by subsequent
        # object-snap interactions against canonical terminal identities.
        if draft.placement_position is None:
            position = self._position_tuple(snap.position)
            self._position = position
            draft.set_placement(position)
            draft.mark_previewing()
            self._preview_active = True
            self._show_preview(position)
            if not draft.definition.terminal_requirements:
                return self._commit_if_valid()
            return True

        if not self._acquire_terminal(draft, snap):
            return False
        self._show_preview(self._position or draft.placement_position)
        return self._commit_if_valid()

    def _commit_if_valid(self) -> bool:
        draft = self._require_creation_context().require_draft()
        if not draft.validate_for_commit():
            return False
        intent = self._build_command()
        prepare = getattr(self.application, "prepare_creation_command", None)
        if not callable(prepare):
            raise RuntimeError("Application must provide prepare_creation_command().")
        command = prepare(intent)
        self.execute_command(command)
        selector = getattr(self.selection_manager, "select_single", None)
        if callable(selector):
            selector(command.payload[draft.definition.id_field])
        self._require_creation_context().complete()
        self._clear_state()
        return True

    def _acquire_terminal(self, draft: CreationDraft, snap: Any) -> bool:
        terminal_name = getattr(snap, "terminal_name", None)
        object_id = getattr(snap, "object_id", None)
        source = getattr(snap, "source", None)
        semantic_name = terminal_name
        if semantic_name is None and getattr(snap, "bus_id", None) is not None:
            # A bus snap is a valid electrical endpoint target for any
            # creation-contract terminal/topology semantic.
            pending = [
                item.terminal_name for item in draft.definition.terminal_requirements
                if draft.endpoints.get(item.terminal_name) is None
            ]
            semantic_name = pending[0] if pending else None
        if not semantic_name:
            return False
        requirements = {item.terminal_name: item for item in draft.definition.terminal_requirements}
        if semantic_name not in requirements or draft.endpoints.get(semantic_name) is not None:
            return False
        try:
            if getattr(snap, "bus_id", None) is not None:
                attachment_id = getattr(snap, "attachment_id", None)
                if not attachment_id:
                    return False
                endpoint = EndpointReference.bus(str(snap.bus_id), str(attachment_id))
            else:
                element_type = getattr(source, "element_type", None)
                if not element_type or not object_id or not terminal_name:
                    return False
                endpoint = EndpointReference.terminal(
                    equipment_type=EquipmentType(str(element_type).strip().lower()),
                    equipment_id=str(object_id),
                    terminal_role=str(terminal_name),
                )
        except (TypeError, ValueError):
            return False
        draft.set_endpoint(semantic_name, endpoint)
        return True

    def on_mouse_move(self, event: Any) -> bool:
        self._ensure_active()
        draft = self._require_creation_context().require_draft()
        if draft.placement_position is not None:
            self._preview_active = True
            self._show_preview(self._position or draft.placement_position)
            return True
        position = self._snap_position(event)
        if position is None:
            return False
        self._position = position
        draft.set_placement(position)
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
        draft = self._require_creation_context().require_draft()
        item = SymbolPreviewItem(
            definition,
            position=position,
            rotation=draft.orientation,
            presentation_state=draft.preview_state,
        )
        replace = getattr(self._preview_layer, "replace", None)
        if not callable(replace):
            raise TypeError("PreviewLayer must provide replace().")
        replace((item,))

    def _build_command(self) -> Any:
        draft = self._require_creation_context().require_draft()
        if self._position is None:
            raise RuntimeError(f"{self.MODEL_NAME} placement has no committed position.")
        draft.mark_committing()
        return CreationCommandFactory.build(
            draft,
            object_id=f"{draft.definition.tool_id}-{uuid4().hex}",
            position=self._position,
        )

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
