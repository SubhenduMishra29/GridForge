"""
File: ui/items/bus_item.py
Location: gridforge/ui/items/bus_item.py

Purpose:
    Defines the graphical representation of an electrical Bus.

Why this file exists:
    In power system SLD (Single Line Diagram), a Bus is the fundamental node.
    This class provides a visual node that can be placed, moved, and identified.

Responsibilities:
    - Render bus as a circular node
    - Maintain a unique identifier (Bus ID)
    - Display label for identification
    - Support user interaction (move/select)

Architecture Role:
    UI Element (Leaf Node in Graphics System)

    This is NOT:
    - Not a data model
    - Not a simulation object
    - Not a source of truth

    This WILL later:
    - Reference core.network.Bus
    - Sync position via controller

Qt Inheritance:
    QGraphicsEllipseItem → provides:
        - Shape (ellipse)
        - Positioning
        - Scene integration
        - Event handling

Design Decisions:
    - Centered geometry (-10,-10,20,20) → simplifies alignment & snapping
    - Label is child item → moves automatically with bus
    - Class-level ID counter → ensures unique IDs without global manager (temporary)

Future Extensions:
    - Voltage level color coding
    - Hover effects
    - Connection ports
    - Snap anchors
"""

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PySide6.QtCore import QRectF
from PySide6.QtGui import QBrush, QColor


class BusItem(QGraphicsEllipseItem):
    """
    Graphical Bus Node.

    Represents a node in the electrical network visually.
    """

    # --------------------------------------------------
    # Class-level counter for unique Bus IDs
    # NOTE:
    # Temporary solution until controller assigns IDs
    # --------------------------------------------------
    _id_counter = 1

    def __init__(self, x: float, y: float):
        """
        Initialize a BusItem.

        Parameters:
            x (float): X coordinate in scene space
            y (float): Y coordinate in scene space
        """

        # --------------------------------------------------
        # Geometry Definition
        # --------------------------------------------------
        # Circle centered at origin (important for alignment)
        super().__init__(QRectF(-10, -10, 20, 20))

        # --------------------------------------------------
        # Assign Unique ID
        # --------------------------------------------------
        self.bus_id = BusItem._id_counter
        BusItem._id_counter += 1

        # --------------------------------------------------
        # Visual Styling
        # --------------------------------------------------
        self.setBrush(QBrush(QColor("yellow")))

        # --------------------------------------------------
        # Position in Scene
        # --------------------------------------------------
        self.setPos(x, y)

        # --------------------------------------------------
        # Interaction Flags
        # --------------------------------------------------
        # Allow dragging
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)

        # Allow selection
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)

        # --------------------------------------------------
        # Label (Child Item)
        # --------------------------------------------------
        # Moves automatically with parent
        self.label = QGraphicsTextItem(f"Bus {self.bus_id}", self)

        self.label.setDefaultTextColor(QColor("white"))

        # Offset label slightly to the right
        self.label.setPos(12, -10)

    # --------------------------------------------------
    # Debug Utility (Optional but useful)
    # --------------------------------------------------
    def __repr__(self):
        return f"<BusItem id={self.bus_id} pos=({self.x():.1f}, {self.y():.1f})>"
