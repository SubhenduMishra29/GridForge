# ============================================================
# File: ui/items/line_item.py
# GridForge V2 — Line Graphics Item
# ============================================================
"""
Visual projection of an authoritative GridForge Line object.

Architecture
------------

    Core / Application Line
              │
              ▼
        LineRenderer
              │
              ▼
           LineItem
              │
              ▼
         GridScene
              │
              ▼
        GraphicsView

LineItem is a presentation object only.

Responsibilities
----------------
LineItem:

    - represents one authoritative Line visually;
    - exposes object_id;
    - stores the visual endpoints in scene coordinates;
    - renders a line between its endpoints;
    - supports visual selection;
    - provides geometry information required by renderers;
    - exposes endpoint-change notifications;
    - optionally retains a reference to the projected model.

LineItem does NOT:

    - own the Line model;
    - modify the Core model directly;
    - determine electrical topology;
    - create or delete Core objects;
    - perform snapping;
    - perform electrical calculations;
    - own persistent selection;
    - implement LineTool behavior;
    - decide connection validity;
    - manage navigation.

Topology
--------
The authoritative electrical connection remains in Core.

LineItem only projects the already-authoritative connection.

Endpoint coordinates are therefore presentation geometry.
They must not be interpreted as the source of electrical
connectivity.

Selection
---------
Persistent application selection belongs to Controller.

QGraphicsItem selection is only a visual projection.

Qt Architecture
---------------
All Qt dependencies must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QGraphicsLineItem,
    QLineF,
    QPen,
    QPointF,
    Qt,
    Signal,
)


class LineItem(QGraphicsLineItem):
    """
    Visual representation of one GridForge Line.

    Parameters
    ----------
    object_id:
        Authoritative identifier of the represented Line.

    start:
        Initial scene-space start point.

    end:
        Initial scene-space end point.

    model:
        Optional authoritative Line object being projected.

        The object is not mutated by LineItem.
    """

    # ========================================================
    # VISUAL DEFAULTS
    # ========================================================

    DEFAULT_LINE_WIDTH = 2.0

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        object_id: Any,
        start: Optional[QPointF] = None,
        end: Optional[QPointF] = None,
        model: Optional[Any] = None,
    ) -> None:
        if object_id is None:
            raise ValueError(
                "object_id must not be None."
            )

        if start is None:
            start = QPointF(
                0.0,
                0.0,
            )

        if end is None:
            end = QPointF(
                0.0,
                0.0,
            )

        self._validate_point(
            start,
            "start",
        )

        self._validate_point(
            end,
            "end",
        )

        super().__init__(
            QLineF(
                start,
                end,
            )
        )

        self.object_id = object_id
        self.model = model

        self.position_changed = Signal(
            object
        )

        self.geometry_changed = Signal(
            object
        )

        self.setFlag(
            QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        self.setFlag(
            QGraphicsLineItem.GraphicsItemFlag.ItemSendsGeometryChanges,
            True,
        )

        self.setPen(
            QPen(
                Qt.GlobalColor.black,
                self.DEFAULT_LINE_WIDTH,
            )
        )

        self._start = QPointF(
            start.x(),
            start.y(),
        )

        self._end = QPointF(
            end.x(),
            end.y(),
        )

    # ========================================================
    # IDENTITY
    # ========================================================

    def get_object_id(
        self,
    ) -> Any:
        """
        Return the authoritative ID of the represented Line.
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

        The returned object is not owned by LineItem.
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
    # ENDPOINT ACCESS
    # ========================================================

    def get_start(
        self,
    ) -> QPointF:
        """
        Return the current start point in scene coordinates.
        """

        line = self.line()

        return QPointF(
            line.p1().x(),
            line.p1().y(),
        )

    # --------------------------------------------------------

    def get_end(
        self,
    ) -> QPointF:
        """
        Return the current end point in scene coordinates.
        """

        line = self.line()

        return QPointF(
            line.p2().x(),
            line.p2().y(),
        )

    # --------------------------------------------------------

    def get_endpoints(
        self,
    ) -> tuple[QPointF, QPointF]:
        """
        Return the current start and end points.
        """

        return (
            self.get_start(),
            self.get_end(),
        )

    # ========================================================
    # ENDPOINT MUTATION
    # ========================================================

    def set_endpoints(
        self,
        start: QPointF,
        end: QPointF,
        *,
        emit: bool = True,
    ) -> None:
        """
        Set both visual endpoints.

        This modifies only presentation geometry.

        Parameters
        ----------
        start:
            New start point.

        end:
            New end point.

        emit:
            Whether to emit ``geometry_changed``.
        """

        self._validate_point(
            start,
            "start",
        )

        self._validate_point(
            end,
            "end",
        )

        new_start = QPointF(
            start.x(),
            start.y(),
        )

        new_end = QPointF(
            end.x(),
            end.y(),
        )

        old_start = self.get_start()
        old_end = self.get_end()

        self.prepareGeometryChange()

        self.setLine(
            QLineF(
                new_start,
                new_end,
            )
        )

        self._start = new_start
        self._end = new_end

        changed = (
            old_start.x()
            != new_start.x()
            or old_start.y()
            != new_start.y()
            or old_end.x()
            != new_end.x()
            or old_end.y()
            != new_end.y()
        )

        if emit and changed:
            self.geometry_changed.emit(
                (
                    new_start,
                    new_end,
                )
            )

    # --------------------------------------------------------

    def set_start(
        self,
        start: QPointF,
    ) -> None:
        """
        Change only the visual start point.
        """

        self.set_endpoints(
            start,
            self.get_end(),
        )

    # --------------------------------------------------------

    def set_end(
        self,
        end: QPointF,
    ) -> None:
        """
        Change only the visual end point.
        """

        self.set_endpoints(
            self.get_start(),
            end,
        )

    # ========================================================
    # POSITION
    # ========================================================

    def get_scene_position(
        self,
    ) -> QPointF:
        """
        Return the item's scene position.

        Normally LineItem geometry is represented directly by
        its line endpoints, while the item's position remains
        the Qt graphics-item transform position.
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
    ) -> None:
        """
        Set the item's Qt scene position.

        This changes only the graphical projection.
        """

        self._validate_point(
            position,
            "position",
        )

        old_position = self.get_scene_position()

        self.setPos(
            QPointF(
                position.x(),
                position.y(),
            )
        )

        if (
            old_position.x()
            != position.x()
            or old_position.y()
            != position.y()
        ):
            self.position_changed.emit(
                QPointF(
                    position.x(),
                    position.y(),
                )
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

        No Core state is modified here.
        """

        position_change = getattr(
            QGraphicsLineItem.GraphicsItemChange,
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
            and value is not None
        ):
            self._validate_point(
                value,
                "position change",
            )

            self.position_changed.emit(
                QPointF(
                    value.x(),
                    value.y(),
                )
            )

        return result

    # ========================================================
    # VISUAL PRESENTATION
    # ========================================================

    def set_pen(
        self,
        pen: QPen,
    ) -> None:
        """
        Set the visual line pen.
        """

        if pen is None:
            raise ValueError(
                "pen must not be None."
            )

        self.setPen(
            pen
        )

    # --------------------------------------------------------

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
    # GEOMETRIC INFORMATION
    # ========================================================

    def length(
        self,
    ) -> float:
        """
        Return the geometric length of the visual line.

        This is a scene-space geometric measurement only.

        It is not an electrical line length.
        """

        return self.line().length()

    # --------------------------------------------------------

    def bounding_rect_scene(
        self,
    ) -> Any:
        """
        Return the line's scene-space bounding rectangle.
        """

        return self.mapRectToScene(
            self.boundingRect()
        )

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic UI state.
        """

        start = self.get_start()
        end = self.get_end()

        return {
            "object_id": self.object_id,
            "start": start,
            "end": end,
            "length": self.length(),
            "position": self.get_scene_position(),
            "selected": self.is_visual_selected(),
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

        start = self.get_start()
        end = self.get_end()

        return (
            "LineItem("
            f"id={self.object_id!r}, "
            f"start=("
            f"{start.x():.2f}, "
            f"{start.y():.2f}"
            "), "
            f"end=("
            f"{end.x():.2f}, "
            f"{end.y():.2f}"
            "), "
            f"selected={self.is_visual_selected()}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "LineItem",
]
