"""Control workspace toolbar using the existing Application command/history boundary.

Author: Subhendu Mishra
"""

from __future__ import annotations

from typing import Any, Callable

from ui.core.qt import QHBoxLayout, QPushButton, QLabel, QWidget


class ControlToolbar(QWidget):
    def __init__(
        self,
        *,
        application: Any,
        on_add_rung: Callable[[], None],
        on_remove_rung: Callable[[], None],
        on_toggle_rung: Callable[[], None],
        on_move_rung_up: Callable[[], None],
        on_cancel_tool: Callable[[], None],
        on_editing_changed: Callable[[bool], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._application = application
        self._editing_widgets: list[QPushButton] = []
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Control", self))

        for text, callback in (
            ("Add Rung", on_add_rung),
            ("Remove Rung", on_remove_rung),
            ("Enable/Disable Rung", on_toggle_rung),
            ("Move Rung Up", on_move_rung_up),
        ):
            button = QPushButton(text, self)
            button.clicked.connect(lambda _checked=False, callback=callback: callback())
            layout.addWidget(button)
            self._editing_widgets.append(button)

        undo = QPushButton("Undo", self)
        undo.clicked.connect(lambda _checked=False: application.undo())
        layout.addWidget(undo)

        redo = QPushButton("Redo", self)
        redo.clicked.connect(lambda _checked=False: application.redo())
        layout.addWidget(redo)

        cancel = QPushButton("Cancel Tool", self)
        cancel.clicked.connect(lambda _checked=False, callback=on_cancel_tool: callback())
        layout.addWidget(cancel)
        self._editing_widgets.append(cancel)

        layout.addStretch(1)
        self._on_editing_changed = on_editing_changed

    def set_editing_enabled(self, enabled: bool) -> None:
        for widget in self._editing_widgets:
            widget.setEnabled(bool(enabled))
        if self._on_editing_changed is not None:
            self._on_editing_changed(bool(enabled))


__all__ = ["ControlToolbar"]
