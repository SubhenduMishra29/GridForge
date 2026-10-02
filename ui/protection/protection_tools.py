# ============================================================
# File: ui/protection/protection_tools.py
# GridForge V2 — Protection Interaction Tools
# Author: Subhendu Mishra
# ============================================================
"""Protection interaction coordinators over the canonical Application boundary."""

from __future__ import annotations

from typing import Any

from core.application.commands.protection_configuration_commands import (
    BindProtectionMeasurementCommand,
    UnbindProtectionMeasurementCommand,
)
from core.application.command import Command
from ui.canvas.engineering_canvas_contract import CanvasFeedback, CanvasInteractionAdapter
from ui.core.selection_manager import SelectionManager
from ui.tools.tool_definition import ToolDefinition
from ui.interaction.interaction_session import InteractionSession


class ProtectionInteractionController:
    """Coordinate transient Protection tools without owning domain state."""

    TOOL_DEFINITIONS = (
        ToolDefinition("select", "Select", "Select Protection objects.", editor_types=("protection",), capabilities=("selection",), supported_modes=("select",)),
        ToolDefinition("connect_measurement", "Connect Measurement", "Bind a measurement channel to a relay input.", editor_types=("protection",), capabilities=("connection",), supported_modes=("connect",)),
        ToolDefinition("inspect", "Inspect", "Inspect Protection objects.", editor_types=("protection",), capabilities=("selection", "inspect"), supported_modes=("select", "edit")),
        ToolDefinition("fit", "Fit", "Fit the Protection view.", editor_types=("protection",), capabilities=("view",), supported_modes=("pan",)),
        ToolDefinition("diagnostics", "Diagnostics", "Inspect Protection diagnostics.", editor_types=("protection",), capabilities=("diagnostics",), supported_modes=("select",)),
    )

    def __init__(self, *, application: Any, selection_manager: SelectionManager,
                 adapter: CanvasInteractionAdapter) -> None:
        self._application = application
        self._selection_manager = selection_manager
        self._adapter = adapter
        self._session = InteractionSession()
        self._active_tool = "select"

    @property
    def active_tool(self) -> str:
        return self._active_tool

    @property
    def session(self) -> InteractionSession:
        return self._session

    def activate(self, tool_id: str) -> None:
        normalized = str(tool_id).strip().lower().replace(" ", "_")
        definitions = {definition.tool_id: definition for definition in self.TOOL_DEFINITIONS}
        if normalized not in definitions:
            raise ValueError(f"Unsupported Protection tool: {tool_id!r}")
        self._session.activate_tool(normalized)
        self._session.cancel_connection()
        self._active_tool = normalized
        self._adapter.set_tool(normalized)

    def cancel(self) -> None:
        self._session.cancel()
        self._session.clear_tool()
        self._active_tool = "select"
        self._adapter.cancel()

    def click_node(self, node: Any) -> Any:
        if self._active_tool == "select":
            self._selection_manager.select_single(node.object_id)
            return None
        if self._active_tool == "inspect":
            self._selection_manager.select_single(node.object_id)
            return None
        if self._active_tool == "fit":
            return "fit"
        if self._active_tool == "diagnostics":
            return "diagnostics"
        if self._active_tool != "connect_measurement":
            return None

        kind = getattr(node, "kind", "")
        if kind == "measurement_channel":
            self._session.begin_connection(str(node.channel_id))
            self._session.set_preview(("measurement", str(node.channel_id)))
            self._adapter.feedback(CanvasFeedback.PREVIEW, f"Measurement channel selected: {node.channel_id}")
            return None
        if kind == "relay_input":
            source_channel = self._session.connection_source_id
            if not source_channel:
                self._adapter.feedback(CanvasFeedback.INVALID, "Select a MeasurementChannel before selecting a Relay input.")
                return None
            try:
                command = self._build_binding_command(node, source_channel)
            except Exception as exc:
                self._adapter.feedback(CanvasFeedback.INVALID, f"Invalid measurement endpoint: {exc}")
                return None
            return self._execute(command)
        self._adapter.feedback(CanvasFeedback.INVALID, "Protection Connect Measurement requires a MeasurementChannel and Relay input.")
        return None

    def _build_binding_command(self, node: Any, channel_id: str) -> Command:
        configurations = self._application.read_protection_configuration()
        relay_id = str(node.relay_id)
        input_name = str(node.input_name)
        configuration = next(
            (
                item for item in configurations
                if str(item.relay_id) == relay_id
                and input_name in tuple(item.input_channel_ids.keys())
            ),
            None,
        )
        if configuration is None:
            # A configured function may not have a previous binding. Resolve the
            # single function configuration for the relay when possible.
            candidates = [item for item in configurations if str(item.relay_id) == relay_id]
            if len(candidates) != 1:
                raise ValueError(
                    f"No unique ProtectionFunctionConfiguration resolves relay input {relay_id}:{input_name}."
                )
            configuration = candidates[0]
        return BindProtectionMeasurementCommand(
            element_id=str(configuration.element_id),
            input_name=input_name,
            channel_id=channel_id,
        )

    def unbind(self, *, element_id: str, input_name: str) -> Any:
        return self._execute(UnbindProtectionMeasurementCommand(
            element_id=element_id,
            input_name=input_name,
        ))

    def _execute(self, command: Command) -> Any:
        try:
            result = self._application.execute(command)
        except Exception as exc:
            self._adapter.feedback(CanvasFeedback.INVALID, f"Protection command rejected: {exc}")
            return None
        if not getattr(result, "success", False):
            self._adapter.feedback(CanvasFeedback.INVALID, getattr(result, "message", "Protection command rejected."))
            return result
        self._session.cancel_connection()
        self._adapter.feedback(CanvasFeedback.CONNECTED, getattr(result, "message", "Protection measurement updated."))
        return result

    def dispose(self) -> None:
        self._session.close()


__all__ = ["ProtectionInteractionController"]
