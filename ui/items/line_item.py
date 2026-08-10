# ============================================================
# File: ui/items/line_item.py
# GridForge Line Graphics Item
# ============================================================
#
# PURPOSE
# -------
# Provides the QGraphicsItem representation of a GridForge
# Line model object.
#
#
# ARCHITECTURE
# ------------
#
#                  Core Line Model
#                         │
#                         ▼
#                   LineRenderer
#                         │
#                         ▼
#                      LineItem
#                         │
#                         ▼
#                  QGraphicsScene
#
#
# RESPONSIBILITIES
# ----------------
#
# LineItem is responsible for:
#
#     - displaying a line between two buses
#     - resolving endpoint positions
#     - selection visual feedback
#     - hover visual feedback
#     - exposing the associated Line model
#
#
# LineItem does NOT:
#
#     - create Line objects
#     - modify topology
#     - perform power-flow calculations
#     - perform snapping
#     - decide which tool is active
#     - move buses
#     - manage the graphics scene
#
#
# STATE OWNERSHIP
# --------------
#
# Persistent selection belongs to:
#
#     Controller.selected_ids
#
# LineItem only represents that state visually.
#
#
# MODEL OWNERSHIP
# --------------
#
# The Line model stores:
#
#     line.from_bus
#     line.to_bus
#
# These are bus IDs.
#
# LineItem resolves those IDs through:
#
#     model.graph.buses
#
# The model remains authoritative.
#
#
# QT RULE
# -------
#
# All Qt imports MUST come through:
#
#     ui.core.qt
#
# Never import PySide6, PyQt6, or PyQt5 directly.
#
# ============================================================

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QColor,
    QGraphicsLineItem,
    QLineF,
    QPen,
)


