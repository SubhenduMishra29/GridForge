# ============================================================
# File: ui/canvas/interaction_manager.py
# Central input routing system (ETAP-style interaction layer)
# ============================================================

from PyQt5.QtCore import QObject


class InteractionManager(QObject):
    """
    Handles all user interaction before delegating to tools.

    Responsibilities:
    - Selection logic
    - Multi-select (Shift/Ctrl)
    - Drag handling
    - Tool dispatch
    """

    def __init__(self, controller, tool_manager, scene):
        super().__init__()

        self.controller = controller
        self.tool_manager = tool_manager
        self.scene = scene

        self.dragging = False
        self.last_pos = None

    # --------------------------------------------------
    def mouse_press(self, event):
        tool = self.tool_manager.current_tool

        if tool:
            tool.mouse_press(event, self)

    # --------------------------------------------------
    def mouse_move(self, event):
        tool = self.tool_manager.current_tool

        if tool:
            tool.mouse_move(event, self)

    # --------------------------------------------------
    def mouse_release(self, event):
        tool = self.tool_manager.current_tool

        if tool:
            tool.mouse_release(event, self)
