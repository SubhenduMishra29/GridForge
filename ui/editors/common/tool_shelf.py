# ============================================================
# File: ui/editors/common/tool_shelf.py
# GridForge V2 — Contextual Tool Shelf
# Author: Subhendu Mishra
# ============================================================
"""Metadata-driven Qt realization of ToolDefinition items."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from ui.core.qt import QIcon, QToolButton, QVBoxLayout, QWidget
from ui.tools.tool_definition import ToolDefinition


class ToolShelf(QWidget):
    """Present contextual ToolDefinitions and route activation to a runtime owner."""

    def __init__(
        self,
        *,
        definitions: Iterable[ToolDefinition] = (),
        activate: Callable[[str], object] | None = None,
        editor_type: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._activate = activate
        self._editor_type = editor_type
        self._definitions: dict[str, ToolDefinition] = {}
        self._buttons: dict[str, QToolButton] = {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self.setObjectName("GridForgeToolShelf")
        self.set_definitions(definitions)

    @property
    def definitions(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._definitions.values())

    def set_activate_handler(self, activate: Callable[[str], object] | None) -> None:
        self._activate = activate

    def set_definitions(self, definitions: Iterable[ToolDefinition]) -> None:
        values = tuple(definitions)
        for definition in values:
            if not isinstance(definition, ToolDefinition):
                raise TypeError("ToolShelf definitions must contain ToolDefinition objects.")
        self._definitions = {definition.tool_id: definition for definition in values if self._editor_type is None or definition.supports_editor(self._editor_type)}
        self._rebuild()

    def _rebuild(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._buttons.clear()
        for definition in self._definitions.values():
            button = QToolButton(self)
            button.setObjectName(f"GridForgeTool_{definition.tool_id}")
            button.setToolTip(definition.description or definition.display_name)
            button.setText(definition.display_name)
            button.setToolButtonStyle(QToolButton.ToolButtonStyle.ToolButtonTextBesideIcon)
            if definition.icon_id:
                button.setIcon(QIcon())
            button.clicked.connect(lambda _checked=False, tool_id=definition.tool_id: self._activate_tool(tool_id))
            self._layout.addWidget(button)
            self._buttons[definition.tool_id] = button
        self._layout.addStretch(1)

    def _activate_tool(self, tool_id: str) -> None:
        if self._activate is not None:
            self._activate(tool_id)

    def set_active_tool(self, tool_id: str | None) -> None:
        for current_id, button in self._buttons.items():
            button.setChecked(current_id == tool_id)


__all__ = ["ToolShelf"]
