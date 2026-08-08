# ============================================================
# File: ui/status/status_bar.py
# Displays coordinates, tool state, and system info
# ============================================================

from PyQt5.QtWidgets import QStatusBar, QLabel


class StatusBar(QStatusBar):
    """
    Professional status bar (ETAP-style)

    Sections:
    - Left: Tool state
    - Right: Cursor coordinates
    """

    def __init__(self):
        super().__init__()

        # --- Tool label (left) ---
        self.tool_label = QLabel("Tool: None")
        self.addWidget(self.tool_label)

        # --- Spacer ---
        self.addPermanentWidget(QLabel("   "))

        # --- Coordinates (right) ---
        self.coord_label = QLabel("X: 0, Y: 0")
        self.addPermanentWidget(self.coord_label)

    # --------------------------------------------------
    def set_tool(self, tool_name: str):
        self.tool_label.setText(f"Tool: {tool_name}")

    # --------------------------------------------------
    def set_coordinates(self, x: float, y: float):
        self.coord_label.setText(f"X: {x:.1f}, Y: {y:.1f}")
