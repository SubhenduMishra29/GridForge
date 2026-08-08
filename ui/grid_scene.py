"""
File: ui/grid_scene.py

Location:
    gridforge/ui/grid_scene.py

Purpose:
    Manages the graphical representation of the network.

Responsibilities:
    - Handle mouse interactions
    - Create and manage graphical objects
    - Maintain current tool mode

Architecture Role:
    UI Interaction Layer (Controller-like behavior inside UI)

Future Evolution:
    Will delegate all object creation to network_controller

Interactions:
    - Creates BusItem (UI object)
    - Later syncs with Core via Controller

Critical Rule:
    This is NOT the source of truth for network data.
"""

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt

from ui.items.bus_item import BusItem


class GridScene(QGraphicsScene):
    """
    Scene containing all graphical elements.

    Key Concept:
        Mode-driven interaction system
    """

    def __init__(self):
        super().__init__()

        # -------------------------------
        # Interaction Mode State
        # -------------------------------
        # Controls behavior of mouse events
        self.mode = "select"

    def set_mode(self, mode):
        """
        Change interaction mode.

        Parameters:
            mode (str):
                'select' → selection mode
                'bus'    → create bus on click
        """
        print(f"[Scene] Mode changed → {mode}")
        self.mode = mode

    def mousePressEvent(self, event):
        """
        Handle mouse click events.

        Flow:
            1. Check active mode
            2. Execute corresponding action
            3. Pass event to base class
        """

        if self.mode == "bus":
            # -------------------------------
            # Get click position
            # -------------------------------
            pos = event.scenePos()

            # -------------------------------
            # Create BusItem
            # -------------------------------
            bus = BusItem(pos.x(), pos.y())

            # -------------------------------
            # Add to scene
            # -------------------------------
            self.addItem(bus)

        # Default Qt behavior (selection, etc.)
        super().mousePressEvent(event)
