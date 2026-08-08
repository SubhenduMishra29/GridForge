"""
File: ui/docks/properties_dock.py

Purpose:
    Displays and edits properties of selected objects.

Features:
    - Context aware (bus / line)
    - Live updates
"""

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QFormLayout,
    QLineEdit, QLabel
)


class PropertiesDock(QDockWidget):
    def __init__(self, controller):
        super().__init__("Properties")

        self.controller = controller
        self.setMinimumWidth(250)

        self.container = QWidget()
        self.layout = QFormLayout()

        self.container.setLayout(self.layout)
        self.setWidget(self.container)

        self.current_obj = None

        # Listen to selection changes
        controller.selection_changed.connect(self.update_properties)

    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def update_properties(self, objects):
        self.clear()

        if not objects:
            self.layout.addRow(QLabel("No selection"))
            return

        obj = objects[0]
        self.current_obj = obj

        if obj["type"] == "bus":
            self._bus_ui(obj)

        elif obj["type"] == "line":
            self._line_ui(obj)

    def _bus_ui(self, bus):
        name_edit = QLineEdit(bus.get("name", ""))

        def on_change():
            bus["name"] = name_edit.text()

        name_edit.editingFinished.connect(on_change)

        self.layout.addRow("Name", name_edit)
        self.layout.addRow("ID", QLabel(str(bus["id"])))

    def _line_ui(self, line):
        self.layout.addRow("Line ID", QLabel(str(line["id"])))
        self.layout.addRow("From", QLabel(str(line["from"])))
        self.layout.addRow("To", QLabel(str(line["to"])))
