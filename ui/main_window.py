"""
File: ui/main_window.py

Location:
    gridforge/ui/main_window.py

Purpose:
    Defines the main application window for GridForge UI.

Responsibilities:
    - Initializes Scene (visual model) and View (viewport)
    - Hosts toolbar and global UI controls
    - Acts as entry point for user interaction

Architecture Role:
    UI Layer (Top Level Container)

Interactions:
    - Talks to GridScene for mode switching
    - Does NOT interact with core/network directly

Critical Rule:
    No electrical or simulation logic here.
"""

from PySide6.QtWidgets import QMainWindow, QToolBar
from ui.grid_view import GridView
from ui.grid_scene import GridScene


class MainWindow(QMainWindow):
    """
    Root window of GridForge application.

    Composition:
        [Toolbar]
        [Graphics View (Canvas)]
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("GridForge")

        # -------------------------------
        # Scene + View Initialization
        # -------------------------------
        # Scene = logical canvas
        # View  = rendered viewport
        self.scene = GridScene()
        self.view = GridView(self.scene)

        self.setCentralWidget(self.view)

        # -------------------------------
        # Toolbar Setup
        # -------------------------------
        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)

        self._create_tools()

    def _create_tools(self):
        """
        Create toolbar actions.

        These actions DO NOT perform operations directly.
        They only change interaction mode inside GridScene.
        """

        self.toolbar.addAction("Select", lambda: self.scene.set_mode("select"))
        self.toolbar.addAction("Bus", lambda: self.scene.set_mode("bus"))
