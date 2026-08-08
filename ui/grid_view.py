"""
File: ui/grid_view.py
Location: gridforge/ui/grid_view.py

Purpose:
    Viewport for rendering the electrical network.

Responsibilities:
    - Displays scene
    - Handles zoom and pan
    - Controls rendering quality

Architecture Role:
    Pure visualization layer
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt


class GridView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

        # Rendering
        self.setRenderHint(QPainter.Antialiasing)

        # Interaction
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # Performance
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    # -------------------------------
    # Zoom (Mouse Wheel)
    # -------------------------------
    def wheelEvent(self, event):
        zoom_factor = 1.15

        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

    # -------------------------------
    # Pan (Middle Mouse)
    # -------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            fake_event = event
            fake_event.button = lambda: Qt.LeftButton
            super().mousePressEvent(fake_event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        super().mouseReleaseEvent(event)
