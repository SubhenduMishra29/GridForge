# ============================================================
# File: ui/items/line_item.py
# GridForge V2 — Line Graphics Item
# ============================================================

"""
Visual projection of an authoritative GridForge Line object.

Architecture
------------

    GridForge Core / Line
              │
              ▼
        Controller
              │
              ▼
        LineItem
              │
              ▼
         GridScene
              │
              ▼
        GraphicsView

LineItem is a presentation projection only.

Responsibilities
----------------
LineItem:

    - represents one authoritative Line visually;
    - retains the authoritative Line model reference;
    - retains the UI Controller reference;
    - obtains visual endpoint coordinates through the
      Controller's public presentation contract;
    - provides visual selection;
    - provides native line geometry;
    - provides visual refresh;
    - does not own engineering state.

LineItem does NOT:

    - own the Line engineering object;
    - access controller.model internals;
    - access graph.buses directly;
    - create or delete Core objects;
    - modify Core state directly;
    - determine electrical topology;
    - perform snapping;
    - perform electrical calculations;
    - perform connection validation;
    - implement LineTool behavior;
    - own persistent application selection;
    - move itself interactively.

Qt Architecture
---------------
All Qt dependencies are imported exclusively through:

    ui.core.qt
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
    """
    Visual representation of one authoritative GridForge Line.
    """

    DEFAULT_LINE_WIDTH = 2.0

    def __init__(
        self,
        line: Any,
        controller: Any,
    ) -> None:
        if line is None:
            raise ValueError(
                "line must not be None."
            )

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        super().__init__(
            QLineF(
                QPointF(0.0, 0.0),
                QPointF(0.0, 0.0),
            )
        )

        self.line_model = line
        self.controller = controller

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
            False,
        )

        self.setPen(
            QPen(
                Qt.GlobalColor.black,
                self.DEFAULT_LINE_WIDTH,
            )
        )

        self.refresh_geometry()

    # ========================================================
    # IDENTITY
    # ========================================================

    @property
    def object_id(self) -> Any:
        """Return the authoritative Line identifier."""

        return self.line_model.id

    # --------------------------------------------------------

    def get_object_id(self) -> Any:
        """Return the authoritative Line identifier."""

        return self.object_id

    # ========================================================
    # MODEL
    # ========================================================

    def get_model(self) -> Any:
        """
        Return the authoritative Line model reference.

        The LineItem does not own or mutate this object.
        """

        return self.line_model

    # ========================================================
    # GEOMETRY
    # ========================================================

    def _resolve_endpoint_positions(
        self,
    ) -> tuple[QPointF, QPointF]:
        """
        Obtain endpoint positions through the Controller's
        public presentation contract.

        LineItem deliberately does not access:

            controller.model.graph
            graph.buses
            Core topology internals
        """

        positions = (
            self.controller.get_line_endpoint_positions(
                self.line_model
            )
        )

        if not isinstance(
            positions,
            tuple,
        ):
            raise TypeError(
                "Controller must return a tuple of two QPointF "
                "objects."
            )

        if len(positions) != 2:
            raise ValueError(
                "Controller must return exactly two endpoints."
            )

        start, end = positions

        self._validate_point(
            start,
            "start",
        )

        self._validate_point(
            end,
            "end",
        )

        return (
            QPointF(
                start.x(),
                start.y(),
            ),
            QPointF(
                end.x(),
                end.y(),
            ),
        )

    # --------------------------------------------------------

    def refresh_geometry(self) -> None:
        """
        Refresh visual geometry from authoritative application
        state.

        No Core state is modified.
        """

        start, end = (
            self._resolve_endpoint_positions()
        )

        self.prepareGeometryChange()

        self.setLine(
            QLineF(
                start,
                end,
            )
        )

    # --------------------------------------------------------

    def get_start(self) -> QPointF:
        """Return the current visual start point."""

        line = self.line()

        return QPointF(
            line.p1().x(),
            line.p1().y(),
        )

    # --------------------------------------------------------

    def get_end(self) -> QPointF:
        """Return the current visual end point."""

        line = self.line()

        return QPointF(
            line.p2().x(),
            line.p2().y(),
        )

    # --------------------------------------------------------

    def get_endpoints(
        self,
    ) -> tuple[QPointF, QPointF]:
        """Return the current visual endpoints."""

        return (
            self.get_start(),
            self.get_end(),
        )

    # ========================================================
    # GEOMETRY INFORMATION
    # ========================================================

    def length(self) -> float:
        """
        Return visual geometric length.

        This is presentation geometry only and is not the
        electrical Line length stored by Core.
        """

        return self.line().length()

    # --------------------------------------------------------

    def bounding_rect_scene(self) -> Any:
        """Return the line bounding rectangle in scene coordinates."""

        return self.mapRectToScene(
            self.boundingRect()
        )

    # ========================================================
    # SELECTION
    # ========================================================

    def request_selection(
        self,
        *,
        multi: bool = False,
    ) -> None:
        """
        Request application-level selection through Controller.
        """

        if not isinstance(
            multi,
            bool,
        ):
            raise TypeError(
                "multi must be a bool."
            )

        self.controller.select(
            self.object_id,
            multi=multi,
        )

    # --------------------------------------------------------

    def set_visual_selected(
        self,
        selected: bool,
    ) -> None:
        """
        Set the Qt visual selection projection only.
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

    def is_visual_selected(self) -> bool:
        """Return the current Qt visual selection state."""

        return bool(
            self.isSelected()
        )

    # ========================================================
    # PRESENTATION
    # ========================================================

    def set_pen(
        self,
        pen: QPen,
    ) -> None:
        """Set the visual line pen."""

        if pen is None:
            raise ValueError(
                "pen must not be None."
            )

        self.setPen(
            pen
        )

    # ========================================================
    # STATE
    # ========================================================

    def get_state(self) -> dict[str, Any]:
        """
        Return a diagnostic presentation snapshot.
        """

        start = self.get_start()
        end = self.get_end()

        return {
            "object_id": self.object_id,
            "start": start,
            "end": end,
            "length": self.length(),
            "selected": self.is_visual_selected(),
            "movable": False,
            "has_model": self.line_model is not None,
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_point(
        point: Any,
        name: str,
    ) -> None:
        """Validate a QPointF-compatible object."""

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
        """Return a concise diagnostic representation."""

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
