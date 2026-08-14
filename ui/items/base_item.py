# ============================================================
# File: ui/items/base_item.py
# GridForge V2 — Base Graphics Item
# ============================================================
#
# PURPOSE
# -------
# Provides common graphics-item infrastructure shared by
# GridForge canvas items.
#
#
# ARCHITECTURE
# ------------
#
#     Core Model
#         │
#         ▼
#     Graphics Item
#         │
#         ├── selection state
#         ├── visual state
#         └── Qt graphics representation
#
#
# IMPORTANT
# ---------
#
# BaseItem is a presentation-layer class.
#
# It does NOT:
#
#     - own authoritative engineering state
#     - modify the Core model directly
#     - perform engineering calculations
#     - perform topology operations
#     - decide which tool is active
#     - perform snapping
#     - manage the graphics scene
#     - allow unrestricted direct movement
#
#
# MOVEMENT
# --------
#
# Graphics movement is deliberately NOT enabled here.
#
# Editing/movement must pass through the GridForge interaction
# and command/application architecture so that Core remains the
# authoritative source of state.
#
#
# QT IMPORT RULE
# --------------
#
# Qt classes are imported exclusively through:
#
#     ui.core.qt
#
# Never import PySide6/PyQt directly from this file.
#
# ============================================================

from __future__ import annotations

from typing import Any

from ui.core.qt import QColor, QGraphicsItem, QPainter, QPen


class BaseItem(QGraphicsItem):
    """
    Base class for GridForge graphics items.

    Provides common model/controller references, selection
    capability, and selection-overlay rendering support.

    Concrete subclasses must implement the QGraphicsItem
    ``boundingRect()`` and ``paint()`` methods.
    """

    def __init__(
        self,
        model_obj: Any,
        controller: Any = None,
    ) -> None:
        """
        Initialize the common graphics-item state.

        Parameters
        ----------
        model_obj:
            Authoritative Core/domain object represented by this
            graphics item.

        controller:
            GridForge application/controller boundary used when
            the graphics item needs to request application-level
            behavior.
        """
        super().__init__()

        self.model = model_obj
        self.controller = controller

        # Selection is a legitimate graphics interaction state.
        #
        # Movement is intentionally NOT enabled here. Any editing
        # of model-backed geometry must go through the appropriate
        # GridForge interaction/tool/command path.
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

    # ========================================================
    # SELECTION OVERLAY
    # ========================================================

    def paint_selection(
        self,
        painter: QPainter,
    ) -> None:
        """
        Paint the common selection overlay.

        Concrete graphics items should call this from their
        ``paint()`` implementation after rendering their normal
        visual representation.

        Parameters
        ----------
        painter:
            Active Qt graphics painter supplied by QGraphicsView.
        """
        if not self.isSelected():
            return

        painter.save()

        pen = QPen(
            QColor(0, 150, 255),
            2,
        )

        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))
        painter.drawRect(self.boundingRect())

        painter.restore()
