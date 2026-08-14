# ============================================================
# File: ui/items/bus_item.py
# GridForge Bus Graphics Item
# ============================================================
#
# PURPOSE
# -------
# Provides the QGraphicsItem representation of a GridForge
# Bus model object.
#
#
# ARCHITECTURE
# ------------
#
#             Core Bus Model
#                    │
#                    ▼
#               BusRenderer
#                    │
#                    ▼
#                 BusItem
#                    │
#                    ▼
#             QGraphicsScene
#
#
# RESPONSIBILITIES
# ----------------
#
# BusItem is responsible for:
#
#     - displaying a bus
#     - maintaining its graphical geometry
#     - hover visual feedback
#     - selection visual feedback
#     - exposing the associated model object
#     - forwarding selection requests to the Controller
#
#
# BusItem does NOT:
#
#     - create or modify Bus model objects
#     - perform electrical calculations
#     - perform snapping
#     - decide which tool is active
#     - create lines
#     - render other model elements
#     - own persistent application selection
#
#
# STATE OWNERSHIP
# ---------------
#
# Persistent application selection belongs to the Controller.
#
# QGraphicsItem selection state is treated as the graphical
# representation of that application state.
#
# The Controller/UI synchronization layer is responsible for
# keeping the two states consistent.
#
#
# HOVER
# -----
#
# Hover is transient graphics state and belongs here.
#
#
# QT RULE
# -------
#
# All Qt imports MUST come through:
#
#     ui.core.qt
#
# This file must never import PySide6, PyQt6, or PyQt5 directly.
#
# ============================================================

from __future__ import annotations

from typing import Any

from ui.core.qt import (
    QBrush,
    QColor,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QPen,
    Qt,
)


class BusItem(QGraphicsEllipseItem):
    """
    Graphical representation of a GridForge Bus.

    The underlying model object remains authoritative.

    The item owns only presentation and transient graphics state.
    """

    # ========================================================
    # VISUAL CONSTANTS
    # ========================================================

    RADIUS = 6.0

    NORMAL_PEN_WIDTH = 1.0
    HOVER_PEN_WIDTH = 2.0
    SELECTED_PEN_WIDTH = 2.5

    # ========================================================
    # COLORS
    # ========================================================

    NORMAL_OUTLINE = QColor(0, 0, 0)
    NORMAL_FILL = QColor(255, 255, 255)

    HOVER_OUTLINE = QColor(255, 200, 0)
    HOVER_FILL = QColor(255, 255, 180)

    SELECTED_OUTLINE = QColor(0, 120, 255)
    SELECTED_FILL = QColor(210, 230, 255)

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        bus: Any,
        controller: Any,
    ) -> None:
        """
        Create a graphical BusItem.

        Parameters
        ----------
        bus:
            GridForge Bus model object.

        controller:
            GridForge application Controller.

        The model object is stored by reference and remains the
        authoritative source of engineering state.
        """

        super().__init__(
            -self.RADIUS,
            -self.RADIUS,
            self.RADIUS * 2.0,
            self.RADIUS * 2.0,
        )

        self.bus = bus
        self.controller = controller

        # ----------------------------------------------------
        # Selection is permitted at the Qt graphics level.
        #
        # Persistent application selection remains owned by
        # Controller.
        # ----------------------------------------------------

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        # ----------------------------------------------------
        # Direct graphical movement is deliberately disabled.
        #
        # Model-backed movement must pass through the proper
        # GridForge interaction/command path.
        # ----------------------------------------------------

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
            False,
        )

        # ----------------------------------------------------
        # Enable transient hover feedback.
        # ----------------------------------------------------

        self.setAcceptHoverEvents(True)

        self._hovered = False

        # ----------------------------------------------------
        # Initial synchronization from authoritative model.
        # ----------------------------------------------------

        self._sync_position_from_model()

        # ----------------------------------------------------
        # Initial visual state.
        # ----------------------------------------------------

        self._apply_visual_state()

    # ========================================================
    # MODEL SYNCHRONIZATION
    # ========================================================

    def _sync_position_from_model(self) -> None:
        """
        Synchronize graphical position from the Bus model.

        The model remains authoritative.
        """

        self.setPos(
            float(self.bus.x),
            float(self.bus.y),
        )

    # ========================================================
    # HOVER HANDLING
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
    # SELECTION REQUEST
    # ========================================================

    def mousePressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward a selection request to the Controller.

        The Controller remains the authoritative owner of
        persistent application selection.
        """

        modifiers = event.modifiers()

        multi_select = bool(
            modifiers
            & (
                Qt.KeyboardModifier.ControlModifier
                | Qt.KeyboardModifier.ShiftModifier
            )
        )

        self.controller.select(
            self.bus.id,
            multi=multi_select,
        )

        # Allow the Qt graphics system to process the event.
        #
        # The Controller/UI synchronization layer remains
        # responsible for authoritative selection state.
        super().mousePressEvent(event)

    # ========================================================
    # VISUAL STATE
    # ========================================================

    def _apply_visual_state(self) -> None:
        """
        Apply the current graphical state.

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
                    self.SELECTED_OUTLINE,
                    self.SELECTED_PEN_WIDTH,
                )
            )

            self.setBrush(
                QBrush(self.SELECTED_FILL)
            )

            return

        if self._hovered:
            self.setPen(
                QPen(
                    self.HOVER_OUTLINE,
                    self.HOVER_PEN_WIDTH,
                )
            )

            self.setBrush(
                QBrush(self.HOVER_FILL)
            )

            return

        self.setPen(
            QPen(
                self.NORMAL_OUTLINE,
                self.NORMAL_PEN_WIDTH,
            )
        )

        self.setBrush(
            QBrush(self.NORMAL_FILL)
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
        React to Qt graphics-item state changes.

        Selection changes update only the visual representation.
        They do not mutate the Core model.
        """

        result = super().itemChange(
            change,
            value,
        )

        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._apply_visual_state()

        return result

    # ========================================================
    # MODEL ACCESS
    # ========================================================

    @property
    def model_object(self) -> Any:
        """
        Return the underlying Bus model object.
        """

        return self.bus

    # ========================================================
    # IDENTIFICATION
    # ========================================================

    @property
    def object_id(self) -> str:
        """
        Return the model ID represented by this graphics item.
        """

        return self.bus.id

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "BusItem("
            f"id={self.bus.id!r}, "
            f"x={self.bus.x}, "
            f"y={self.bus.y}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "BusItem",
]
