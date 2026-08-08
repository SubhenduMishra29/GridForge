"""
File: ui/controller/interaction_controller.py

Purpose:
    Central interaction manager for editor behavior.

This handles:
    - Modes (select, bus, line)
    - Mouse interactions
    - Temporary drawing states

This is the brain of the UI.
"""

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtGui import QPen

from ui.items.bus_item import BusItem
from ui.theme import LINE_COLOR


class InteractionController:
    MODE_SELECT = "select"
    MODE_BUS = "bus"
    MODE_LINE = "line"

    def __init__(self, scene):
        self.scene = scene

        # Current mode
        self.mode = self.MODE_SELECT

        # Line drawing state
        self.start_item = None
        self.preview_line = None

    # --------------------------------------------------
    # MODE MANAGEMENT
    # --------------------------------------------------
    def set_mode(self, mode):
        self.mode = mode
        self.reset()

    def reset(self):
        if self.preview_line:
            self.scene.removeItem(self.preview_line)
            self.preview_line = None
        self.start_item = None

    # --------------------------------------------------
    # MOUSE EVENTS
    # --------------------------------------------------
    def mouse_press(self, event):
        pos = event.scenePos()

        if self.mode == self.MODE_BUS:
            self._handle_bus(pos)

        elif self.mode == self.MODE_LINE:
            self._handle_line_click(pos)

    def mouse_move(self, event):
        if self.mode == self.MODE_LINE and self.start_item:
            self._update_preview(event.scenePos())

    # --------------------------------------------------
    # MODE HANDLERS
    # --------------------------------------------------
    def _handle_bus(self, pos):
        x, y = self.scene.snap(pos)
        self.scene.addItem(BusItem(x, y))

    def _handle_line_click(self, pos):
        item = self._get_bus_at(pos)

        if not item:
            return

        # First click
        if not self.start_item:
            self.start_item = item
            self._start_preview(item.pos())

        else:
            # Second click → finalize
            self._create_line(self.start_item.pos(), item.pos())
            self.reset()

    # --------------------------------------------------
    # LINE DRAWING
    # --------------------------------------------------
    def _start_preview(self, start_pos):
        self.preview_line = QGraphicsLineItem()
        self.preview_line.setPen(QPen(LINE_COLOR, 2, Qt.DashLine))
        self.scene.addItem(self.preview_line)

        self.preview_line.setLine(
            start_pos.x(), start_pos.y(),
            start_pos.x(), start_pos.y()
        )

    def _update_preview(self, pos):
        if not self.preview_line or not self.start_item:
            return

        sp = self.start_item.pos()
        self.preview_line.setLine(sp.x(), sp.y(), pos.x(), pos.y())

    def _create_line(self, p1, p2):
        line = QGraphicsLineItem(
            p1.x(), p1.y(),
            p2.x(), p2.y()
        )
        line.setPen(QPen(LINE_COLOR, 2))
        self.scene.addItem(line)

    # --------------------------------------------------
    # UTIL
    # --------------------------------------------------
    def _get_bus_at(self, pos):
        items = self.scene.items(pos)
        for item in items:
            if isinstance(item, BusItem):
                return item
        return None
