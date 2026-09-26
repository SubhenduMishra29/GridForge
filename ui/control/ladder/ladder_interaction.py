"""Transient Ladder interaction boundary.

Preview objects are presentation-only. Persistent placement is an immutable
Application command and never a direct Core mutation.
"""

from __future__ import annotations

from uuid import uuid4
from typing import Any

from ui.core.qt import QGraphicsRectItem, QPen
from core.application.commands.control_commands import AddControlComponent
from ui.control.control_tool_palette import ControlToolDescriptor


class LadderInteraction:
    def __init__(self, *, application: Any, canvas: Any) -> None:
        self._application = application
        self._canvas = canvas
        self._active: ControlToolDescriptor | None = None
        self._preview = None

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
        if descriptor is None or descriptor.component_type is None:
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
