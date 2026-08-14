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
#     - refreshing graphical geometry from the model
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
#     - mutate the Core model
#
#
# STATE OWNERSHIP
# ---------------
#
# Persistent application selection belongs to the Controller.
#
# The QGraphicsItem selection state is only its graphical
# representation.
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
# The LineItem resolves those IDs through the authoritative
# application model exposed by the Controller.
#
# All access is read-only.
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
    QGraphicsItem,
    QGraphicsLineItem,
    QLineF,
    QPen,
    Qt,
)


class LineItem(QGraphicsLineItem):
    """
    Graphical representation of a GridForge Line.

    The LineItem is a presentation object only.

    The underlying Line model remains authoritative for topology
    and electrical state.
    """

    # ========================================================
    # VISUAL CONSTANTS
    # ========================================================

    NORMAL_WIDTH = 2.0
    HOVER_WIDTH = 3.0
    SELECTED_WIDTH = 4.0

    NORMAL_COLOR = Qt.GlobalColor.black
    HOVER_COLOR = Qt.GlobalColor.yellow
    SELECTED_COLOR = Qt.GlobalColor.blue

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        line: Any,
        controller: Any,
    ) -> None:
        """
        Create a graphical LineItem.

        Parameters
        ----------
        line:
            GridForge Line model object.

        controller:
            GridForge application Controller.

        The Line model and application model are accessed
        read-only by this presentation object.
        """

        super().__init__()

        self.line_model = line
        self.controller = controller

        # ----------------------------------------------------
        # Transient graphics state.
        # ----------------------------------------------------

        self._hovered = False

        # ----------------------------------------------------
        # Selection.
        #
        # Direct movement is intentionally disabled.
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
        # Hover feedback.
        # ----------------------------------------------------

        self.setAcceptHoverEvents(True)

        # ----------------------------------------------------
        # Initial geometry and appearance.
        # ----------------------------------------------------

        self._sync_geometry()
        self._apply_visual_state()

    # ========================================================
    # AUTHORITATIVE MODEL ACCESS
    # ========================================================

    def _get_model(self) -> Optional[Any]:
        """
        Return the authoritative application model.

        The access is read-only from the LineItem perspective.
        """

        if self.controller is None:
            return None

        return getattr(
            self.controller,
            "model",
            None,
        )

    # ========================================================
    # ENDPOINT RESOLUTION
    # ========================================================

    def _get_bus(
        self,
        bus_id: str,
    ) -> Optional[Any]:
        """
        Resolve a bus ID to its corresponding Bus model object.

        Returns None when the application model or endpoint
        cannot currently be resolved.
        """

        model = self._get_model()

        if model is None:
            return None

        graph = getattr(
            model,
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

    def _get_endpoint_buses(
        self,
    ) -> tuple[Optional[Any], Optional[Any]]:
        """
        Resolve both endpoint buses of the Line.

        Returns
        -------
        tuple
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
        Synchronize graphical geometry from the authoritative
        model.

        The Line stores endpoint IDs. The endpoint Bus objects
        provide their current graphical coordinates.
        """

        from_bus, to_bus = self._get_endpoint_buses()

        # ----------------------------------------------------
        # Endpoint not currently resolvable.
        #
        # Keep the item valid without inventing geometry.
        # ----------------------------------------------------

        if from_bus is None or to_bus is None:
            self.setLine(QLineF())
            return

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
        Enter transient hover state.
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
        Leave transient hover state.
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
        Forward a selection request to the Controller.

        Persistent application selection remains outside the
        graphics item.
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
        Apply the current visual state.

        Priority:

            Selected
                ↓
            Hover
                ↓
            Normal
        """

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
        React to QGraphicsItem selection-state changes.
        """

        result = super().itemChange(
            change,
            value,
        )

        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._apply_visual_state()

        return result

    # ========================================================
    # MODEL SYNCHRONIZATION
    # ========================================================

    def refresh_from_model(self) -> None:
        """
        Refresh graphical geometry from the current model state.

        This method performs no model mutation.
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
        Return the currently resolved 'from' Bus model object.
        """

        return self._get_bus(
            self.line_model.from_bus
        )

    # --------------------------------------------------------

    @property
    def to_bus(self) -> Optional[Any]:
        """
        Return the currently resolved 'to' Bus model object.
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
