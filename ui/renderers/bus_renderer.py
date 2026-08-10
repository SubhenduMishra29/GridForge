# ============================================================
# File: ui/renderers/bus_renderer.py
# Bus Renderer (with hover highlighting)
# ============================================================

from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import QRectF
from ui.core.renderer_registry import register_renderer


@register_renderer("bus")
class BusRenderer:
    """
    Renders buses with optional hover highlighting.

    Visual States:
    --------------
    - Normal → default style
    - Hover  → highlighted (snap feedback)
    """

    RADIUS = 6

    def __init__(self, controller):
        self.controller = controller

    # =====================================================
    # MAIN DRAW ENTRY
    # =====================================================

    def render(self, painter):
        """
        Draw all buses.
        """

        graph = self.controller.model.graph
        tool = self.controller.active_tool

        hover_bus = None

        # Ask tool for hover state (if supported)
        if hasattr(tool, "get_hover_bus"):
            hover_bus = tool.get_hover_bus()

        for bus in graph.all_buses():
            self.draw_bus(painter, bus, hover_bus)

    # =====================================================
    # DRAW SINGLE BUS
    # =====================================================

    def draw_bus(self, painter, bus, hover_bus):
        """
        Draw a single bus with proper styling.
        """

        x = bus.x
        y = bus.y

        rect = QRectF(
            x - self.RADIUS,
            y - self.RADIUS,
            self.RADIUS * 2,
            self.RADIUS * 2
        )

        # ----------------------------------------------
        # STYLE SELECTION
        # ----------------------------------------------

        if bus == hover_bus:
            pen = QPen(QColor(255, 200, 0), 2)   # yellow border
            brush = QBrush(QColor(255, 255, 180))  # light fill
        else:
            pen = QPen(QColor(0, 0, 0), 1)
            brush = QBrush(QColor(255, 255, 255))

        painter.setPen(pen)
        painter.setBrush(brush)

        painter.drawEllipse(rect)
