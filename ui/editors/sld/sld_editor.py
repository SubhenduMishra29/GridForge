# ============================================================
# File: ui/editors/sld/sld_editor.py
# GridForge V2 — SLD Editor
# Author: Subhendu Mishra
# ============================================================

"""SLD editor composition over the canonical GridForge SLD surface."""

from __future__ import annotations

from ui.core.qt import QHBoxLayout, QToolBar, QVBoxLayout, QWidget
from ui.editors.common.editor_host import EditorRegionFrame


class SLDEditor(QWidget):
    """Compose Header, Tool Shelf, Canvas, Inspector, Overlay and Status regions."""

    editor_type = "sld"

    def __init__(
        self,
        *,
        canvas: QWidget,
        tool_shelf: QWidget | None = None,
        inspector: QWidget | None = None,
        diagnostics: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._canvas = canvas
        header = QToolBar("SLD", self)
        header.setObjectName("SLDEditorHeader")
        header.addAction("Select")
        header.addAction("Move")
        header.addAction("Connect")
        header.addAction("Snap")
        header.addAction("Grid")
        header.addAction("Validate")

        canvas_region = EditorRegionFrame("", parent=self)
        canvas_region.set_widget(canvas)
        center = QWidget(self)
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        if tool_shelf is not None:
            center_layout.addWidget(tool_shelf)
        center_layout.addWidget(canvas_region, 1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(header)
        body = QHBoxLayout()
        body.addWidget(center, 1)
        if inspector is not None:
            inspector_region = EditorRegionFrame("Inspector", parent=self)
            inspector_region.set_widget(inspector)
            body.addWidget(inspector_region)
        root.addLayout(body, 1)
        if diagnostics is not None:
            diagnostics_region = EditorRegionFrame("Diagnostics", parent=self)
            diagnostics_region.set_widget(diagnostics)
            root.addWidget(diagnostics_region)
        self.setObjectName("SLDEditor")


__all__ = ["SLDEditor"]
