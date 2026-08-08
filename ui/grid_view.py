"""
File: ui/grid_view.py

Location:
    gridforge/ui/grid_view.py

Purpose:
    Defines the viewport for rendering the electrical network.

Responsibilities:
    - Render QGraphicsScene
    - Handle zoom, pan, selection
    - Improve visual quality (anti-aliasing)

Architecture Role:
    Pure View Layer (NO business logic)

Interactions:
    - Receives scene from MainWindow
    - Displays graphical items (BusItem, LineItem, etc.)

Critical Rule:
    Never store electrical state here.
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtGui import QPainter


class GridView(QGraphicsView):
    """
    Visual viewport for GridScene.
    """

    def __init__(self, scene):
        super().__init__(scene)

        # -------------------------------
        # Rendering Settings
        # -------------------------------
        # Smooth edges for better visuals
        self.setRenderHint(QPainter.Antialiasing)

        # -------------------------------
        # Interaction Mode
        # -------------------------------
        # Enables drag-to-select rectangle
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # -------------------------------
        # Performance Mode
        # -------------------------------
        # Redraw entire viewport (safe for now)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
