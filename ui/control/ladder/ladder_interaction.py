"""Transient Ladder interaction boundary.

Preview objects are presentation-only. Persistent placement is an immutable
Application command and never a direct Core mutation.
"""

from __future__ import annotations

from uuid import uuid4
from typing import Any

from ui.core.qt import QGraphicsRectItem, QPen, QPointF, QTransform
from core.application.commands.control_commands import AddControlComponent, ConnectControlSignals, DisconnectControlSignals
from ui.control.control_tool_palette import ControlToolDescriptor


class LadderInteraction:
    def __init__(self, *, application: Any, canvas: Any) -> None:
        self._application = application
        self._canvas = canvas
        self._active: ControlToolDescriptor | None = None
        self._preview = None
        self._signal_source: str | None = None

    @property
    def active_tool(self) -> ControlToolDescriptor | None:
        return self._active

    def activate(self, descriptor: ControlToolDescriptor) -> None:
        self.cancel()
        self._active = descriptor

    def cancel(self) -> None:
        if self._preview is not None:
            self._canvas.removeItem(self._preview)
            self._preview = None
        self._active = None
        self._signal_source = None

    def preview(self, x: float, y: float) -> None:
        if self._active is None or self._active.component_type is None:
            return
        if self._preview is None:
            self._preview = QGraphicsRectItem(0.0, 0.0, 90.0, 46.0)
            self._preview.setOpacity(0.45)
            self._preview.setPen(QPen())
            self._canvas.addItem(self._preview)
        self._preview.setPos(float(x), float(y))

    def place(self, x: float, y: float, *, rung_id: str = "rung-001") -> Any:
        descriptor = self._active
        if descriptor is None:
            return None

        if descriptor.tool_id in {"signal.connect", "signal.disconnect"}:
            item = self._canvas.itemAt(QPointF(float(x), float(y)), QTransform())
            component_id = getattr(item, "object_id", None)
            if component_id is None:
                return None
            if self._signal_source is None:
                self._signal_source = str(component_id)
                return None
            source_id = self._signal_source
            target_id = str(component_id)
            self._signal_source = None
            read_model = self._application.read_control()
            source = next((c for c in read_model.components if c.component_id == source_id), None)
            target = next((c for c in read_model.components if c.component_id == target_id), None)
            if source is None or target is None:
                return None
            if not source.outputs or not target.inputs:
                return None
            command_type = ConnectControlSignals if descriptor.tool_id == "signal.connect" else DisconnectControlSignals
            return self._application.execute(command_type(
                source_component=source_id,
                source_output=source.outputs[0],
                target_component=target_id,
                target_input=target.inputs[0],
            ))

        if descriptor.component_type is None:
            return None

        position = max(0, int(float(x) // 120.0))
        result = self._application.execute(AddControlComponent(
            component_id=f"control-{uuid4().hex[:12]}",
            component_type=descriptor.component_type,
            rung_id=rung_id,
            position=position,
        ))
        self.cancel()
        return result


__all__ = ["LadderInteraction"]
