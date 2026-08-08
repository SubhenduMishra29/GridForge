# ============================================================
# File: ui/panels/console_panel.py
# Logs system messages / validation output
# ============================================================

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit


class ConsolePanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.text = QTextEdit()
        self.text.setReadOnly(True)

        layout.addWidget(self.text)

    def log(self, message):
        self.text.append(message)