class LineItem(QGraphicsLineItem):
    """
    Graphical representation of a GridForge Line.

    The LineItem is a view object only.

    The underlying Line model remains the authoritative source
    of topology and electrical data.
    """

    # ========================================================
    # VISUAL CONSTANTS
    # ========================================================

    NORMAL_WIDTH = 2.0
    HOVER_WIDTH = 3.0
    SELECTED_WIDTH = 4.0

    NORMAL_COLOR = QColor(40, 40, 40)
    HOVER_COLOR = QColor(255, 200, 0)
    SELECTED_COLOR = QColor(0, 120, 255)

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        line: Any,
        model: Any,
    ) -> None:
        """
        Create a graphical LineItem.

        Parameters
        ----------
        line:
            GridForge Line model object.

        model:
            Complete GridForge model.

        The model is used only for resolving the endpoint buses.
        """

        super().__init__()

        self.line_model = line
        self.model = model

        # Optional Controller reference.
        #
        # LineRenderer may inject this later through
        # set_controller().
        self.controller: Optional[Any] = None

        # ----------------------------------------------------
        # Transient visual state.
        # ----------------------------------------------------

        self._hovered = False

        # ----------------------------------------------------
        # Enable selection.
        # ----------------------------------------------------

        self.setFlag(
            QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        # ----------------------------------------------------
        # Enable hover events.
        # ----------------------------------------------------

        self.setAcceptHoverEvents(True)

        # ----------------------------------------------------
        # Build initial geometry.
        # ----------------------------------------------------

        self._sync_geometry()

        # ----------------------------------------------------
        # Apply initial visual appearance.
        # ----------------------------------------------------

        self._apply_visual_state()

    # ========================================================
    # CONTROLLER
    # ========================================================

    def set_controller(
        self,
        controller: Any,
    ) -> None:
        """
        Attach the GridForge Controller.

        This method intentionally does not require the
        Controller during initial construction.

        That keeps LineRenderer flexible.
        """

        self.controller = controller

    # ========================================================
    # ENDPOINT RESOLUTION
    # ========================================================

    def _get_bus(
        self,
        bus_id: str,
    ) -> Optional[Any]:
        """
        Resolve a bus ID to the corresponding Bus model object.

        Returns
        -------
        Bus | None

        None is returned when the endpoint cannot be resolved.

        This method performs read-only model access.
        """

        graph = getattr(
            self.model,
            "graph",
            None,
        )

        if graph is None:
            return None

        buses = getattr(
            graph,
            "buses",
            None,
        )

        if buses is None:
            return None

        return buses.get(bus_id)

    # --------------------------------------------------------

    def _get_endpoint_buses(self) -> tuple[
        Optional[Any],
        Optional[Any],
    ]:
        """
        Resolve both endpoint buses of the Line.

        Returns:

            (from_bus, to_bus)
        """

        from_bus = self._get_bus(
            self.line_model.from_bus
        )

        to_bus = self._get_bus(
            self.line_model.to_bus
        )

        return from_bus, to_bus

    # ========================================================
    # GEOMETRY
    # ========================================================

    def _sync_geometry(self) -> None:
        """
        Synchronize the graphics geometry with the model.

        The Line model contains endpoint IDs rather than
        graphics coordinates.

        Therefore the graphical line is calculated from the
        current positions of the endpoint Bus objects.
        """

        from_bus, to_bus = self._get_endpoint_buses()

        # ----------------------------------------------------
        # Invalid topology reference.
        # ----------------------------------------------------
        #
        # A line whose endpoint cannot be resolved should not
        # crash the entire UI.
        #
        # The line is simply rendered as zero-length until the
        # model becomes valid.
        # ----------------------------------------------------

        if from_bus is None or to_bus is None:

            self.setLine(
                QLineF()
            )

            return

        # ----------------------------------------------------
        # Create graphical line from bus coordinates.
        # ----------------------------------------------------

        self.setLine(
            QLineF(
                float(from_bus.x),
                float(from_bus.y),
                float(to_bus.x),
                float(to_bus.y),
            )
        )

    # ========================================================
    # HOVER
    # ========================================================

    def hoverEnterEvent(
        self,
        event: Any,
    ) -> None:
        """
        Highlight the line when the mouse enters it.
        """

        self._hovered = True

        self._apply_visual_state()

        super().hoverEnterEvent(event)

    # --------------------------------------------------------

    def hoverLeaveEvent(
        self,
        event: Any,
    ) -> None:
        """
        Remove hover highlighting when the mouse leaves.
        """

        self._hovered = False

        self._apply_visual_state()

        super().hoverLeaveEvent(event)

    # ========================================================
    # SELECTION
    # ========================================================

    def mousePressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Handle selection of the Line.

        Persistent selection is delegated to Controller.
        """

        if self.controller is not None:

            modifiers = event.modifiers()

            multi_select = bool(
                modifiers
                & (
                    Qt.KeyboardModifier.ControlModifier
                    | Qt.KeyboardModifier.ShiftModifier
                )
            )

            self.controller.select(
                self.line_model.id,
                multi=multi_select,
            )

        super().mousePressEvent(event)

    # ========================================================
    # VISUAL STATE
    # ========================================================

    def _apply_visual_state(self) -> None:
        """
        Apply the appropriate visual appearance.

        Priority:

            Selected
                ↓
            Hover
                ↓
            Normal
        """

        # ----------------------------------------------------
        # Selected
        # ----------------------------------------------------

        if self.isSelected():

            self.setPen(
                QPen(
                    self.SELECTED_COLOR,
                    self.SELECTED_WIDTH,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )

            return

        # ----------------------------------------------------
        # Hover
        # ----------------------------------------------------

        if self._hovered:

            self.setPen(
                QPen(
                    self.HOVER_COLOR,
                    self.HOVER_WIDTH,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )

            return

        # ----------------------------------------------------
        # Normal
        # ----------------------------------------------------

        self.setPen(
            QPen(
                self.NORMAL_COLOR,
                self.NORMAL_WIDTH,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )

    # ========================================================
    # QT SELECTION SYNCHRONIZATION
    # ========================================================

    def itemChange(
        self,
        change: Any,
        value: Any,
    ) -> Any:
        """
        React to Qt selection-state changes.

        This keeps the line appearance synchronized with the
        QGraphicsItem selection state.
        """

        result = super().itemChange(
            change,
            value,
        )

        if (
            change
            == QGraphicsLineItem.GraphicsItemChange.ItemSelectedChange
        ):
            self._apply_visual_state()

        return result

    # ========================================================
    # MODEL SYNCHRONIZATION
    # ========================================================

    def refresh_from_model(self) -> None:
        """
        Refresh line geometry from the current model.

        This method is intentionally read-only with respect
        to the model.

        It will become useful when the canvas moves to
        incremental rendering.
        """

        self._sync_geometry()

    # ========================================================
    # MODEL ACCESS
    # ========================================================

    @property
    def model_object(self) -> Any:
        """
        Return the underlying Line model object.
        """

        return self.line_model

    # --------------------------------------------------------

    @property
    def object_id(self) -> str:
        """
        Return the model ID represented by this graphics item.
        """

        return self.line_model.id

    # ========================================================
    # ENDPOINT ACCESS
    # ========================================================

    @property
    def from_bus(self) -> Optional[Any]:
        """
        Return the resolved 'from' Bus model object.
        """

        return self._get_bus(
            self.line_model.from_bus
        )

    # --------------------------------------------------------

    @property
    def to_bus(self) -> Optional[Any]:
        """
        Return the resolved 'to' Bus model object.
        """

        return self._get_bus(
            self.line_model.to_bus
        )

    # ========================================================
    # DEBUG
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "LineItem("
            f"id={self.line_model.id!r}, "
            f"from={self.line_model.from_bus!r}, "
            f"to={self.line_model.to_bus!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "LineItem",
]
```
