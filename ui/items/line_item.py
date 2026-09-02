# ============================================================
# File: ui/items/line_item.py
# GridForge V2 — Line Graphics Item
# Author: Subhendu Mishra
# ============================================================

"""Presentation-only Line graphics realization.

LineItem is a specialized SLD connection projection. It consumes stable
identity and renderer-neutral endpoint geometry. It does not retain a Core
Line object and does not depend on a Controller.

Architecture
------------

    SLDCanvasSnapshot
          │
          ▼
       LineItem
          │
          ▼
    QGraphicsScene

Electrical topology, engineering length, validation, and application
selection remain outside this graphics item.
"""

from __future__ import annotations

from typing import Any

from ui.core.qt import (
    QGraphicsItem,
    QGraphicsLineItem,
    QLineF,
    QPen,
    QPointF,
    Qt,
)


class LineItem(QGraphicsLineItem):
    """Specialized presentation projection for one SLD connection."""

    DEFAULT_LINE_WIDTH = 2.0

    def __init__(
        self,
        object_id: Any,
        start: QPointF,
        end: QPointF,
    ) -> None:
        if object_id is None:
            raise ValueError("object_id must not be None.")
        self._validate_point(start, "start")
        self._validate_point(end, "end")

        super().__init__(QLineF(start, end))
        self._object_id = object_id

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
            False,
        )
        self.setPen(QPen(Qt.GlobalColor.black, self.DEFAULT_LINE_WIDTH))

    @property
    def object_id(self) -> Any:
        """Return stable represented-object identity."""
        return self._object_id

    def get_object_id(self) -> Any:
        """Return stable represented-object identity."""
        return self._object_id

    def set_visual_endpoints(self, start: QPointF, end: QPointF) -> None:
        """Update visual endpoints without changing electrical state."""
        self._validate_point(start, "start")
        self._validate_point(end, "end")
        self.prepareGeometryChange()
        self.setLine(QLineF(start, end))

    def get_start(self) -> QPointF:
        """Return current visual start point."""
        line = self.line()
        return QPointF(line.p1().x(), line.p1().y())

    def get_end(self) -> QPointF:
        """Return current visual end point."""
        line = self.line()
        return QPointF(line.p2().x(), line.p2().y())

    def get_endpoints(self) -> tuple[QPointF, QPointF]:
        """Return current visual endpoints."""
        return self.get_start(), self.get_end()

    def length(self) -> float:
        """Return visual geometric length only."""
        return float(self.line().length())

    def bounding_rect_scene(self) -> Any:
        """Return the line bounding rectangle in scene coordinates."""
        return self.mapRectToScene(self.boundingRect())

    def set_visual_selected(self, selected: bool) -> None:
        """Set Qt selection presentation state only."""
        if not isinstance(selected, bool):
            raise TypeError("selected must be a bool.")
        self.setSelected(selected)

    def is_visual_selected(self) -> bool:
        """Return current Qt selection presentation state."""
        return bool(self.isSelected())

    def set_pen(self, pen: QPen) -> None:
        """Set visual line pen."""
        if pen is None:
            raise ValueError("pen must not be None.")
        self.setPen(pen)

    def get_state(self) -> dict[str, Any]:
        """Return presentation-only diagnostic state."""
        start = self.get_start()
        end = self.get_end()
        return {
            "object_id": self.object_id,
            "start": start,
            "end": end,
            "length": self.length(),
            "selected": self.is_visual_selected(),
            "movable": False,
        }

    @staticmethod
    def _validate_point(point: Any, name: str) -> None:
        """Validate a QPointF-compatible object."""
        if point is None:
            raise ValueError(f"{name} must not be None.")
        if not callable(getattr(point, "x", None)):
            raise TypeError(f"{name} must provide x().")
        if not callable(getattr(point, "y", None)):
            raise TypeError(f"{name} must provide y().")

    def __repr__(self) -> str:
        """Return a concise diagnostic representation."""
        start = self.get_start()
        end = self.get_end()
        return (
            "LineItem("
            f"object_id={self.object_id!r}, "
            f"start=({start.x():.2f}, {start.y():.2f}), "
            f"end=({end.x():.2f}, {end.y():.2f}), "
            f"selected={self.is_visual_selected()}"
            ")"
        )


__all__ = ["LineItem"]
