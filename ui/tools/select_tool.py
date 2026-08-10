"""
Select Tool
"""

class SelectTool:
    tool_id = "select"

    def __init__(self, controller, scene):
        self.controller = controller
        self.scene = scene

    def mouse_press(self, event, context):
        print("Select: mouse press")

    def mouse_move(self, event, context):
        pass

    def mouse_release(self, event, context):
        pass
