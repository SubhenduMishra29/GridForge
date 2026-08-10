"""
Snap System

Location:
---------
ui/core/snap_system.py

Purpose:
--------
Provides spatial queries for snapping user input to model elements.

Current Features:
-----------------
- Snap to nearest bus

Future Extensions:
------------------
- Snap to line
- Grid snapping
- Priority rules
"""

from math import hypot


class SnapSystem:
    def __init__(self, controller, radius=20):
        """
        Parameters:
        -----------
        controller : Controller
        radius     : float
            Max snapping distance in scene units (pixels)
        """
        self.controller = controller
        self.radius = radius

    # ==========================================================
    # BUS SNAP
    # ==========================================================

    def snap_to_bus(self, pos):
        """
        Find nearest bus within snapping radius.

        Parameters:
        -----------
        pos : QPointF

        Returns:
        --------
        (snapped_pos, bus) OR (original_pos, None)
        """

        model = self.controller.model

        nearest_bus = None
        min_dist = float("inf")

        for bus in model.graph.buses.values():
            dx = bus.x - pos.x()
            dy = bus.y - pos.y()
            dist = hypot(dx, dy)

            if dist < self.radius and dist < min_dist:
                min_dist = dist
                nearest_bus = bus

        if nearest_bus:
            return pos.__class__(nearest_bus.x, nearest_bus.y), nearest_bus

        return pos, None
