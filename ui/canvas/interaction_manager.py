"""
Interaction Manager

Location:
---------
ui/canvas/interaction_manager.py

Purpose:
--------
Central input routing system for the canvas.

This layer sits between:
→ Raw Qt events
→ Tool logic

Responsibilities:
-----------------
- Receive mouse events from the canvas
- Determine active tool
- Delegate events to that tool
- React to tool changes via controller

It does NOT:
--------------
- Implement tool logic
- Know about specific tools
- Contain rendering logic

Architecture:
-------------
Canvas → InteractionManager → Active Tool

Tool switching is controlled via:
controller.set_tool(...) → event → InteractionManager updates tool
"""

from ui.core.qt import QObject
from ui.core.snap_system import SnapSystem

class InteractionManager(QObject):
    """
    Handles all user interaction and routes it to the active tool.
    """

    def __init__(self, controller, scene):
        super().__init__()

        # ----------------------------------------------------------
        # Core references
        # ----------------------------------------------------------
        self.controller = controller
        self.scene = scene

        # ----------------------------------------------------------
        # Active tool (set via controller events)
        # ----------------------------------------------------------
        self._current_tool = None

        # ----------------------------------------------------------
        # Interaction state
        # ----------------------------------------------------------
        self.dragging = False
        self.last_pos = None

        # ----------------------------------------------------------
        # Subscribe to tool changes
        # ----------------------------------------------------------
        self.controller.subscribe("tool_changed", self._on_tool_changed)

    # ==============================================================
    # TOOL MANAGEMENT
    # ==============================================================

    def _on_tool_changed(self, tool_id: str):
        """
        Called when the active tool changes.

        This method resolves the actual tool instance.
        """

        # Ask scene (or tool registry) for tool instance
        # NOTE: scene will provide tool instances (we will define this next)
        tool = self.scene.get_tool(tool_id)

        self._current_tool = tool

        print(f"[InteractionManager] Switched to tool: {tool_id}")

    # ==============================================================
    # EVENT ROUTING
    # ==============================================================

    def mouse_press(self, event):
        """
        Handle mouse press event.
        """

        if self._current_tool:
            self._current_tool.mouse_press(event, self)

    def mouse_move(self, event):
        """
        Handle mouse move event.
        """

        if self._current_tool:
            self._current_tool.mouse_move(event, self)

    def mouse_release(self, event):
        """
        Handle mouse release event.
        """

        if self._current_tool:
            self._current_tool.mouse_release(event, self)
"""
Interaction Manager (updated)

Now also manages:
- Preview layer
"""

from ui.canvas.preview_layer import PreviewLayer
from ui.core.tool_registry import create_tool


class InteractionManager:
    def __init__(self, view, controller):
        self.view = view
        self.controller = controller

        self.current_tool = None

        # ✅ NEW: Preview system
        self.preview = PreviewLayer(view.scene())

        # Listen for tool changes
        controller.subscribe("tool_changed", self.on_tool_changed)

    # ----------------------------------------------------------

    def on_tool_changed(self, tool_id):
        self.current_tool = create_tool(tool_id, self.controller, self)

        # Clear preview when switching tools
        self.preview.clear()

    # ==========================================================
    # EVENT FORWARDING
    # ==========================================================

    def mouse_press(self, event):
        if self.current_tool:
            self.current_tool.mouse_press(event)

    def mouse_move(self, event):
        if self.current_tool:
            self.current_tool.mouse_move(event)

    def mouse_release(self, event):
        if self.current_tool:
            self.current_tool.mouse_release(event)

    # ----------------------------------------------------------

    def map_to_scene(self, event):
        return self.view.mapToScene(event.pos())
