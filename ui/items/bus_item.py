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
#     - notifying the Controller when selected
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
#
#
# STATE OWNERSHIP
# --------------
#
# Persistent application selection belongs to:
#
#     Controller.selected_ids
#
# BusItem.selected state is therefore only a visual
# representation of Controller state.
#
#
# HOVER
# -----
#
# Hover is transient graphics state and belongs here.
#
# This avoids forcing BusRenderer to know which tool is active.
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
    QPen,
    Qt,
)


class BusItem(QGraphicsEllipseItem):
    """
    Graphical representation of a GridForge Bus.

    The BusItem is intentionally lightweight.

    The underlying model object remains the authoritative source
    of bus data.
    """

    # ========================================================
    # VISUAL CONSTANTS
    # ========================================================

    # Radius of the normal bus symbol in scene units.
    RADIUS = 6.0

    # Width of the normal outline.
    NORMAL_PEN_WIDTH = 1.0

    # Width of the highlighted outline.
    HOVER_PEN_WIDTH = 2.0

    # Width of the selected outline.
    SELECTED_PEN_WIDTH = 2.5

    # ========================================================
    # COLORS
    # ========================================================
    #
    # Centralized here so visual state can evolve without
    # changing BusRenderer.
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
            GridForge Controller.

        The model object is stored by reference. The BusItem does
        not copy or replace the model data.
        """

        self.bus = bus
        self.controller = controller

        # ----------------------------------------------------
        # Initialize geometry from the model.
        # ----------------------------------------------------

        super().__init__(
            -self.RADIUS,
            -self.RADIUS,
            self.RADIUS * 2.0,
            self.RADIUS * 2.0,
        )

        # ----------------------------------------------------
        # Graphics flags
        # ----------------------------------------------------
        #
        # ItemIsSelectable:
        #     Allows Qt to represent selection visually.
        #
        # ItemIsMovable is deliberately NOT enabled here.
        #
        # Movement must eventually be controlled by the proper
        # GridForge interaction tool so that moving a bus updates
        # the model rather than only moving the QGraphicsItem.
        # ----------------------------------------------------

        self.setFlag(
            QGraphicsEllipseItem.ItemIsSelectable,
            True,
        )

        # ----------------------------------------------------
        # Enable Qt hover events.
        # ----------------------------------------------------

        self.setAcceptHoverEvents(True)

        # ----------------------------------------------------
        # Store model coordinates as the item's scene position.
        # ----------------------------------------------------

        self._sync_position_from_model()

        # ----------------------------------------------------
        # Set initial visual state.
        # ----------------------------------------------------

        self._hovered = False

        self._apply_visual_state()

    # ========================================================
    # MODEL SYNCHRONIZATION
    # ========================================================

    def _sync_position_from_model(self) -> None:
        """
        Synchronize the graphical position with the Bus model.

        The Bus model remains authoritative.
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
        Handle mouse entering the bus graphics item.

        Hover is transient UI state and does not modify the model.
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
        Handle mouse leaving the bus graphics item.
        """

        self._hovered = False

        self._apply_visual_state()

        super().hoverLeaveEvent(event)

    # ========================================================
    # SELECTION HANDLING
    # ========================================================

    def mousePressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Handle mouse press on the BusItem.

        Selection is delegated to the Controller.

        The graphics item does not become the source of truth.
        """

        # ----------------------------------------------------
        # Determine whether a multi-selection modifier is held.
        # ----------------------------------------------------

        modifiers = event.modifiers()

        multi_select = bool(
            modifiers
            & (
                Qt.KeyboardModifier.ControlModifier
                | Qt.KeyboardModifier.ShiftModifier
            )
        )

        # ----------------------------------------------------
        # Update persistent application selection.
        # ----------------------------------------------------

        self.controller.select(
            self.bus.id,
            multi=multi_select,
        )

        # ----------------------------------------------------
        # Let QGraphicsItem process the original event as well.
        # ----------------------------------------------------

        super().mousePressEvent(event)

    # ========================================================
    # VISUAL STATE
    # ========================================================

    def _apply_visual_state(self) -> None:
        """
        Apply the correct visual appearance.

        Priority:

            Selected
                ↓
            Hover
                ↓
            Normal

        Selection has higher visual priority than hover.
        """

        # ----------------------------------------------------
        # Selected state
        # ----------------------------------------------------

        if self.isSelected():

            self.setPen(
                QPen(
                    self.SELECTED_OUTLINE,
                    self.SELECTED_PEN_WIDTH,
                )
            )

            self.setBrush(
                QBrush(
                    self.SELECTED_FILL
                )
            )

            return

        # ----------------------------------------------------
        # Hover state
        # ----------------------------------------------------

        if self._hovered:

            self.setPen(
                QPen(
                    self.HOVER_OUTLINE,
                    self.HOVER_PEN_WIDTH,
                )
            )

            self.setBrush(
                QBrush(
                    self.HOVER_FILL
                )
            )

            return

        # ----------------------------------------------------
        # Normal state
        # ----------------------------------------------------

        self.setPen(
            QPen(
                self.NORMAL_OUTLINE,
                self.NORMAL_PEN_WIDTH,
            )
        )

        self.setBrush(
            QBrush(
                self.NORMAL_FILL
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
        React when Qt changes the item's selection state.

        This ensures the visual style always follows the actual
        QGraphicsItem selection state.
        """

        result = super().itemChange(
            change,
            value,
        )

        if (
            change
            == QGraphicsEllipseItem.GraphicsItemChange.ItemSelectedChange
        ):
            self._apply_visual_state()

        return result

    # ========================================================
    # MODEL ACCESS
    # ========================================================

    @property
    def model_object(self) -> Any:
        """
        Return the underlying Bus model object.

        This provides a consistent interface for future
        selection and inspection systems.
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
```
