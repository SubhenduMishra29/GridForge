# ============================================================
# File: ui/editors/protection/protection_editor.py
# GridForge V2 — Protection Editor
# Author: Subhendu Mishra
# ============================================================

"""Protection editor adapter around the canonical Protection workspace."""

from __future__ import annotations

from ui.core.qt import QVBoxLayout, QWidget
from ui.editors.common.editor_host import EditorRegionFrame


class ProtectionEditor(QWidget):
    editor_type = "protection"

    def __init__(self, *, surface: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        region = EditorRegionFrame("", parent=self)
        region.set_widget(surface)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(region)
        self.setObjectName("ProtectionEditor")


__all__ = ["ProtectionEditor"]
