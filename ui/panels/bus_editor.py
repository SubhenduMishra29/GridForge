# ui/panels/bus_editor.py

from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QComboBox, QPushButton
)


class BusEditor(QWidget):
    def __init__(self):
        super().__init__()

        self.current_bus_id = None
        self.controller = None

        self.layout = QFormLayout()

        self.type_box = QComboBox()
        self.type_box.addItems(["PQ", "PV", "SLACK"])

        self.p_input = QLineEdit()
        self.q_input = QLineEdit()
        self.v_input = QLineEdit()

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_changes)

        self.layout.addRow("Type", self.type_box)
        self.layout.addRow("P", self.p_input)
        self.layout.addRow("Q", self.q_input)
        self.layout.addRow("V", self.v_input)
        self.layout.addRow(self.apply_btn)

        self.setLayout(self.layout)

    # ---------------------------------------------------------
    # LOAD BUS DATA
    # ---------------------------------------------------------
    def load_bus(self, bus_id, controller):
        self.current_bus_id = bus_id
        self.controller = controller

        bus = controller.network.bus_lookup[bus_id]

        self.type_box.setCurrentText(bus.type)
        self.p_input.setText(str(bus.P))
        self.q_input.setText(str(bus.Q))
        self.v_input.setText(str(bus.V))

    # ---------------------------------------------------------
    # APPLY CHANGES
    # ---------------------------------------------------------
    def apply_changes(self):
        if not self.current_bus_id:
            return

        bus = self.controller.network.bus_lookup[self.current_bus_id]

        bus.type = self.type_box.currentText()
        bus.P = float(self.p_input.text())
        bus.Q = float(self.q_input.text())
        bus.V = float(self.v_input.text())
