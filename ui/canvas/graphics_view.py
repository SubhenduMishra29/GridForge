"""
Graphics View

Location:
---------
ui/canvas/graphics_view.py

Purpose:
--------
Custom QGraphicsView responsible for:
- Hosting the QGraphicsScene
- Forwarding user input to InteractionManager
- Managing viewport behavior (zoom, pan in future)

Design Responsibilities:
------------------------
- DOES handle raw Qt events
- DOES forward events to InteractionManager
- DOES NOT contain business logic
- DOES NOT modify model directly

Architecture Role:
------------------
Qt View Layer → InteractionManager → Tools → Controller → Model
"""

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt

from ui.canvas.interaction_manager import InteractionManager


class GraphicsView(QGraphicsView):
    def __init__(self, controller, parent=None):
        """
        Parameters:
        -----------
        controller : Controller
        parent     : QWidget (optional)
        """
        super().__init__(parent)

        self.controller = controller

        # ------------------------------------------------------
        # Scene setup
        # ------------------------------------------------------
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # ------------------------------------------------------
        # Interaction system
        # ------------------------------------------------------
        self.interaction_manager = InteractionManager(self, controller)

        # ------------------------------------------------------
        # View configuration
        # ------------------------------------------------------

        # Enable mouse move events without pressing button
        # REQUIRED for preview line
        self.setMouseTracking(True)

        # Optional: smoother rendering
        self.setRenderHints(self.renderHints())

        # Optional: disable scroll bars (clean look)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    # ==========================================================
    # EVENT FORWARDING
    # ==========================================================

    def mousePressEvent(self, event):
        """
        Forward mouse press to interaction system.
        """
        self.interaction_manager.mouse_press(event)
        super().mousePressEvent(event)

    # ----------------------------------------------------------

    def mouseMoveEvent(self, event):
        """
        Forward mouse move (used for preview updates).
        """
        self.interaction_manager.mouse_move(event)
        super().mouseMoveEvent(event)

    # ----------------------------------------------------------

    def mouseReleaseEvent(self, event):
        """
        Forward mouse release.
        """
        self.interaction_manager.mouse_release(event)
        super().mouseReleaseEvent(event)

    # ==========================================================
    # ACCESSORS
    # ==========================================================

    def get_scene(self):
        """
        Explicit accessor for scene (avoids direct attribute use).
        """
        return self._scene
