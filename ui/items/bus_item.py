"""
File: ui/items/bus_item.py

Location:
    gridforge/ui/items/bus_item.py

Purpose:
    Graphical representation of an electrical bus.

Responsibilities:
    - Draw bus node
    - Allow movement and selection
    - Represent position in UI

Architecture Role:
    UI Element (Visual Node)

Future Integration:
    - Will hold reference to core.network.Bus object
    - Will sync position changes via controller

Critical Rule:
    No electrical properties stored here permanently.
"""

from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtCore import QRectF
from PySide6.QtGui import QBrush, QColor


class BusItem(QGraphicsEllipseItem):
    """
    Circular node representing a bus.
    """

    def __init__(self, x, y):
        """
        Initialize graphical bus.

        Parameters:
            x (float): X coordinate in scene
            y (float): Y coordinate in scene
        """

        # -------------------------------
        # Define Shape
        # -------------------------------
        # Circle centered at (0,0)
        super().__init__(QRectF(-10, -10, 20, 20))

        # -------------------------------
        # Visual Appearance
        # -------------------------------
        self.setBrush(QBrush(QColor("yellow")))

        # -------------------------------
        # Position in Scene
        # -------------------------------
        self.setPos(x, y)

        # -------------------------------
        # Interaction Flags
        # -------------------------------
        # Allow dragging
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)

        # Allow selection
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)
