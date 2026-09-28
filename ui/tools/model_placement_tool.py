# ============================================================
# File: ui/tools/model_placement_tool.py
# GridForge V2 — Model Placement Tool
# Author: Subhendu Mishra
# ============================================================
"""Shared position-first placement behavior for concrete model tools."""

from __future__ import annotations

from typing import Any, Optional, Tuple
from uuid import uuid4

from core.application.commands.draft_commands import AddDraftEquipmentCommand, UpdateDraftEquipmentCommand
from core.application.draft import DraftEndpoint
from .tool_base import ToolBase
from ui.canvas.symbol_preview_item import SymbolPreviewItem
from ui.creation.creation_context import CreationContext
from ui.creation.command_factory import CreationCommandFactory
from ui.tools.endpoint_identity_adapter import EndpointIdentityAdapter


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
        self._endpoint_acquired_this_interaction = False
        self._accepted_endpoint_snap: Any | None = None
        self._active_draft_id: str | None = None

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
        self._active_draft_id = None
        self._clear_state()

    def on_deactivate(self) -> None:
        self._clear_state()

    def on_mouse_press(self, event: Any) -> bool:
        self._ensure_active()
        draft = self._require_creation_context().require_draft()
        if draft.placement_position is None:
            snap = self._snap_result(event)
        else:
            if not draft.configuration_complete:
                self._report_feedback("Required engineering parameter missing.")
                return False
            # A physical terminal does not imply that an initial target
            # endpoint must be acquired. Only an explicitly required
            # creation role enters endpoint snapping/progression.
            if self._pending_creation_role(draft) is None:
                return False
            snap = self._snap_endpoint_result(event)
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
            self._persist_new_draft(draft)
            self._preview_active = True
            self._endpoint_acquired_this_interaction = False
            self._show_preview(position)
            return True

        if not self._acquire_terminal(draft, snap):
            return False
        self._show_preview(self._position or draft.placement_position)
        return True

    def commit_creation(self) -> bool:
        """Commit the active CreationDraft through the canonical Application boundary."""
        self._ensure_active()
        draft = self._require_creation_context().require_draft()
        if not draft.validate_for_commit():
            self._report_feedback("Draft configuration, placement, or endpoint validation failed.")
            return False
        command = self._build_command()
        result = self.execute_command(command)
        if not result.success:
            self._report_feedback(result.message)
            return False
        self._require_creation_context().complete()
        self._clear_state()
        self._active_draft_id = None
        self._report_feedback(f"{draft.equipment_type} committed.")
        return True

    def _commit_if_valid(self) -> bool:
        return self.commit_creation()

    def _draft_network(self) -> Any:
        draft_network = getattr(self.application, "draft_network", None)
        if draft_network is None:
            raise RuntimeError("Application DraftNetwork is not configured.")
        return draft_network

    def _persist_new_draft(self, draft: Any) -> None:
        if self._active_draft_id is not None:
            return
        self._active_draft_id = f"draft-{draft.definition.tool_id}-{uuid4().hex}"
        item = {
            "draft_id": self._active_draft_id,
            "equipment_type": draft.equipment_type,
            "display_name": draft.equipment_type,
            "terminal_contract": tuple(r.terminal_name for r in draft.definition.terminal_requirements),
            "engineering_data": dict(draft.values),
            "endpoints": {},
            "placement": tuple(draft.placement_position or (0.0, 0.0)),
            "presentation": {},
            "validation_state": dict(draft.validation_state),
            "command_type": draft.definition.command_type,
            "id_field": draft.definition.id_field,
            "parameter_mapping": dict(draft.definition.parameter_mapping),
            "endpoint_mapping": dict(draft.definition.endpoint_mapping),
        }
        self.execute_command(AddDraftEquipmentCommand(equipment=item))
        sld = getattr(self.application, "sld_service", None)
        if sld is not None:
            from core.application.commands.sld_commands import AddSLDNodeCommand
            self.execute_command(AddSLDNodeCommand(
                node_id=f"sld-draft-{self._active_draft_id}", equipment_id=None,
                x=float(item["placement"][0]), y=float(item["placement"][1]),
                presentation_owner="engineer", element_type=draft.equipment_type,
                presentation_properties={"draft_id": self._active_draft_id, "lifecycle_state": "DRAFT"},
            ))

    def persist_transient_draft(self) -> None:
        if self._active_draft_id is None or self._creation_context is None or self._creation_context.draft is None:
            return
        draft = self._creation_context.draft
        self.execute_command(UpdateDraftEquipmentCommand(
            draft_id=self._active_draft_id,
            changes={"engineering_data": dict(draft.values), "placement": draft.placement_position,
                     "validation_state": dict(draft.validation_state)},
        ))

    def persist_transient_draft_endpoint(self, endpoint: DraftEndpoint, role: str) -> None:
        if self._active_draft_id is None:
            return
        self.execute_command(UpdateDraftEquipmentCommand(
            draft_id=self._active_draft_id, changes={"endpoints": {role: endpoint}},
        ))

    @staticmethod
    def _pending_creation_role(draft: CreationDraft) -> str | None:
        """Return the first missing explicitly required initial endpoint role."""
        for requirement in draft.definition.topology_requirements:
            if requirement.required and draft.endpoints.get(requirement.name) is None:
                return requirement.name
        for requirement in draft.definition.terminal_requirements:
            if requirement.initial_endpoint_required and draft.endpoints.get(requirement.terminal_name) is None:
                return requirement.terminal_name
        return None

    def _acquire_terminal(self, draft: CreationDraft, snap: Any) -> bool:
        pending_role = self._pending_creation_role(draft)
        if pending_role is None:
            return False
        endpoint = self._draft_endpoint_from_snap(snap)
        if endpoint is None:
            self._report_feedback("Draft equipment can only connect to another draft endpoint.")
            return False
        draft.set_endpoint(pending_role, endpoint)
        self._accepted_endpoint_snap = snap
        self._endpoint_acquired_this_interaction = True
        self.persist_transient_draft_endpoint(endpoint, pending_role)
        return True

    @staticmethod
    def _draft_endpoint_from_snap(snap: Any) -> DraftEndpoint | None:
        source = getattr(snap, "source", None)
        draft_id = getattr(snap, "draft_id", None) or getattr(source, "draft_id", None)
        properties = getattr(source, "properties", None)
        if draft_id is None and isinstance(properties, dict):
            draft_id = properties.get("draft_id")
        role = getattr(snap, "terminal_name", None)
        if not isinstance(draft_id, str) or not draft_id or not isinstance(role, str) or not role:
            return None
        equipment = getattr(source, "equipment", None)
        equipment_type = getattr(equipment, "equipment_type", None)
        return DraftEndpoint(draft_id=draft_id, terminal_role=role, endpoint_kind=str(equipment_type or "terminal").lower())

    def _report_feedback(self, message: str) -> None:
        """Use an existing presentation feedback hook when the composition provides one."""
        for name in ("show_status_message", "set_status_message", "notify_user"):
            callback = getattr(self.controller, name, None)
            if callable(callback):
                callback(message)
                return

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
        self._preview_active = True
        self._show_preview(position)
        return True

    def on_mouse_release(self, event: Any) -> bool:
        self._ensure_active()
        draft = self._require_creation_context().require_draft()

        # Endpoint acquisition is press-authoritative: release must not
        # perform a second snap that can replace the accepted target.
        if self._endpoint_acquired_this_interaction and self._accepted_endpoint_snap is not None:
            self._show_preview(self._position or draft.placement_position)
            self._endpoint_acquired_this_interaction = False
            self._accepted_endpoint_snap = None
            pending_role = self._pending_creation_role(draft)
            if pending_role is not None:
                self._report_feedback(f"Another endpoint is still required: {pending_role}.")
                return False
            return self._commit_if_valid()

        position = self._snap_position(event)
        if position is None:
            return False
        if draft.placement_position is None:
            self._position = position
            draft.set_placement(position)
            self._preview_active = True
            self._show_preview(position)
            return False
        pending_role = self._pending_creation_role(draft)
        if pending_role is None:
            self._position = draft.placement_position
            self._show_preview(self._position)
            return self._commit_if_valid()
        self._report_feedback(f"Another endpoint is still required: {pending_role}.")
        self._show_preview(self._position or draft.placement_position)
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
        self.persist_transient_draft()
        self._clear_state()
        self._active_draft_id = None
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

    def _snap_endpoint_result(self, event: Any) -> Any:
        scene_position = self.event_position(event)
        snap_endpoint = getattr(self.get_snap_system(), "snap_endpoint", None)
        if not callable(snap_endpoint):
            raise TypeError("SnapSystem must provide snap_endpoint().")
        result = snap_endpoint(scene_position)
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
        if draft.placement_position is None:
            raise RuntimeError(f"{self.MODEL_NAME} placement has no committed position.")
        draft.mark_committing()
        return self.application.prepare_creation_command(
            CreationCommandFactory.build(
                draft,
                object_id=f"{draft.definition.tool_id}-{uuid4().hex}",
            )
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
        self._endpoint_acquired_this_interaction = False
        self._accepted_endpoint_snap = None
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
            "placement_phase": (
                self._creation_context.draft.phase.value
                if self._creation_context is not None and self._creation_context.draft is not None
                else "INACTIVE"
            ),
            "required_endpoints": (
                tuple(item.terminal_name for item in self._creation_context.draft.definition.terminal_requirements
                      if self._creation_context.draft.endpoints.get(item.terminal_name) is None)
                if self._creation_context is not None and self._creation_context.draft is not None
                else ()
            ),
        })
        return state


__all__ = ["ModelPlacementTool"]