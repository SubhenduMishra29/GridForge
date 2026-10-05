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
from ui.creation.creation_context import CreationContext, CreationDraft
from core.application.commands.draft_commands import AddDraftEquipmentCommand
from .endpoint_identity_adapter import EndpointIdentityAdapter


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
            if self._active_draft_id is None:
                self._active_draft_id = f"{draft.definition.tool_id}-draft-{uuid4().hex}"
            position = self._position_tuple(snap.position)
            self._position = position
            draft.set_placement(position)
            draft.mark_previewing()
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
        equipment_type = draft.equipment_type
        equipment_id = self._active_draft_id or f"{draft.definition.tool_id}-draft-{uuid4().hex}"
        if not draft.validate_for_commit():
            self._report_feedback(
                f"CREATION_INTENT_FAILED: {equipment_type} validation failed: "
                + "; ".join(draft.validation_state.get("final", ()))
            )
            return False
        try:
            draft.mark_committing()
            equipment = {
                "draft_id": equipment_id,
                "equipment_type": equipment_type,
                "display_name": draft.definition.equipment_type,
                "terminal_contract": tuple(item.terminal_name for item in draft.definition.terminal_requirements),
                "engineering_data": dict(draft.snapshot_values()),
                # Preserve every explicitly acquired creation endpoint using
                # the canonical persisted DraftEndpointReference. The UI
                # endpoint object itself never becomes draft/Core identity.
                "endpoints": {
                    str(role): self._to_draft_endpoint_reference(
                        endpoint,
                        draft_id=equipment_id,
                        equipment_type=equipment_type,
                        terminal_role=str(role),
                    ).to_dict()
                    for role, endpoint in draft.snapshot_endpoints().items()
                },
                "placement": draft.placement_position,
                "presentation": dict(draft.preview_state),
                "validation_state": dict(draft.validation_state),
                "command_type": draft.definition.command_type,
                "id_field": draft.definition.id_field,
                "parameter_mapping": dict(draft.definition.parameter_mapping),
                "endpoint_mapping": dict(draft.definition.endpoint_mapping),
            }
            command = AddDraftEquipmentCommand(equipment=equipment)
            result = self.execute_command(command)
        except Exception as exc:
            self._report_feedback(f"DRAFT_COMMAND_FAILED: equipment={equipment_type} id={equipment_id} message={exc}")
            return False
        if not getattr(result, "success", False):
            self._report_feedback(f"DRAFT_COMMAND_FAILED: equipment={equipment_type} id={equipment_id} message={result.message}")
            return False
        # The Application commit is the semantic source of truth. The SLD
        # projection/render pipeline creates the canonical permanent graphics
        # item and owns its snap registration. Never promote the transient
        # SymbolPreviewItem into a committed presentation.
        self._require_creation_context().complete()
        self._clear_state()
        selector = getattr(self.selection_manager, "select_single", None)
        if callable(selector):
            selector(equipment_id)
        self._report_feedback(f"{equipment_type} committed.")
        return True
    @staticmethod
    def _to_draft_endpoint_reference(
        endpoint: Any,
        *,
        draft_id: str,
        equipment_type: str,
        terminal_role: str,
    ):
        """Persist only canonical DraftEndpointReference values."""
        from core.application.draft.network import DraftEndpointReference
        from core.model import EndpointReference

        if isinstance(endpoint, DraftEndpointReference):
            return endpoint
        if not isinstance(endpoint, EndpointReference):
            raise TypeError(
                f"Creation endpoint for {terminal_role!r} must be an EndpointReference."
            )
        if endpoint.is_bus:
            return DraftEndpointReference.bus(
                bus_id=str(endpoint.object_id),
                attachment_id=str(endpoint.attachment_id),
            )
        # A terminal endpoint acquired during creation identifies the external
        # Core endpoint; it must not be rewritten as the placed equipment's
        # own terminal identity.
        return DraftEndpointReference.terminal(
            draft_id=str(endpoint.object_id),
            equipment_type=str(endpoint.equipment_type.value),
            terminal_role=str(endpoint.terminal_role),
            scope="core",
        )

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
        try:
            endpoint = EndpointIdentityAdapter.from_snap_result(snap)
        except (TypeError, ValueError) as exc:
            self._report_feedback(f"CREATION_INTENT_FAILED: {exc}")
            return False
        draft.set_endpoint(pending_role, endpoint)
        self._accepted_endpoint_snap = snap
        self._endpoint_acquired_this_interaction = True
        return True

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
            return self.commit_creation()

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
            return self.commit_creation()
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
        result = snap(scene_position, allow_grid=True, allow_object=True, intent="PLACE")
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
            terminal_names=tuple(item.terminal_name for item in draft.definition.terminal_requirements),
            element_type=draft.equipment_type,
        )
        replace = getattr(self._preview_layer, "replace", None)
        if not callable(replace):
            raise TypeError("PreviewLayer must provide replace().")
        replace((item,))

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
        self._active_draft_id = None
        if self._preview_layer is not None:
            clear_preview = getattr(self._preview_layer, "clear_preview", None)
            if callable(clear_preview):
                clear_preview()
            else:
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