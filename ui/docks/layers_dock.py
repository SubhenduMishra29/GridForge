"""
File: ui/docks/layers_dock.py

Purpose:
    Manage layers:
        - Visibility
        - Locking
        - Organization
"""

from PySide6.QtWidgets import (
    QDockWidget, QListWidget, QListWidgetItem,
    QVBoxLayout, QWidget, QPushButton
)


class LayersDock(QDockWidget):
    def __init__(self, controller):
        super().__init__("Layers")

        self.controller = controller

        container = QWidget()
        layout = QVBoxLayout()

        self.list_widget = QListWidget()

        self.add_btn = QPushButton("Add Layer")
        self.add_btn.clicked.connect(self.add_layer)

        layout.addWidget(self.list_widget)
        layout.addWidget(self.add_btn)

        container.setLayout(layout)
        self.setWidget(container)

        self.refresh()

    def refresh(self):
        self.list_widget.clear()

        for layer in self.controller.model.layers:
            item = QListWidgetItem(layer["name"])
            self.list_widget.addItem(item)

    def add_layer(self):
        name = f"Layer {len(self.controller.model.layers) + 1}"
        self.controller.model.layers.append({
            "name": name,
            "visible": True,
            "locked": False
        })
        self.refresh()
