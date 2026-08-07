# ui/canvas/grid_canvas.py

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QPoint

from ui.controllers.network_controller import NetworkController


class GridCanvas(QWidget):
    def __init__(self):
        super().__init__()

        self.controller = NetworkController()

        self.buses = {}   # ui_id -> QPoint
        self.lines = []   # [(ui_from, ui_to)]

        self.selected_bus = None
        self.bus_radius = 10

        self.setMinimumSize(800, 600)

    # ---------------------------------------------------------
    # MOUSE EVENTS
    # ---------------------------------------------------------
    def mousePressEvent(self, event):
        pos = event.pos()

        clicked_bus = self._find_bus(pos)

        if clicked_bus:
            self._handle_bus_click(clicked_bus)
        else:
            self._create_bus(pos)

        self.update()

    # ---------------------------------------------------------
    # CREATE BUS
    # ---------------------------------------------------------
    def _create_bus(self, pos):
        ui_id = f"ui_{len(self.buses) + 1}"

        self.controller.create_bus(ui_id)
        self.buses[ui_id] = pos

    # ---------------------------------------------------------
    # HANDLE BUS CLICK
    # ---------------------------------------------------------
    def _handle_bus_click(self, ui_id):
        if self.selected_bus is None:
            self.selected_bus = ui_id
        else:
            if self.selected_bus != ui_id:
                self._create_line(self.selected_bus, ui_id)

            self.selected_bus = None

    # ---------------------------------------------------------
    # CREATE LINE
    # ---------------------------------------------------------
    def _create_line(self, from_id, to_id):
        self.controller.create_line(from_id, to_id)
        self.lines.append((from_id, to_id))

    # ---------------------------------------------------------
    # FIND BUS
    # ---------------------------------------------------------
    def _find_bus(self, pos):
        for ui_id, bus_pos in self.buses.items():
            if (bus_pos - pos).manhattanLength() < self.bus_radius:
                return ui_id
        return None

    # ---------------------------------------------------------
    # PAINT
    # ---------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw lines
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)

        for from_id, to_id in self.lines:
            p1 = self.buses[from_id]
            p2 = self.buses[to_id]
            painter.drawLine(p1, p2)

        # Draw buses
        for ui_id, pos in self.buses.items():
            if ui_id == self.selected_bus:
                painter.setBrush(Qt.red)
            else:
                painter.setBrush(Qt.white)

            painter.drawEllipse(pos, self.bus_radius, self.bus_radius)
