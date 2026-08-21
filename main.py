# ============================================================

# GridForge V2

# ============================================================

# File:

# main.py

#

# Purpose:

# Application bootstrap and composition root for GridForge V2.

#

# Architectural Role:

# main.py is the executable composition root.

#

# Responsibilities:

# - create QApplication;

# - create the authoritative Grid model;

# - create the UI Controller;

# - create MainWindow;

# - show MainWindow;

# - start the Qt event loop.

#

# It does NOT:

# - implement UI logic;

# - implement business logic;

# - perform electrical calculations;

# - create individual panels;

# - create tools;

# - perform rendering;

# - perform simulation;

# - own workspace policy.

#

# Workspace orchestration will be injected here when the

# WorkspaceController is introduced and locked.

# ============================================================

"""
GridForge V2 — Application Entry Point.

Application bootstrap and composition root.

This module intentionally contains only application-level
composition and Qt event-loop startup.
"""

from **future** import annotations

import sys

from PySide6.QtWidgets import QApplication

from core.model.grid import Grid
from ui.core.controller import Controller
from ui.main_window import MainWindow

def main() -> int:
"""
Start the GridForge application.

```
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

model = Grid(
    name="GridForge"
)

# ========================================================
# UI CONTROLLER
# ========================================================

controller = Controller(
    core=model
)

# ========================================================
# ROOT WINDOW
# ========================================================

window = MainWindow(
    controller=controller
)

# ========================================================
# SHOW
# ========================================================

window.show()

# ========================================================
# EVENT LOOP
# ========================================================

return app.exec()
```

# ============================================================

# PYTHON ENTRY GUARD

# ============================================================

if **name** == "**main**":
sys.exit(
main()
)
