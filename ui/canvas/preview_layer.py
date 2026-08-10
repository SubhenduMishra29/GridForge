"""
Preview Layer

Location:
---------
ui/canvas/preview_layer.py

Purpose:
--------
Handles temporary (non-model) visuals such as:
- Rubber-band line preview
- Hover indicators (future)
- Placement previews

Key Design Rule:
----------------
Preview graphics:
- Are NOT part of the model
- Are NOT persisted
- Are removed/updated every frame as needed
"""

from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtGui import QPen
from PySide6.QtCore import Qt


class PreviewLayer:
    def __init__(self, scene):
        """
        Parameters:
        -----------
        scene : QGraphicsScene
        """
        self.scene = scene

        # Currently active preview line (if any)
        self._line_item = None

        # Visual style (dashed line)
        self._pen = QPen(Qt.gray, 2, Qt.DashLine)

    # ==========================================================
    # LINE PREVIEW
    # ==========================================================

    def show_line(self, start_pos, end_pos):
        """
        Create or update a preview line.

        Parameters:
        -----------
        start_pos : QPointF
        end_pos   : QPointF
        """

        # Create line if it doesn't exist
        if self._line_item is None:
            self._line_item = QGraphicsLineItem()
            self._line_item.setPen(self._pen)
            self.scene.addItem(self._line_item)

        # Update geometry
        self._line_item.setLine(
            start_pos.x(),
            start_pos.y(),
            end_pos.x(),
            end_pos.y()
        )

    # ----------------------------------------------------------

    def clear(self):
        """
        Remove all preview visuals.
        """
        if self._line_item:
            self.scene.removeItem(self._line_item)
            self._line_item = None
