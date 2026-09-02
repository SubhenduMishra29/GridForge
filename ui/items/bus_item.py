# ============================================================
# File: ui/items/bus_item.py
# GridForge V2 — Bus Graphics Item
# Author: Subhendu Mishra
# ============================================================

"""Presentation-only Bus graphics realization.

BusItem is a specialized SLD graphics projection. It receives stable identity
and presentation geometry; it does not retain or depend on an authoritative
Core Bus object.

Architecture
------------

    SLDCanvasSnapshot / presentation data
                    │
                    ▼
                 BusItem
                    │
                    ▼
              QGraphicsScene

BusItem owns graphical state only: geometry, appearance, selection projection,
and graphical movement. Electrical truth and application mutation remain
outside the graphics item.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QBrush,
    QGraphicsItem,
    QGraphicsObject,
    QPainter,
    QPen,
    QPointF,
    QRectF,
    Qt,
    Signal,
)

from .base_item import BaseItem


class BusItem(BaseItem):
    """Specialized presentation projection for one SLD bus node."""

    DEFAULT_RADIUS = 8.0
    DEFAULT_LINE_WIDTH = 1.5

    position_changed = Signal(object)

    def __init__(
        self,
        object_id: Any,
        position: Optional[QPointF] = None,
        radius: float = DEFAULT_RADIUS,
        parent: Optional[QGraphicsObject] = None,
    ) -> None:
        super().__init__(object_id=object_id, parent=parent)
        self._validate_radius(radius)
        self._radius = float(radius)

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
            True,
        )
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
            True,
        )

        self._pen = QPen(Qt.GlobalColor.black, self.DEFAULT_LINE_WIDTH)
        self._brush = QBrush(Qt.GlobalColor.white)
        self._suppress_position_signal = False

        if position is not None:
            self._validate_point(position, "position")
            self.set_scene_position(float(position.x()), float(position.y()))

    def get_scene_position(self) -> tuple[float, float]:
        """Return graphical scene position only."""
        position = self.scenePos()
        return float(position.x()), float(position.y())

    def set_scene_position(self, x: float, y: float) -> None:
        """Set graphical position without touching Core state."""
        self._validate_coordinate(x, "x")
        self._validate_coordinate(y, "y")

        old_x, old_y = self.get_scene_position()
        new_x, new_y = float(x), float(y)
        if old_x == new_x and old_y == new_y:
            return

        self._suppress_position_signal = True
        try:
            super().set_scene_position(new_x, new_y)
        finally:
            self._suppress_position_signal = False

        self.position_changed.emit(QPointF(new_x, new_y))

    def itemChange(self, change: Any, value: Any) -> Any:
        """Observe Qt-driven graphical position changes only."""
        result = super().itemChange(change, value)
        if (
            change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
            and value is not None
            and not self._suppress_position_signal
        ):
            self._validate_point(value, "position")
            self.position_changed.emit(QPointF(value.x(), value.y()))
        return result

    def boundingRect(self) -> QRectF:
        """Return the local Bus symbol bounds."""
        radius = self._radius
        return QRectF(-radius, -radius, radius * 2.0, radius * 2.0)

    def paint(
        self,
        painter: QPainter,
        option: Any,
        widget: Optional[Any] = None,
    ) -> None:
        """Paint the Bus symbol without evaluating engineering semantics."""
        del option, widget
        if painter is None:
            return
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawEllipse(self.boundingRect())

    def set_radius(self, radius: float) -> None:
        """Change visual Bus radius."""
        self._validate_radius(radius)
        radius = float(radius)
        if radius == self._radius:
            return
        self.prepareGeometryChange()
        self._radius = radius
        self.update()

    def get_radius(self) -> float:
        """Return visual Bus radius."""
        return self._radius

    def set_pen(self, pen: QPen) -> None:
        """Set visual outline pen."""
        if not isinstance(pen, QPen):
            raise TypeError("pen must be a QPen.")
        self._pen = QPen(pen)
        self.update()

    def get_pen(self) -> QPen:
        """Return a copy of the visual outline pen."""
        return QPen(self._pen)

    def set_brush(self, brush: QBrush) -> None:
        """Set visual fill brush."""
        if not isinstance(brush, QBrush):
            raise TypeError("brush must be a QBrush.")
        self._brush = QBrush(brush)
        self.update()

    def get_brush(self) -> QBrush:
        """Return a copy of the visual fill brush."""
        return QBrush(self._brush)

    def set_visual_selected(self, selected: bool) -> None:
        """Set graphical selection projection only."""
        self.set_graphical_selected(selected)

    def is_visual_selected(self) -> bool:
        """Return graphical selection state."""
        return self.is_selected()

    def get_state(self) -> dict[str, Any]:
        """Return presentation-only diagnostic state."""
        state = super().get_state()
        state.update(
            {
                "radius": self._radius,
                "movable": bool(
                    self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                ),
                "selectable": bool(
                    self.flags()
                    & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                ),
            }
        )
        return state

    @staticmethod
    def _validate_coordinate(value: Any, name: str) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a numeric value.")

    @staticmethod
    def _validate_radius(radius: Any) -> None:
        if isinstance(radius, bool) or not isinstance(radius, (int, float)):
            raise TypeError("radius must be a numeric value.")
        if radius <= 0:
            raise ValueError("radius must be greater than zero.")

    @staticmethod
    def _validate_point(point: Any, name: str) -> None:
        if point is None:
            raise ValueError(f"{name} must not be None.")
        if not callable(getattr(point, "x", None)):
            raise TypeError(f"{name} must provide x().")
        if not callable(getattr(point, "y", None)):
            raise TypeError(f"{name} must provide y().")

    def __repr__(self) -> str:
        """Return a concise diagnostic representation."""
        x, y = self.get_scene_position()
        return (
            "BusItem("
            f"object_id={self.object_id!r}, "
            f"position=({x:.2f}, {y:.2f}), "
            f"radius={self._radius:.2f}, "
            f"selected={self.is_selected()}"
            ")"
        )


__all__ = ["BusItem"]
