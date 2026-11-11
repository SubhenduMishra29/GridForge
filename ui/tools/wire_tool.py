# ============================================================
# File: ui/tools/wire_tool.py
# GridForge V2 — Simple Wired Connection Tool
# Author: Subhendu Mishra
# ============================================================
"""Create a logical endpoint-to-endpoint connection without Line/Cable semantics."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from core.application.commands.simple_wire_commands import CreateSimpleWireConnectionCommand
from core.application.commands.draft_commands import CreateDraftConnectionCommand
from core.application.draft.network import DraftEndpointReference

from ui.connections.connection_preview import ConnectionPreview
from ui.core.qt import QPointF

from .endpoint_identity_adapter import EndpointIdentityAdapter
from ui.core.snap_system import SnapIntent, SnapType
from .tool_base import ToolBase


class WireTool(ToolBase):
    """Capture two valid electrical endpoints and submit one canonical connection command."""

    TOOL_ID = "wire"

    def __init__(self, controller: Any, application: Any, selection_manager: Any, snap_system: Any, preview_layer: Any = None) -> None:
        super().__init__(controller=controller, application=application, selection_manager=selection_manager, snap_system=snap_system)
        self._start_position: Optional[Tuple[float, float]] = None
        self._start_snap: Any = None
        self._current_position: Optional[Tuple[float, float]] = None
        self._last_snap_result: Any = None
        self._last_command_result: Any = None
        self._failure_reason = ""
        self._preview = ConnectionPreview()
        self._preview_layer = preview_layer or getattr(controller, "preview_layer", None)
        self._preview_owner = f"wire-tool:{id(self)}"
        self._wire_layer_id: str | None = None

    @property
    def tool_id(self) -> str:
        return self.TOOL_ID

    @property
    def has_source_endpoint(self) -> bool:
        """Return whether the first electrical endpoint has been acquired."""
        return self._preview.source_endpoint is not None

    @property
    def name(self) -> str:
        return "Simple Wired Connection"

    @property
    def description(self) -> str:
        return "Connect two SLD endpoints without creating a Line or Cable object."

    def on_activate(self) -> None:
        self._last_snap_result = None
        self._last_command_result = None
        self._clear_state()

    def on_deactivate(self) -> None:
        self._clear_state()
        self._last_snap_result = None
        self._last_command_result = None

    def on_mouse_press(self, event: Any) -> bool:
        self._ensure_active()
        snap_result = self._snap(event)
        self._last_snap_result = snap_result
        if snap_result is None:
            return False
        if getattr(snap_result, "snap_type", None) is not SnapType.OBJECT:
            return False
        position = self._position_tuple(snap_result.position)
        endpoint = self._authoring_endpoint(snap_result)
        if self._preview.source_endpoint is None:
            self._failure_reason = ""
            self._preview.begin(endpoint)
            self._wire_layer_id = self._capture_active_layer_id()
            self._start_snap = snap_result
            self._start_position = position
            self._current_position = position
            self._preview.update_cursor(position)
            self._show_preview()
            return True
        self._current_position = position
        self._failure_reason = ""
        self._preview.update_target(endpoint, valid=True)
        self._preview.update_cursor(position)
        endpoint_pair = self._preview.get_endpoint_pair()
        if endpoint_pair is None:
            self._preview.update_target(
                None,
                valid=False,
                reason="A source endpoint is required before committing a Simple Wire.",
            )
            self._show_preview()
            return False
        presentation_route = self._route_payload(self._start_position, position)
        try:
            result = self._execute_connection(
                endpoint_pair[0],
                endpoint_pair[1],
                source_snap=self._start_snap,
                target_snap=snap_result,
                presentation_route=presentation_route,
            )
        except Exception as exc:
            # Preserve the original failure for the interaction/error boundary,
            # but also retain an actionable reason in the live wire preview.
            self._last_command_result = exc
            self._failure_reason = f"Connection was not created: {type(exc).__name__}: {exc}"
            self._preview.update_target(
                endpoint_pair[1],
                valid=False,
                reason=self._failure_reason,
            )
            self._show_preview()
            raise

        self._last_command_result = result
        if not getattr(result, "success", False):
            # A failed Application command is not a committed connection.
            # Keep the source endpoint and show why the attempted wire failed.
            reason = str(getattr(result, "message", "") or "").strip()
            if not reason:
                reason = "The Application rejected the connection command."
            self._failure_reason = f"Connection was not created: {reason}"
            self._preview.update_target(
                endpoint_pair[1],
                valid=False,
                reason=self._failure_reason,
            )
            self._show_preview()
            return False
        self._clear_state()
        return True

    def on_mouse_move(self, event: Any) -> bool:
        self._ensure_active()
        if self._preview.source_endpoint is None:
            return False
        snap_result = self._snap(event)
        self._last_snap_result = snap_result
        if snap_result is None:
            position = self._position_tuple(self.event_position(event))
            self._current_position = position
            self._preview.update_cursor(position)
            self._preview.update_target(
                None,
                valid=False,
                reason="Move the cursor onto a stable electrical object endpoint.",
            )
            self._show_preview()
            return True

        position = self._position_tuple(snap_result.position)
        self._current_position = position
        self._preview.update_cursor(position)

        # Grid/none snaps are valid cursor positions but are not electrical
        # endpoints. Never pass them to EndpointIdentityAdapter: the adapter
        # deliberately rejects missing object identity so that presentation
        # geometry cannot be promoted into an electrical connection.
        if getattr(getattr(snap_result, "snap_type", None), "name", None) != "OBJECT":
            self._preview.update_target(
                None,
                valid=False,
                reason="Move the cursor onto a stable electrical object endpoint.",
            )
            self._show_preview()
            return True

        endpoint = self._authoring_endpoint(snap_result)
        self._preview.update_target(endpoint, valid=True)
        self._show_preview()
        return True

    def on_mouse_release(self, event: Any) -> bool:
        self._ensure_active()
        return self._preview.source_endpoint is not None

    def on_mouse_double_click(self, event: Any) -> bool:
        # A double-click is not a second wire endpoint gesture. Qt emits a
        # distinct double-click event after the first press/release sequence;
        # forwarding it to on_mouse_press can start a new wire immediately
        # after a successful connection cleared the preview state.
        del event
        return False

    def on_key_press(self, event: Any) -> bool:
        self._ensure_active()
        if self._is_escape_event(event):
            return self.on_cancel()
        return False

    def on_cancel(self) -> bool:
        self._ensure_active()
        had_state = self._preview.source_endpoint is not None
        self._clear_state()
        return had_state

    def on_reset(self) -> None:
        self._ensure_active()
        self._clear_state()

    def _snap(self, event: Any) -> Any:
        scene_position = self.event_position(event)
        if isinstance(scene_position, (tuple, list)) and len(scene_position) >= 2:
            scene_position = QPointF(float(scene_position[0]), float(scene_position[1]))
        snap = getattr(self.get_snap_system(), "snap", None)
        if not callable(snap):
            raise TypeError("SnapSystem must provide snap().")
        intent = SnapIntent.WIRE_TARGET if self._preview.source_endpoint is not None else SnapIntent.WIRE_START
        result = snap(scene_position, allow_grid=False, allow_object=True, intent=intent)
        if getattr(result, "position", None) is None:
            return None
        return result

    def _execute_connection(
        self,
        endpoint_from: Any,
        endpoint_to: Any,
        *,
        source_snap: Any,
        target_snap: Any,
        presentation_route: dict | None = None,
    ) -> Any:
        del source_snap, target_snap
        if endpoint_from is None or endpoint_to is None:
            raise ValueError("WireTool requires two canonical electrical endpoint references.")
        if endpoint_from == endpoint_to:
            self._preview.update_target(
                endpoint_to,
                valid=False,
                reason="Choose a different electrical endpoint.",
            )
            self._show_preview()
            return None
        if isinstance(endpoint_from, DraftEndpointReference) or isinstance(endpoint_to, DraftEndpointReference):
            source = self._as_draft_endpoint(endpoint_from)
            target = self._as_draft_endpoint(endpoint_to)
            existing_id = self._existing_draft_connection_id(source, target)
            if existing_id is not None:
                self._preview.update_target(
                    endpoint_to,
                    valid=False,
                    reason=f"These endpoints are already connected by {existing_id}.",
                )
                self._show_preview()
                self._report_feedback(
                    f"Wire not created: these endpoints are already connected ({existing_id})."
                )
                return None
            from uuid import uuid4
            command = CreateDraftConnectionCommand(
                document_id=getattr(self.application.presentation, "document_id", None),
                connection={
                    "connection_id": f"draft-wire-{uuid4().hex}",
                    "source": source.to_dict(),
                    "target": target.to_dict(),
                    "connection_kind": "simple_wire",
                    "route": dict(presentation_route or {}),
                    "layer_id": self._wire_layer_id or "default",
                }
            )
        else:
            command = CreateSimpleWireConnectionCommand(
                endpoint_a=endpoint_from,
                endpoint_b=endpoint_to,
                presentation_route=presentation_route,
            )
        return self.execute_command(command)

    def _capture_active_layer_id(self) -> str:
        """Capture the active document layer when the first wire endpoint is acquired."""
        getter = getattr(self.controller, "get_sld_controller", None)
        sld_controller = getter() if callable(getter) else None
        layer_id = getattr(sld_controller, "active_layer_id", "default")
        if not isinstance(layer_id, str) or not layer_id.strip():
            raise ValueError("Wire authoring requires a valid active SLD presentation layer.")
        return layer_id.strip()

    @staticmethod
    def _authoring_endpoint(snap_result: Any) -> Any:
        """Resolve one snap through the canonical identity adapter before assigning draft scope."""
        endpoint = EndpointIdentityAdapter.from_snap_result(snap_result)
        draft_id = getattr(snap_result, "draft_id", None)
        if draft_id is None:
            return endpoint
        if str(draft_id).strip() != str(endpoint.object_id):
            raise ValueError("Draft snap identity does not match the resolved endpoint object.")

        # Draft scope is assigned only after the presentation source, snap
        # candidate and canonical endpoint have agreed. The same endpoint
        # representation is used by preview and the command payload.
        if endpoint.is_bus:
            return DraftEndpointReference.bus(
                bus_id=str(endpoint.object_id),
                attachment_id=str(endpoint.attachment_id),
                scope="draft",
            )
        if endpoint.is_terminal:
            return DraftEndpointReference.terminal(
                draft_id=str(endpoint.object_id),
                equipment_type=str(endpoint.equipment_type.value),
                terminal_role=str(endpoint.terminal_role),
                scope="draft",
            )
        raise ValueError("Unsupported draft electrical endpoint kind.")

    @staticmethod
    def _as_draft_endpoint(endpoint: Any) -> DraftEndpointReference:
        if isinstance(endpoint, DraftEndpointReference):
            return endpoint
        from core.model import EndpointReference
        if not isinstance(endpoint, EndpointReference):
            raise TypeError("Unsupported endpoint type for draft connection.")
        if endpoint.is_bus:
            return DraftEndpointReference.bus(
                bus_id=str(endpoint.object_id),
                attachment_id=str(endpoint.attachment_id),
                scope="core",
            )
        return DraftEndpointReference.terminal(
            draft_id=str(endpoint.object_id),
            equipment_type=str(endpoint.equipment_type.value),
            terminal_role=str(endpoint.terminal_role),
            scope="core",
        )

    def _existing_draft_connection_id(
        self,
        source: DraftEndpointReference,
        target: DraftEndpointReference,
    ) -> str | None:
        """Avoid dispatching a duplicate draft wire for an existing endpoint pair."""
        reader = getattr(self.application, "read_draft_network", None)
        if not callable(reader):
            return None
        try:
            snapshot = reader()
        except (RuntimeError, TypeError, ValueError):
            # The Application command handler remains the authoritative guard.
            return None
        if not isinstance(snapshot, dict):
            return None
        connections = snapshot.get("connections", ())
        if not isinstance(connections, (list, tuple)):
            return None
        source_data = source.to_dict()
        target_data = target.to_dict()
        for item in connections:
            if not isinstance(item, dict):
                continue
            connection_source = item.get("source")
            connection_target = item.get("target")
            if not isinstance(connection_source, dict) or not isinstance(connection_target, dict):
                continue
            if (
                (connection_source == source_data and connection_target == target_data)
                or (connection_source == target_data and connection_target == source_data)
            ):
                connection_id = item.get("connection_id")
                return str(connection_id) if connection_id else "an existing draft connection"
        return None

    @staticmethod
    def _route_payload(
        start: Tuple[float, float] | None,
        end: Tuple[float, float],
    ) -> dict[str, Any]:
        """Build canonical orthogonal presentation metadata (bend points only)."""
        if start is None:
            raise ValueError("A source position is required to route a wire.")
        sx, sy = float(start[0]), float(start[1])
        ex, ey = float(end[0]), float(end[1])
        bends = [] if sx == ex or sy == ey else [[ex, sy]]
        return {"routing_mode": "orthogonal", "ownership": "auto", "points": bends}

    def _preview_polyline(self) -> tuple[Tuple[float, float], ...]:
        if self._start_position is None or self._current_position is None:
            return ()
        start = self._start_position
        end = self._current_position
        route = self._route_payload(start, end)
        points = [start, *(tuple(point) for point in route["points"]), end]
        # Keep both endpoint entries even when they coincide at wire start;
        # PreviewLayer safely omits zero-length graphics segments.
        return tuple(points)

    def _report_feedback(self, message: str) -> None:
        for name in ("show_status_message", "set_status_message", "notify_user"):
            callback = getattr(self.controller, name, None)
            if callable(callback):
                callback(message)
                return

    def _show_preview(self) -> None:
        layer = self._preview_layer
        if layer is None or self._start_position is None or self._current_position is None:
            return
        points = self._preview_polyline()
        show_polyline = getattr(layer, "show_polyline", None)
        if callable(show_polyline):
            show_polyline(self._preview_owner, points)
            items_getter = getattr(layer, "items_for_owner", None)
            items = tuple(items_getter(self._preview_owner)) if callable(items_getter) else ()
        else:
            show_segment = getattr(layer, "show_segment", None)
            if not callable(show_segment):
                return
            show_segment(self._start_position, self._current_position)
            items_getter = getattr(layer, "items", None)
            items = tuple(items_getter()) if callable(items_getter) else ()
        reason = self._failure_reason or self._preview.validation_reason
        if reason and items:
            set_tooltip = getattr(items[-1], "setToolTip", None)
            if callable(set_tooltip):
                set_tooltip(reason)

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
        if self._preview_layer is not None:
            clear_owner = getattr(self._preview_layer, "clear_owner", None)
            if callable(clear_owner):
                clear_owner(self._preview_owner)
            else:
                clear_preview = getattr(self._preview_layer, "clear_preview", None)
                if callable(clear_preview):
                    clear_preview()
                else:
                    clear = getattr(self._preview_layer, "clear", None)
                    if callable(clear):
                        clear()
        self._start_position = None
        self._wire_layer_id = None
        self._failure_reason = ""
        self._start_snap = None
        self._current_position = None
        self._preview.reset()

    def get_state(self) -> dict[str, Any]:
        state = super().get_state()
        state.update({
            "start_position": self._start_position,
            "current_position": self._current_position,
            "preview": self._preview.get_state(),
            "last_snap_result": self._last_snap_result,
            "last_command_result": self._last_command_result,
        })
        return state


__all__ = ["WireTool"]
