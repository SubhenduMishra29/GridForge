"""
File: ui/grid_scene.py
Location: gridforge/ui/grid_scene.py

Purpose:
    Manages graphical layout and interaction.

Responsibilities:
    - Handle mouse interaction
    - Maintain mode (select, bus, etc.)
    - Create UI elements

Architecture Role:
    UI interaction layer
"""

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QPen, QColor
from ui.items.bus_item import BusItem


class GridScene(QGraphicsScene):
    def __init__(self):
        super().__init__()

        self.mode = "select"

    # -------------------------------
    # Mode Control
    # -------------------------------
    def set_mode(self, mode):
        print(f"[Scene] Mode → {mode}")
        self.mode = mode

    # -------------------------------
    # Mouse Interaction
    # -------------------------------
    def mousePressEvent(self, event):
        if self.mode == "bus":
            pos = event.scenePos()
            bus = BusItem(pos.x(), pos.y())
            self.addItem(bus)

        super().mousePressEvent(event)

    # -------------------------------
    # Grid Background
    # -------------------------------
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)

        grid_size = 20

        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)

        pen = QPen(QColor(50, 50, 50, 100))
        painter.setPen(pen)

        # Vertical lines
        x = left
        while x < rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += grid_size

        # Horizontal lines
        y = top
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += grid_size
