"""
File: main.py
Location: gridforge/main.py

Purpose:
    Application entry point.

Why this file exists:
    Every Qt application requires:
        1. QApplication instance
        2. Main window creation
        3. Event loop execution

Responsibilities:
    - Initialize QApplication
    - Create MainWindow
    - Launch UI

Architecture Role:
    Application Bootstrap Layer

    This is NOT:
    - Not UI logic
    - Not business logic
    - Not controller

Design Decisions:
    - Keep minimal and clean
    - No logic beyond startup
"""

import sys

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """
    Application entry function.
    """

    # --------------------------------------------------
    # Create Qt Application
    # --------------------------------------------------
    app = QApplication(sys.argv)

    # --------------------------------------------------
    # Create Main Window
    # --------------------------------------------------
    window = MainWindow()
    window.show()

    # --------------------------------------------------
    # Start Event Loop
    # --------------------------------------------------
    sys.exit(app.exec())


# ------------------------------------------------------
# Python Entry Guard
# ------------------------------------------------------
if __name__ == "__main__":
    main()
