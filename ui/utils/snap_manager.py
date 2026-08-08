"""
File: ui/utils/snap_manager.py

Purpose:
    Central snapping + guide computation
"""

from PySide6.QtCore import QPointF
from ui.theme import GRID_SIZE


class SnapManager:
    def __init__(self, scene):
        self.scene = scene

        self.snap_to_grid = True
        self.snap_to_items = True

        self.threshold = 10  # pixel tolerance

    # --------------------------------------------------
    # MAIN SNAP FUNCTION
    # --------------------------------------------------
    def snap(self, pos):
        x, y = pos.x(), pos.y()

        if self.snap_to_grid:
            x, y = self._snap_grid(x, y)

        if self.snap_to_items:
            x, y = self._snap_items(x, y)

        return QPointF(x, y)

    # --------------------------------------------------
    # GRID SNAP
    # --------------------------------------------------
    def _snap_grid(self, x, y):
        gx = round(x / GRID_SIZE) * GRID_SIZE
        gy = round(y / GRID_SIZE) * GRID_SIZE
        return gx, gy

    # --------------------------------------------------
    # OBJECT SNAP (ALIGNMENT)
    # --------------------------------------------------
    def _snap_items(self, x, y):
        for item in self.scene.items():
            if hasattr(item, "bus_id"):
                ix = item.pos().x()
                iy = item.pos().y()

                if abs(ix - x) < self.threshold:
                    x = ix
                if abs(iy - y) < self.threshold:
                    y = iy

        return x, y
