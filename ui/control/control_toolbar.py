"""Control workspace toolbar using the existing Application command/history boundary."""

from __future__ import annotations

from typing import Any
from ui.core.qt import QHBoxLayout, QPushButton, QLabel, QWidget


class ControlToolbar(QWidget):
    def __init__(self, *, application: Any, on_add_rung, on_remove_rung, on_toggle_rung, on_move_rung_up, on_cancel_tool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._application = application
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Control", self))
        add = QPushButton("Add Rung", self)
        add.clicked.connect(lambda _checked=False, callback=on_add_rung: callback())
        layout.addWidget(add)
        remove = QPushButton("Remove Rung", self)
        remove.clicked.connect(lambda _checked=False, callback=on_remove_rung: callback())
        layout.addWidget(remove)
        toggle = QPushButton("Enable/Disable Rung", self)
        toggle.clicked.connect(lambda _checked=False, callback=on_toggle_rung: callback())
        layout.addWidget(toggle)
        move = QPushButton("Move Rung Up", self)
        move.clicked.connect(lambda _checked=False, callback=on_move_rung_up: callback())
        layout.addWidget(move)
        undo = QPushButton("Undo", self)
        undo.clicked.connect(lambda _checked=False: application.undo())
        layout.addWidget(undo)
        redo = QPushButton("Redo", self)
        redo.clicked.connect(lambda _checked=False: application.redo())
        layout.addWidget(redo)
        cancel = QPushButton("Cancel Tool", self)
        cancel.clicked.connect(lambda _checked=False, callback=on_cancel_tool: callback())
        layout.addWidget(cancel)
        layout.addStretch(1)


__all__ = ["ControlToolbar"]
