# ============================================================
# File: ui/docking/dock_manager.py
# Handles dock creation and layout
# ============================================================

from PyQt5.QtWidgets import QDockWidget


class DockManager:
    """
    Centralized dock creation system
    """

    def __init__(self, main_window):
        self.main_window = main_window

    def add_dock(self, name, widget, area):
        dock = QDockWidget(name)
        dock.setWidget(widget)
        self.main_window.addDockWidget(area, dock)
        return dock
