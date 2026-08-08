"""
File: ui/main_window.py
Location: gridforge/ui/main_window.py

Purpose:
    Main application window for GridForge UI.

Responsibilities:
    - Initializes Scene (model view) and View (viewport)
    - Hosts toolbar for interaction modes
    - Routes user commands to scene

Architecture Role:
    Top-level UI container

Critical Rule:
    No electrical logic here.
"""

from PySide6.QtWidgets import QMainWindow, QToolBar
from ui.grid_view import GridView
from ui.grid_scene import GridScene


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GridForge")

        # Scene + View
        self.scene = GridScene()
        self.view = GridView(self.scene)
        self.setCentralWidget(self.view)

        # Toolbar
        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)

        self._create_tools()

    def _create_tools(self):
        """Create mode-switching tools."""
        self.toolbar.addAction("Select", lambda: self.scene.set_mode("select"))
        self.toolbar.addAction("Bus", lambda: self.scene.set_mode("bus"))
