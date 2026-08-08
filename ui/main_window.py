"""
File: ui/main_window.py
Location: gridforge/ui/main_window.py

Purpose:
    Defines the main application window.

Why this file exists:
    This is the top-level UI container that:
        - Holds the graphics view
        - Manages layout
        - Acts as integration point for all UI components

Responsibilities:
    - Initialize GridScene
    - Initialize GridView
    - Embed view into window
    - Configure window properties

Architecture Role:
    UI Root Layer

    This is NOT:
    - Not business logic
    - Not simulation
    - Not controller

    This WILL later:
    - Connect to controller
    - Add toolbars (modes)
    - Add menus (file/edit/view)
    - Manage status bar

Qt Inheritance:
    QMainWindow → provides:
        - Central widget system
        - Menu bar
        - Toolbars
        - Docking system

Design Decisions:
    - Use GridView as central widget
    - Scene created here (temporary; may move to controller later)
    - Keep minimal logic → clean separation

Future Extensions:
    - Toolbar for modes (Bus, Line, Select)
    - Status bar (coordinates, info)
    - Dock panels (properties, logs)
"""

from PySide6.QtWidgets import QMainWindow

from ui.scene.grid_scene import GridScene
from ui.views.grid_view import GridView


class MainWindow(QMainWindow):
    """
    Main Application Window.
    """

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # --------------------------------------------------
        # Window Configuration
        # --------------------------------------------------
        self.setWindowTitle("GridForge - Power System Designer")
        self.resize(1000, 700)

        # --------------------------------------------------
        # Scene Initialization
        # --------------------------------------------------
        self.scene = GridScene()

        # --------------------------------------------------
        # View Initialization
        # --------------------------------------------------
        self.view = GridView(self.scene)

        # --------------------------------------------------
        # Set Central Widget
        # --------------------------------------------------
        # QMainWindow requires a central widget
        self.setCentralWidget(self.view)

        # --------------------------------------------------
        # Future Hooks (DO NOT IMPLEMENT YET)
        # --------------------------------------------------
        # self._create_toolbar()
        # self._create_menus()
        # self._create_status_bar()
