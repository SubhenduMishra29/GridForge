"""
Updated GridScene with Mode Awareness
"""

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt

from ui.items.bus_item import BusItem
from ui.modes import EditorMode


class GridScene(QGraphicsScene):
    """
    Scene with mode-based interaction.
    """

    def __init__(self):
        super().__init__()

        # --------------------------------------------------
        # Scene Setup
        # --------------------------------------------------
        self.setSceneRect(0, 0, 2000, 2000)

        # --------------------------------------------------
        # Mode State
        # --------------------------------------------------
        self.mode = EditorMode.SELECT

    # --------------------------------------------------
    # Mode Setter
    # --------------------------------------------------
    def set_mode(self, mode: EditorMode):
        """Set current editor mode."""
        self.mode = mode
        print(f"[MODE] Switched to {mode.name}")

    # --------------------------------------------------
    # Mouse Interaction
    # --------------------------------------------------
    def mousePressEvent(self, event):
        """
        Handle mouse click based on current mode.
        """

        if event.button() == Qt.LeftButton:

            # ----------------------------------------------
            # MODE: ADD BUS
            # ----------------------------------------------
            if self.mode == EditorMode.ADD_BUS:
                pos = event.scenePos()

                bus = BusItem(pos.x(), pos.y())
                self.addItem(bus)

                print(f"[ADD BUS] {bus}")

                return  # prevent default behavior

            # ----------------------------------------------
            # MODE: SELECT (default Qt behavior)
            # ----------------------------------------------
            elif self.mode == EditorMode.SELECT:
                super().mousePressEvent(event)
                return

            # ----------------------------------------------
            # MODE: ADD LINE (future)
            # ----------------------------------------------
            elif self.mode == EditorMode.ADD_LINE:
                print("[INFO] Line mode not implemented yet")
                return

        # Default fallback
        super().mousePressEvent(event)
