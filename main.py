# ============================================================
# GridForge V2
# ============================================================
# File:
#     main.py
#
# Author:
#     Subhendu Mishra
#
# Purpose:
#     Application bootstrap and composition root for GridForge V2.
#
# Architectural Role:
#     main.py is the executable composition root.
#
# It is responsible only for:
#
#     1. Creating the Qt application.
#     2. Creating the authoritative application/domain context.
#     3. Creating the UI Controller.
#     4. Creating and initializing the MainWindow.
#     5. Showing the main window.
#     6. Starting the Qt event loop.
#
# It does NOT:
#
#     - implement UI logic;
#     - implement business logic;
#     - perform electrical calculations;
#     - manipulate the electrical model;
#     - create individual UI components;
#     - create tools;
#     - manage tool lifecycle;
#     - handle canvas interaction;
#     - perform rendering;
#     - perform simulation;
#     - perform analysis.
#
# Composition
# -----------
#
#     QApplication
#          |
#          v
#     Grid
#     (authoritative domain model)
#          |
#          v
#     Controller
#     (UI coordination state)
#          |
#          v
#     create_main_window()
#          |
#          v
#     MainWindow
#          |
#          v
#     UI Plugin System
#
# Dependency Direction
# --------------------
#
#     Application Bootstrap
#             |
#             +---- Core / Domain
#             |
#             +---- UI Controller
#             |
#             +---- MainWindow
#                        |
#                        v
#                   UI Plugins
#
# Qt Boundary
# -----------
#
# Qt is permitted here because main.py is part of the
# application bootstrap layer.
#
# No Qt implementation details are propagated into the
# GridForge domain model.
#
# ============================================================

"""
GridForge V2 — Application Entry Point.

Application bootstrap and composition root.

This module intentionally contains only application-level
composition and Qt event-loop startup.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from core.model.grid import Grid
from ui.core.controller import Controller
from ui.main_window import create_main_window


def main() -> int:
    """
    Start the GridForge application.

    Returns
    -------
    int
        Qt application exit code.
    """

    # ========================================================
    # APPLICATION
    # ========================================================

    app = QApplication(sys.argv)

    # ========================================================
    # AUTHORITATIVE DOMAIN MODEL
    # ========================================================
    #
    # Grid is the central GridForge electrical-network
    # container.
    #
    # It is created here because main.py is the application
    # composition root.
    #
    # The UI does not create or own the electrical model.
    # ========================================================

    model = Grid(
        name="GridForge"
    )

    # ========================================================
    # UI CONTROLLER
    # ========================================================
    #
    # Controller stores UI coordination state only.
    #
    # It receives the authoritative model as a reference but
    # does not become its owner and does not perform domain
    # calculations.
    # ========================================================

    controller = Controller(
        core=model
    )

    # ========================================================
    # ROOT WINDOW
    # ========================================================
    #
    # create_main_window() constructs the thin MainWindow
    # shell and initializes the UI composition.
    #
    # MainWindow does not construct individual concrete UI
    # components directly; composition remains within the
    # plugin system.
    # ========================================================

    window = create_main_window(
        controller=controller
    )

    window.show()

    # ========================================================
    # EVENT LOOP
    # ========================================================

    return app.exec()


# ============================================================
# PYTHON ENTRY GUARD
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
