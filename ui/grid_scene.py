"""
File: ui/grid_scene.py
Location: gridforge/ui/grid_scene.py

Purpose:
    Defines the graphical scene (canvas) where all network elements are placed.

Why this file exists:
    In Qt Graphics Architecture:
        - QGraphicsScene = logical space (model of visual world)
        - QGraphicsView  = viewport (camera)

    This class manages:
        - What exists on the canvas
        - How user interacts with it
        - What happens on mouse input

Responsibilities:
    - Maintain interaction mode (select, add bus, etc.)
    - Handle mouse events
    - Create UI elements (BusItem)
    - Draw background grid

Architecture Role:
    UI Interaction Layer (pre-controller stage)

    IMPORTANT:
    This is NOT the electrical model.
    It is only a visual + interaction layer.

Future Evolution:
    - Will delegate object creation to controller
    - Will sync with core.network
    - Will enforce topology rules

Design Pattern:
    Mode-driven interaction system

        mode = "select" → default selection behavior
        mode = "bus"    → clicking creates bus

Critical Rules:
    - No electrical calculations
    - No persistent data ownership
    - No direct solver calls
"""

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Qt

from ui.items.bus_item import BusItem


class GridScene(QGraphicsScene):
    """
    Main canvas scene.

    Handles:
        - User input (mouse)
        - Object placement
        - Background rendering
    """

    def __init__(self):
        super().__init__()

        # --------------------------------------------------
        # Interaction Mode State
        # --------------------------------------------------
        # Controls behavior of mouse actions
        self.mode = "select"

        # --------------------------------------------------
        # Scene Configuration
        # --------------------------------------------------
        # Large workspace (acts like infinite canvas initially)
        self.setSceneRect(-5000, -5000, 10000, 10000)

    # --------------------------------------------------
    # MODE MANAGEMENT
    # --------------------------------------------------
    def set_mode(self, mode: str):
        """
        Set current interaction mode.

        Parameters:
            mode (str):
                'select' → default selection mode
                'bus'    → create bus on click
        """
        print(f"[GridScene] Mode changed → {mode}")
        self.mode = mode

    # --------------------------------------------------
    # MOUSE EVENTS
    # --------------------------------------------------
    def mousePressEvent(self, event):
        """
        Handle mouse press events.

        Execution Flow:
            1. Check active mode
            2. Execute mode-specific logic
            3. Pass event to Qt default handler

        Modes:
            'bus':
                - Create BusItem at clicked position
        """

        if self.mode == "bus":
            # ------------------------------------------
            # Get click position in scene coordinates
            # ------------------------------------------
            pos = event.scenePos()

            # ------------------------------------------
            # Create Bus UI object
            # ------------------------------------------
            bus = BusItem(pos.x(), pos.y())

            # ------------------------------------------
            # Add to scene
            # ------------------------------------------
            self.addItem(bus)

            # Debug log
            print(f"[GridScene] Bus created at ({pos.x():.1f}, {pos.y():.1f})")

        # ------------------------------------------
        # Default Qt handling (selection, etc.)
        # ------------------------------------------
        super().mousePressEvent(event)

    # --------------------------------------------------
    # BACKGROUND GRID RENDERING
    # --------------------------------------------------
    def drawBackground(self, painter, rect):
        """
        Draw engineering grid.

        Called automatically by Qt before rendering items.

        Purpose:
            - Visual alignment reference
            - Future snapping base

        Performance Note:
            Only visible region is drawn (rect)
        """

        super().drawBackground(painter, rect)

        grid_size = 20  # pixels

        # Align grid to scene coordinates
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)

        pen = QPen(QColor(50, 50, 50, 100))  # subtle grey
        painter.setPen(pen)

        # ------------------------------------------
        # Draw Vertical Lines
        # ------------------------------------------
        x = left
        while x < rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += grid_size

        # ------------------------------------------
        # Draw Horizontal Lines
        # ------------------------------------------
        y = top
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += grid_size
