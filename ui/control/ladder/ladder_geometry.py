"""Presentation-only geometry policy for the Control/Ladder workspace.

Author: Subhendu Mishra
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ui.core.qt import QRectF


class LadderGeometryPolicy:
    """Single Qt-side geometry policy shared by projection and interaction."""

    RUNG_HEIGHT = 80.0
    RUNG_LINE_OFFSET = 24.0
    COMPONENT_WIDTH = 90.0
    COMPONENT_HEIGHT = 46.0
    POSITION_WIDTH = 120.0
    COMPONENT_X_OFFSET = 8.0
    PORT_MARGIN = 6.0
    SNAP_TOLERANCE = 40.0

    @classmethod
    def rung_y(cls, order: int) -> float:
        return float(order) * cls.RUNG_HEIGHT

    @classmethod
    def rung_line_y(cls, order: int) -> float:
        return cls.rung_y(order) + cls.RUNG_LINE_OFFSET

    @classmethod
    def component_x(cls, position: int) -> float:
        return float(position) * cls.POSITION_WIDTH + cls.COMPONENT_X_OFFSET

    @classmethod
    def component_rect(cls, *, order: int, position: int) -> QRectF:
        return QRectF(
            cls.component_x(position),
            cls.rung_y(order),
            cls.COMPONENT_WIDTH,
            cls.COMPONENT_HEIGHT,
        )

    @classmethod
    def snap_rung(cls, y: float, rungs: Iterable[Any]) -> Any | None:
        candidates = tuple(rungs)
        if not candidates:
            return None
        rung = min(candidates, key=lambda item: abs(cls.rung_y(int(item.order)) - float(y)))
        if abs(cls.rung_y(int(rung.order)) - float(y)) > cls.SNAP_TOLERANCE:
            return None
        return rung

    @classmethod
    def snap_position(cls, x: float) -> int:
        return max(0, int(round((float(x) - cls.COMPONENT_X_OFFSET) / cls.POSITION_WIDTH)))

    @classmethod
    def port_local_y(cls, index: int, count: int) -> float:
        if count <= 0:
            return cls.COMPONENT_HEIGHT / 2.0
        return cls.COMPONENT_HEIGHT * (float(index) + 1.0) / (float(count) + 1.0)

    @classmethod
    def input_port_position(cls, *, order: int, position: int, index: int, count: int) -> tuple[float, float]:
        rect = cls.component_rect(order=order, position=position)
        return rect.left(), rect.top() + cls.port_local_y(index, count)

    @classmethod
    def output_port_position(cls, *, order: int, position: int, index: int, count: int) -> tuple[float, float]:
        rect = cls.component_rect(order=order, position=position)
        return rect.right(), rect.top() + cls.port_local_y(index, count)


__all__ = ["LadderGeometryPolicy"]
