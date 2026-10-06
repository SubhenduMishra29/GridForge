# ============================================================
# File: ui/editors/common/tool_shelf.py
# GridForge V2 — Editor Tool Shelf
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from ui.core.qt import QFormLayout, QIcon, QLabel, QToolButton, QVBoxLayout, QWidget, Qt
from ui.core.action_router import UIActionRouter
from ui.tools.tool_definition import ToolDefinition


class ToolShelf(QWidget):
    """Presentation surface over canonical ToolDefinitions and ActionRouter."""

    def __init__(
        self,
        *,
        definitions: Iterable[ToolDefinition] = (),
        activate: Callable[[str], object] | None = None,
        action_router: UIActionRouter | None = None,
        editor_type: str | None = None,
        icon_provider: Callable[[str], QIcon | None] | None = None,
        active_tool_provider: Callable[[], str | None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._activate = activate
        self._action_router = action_router
        self._editor_type = editor_type
        self._icon_provider = icon_provider
        self._active_tool_provider = active_tool_provider
        self._definitions: dict[str, ToolDefinition] = {}
        self._buttons: dict[str, QToolButton] = {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self.setObjectName("GridForgeToolShelf")
        self.set_action_router(action_router)
        self.set_definitions(definitions)

    @property
    def definitions(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._definitions.values())

    def set_action_router(self, router: UIActionRouter | None) -> None:
        if router is not None and not isinstance(router, UIActionRouter):
            raise TypeError("action_router must be a UIActionRouter or None.")
        self._action_router = router
        self.refresh_runtime_state()

    def set_activate_handler(self, activate: Callable[[str], object] | None) -> None:
        self._activate = activate

    def set_active_tool_provider(self, provider: Callable[[], str | None] | None) -> None:
        self._active_tool_provider = provider
        self.refresh_runtime_state()

    def refresh_runtime_state(self) -> None:
        tool_id = self._active_tool_provider() if self._active_tool_provider is not None else None
        self.set_active_tool(tool_id)
        router = self._action_router
        for definition in self._definitions.values():
            action_id = f"tool.{definition.tool_id}"
            button = self._buttons.get(definition.tool_id)
            if button is not None and router is not None and router.has(action_id):
                button.setEnabled(router.is_enabled(action_id))

    def set_definitions(self, definitions: Iterable[ToolDefinition]) -> None:
        values = tuple(definitions)
        for definition in values:
            if not isinstance(definition, ToolDefinition):
                raise TypeError("ToolShelf definitions must contain ToolDefinition objects.")
        self._definitions = {
            definition.tool_id: definition
            for definition in values
            if self._editor_type is None or definition.supports_editor(self._editor_type)
        }
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
            button.setCheckable(True)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            if definition.icon_id and self._icon_provider is not None:
                icon = self._icon_provider(definition.icon_id)
                if icon is not None:
                    button.setIcon(icon)
            button.clicked.connect(lambda _checked=False, tool_id=definition.tool_id: self._activate_tool(tool_id))
            self._layout.addWidget(button)
            self._buttons[definition.tool_id] = button
        self._layout.addStretch(1)
        self.refresh_runtime_state()

    def _activate_tool(self, tool_id: str) -> None:
        action_router = self._action_router
        action_id = f"tool.{tool_id}"
        try:
            if action_router is not None and action_router.has(action_id):
                action_router.dispatch(action_id)
            elif self._activate is not None:
                # Compatibility only: the normal GridForge runtime path is
                # always ActionRouter → canonical tool handler.
                self._activate(tool_id)
        finally:
            # Button state is never authoritative; always reconcile from the
            # canonical ToolManager/Controller state after success or failure.
            self.refresh_runtime_state()

    def set_active_tool(self, tool_id: str | None) -> None:
        for current_id, button in self._buttons.items():
            button.setChecked(current_id == tool_id)


class ToolSettingsPanel(QWidget):
    """Presentation-only contextual settings for the active ToolDefinition."""

    def __init__(self, *, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = QLabel("No active tool", self)
        self._form = QFormLayout()
        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addLayout(self._form)
        self.setObjectName("GridForgeToolSettings")

    def set_context(self, context: object | None) -> None:
        while self._form.rowCount():
            self._form.removeRow(0)
        tool_id = getattr(context, "active_tool", None) if context is not None else None
        settings = getattr(context, "tool_settings", None) if context is not None else None
        self._title.setText(f"Tool: {tool_id or 'None'}")
        if settings is None:
            return
        for key, value in sorted(dict(getattr(settings, "values", {}) or {}).items()):
            self._form.addRow(QLabel(str(key), self), QLabel(str(value), self))


__all__ = ["ToolShelf", "ToolSettingsPanel"]
