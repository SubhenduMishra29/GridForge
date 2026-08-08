"""
File: ui/views/grid_view.py
Location: gridforge/ui/views/grid_view.py

Purpose:
    Defines the visual viewport for rendering the GridScene.

Why this file exists:
    In Qt Graphics Framework:
        - Scene = holds items & logic
        - View = displays the scene to the user

    This separation allows:
        - Multiple views for same scene (future feature)
        - Independent control of zoom, pan, rendering

Responsibilities:
    - Display GridScene
    - Handle zooming (mouse wheel)
    - Enable panning
    - Improve rendering quality

Architecture Role:
    UI View Layer (Presentation Layer)

Qt Inheritance:
    QGraphicsView → provides:
        - Camera/viewport into scene
        - Transformations (zoom, pan)
        - Rendering pipeline

Design Decisions:
    - Anchor zoom under mouse → intuitive UX
    - Use transformation scaling → efficient zoom
    - Enable hand drag → natural panning
    - Antialiasing → cleaner visuals

Future Extensions:
    - Grid background rendering
    - Snap-to-grid visuals
    - Mini-map
    - Zoom limits
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt


class GridView(QGraphicsView):
    """
    Graphics View for displaying the electrical grid scene.
    """

    def __init__(self, scene):
        """
        Initialize the view.

        Parameters:
            scene (QGraphicsScene): The scene to display
        """
        super().__init__(scene)

        # --------------------------------------------------
        # Rendering Settings
        # --------------------------------------------------
        # Smooth edges for better visuals
        self.setRenderHint(QPainter.Antialiasing)

        # --------------------------------------------------
        # Zoom Behavior Configuration
        # --------------------------------------------------
        # Zoom happens relative to mouse position
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        # --------------------------------------------------
        # Panning Configuration
        # --------------------------------------------------
        # Allows click + drag to move around scene
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        # --------------------------------------------------
        # UI Behavior
        # --------------------------------------------------
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        # Optional: Disable scrollbars (clean UI)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # --------------------------------------------------
        # Internal Zoom Control
        # --------------------------------------------------
        self._zoom_factor = 1.15

    # --------------------------------------------------
    # Mouse Wheel → Zoom
    # --------------------------------------------------
    def wheelEvent(self, event):
        """
        Handles zoom in/out using mouse wheel.
        """
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    # --------------------------------------------------
    # Zoom Helpers
    # --------------------------------------------------
    def zoom_in(self):
        """Zoom into the scene."""
        self.scale(self._zoom_factor, self._zoom_factor)

    def zoom_out(self):
        """Zoom out of the scene."""
        self.scale(1 / self._zoom_factor, 1 / self._zoom_factor)
