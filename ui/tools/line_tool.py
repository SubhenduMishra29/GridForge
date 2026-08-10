# ============================================================
# File: ui/tools/line_tool.py
# Line Tool (Snap-to-Bus + Preview)
# ============================================================

from PySide6.QtCore import QPointF
from ui.core.tool_registry import register_tool


@register_tool("line")
class LineTool:
    """
    Line drawing tool with topology awareness.

    Flow:
    -----
    Click 1 → select start bus (snaps)
    Move → preview line (snaps)
    Click 2 → create line between buses
    """

    SNAP_RADIUS = 20  # pixels

    def __init__(self, controller, interaction_manager):
        self.controller = controller
        self.im = interaction_manager

        self.start_bus = None
        self.current_pos = None

    # ==========================================================
    # SNAP LOGIC
    # ==========================================================

    def snap_to_bus(self, pos: QPointF):
        """
        Returns nearest bus within SNAP_RADIUS, else None.
        """

        graph = self.controller.model.graph

        nearest = None
        min_dist_sq = self.SNAP_RADIUS ** 2

        px = pos.x()
        py = pos.y()

        for bus in graph.all_buses():

            dx = bus.x - px
            dy = bus.y - py

            dist_sq = dx * dx + dy * dy

            if dist_sq <= min_dist_sq:
                min_dist_sq = dist_sq
                nearest = bus

        return nearest

    # ==========================================================
    # MOUSE EVENTS
    # ==========================================================

    def mouse_press(self, event):
        pos = self.im.map_to_scene(event)

        snapped_bus = self.snap_to_bus(pos)

        # First click → select start bus
        if self.start_bus is None:

            if snapped_bus:
                self.start_bus = snapped_bus

            return

        # Second click → create line
        if snapped_bus and snapped_bus != self.start_bus:

            graph = self.controller.model.graph

            graph.add_line(
                self.start_bus.id,
                snapped_bus.id,
                r=0.01,
                x=0.05,
                b=0.0,
            )

            # Notify system
            self.controller.notify("model_changed")

        # Reset tool state
        self.start_bus = None
        self.current_pos = None

        # Clear preview
        self.im.preview.clear()

    # ----------------------------------------------------------

    def mouse_move(self, event):
        if self.start_bus is None:
            return

        pos = self.im.map_to_scene(event)

        snapped_bus = self.snap_to_bus(pos)

        # Snap preview if near a bus
        if snapped_bus:
            self.current_pos = QPointF(
                snapped_bus.x,
                snapped_bus.y
            )
        else:
            self.current_pos = pos

        # Draw preview
        self.im.preview.show_line(
            QPointF(self.start_bus.x, self.start_bus.y),
            self.current_pos
        )

    # ----------------------------------------------------------

    def mouse_release(self, event):
        pass
