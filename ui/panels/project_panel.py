# ============================================================
# File: ui/panels/project_panel.py
# Displays project structure and files
# ============================================================

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget


class ProjectPanel(QWidget):
    """
    Shows project files (multi-file support)
    """

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.list = QListWidget()
        layout.addWidget(self.list)

    def set_files(self, files):
        self.list.clear()
        self.list.addItems(files)
