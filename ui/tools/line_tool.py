"""
Line Tool (with preview)

Flow:
-----
Click 1 → store start point
Move mouse → update preview line
Click 2 → create line in model
"""

from ui.core.tool_registry import register_tool


@register_tool("line")
class LineTool:
    def __init__(self, controller, interaction_manager):
        self.controller = controller
        self.im = interaction_manager

        self.start_pos = None

    # ==========================================================
    # MOUSE EVENTS
    # ==========================================================

    def mouse_press(self, event):
        pos = self.im.map_to_scene(event)

        # First click
        if self.start_pos is None:
            self.start_pos = pos
            return

        # Second click → create line
        model = self.controller.model

        model.graph.add_line(
            self.start_pos.x(),
            self.start_pos.y(),
            pos.x(),
            pos.y()
        )

        # Reset
        self.start_pos = None

        # Clear preview
        self.im.preview.clear()

        # Trigger redraw
        self.controller.notify("model_changed")

    # ----------------------------------------------------------

    def mouse_move(self, event):
        """
        Update preview while dragging.
        """
        if self.start_pos is None:
            return

        current_pos = self.im.map_to_scene(event)

        # Draw preview line
        self.im.preview.show_line(self.start_pos, current_pos)

    # ----------------------------------------------------------

    def mouse_release(self, event):
        pass
