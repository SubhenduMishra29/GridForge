# ============================================================
# File: ui/editors/control/control_editor.py
# GridForge V2 — Control Editor
# Author: Subhendu Mishra
# ============================================================

"""Control editor adapter around the canonical Control workspace."""

from __future__ import annotations

from ui.core.qt import QVBoxLayout, QWidget
from ui.editors.common.editor_host import EditorRegionFrame


class ControlEditor(QWidget):
    editor_type = "control"

    def __init__(self, *, surface: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        region = EditorRegionFrame("", parent=self)
        region.set_widget(surface)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(region)
        self.setObjectName("ControlEditor")


__all__ = ["ControlEditor"]
