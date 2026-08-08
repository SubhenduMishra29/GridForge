"""
File: ui/overlay/guides_overlay.py

Draws alignment guides
"""

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPen
from PySide6.QtCore import Qt


class GuidesOverlay(QGraphicsItem):
    def __init__(self):
        super().__init__()

        self.lines = []

    def set_lines(self, lines):
        self.lines = lines
        self.update()

    def boundingRect(self):
        return self.scene().sceneRect()

    def paint(self, painter, option, widget):
        pen = QPen(Qt.green, 1, Qt.DashLine)
        painter.setPen(pen)

        for line in self.lines:
            painter.drawLine(*line)
