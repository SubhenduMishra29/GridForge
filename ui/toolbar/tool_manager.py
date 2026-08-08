# ============================================================
# File: ui/toolbar/tool_manager.py
# Manages active tool
# ============================================================

class ToolManager:
    """
    Holds and switches active tool
    """

    def __init__(self, controller):
        self.controller = controller
        self.tools = {}
        self.current_tool = None

    def register_tool(self, name, tool):
        self.tools[name] = tool

    def set_tool(self, name):
        self.current_tool = self.tools.get(name)
        self.controller.set_tool(name)
