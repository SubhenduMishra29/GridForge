# ============================================================
# File: ui/items/bus_item.py
# GridForge V2 — Bus Graphics Item
# ============================================================

"""
GridForge V2 — Bus Graphics Item.

BusItem is a presentation-layer projection of one authoritative
GridForge Bus object.

Architectural rules
-------------------

    Core Bus
       │
       ▼
    BusItem
       │
       ▼
   QGraphicsScene
       │
       ▼
   GraphicsView

BusItem:

    - owns graphical state only;
    - stores stable object identity;
    - optionally stores a non-owning model reference;
    - provides Bus-specific geometry;
    - provides graphical selection;
    - provides graphical movement;
    - emits graphical position changes.

BusItem does NOT:

    - own engineering truth;
    - modify Core directly;
    - determine electrical topology;
    - perform engineering calculations;
    - perform snapping;
    - perform connection validation;
    - own application selection;
    - create Lines;
    - manage tools;
    - manage controllers;
    - perform navigation.

All Qt dependencies are imported through ui.core.qt.
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


# ============================================================
# BUS ITEM
# ============================================================


class BusItem(BaseItem):
    """
    Graphical representation of one authoritative GridForge Bus.
    """

    # ========================================================
    # VISUAL DEFAULTS
    # ========================================================

    DEFAULT_RADIUS = 8.0
    DEFAULT_LINE_WIDTH = 1.5

    # ========================================================
    # SIGNALS
    # ========================================================

    position_changed = Signal(object)

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        object_id: Any,
        position: Optional[QPointF] = None,
        radius: float = DEFAULT_RADIUS,
        model: Optional[Any] = None,
        parent: Optional[QGraphicsObject] = None,
    ) -> None:
        super().__init__(
            object_id=object_id,
            parent=parent,
        )

        self._validate_radius(radius)

        self._radius = float(radius)
        self._model = model

        # ----------------------------------------------------
        # Qt interaction configuration
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Presentation state.
        #
        # QGraphicsObject does not provide pen/brush storage,
        # therefore BusItem owns these visual properties itself.
        # ----------------------------------------------------

        self._pen = QPen(
            Qt.GlobalColor.black,
            self.DEFAULT_LINE_WIDTH,
        )

        self._brush = QBrush(
            Qt.GlobalColor.white,
        )

        # Prevent duplicate position notifications when
        # set_scene_position() calls setPos().
        self._suppress_position_signal = False

        if position is not None:
            self._validate_point(
                position,
                "position",
            )

            self.set_scene_position(
                float(position.x()),
                float(position.y()),
            )

    # ========================================================
    # MODEL PROJECTION
    # ========================================================

    def get_model(self) -> Optional[Any]:
        """
        Return the optional projected model reference.

        BusItem never owns or mutates this object.
        """

        return self._model

    # --------------------------------------------------------

    def set_model(
        self,
        model: Optional[Any],
    ) -> None:
        """
        Replace the projected model reference.
        """

        self._model = model

    # ========================================================
    # POSITION
    # ========================================================

    def get_scene_position(self) -> tuple[float, float]:
        """
        Return graphical scene position.

        Maintains the BaseItem position contract.
        """

        position = self.scenePos()

        return (
            float(position.x()),
            float(position.y()),
        )

    # --------------------------------------------------------

    def set_scene_position(
        self,
        x: float,
        y: float,
    ) -> None:
        """
        Set graphical scene position.

        This intentionally preserves BaseItem's public
        set_scene_position(x, y) contract.
        """

        self._validate_coordinate(
            x,
            "x",
        )

        self._validate_coordinate(
            y,
            "y",
        )

        old_x, old_y = self.get_scene_position()

        new_x = float(x)
        new_y = float(y)

        if old_x == new_x and old_y == new_y:
            return

        self._suppress_position_signal = True

        try:
            super().set_scene_position(
                new_x,
                new_y,
            )
        finally:
            self._suppress_position_signal = False

        self.position_changed.emit(
            QPointF(
                new_x,
                new_y,
            )
        )

    # ========================================================
    # QT POSITION CHANGE
    # ========================================================

    def itemChange(
        self,
        change: Any,
        value: Any,
    ) -> Any:
        """
        Observe Qt-driven position changes.

        Only presentation state is reported.
        """

        result = super().itemChange(
            change,
            value,
        )

        if (
            change
            == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
        ):
            if (
                value is not None
                and not self._suppress_position_signal
            ):
                self._validate_point(
                    value,
                    "position",
                )

                self.position_changed.emit(
                    QPointF(
                        value.x(),
                        value.y(),
                    )
                )

        return result

    # ========================================================
    # GEOMETRY
    # ========================================================

    def boundingRect(self) -> QRectF:
        """
        Return the local bounding rectangle of the Bus symbol.
        """

        radius = self._radius

        return QRectF(
            -radius,
            -radius,
            radius * 2.0,
            radius * 2.0,
        )

    # ========================================================
    # PAINTING
    # ========================================================

    def paint(
        self,
        painter: QPainter,
        option: Any,
        widget: Optional[Any] = None,
    ) -> None:
        """
        Paint the Bus symbol.

        No engineering semantics are evaluated here.
        """

        del option
        del widget

        if painter is None:
            return

        painter.setPen(
            self._pen
        )

        painter.setBrush(
            self._brush
        )

        painter.drawEllipse(
            self.boundingRect()
        )

    # ========================================================
    # RADIUS
    # ========================================================

    def set_radius(
        self,
        radius: float,
    ) -> None:
        """
        Change the visual Bus radius.
        """

        self._validate_radius(radius)

        radius = float(radius)

        if radius == self._radius:
            return

        self.prepareGeometryChange()

        self._radius = radius

        self.update()

    # --------------------------------------------------------

    def get_radius(self) -> float:
        """
        Return the visual Bus radius.
        """

        return self._radius

    # ========================================================
    # PEN
    # ========================================================

    def set_pen(
        self,
        pen: QPen,
    ) -> None:
        """
        Set the visual outline pen.
        """

        if not isinstance(
            pen,
            QPen,
        ):
            raise TypeError(
                "pen must be a QPen."
            )

        self._pen = QPen(pen)

        self.update()

    # --------------------------------------------------------

    def get_pen(self) -> QPen:
        """
        Return a copy of the current visual pen.
        """

        return QPen(self._pen)

    # ========================================================
    # BRUSH
    # ========================================================

    def set_brush(
        self,
        brush: QBrush,
    ) -> None:
        """
        Set the visual fill brush.
        """

        if not isinstance(
            brush,
            QBrush,
        ):
            raise TypeError(
                "brush must be a QBrush."
            )

        self._brush = QBrush(brush)

        self.update()

    # --------------------------------------------------------

    def get_brush(self) -> QBrush:
        """
        Return a copy of the current visual brush.
        """

        return QBrush(self._brush)

    # ========================================================
    # SELECTION
    # ========================================================

    def set_visual_selected(
        self,
        selected: bool,
    ) -> None:
        """
        Set graphical selection only.
        """

        self.set_graphical_selected(
            selected
        )

    # --------------------------------------------------------

    def is_visual_selected(self) -> bool:
        """
        Return graphical selection state.
        """

        return self.is_selected()

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(self) -> dict[str, Any]:
        """
        Return presentation-layer diagnostic state.
        """

        state = super().get_state()

        state.update(
            {
                "radius": self._radius,
                "movable": bool(
                    self.flags()
                    & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                ),
                "selectable": bool(
                    self.flags()
                    & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                ),
                "has_model": self._model is not None,
            }
        )

        return state

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_coordinate(
        value: Any,
        name: str,
    ) -> None:
        """
        Validate a numeric coordinate.
        """

        if (
            isinstance(value, bool)
            or not isinstance(
                value,
                (int, float),
            )
        ):
            raise TypeError(
                f"{name} must be a numeric value."
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_radius(
        radius: Any,
    ) -> None:
        """
        Validate the visual radius.
        """

        if (
            isinstance(radius, bool)
            or not isinstance(
                radius,
                (int, float),
            )
        ):
            raise TypeError(
                "radius must be a numeric value."
            )

        if radius <= 0:
            raise ValueError(
                "radius must be greater than zero."
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_point(
        point: Any,
        name: str,
    ) -> None:
        """
        Validate a QPointF-compatible object.
        """

        if point is None:
            raise ValueError(
                f"{name} must not be None."
            )

        if not callable(
            getattr(
                point,
                "x",
                None,
            )
        ):
            raise TypeError(
                f"{name} must provide x()."
            )

        if not callable(
            getattr(
                point,
                "y",
                None,
            )
        ):
            raise TypeError(
                f"{name} must provide y()."
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        x, y = self.get_scene_position()

        return (
            "BusItem("
            f"object_id={self.object_id!r}, "
            f"position=({x:.2f}, {y:.2f}), "
            f"radius={self._radius:.2f}, "
            f"selected={self.is_selected()}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "BusItem",
]
