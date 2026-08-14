# ============================================================
# File: ui/items/bus_item.py
# GridForge V2 — Bus Graphics Item
# ============================================================
"""
Graphics projection of an authoritative GridForge Bus object.

Architecture
------------

    Core / Application Bus
              │
              ▼
        BusRenderer
              │
              ▼
           BusItem
              │
              ▼
         GridScene
              │
              ▼
        GraphicsView

BusItem is a visual projection only.

Responsibilities
----------------
BusItem:

    - represents one authoritative Bus visually;
    - exposes object_id;
    - maintains its canvas position;
    - provides a selectable/movable graphics representation;
    - provides a stable visual bounding geometry;
    - exposes presentation state required by renderers;
    - emits position-change information through the graphics
      item mechanism.

BusItem does NOT:

    - own the Bus model;
    - modify the Core model directly;
    - perform electrical calculations;
    - determine topology;
    - perform snapping;
    - own application selection;
    - create Lines or other model objects;
    - implement tool behavior;
    - perform rendering orchestration.

Identity
--------
``object_id`` is the authoritative application/Core object ID.

The item may retain a reference to the projected object for
presentation purposes, but that object remains owned by the
application/Core layer.

Selection
---------
QGraphicsItem selection is only a visual projection.

Persistent application selection remains owned by Controller
through SelectionManager.

Movement
--------
The item is movable as a Qt graphics object so canvas interaction
can provide immediate visual feedback.

A position change is exposed through ``position_changed``.
Application/Core mutation must be performed by the appropriate
controller/command path rather than directly by this item.

Qt Architecture
---------------
All Qt dependencies are imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QBrush,
    QGraphicsEllipseItem,
    QPen,
    QPointF,
    Qt,
    Signal,
)


class BusItem(QGraphicsEllipseItem):
    """
    Visual representation of one GridForge Bus.

    The item deliberately contains no electrical-domain logic.

    Parameters
    ----------
    object_id:
        Authoritative identifier of the represented Bus.

    position:
        Initial scene position.

    radius:
        Visual radius of the bus symbol.

    model:
        Optional authoritative Bus object being projected.

        The item does not mutate this object.
    """

    # ========================================================
    # VISUAL DEFAULTS
    # ========================================================

    DEFAULT_RADIUS = 8.0

    DEFAULT_LINE_WIDTH = 1.5

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        object_id: Any,
        position: Optional[QPointF] = None,
        radius: float = DEFAULT_RADIUS,
        model: Optional[Any] = None,
    ) -> None:
        if object_id is None:
            raise ValueError(
                "object_id must not be None."
            )

        if not isinstance(
            radius,
            (int, float),
        ) or isinstance(
            radius,
            bool,
        ):
            raise TypeError(
                "radius must be a numeric value."
            )

        if radius <= 0:
            raise ValueError(
                "radius must be greater than zero."
            )

        super().__init__(
            -float(radius),
            -float(radius),
            float(radius) * 2.0,
            float(radius) * 2.0,
        )

        self.object_id = object_id
        self.model = model
        self.radius = float(radius)

        self._position = QPointF(
            0.0,
            0.0,
        )

        # ----------------------------------------------------
        # Graphics-item interaction state.
        # ----------------------------------------------------

        self.setFlag(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        self.setFlag(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable,
            True,
        )

        self.setFlag(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges,
            True,
        )

        # ----------------------------------------------------
        # Default visual appearance.
        #
        # Renderer layers may replace these presentation
        # attributes.
        # ----------------------------------------------------

        self.setPen(
            QPen(
                Qt.GlobalColor.black,
                self.DEFAULT_LINE_WIDTH,
            )
        )

        self.setBrush(
            QBrush(
                Qt.GlobalColor.white
            )
        )

        # ----------------------------------------------------
        # Position-change notification.
        #
        # This is a UI notification only. It does not mutate
        # the Core model.
        # ----------------------------------------------------

        self.position_changed = Signal(
            object
        )

        if position is not None:
            self.set_scene_position(
                position,
                emit=False,
            )

    # ========================================================
    # IDENTITY
    # ========================================================

    def get_object_id(
        self,
    ) -> Any:
        """
        Return the authoritative ID of the represented Bus.
        """

        return self.object_id

    # ========================================================
    # MODEL PROJECTION
    # ========================================================

    def get_model(
        self,
    ) -> Optional[Any]:
        """
        Return the projected model object, if supplied.

        The returned object is not owned by BusItem.
        """

        return self.model

    # --------------------------------------------------------

    def set_model(
        self,
        model: Optional[Any],
    ) -> None:
        """
        Replace the projected model reference.

        This changes only the UI projection reference.
        """

        self.model = model

    # ========================================================
    # POSITION
    # ========================================================

    def get_scene_position(
        self,
    ) -> QPointF:
        """
        Return the current scene position.
        """

        position = self.pos()

        return QPointF(
            position.x(),
            position.y(),
        )

    # --------------------------------------------------------

    def set_scene_position(
        self,
        position: QPointF,
        *,
        emit: bool = True,
    ) -> None:
        """
        Set the item's scene position.

        Parameters
        ----------
        position:
            Target scene coordinate.

        emit:
            Whether to emit ``position_changed``.

        This method changes only the graphical projection.
        """

        self._validate_point(
            position,
            "position",
        )

        new_position = QPointF(
            position.x(),
            position.y(),
        )

        old_position = self.get_scene_position()

        self.setPos(
            new_position
        )

        self._position = new_position

        if (
            emit
            and (
                old_position.x()
                != new_position.x()
                or old_position.y()
                != new_position.y()
            )
        ):
            self.position_changed.emit(
                new_position
            )

    # ========================================================
    # GEOMETRY CHANGE
    # ========================================================

    def itemChange(
        self,
        change: Any,
        value: Any,
    ) -> Any:
        """
        Observe Qt graphics-item position changes.

        This method never writes to the Core model.
        """

        position_change = getattr(
            QGraphicsEllipseItem.GraphicsItemChange,
            "ItemPositionHasChanged",
            None,
        )

        result = super().itemChange(
            change,
            value,
        )

        if (
            position_change is not None
            and change == position_change
        ):
            if value is not None:
                self._validate_point(
                    value,
                    "position change",
                )

                self._position = QPointF(
                    value.x(),
                    value.y(),
                )

                self.position_changed.emit(
                    QPointF(
                        value.x(),
                        value.y(),
                    )
                )

        return result

    # ========================================================
    # VISUAL CONFIGURATION
    # ========================================================

    def set_radius(
        self,
        radius: float,
    ) -> None:
        """
        Change the visual bus radius.

        This is presentation state only.
        """

        if not isinstance(
            radius,
            (int, float),
        ) or isinstance(
            radius,
            bool,
        ):
            raise TypeError(
                "radius must be a numeric value."
            )

        if radius <= 0:
            raise ValueError(
                "radius must be greater than zero."
            )

        radius = float(radius)

        center = self.get_scene_position()

        self.prepareGeometryChange()

        self.radius = radius

        self.setRect(
            -radius,
            -radius,
            radius * 2.0,
            radius * 2.0,
        )

        self.setPos(
            center
        )

    # --------------------------------------------------------

    def get_radius(
        self,
    ) -> float:
        """
        Return the current visual radius.
        """

        return self.radius

    # --------------------------------------------------------

    def set_pen(
        self,
        pen: QPen,
    ) -> None:
        """
        Set the bus outline presentation.
        """

        if pen is None:
            raise ValueError(
                "pen must not be None."
            )

        self.setPen(
            pen
        )

    # --------------------------------------------------------

    def set_brush(
        self,
        brush: QBrush,
    ) -> None:
        """
        Set the bus fill presentation.
        """

        if brush is None:
            raise ValueError(
                "brush must not be None."
            )

        self.setBrush(
            brush
        )

    # ========================================================
    # SELECTION PRESENTATION
    # ========================================================

    def set_visual_selected(
        self,
        selected: bool,
    ) -> None:
        """
        Set the Qt selection projection.

        Persistent application selection remains owned by
        Controller/SelectionManager.
        """

        if not isinstance(
            selected,
            bool,
        ):
            raise TypeError(
                "selected must be a bool."
            )

        self.setSelected(
            selected
        )

    # --------------------------------------------------------

    def is_visual_selected(
        self,
    ) -> bool:
        """
        Return the current Qt visual selection state.
        """

        return bool(
            self.isSelected()
        )

    # ========================================================
    # PRESENTATION STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic UI state.
        """

        position = self.get_scene_position()

        return {
            "object_id": self.object_id,
            "position": position,
            "radius": self.radius,
            "selected": self.is_visual_selected(),
            "movable": bool(
                self.flags()
                & QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable
            ),
            "selectable": bool(
                self.flags()
                & QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable
            ),
            "has_model": self.model is not None,
        }

    # ========================================================
    # VALIDATION
    # ========================================================

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
            getattr(point, "x", None),
        ):
            raise TypeError(
                f"{name} must provide x()."
            )

        if not callable(
            getattr(point, "y", None),
        ):
            raise TypeError(
                f"{name} must provide y()."
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        position = self.get_scene_position()

        return (
            "BusItem("
            f"id={self.object_id!r}, "
            f"position=("
            f"{position.x():.2f}, "
            f"{position.y():.2f}"
            "), "
            f"selected={self.is_visual_selected()}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "BusItem",
]
