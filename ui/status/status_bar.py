from PySide6.QtWidgets import QStatusBar, QLabel


class StatusBar(QStatusBar):
    def __init__(self, controller):
        super().__init__()

        self.coord = QLabel("X:0 Y:0")
        self.tool = QLabel("Tool: Select")

        self.addPermanentWidget(self.coord)
        self.addPermanentWidget(self.tool)

        controller.tool_changed.connect(self.set_tool)

    def set_tool(self, name):
        self.tool.setText(f"Tool: {name.capitalize()}")

    def update_coords(self, x, y):
        self.coord.setText(f"X:{int(x)} Y:{int(y)}")
