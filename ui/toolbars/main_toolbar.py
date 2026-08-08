from PySide6.QtWidgets import QToolBar, QAction


class MainToolbar(QToolBar):
    def __init__(self, controller):
        super().__init__("Tools")
        self.controller = controller
        self._build()

    def _build(self):
        self._add_tool("Select", "select")
        self._add_tool("Bus", "bus")
        self._add_tool("Line", "line")

    def _add_tool(self, name, tool_id):
        action = QAction(name, self)
        action.triggered.connect(lambda: self.controller.set_tool(tool_id))
        self.addAction(action)
