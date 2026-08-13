"""
GridForge V2 — Application Entry Point
=======================================

File:
    main.py

Purpose
-------
Application bootstrap entry point for GridForge.

Responsibilities
----------------
This module is responsible only for:

    1. Creating the QApplication instance.
    2. Creating the MainWindow.
    3. Showing the MainWindow.
    4. Starting the Qt event loop.

Architecture Role
-----------------
Application Bootstrap Layer

This module does NOT:

    - implement UI logic;
    - own application/domain state;
    - create the Controller;
    - create tools;
    - manage tool lifecycle;
    - perform rendering;
    - handle canvas input;
    - perform electrical calculations;
    - perform simulation;
    - mutate the Core model.

Qt Architecture
---------------
Qt access is routed through the GridForge Qt abstraction
boundary:

    ui.core.qt

No direct PySide6/PyQt imports are used here.
"""

from __future__ import annotations

import sys

from ui.core.qt import QApplication
from ui.main_window import MainWindow


def main() -> None:
    """
    Bootstrap and launch the GridForge application.

    Application lifecycle:

        QApplication
             │
             ▼
        MainWindow
             │
             ▼
        Qt Event Loop
    """

    # --------------------------------------------------------
    # Create the Qt application.
    # --------------------------------------------------------

    app = QApplication(sys.argv)

    # --------------------------------------------------------
    # Create the main application window.
    #
    # MainWindow is the composition boundary for the UI.
    # --------------------------------------------------------

    window = MainWindow()
    window.show()

    # --------------------------------------------------------
    # Start the Qt event loop.
    # --------------------------------------------------------

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


__all__ = [
    "main",
]
