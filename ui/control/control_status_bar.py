"""Control workspace diagnostic/status presentation."""

from __future__ import annotations

from ui.core.qt import QLabel, QHBoxLayout, QWidget


class ControlStatusBar(QWidget):
    def __init__(self, *, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = QLabel("Control: Ready", self)
        layout = QHBoxLayout(self)
        layout.addWidget(self._label)
        layout.addStretch(1)

    def set_status(self, text: str) -> None:
        self._label.setText(str(text))


__all__ = ["ControlStatusBar"]
