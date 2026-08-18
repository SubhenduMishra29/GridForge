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

LineItem is a presentation projection only.

Responsibilities
----------------
LineItem:

    - represents one authoritative Line visually;
    - retains the authoritative Line model reference;
    - retains the UI Controller reference;
    - resolves visual endpoint coordinates from the
      authoritative application model;
    - provides visual selection;
    - provides line geometry required by renderers;
    - reports selection requests through the Controller.

LineItem does NOT:

    - own the Line engineering object;
    - create or delete Core objects;
    - modify Core state directly;
    - determine electrical topology;
    - perform snapping;
    - perform electrical calculations;
    - perform connection validation;
    - implement LineTool behavior;
    - own persistent application selection;
    - move itself interactively;
    - maintain an independent engineering endpoint state.

Topology
--------
The authoritative electrical connection remains in GridForge
Core.

The LineItem visual geometry is derived from the authoritative
model through the Controller/application model.

The graphics item therefore never becomes the source of
electrical connectivity.

Selection
---------
QGraphicsItem selection is a visual projection.

Persistent application selection remains owned by the
Controller/SelectionManager.

Selection requests are routed through:

    LineItem
       │
       ▼
    Controller
       │
       ▼
    SelectionManager / application state

Movement
--------
LineItem is intentionally NOT movable.

Line geometry changes are authoritative application updates,
not arbitrary QGraphicsItem movement.

Qt Architecture
---------------
All Qt dependencies are imported exclusively through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
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

    Parameters
    ----------
    line:
        Authoritative GridForge Line model object.

    controller:
        UI/application controller responsible for application
        operations and selection state.

    Notes
    -----
    LineItem deliberately remains a QGraphicsLineItem instead of
    inheriting from BaseItem because Qt's graphics-item hierarchy
    requires the specialized QGraphicsLineItem base for native
    line geometry behavior.
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

        # ----------------------------------------------------
        # Selection is allowed visually, but movement is
        # deliberately prohibited.
        # ----------------------------------------------------

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
            False,
        )

        # ----------------------------------------------------
        # Default presentation.
        #
        # Concrete renderers may replace this presentation.
        # ----------------------------------------------------

        self.setPen(
            QPen(
                Qt.GlobalColor.black,
                self.DEFAULT_LINE_WIDTH,
            )
        )

        # ----------------------------------------------------
        # Initialize geometry from the authoritative model.
        # ----------------------------------------------------

        self.refresh_geometry()

    # ========================================================
    # IDENTITY
    # ========================================================

    @property
    def object_id(self) -> Any:
        """
        Return the authoritative Line identifier.
        """

        return self.line_model.id

    # --------------------------------------------------------

    def get_object_id(self) -> Any:
        """
        Return the authoritative Line identifier.
        """

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
        Resolve the visual endpoints from the authoritative
        application model.

        Endpoint positions are obtained through the controller's
        authoritative model graph.

        Returns
        -------
        tuple[QPointF, QPointF]
            Start and end scene positions.
        """

        graph = self.controller.model.graph
        buses = graph.buses

        start_bus = buses[self.line_model.from_bus]
        end_bus = buses[self.line_model.to_bus]

        start_position = start_bus.position
        end_position = end_bus.position

        return (
            QPointF(
                start_position.x,
                start_position.y,
            ),
            QPointF(
                end_position.x,
                end_position.y,
            ),
        )

    # --------------------------------------------------------

    def refresh_geometry(self) -> None:
        """
        Refresh the visual line geometry from authoritative
        application state.

        This method performs presentation projection only.

        No Core state is modified.
        """

        start, end = self._resolve_endpoint_positions()

        self.prepareGeometryChange()

        self.setLine(
            QLineF(
                start,
                end,
            )
        )

    # --------------------------------------------------------

    def get_start(self) -> QPointF:
        """
        Return the current visual start point.
        """

        line = self.line()

        return QPointF(
            line.p1().x(),
            line.p1().y(),
        )

    # --------------------------------------------------------

    def get_end(self) -> QPointF:
        """
        Return the current visual end point.
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
        Return the current visual endpoints.
        """

        return (
            self.get_start(),
            self.get_end(),
        )

    # ========================================================
    # GEOMETRY INFORMATION
    # ========================================================

    def length(self) -> float:
        """
        Return the visual geometric length.

        This is presentation geometry only.

        It is NOT the electrical line length stored by Core.
        """

        return self.line().length()

    # --------------------------------------------------------

    def bounding_rect_scene(self) -> Any:
        """
        Return the line's bounding rectangle in scene
        coordinates.
        """

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
        Request application-level selection through the
        Controller.

        LineItem does not own persistent selection state.
        """

        if not isinstance(multi, bool):
            raise TypeError(
                "multi must be a bool."
            )

        self.controller.select(
            self.object_id,
            multi=multi,
        )

    # --------------------------------------------------------

    def itemChange(
        self,
        change: Any,
        value: Any,
    ) -> Any:
        """
        Observe visual selection changes.

        Selection changes are routed to the Controller.

        No engineering state is modified directly here.
        """

        selection_change = getattr(
            QGraphicsItem.GraphicsItemChange,
            "ItemSelectedChange",
            None,
        )

        if (
            selection_change is not None
            and change == selection_change
            and value
        ):
            # The visual selection change is allowed to occur
            # through Qt. Persistent application selection is
            # handled by the Controller.
            pass

        return super().itemChange(
            change,
            value,
        )

    # --------------------------------------------------------

    def set_visual_selected(
        self,
        selected: bool,
    ) -> None:
        """
        Set the Qt visual selection projection.

        This does not alter application/Core selection state.
        """

        if not isinstance(selected, bool):
            raise TypeError(
                "selected must be a bool."
            )

        self.setSelected(selected)

    # --------------------------------------------------------

    def is_visual_selected(self) -> bool:
        """
        Return the current Qt visual selection state.
        """

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
        """
        Set the visual line pen.
        """

        if pen is None:
            raise ValueError(
                "pen must not be None."
            )

        self.setPen(pen)

    # ========================================================
    # STATE
    # ========================================================

    def get_state(self) -> dict[str, Any]:
        """
        Return a diagnostic presentation snapshot.

        The returned state does not become authoritative
        engineering state.
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
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
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
