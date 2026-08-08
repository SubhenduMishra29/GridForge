"""
File: ui/items/bus_item.py
Location: gridforge/ui/items/bus_item.py

Purpose:
    Graphical representation of a bus.

Responsibilities:
    - Draw node
    - Allow movement and selection
    - Display ID label

Future:
    Will link to core Bus object
"""

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PySide6.QtCore import QRectF
from PySide6.QtGui import QBrush, QColor


class BusItem(QGraphicsEllipseItem):

    _id_counter = 1

    def __init__(self, x, y):
        super().__init__(QRectF(-10, -10, 20, 20))

        # Unique ID
        self.bus_id = BusItem._id_counter
        BusItem._id_counter += 1

        # Appearance
        self.setBrush(QBrush(QColor("yellow")))
        self.setPos(x, y)

        # Interaction
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)

        # Label
        self.label = QGraphicsTextItem(f"Bus {self.bus_id}", self)
        self.label.setDefaultTextColor(QColor("white"))
        self.label.setPos(12, -10)
