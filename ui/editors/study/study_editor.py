# ============================================================
# File: ui/editors/study/study_editor.py
# GridForge V2 — Study Editor
# Author: Subhendu Mishra
# ============================================================

"""Extensible study/results editor host."""

from __future__ import annotations

from ui.core.qt import QLabel, QVBoxLayout, QWidget
from ui.editors.common.editor_host import EditorRegionFrame


class StudyEditor(QWidget):
    editor_type = "study"

    def __init__(self, *, surface: QWidget | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        canvas = surface if surface is not None else QLabel("Study / Simulation results", self)
        region = EditorRegionFrame("", parent=self)
        region.set_widget(canvas)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(region)
        self.setObjectName("StudyEditor")


__all__ = ["StudyEditor"]
