# ============================================================
# File: ui/editors/common/tool_shelf.py
# GridForge V2 — Editor Tool Shelf
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any
import logging

from ui.core.qt import QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QIcon, QLabel, QLineEdit, QScrollArea, QToolButton, QVBoxLayout, QWidget, Qt, QSize
from ui.core.action_router import UIActionRouter
from ui.tools.tool_definition import ToolDefinition
from ui.tools.tool_settings import ToolSettingDefinition, ToolSettings

_LOG = logging.getLogger(__name__)


class ToolShelf(QWidget):
    """Presentation surface over canonical ToolDefinitions and ActionRouter."""

    def __init__(
        self,
        *,
        definitions: Iterable[ToolDefinition] = (),
        activate: Callable[[str], object] | None = None,
        action_router: UIActionRouter | None = None,
        editor_type: str | None = None,
        icon_provider: Callable[[ToolDefinition], QIcon | None] | None = None,
        active_tool_provider: Callable[[], str | None] | None = None,
        compact_mode: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._activate = activate
        self._action_router = action_router
        self._editor_type = editor_type
        self._icon_provider = icon_provider
        self._active_tool_provider = active_tool_provider
        self._compact_mode = bool(compact_mode)
        self._definitions: dict[str, ToolDefinition] = {}
        self._buttons: dict[str, QToolButton] = {}
        self.setObjectName("GridForgeToolShelf")
        self.setMinimumWidth(44 if self._compact_mode else 132)
        self._scroll_area = QScrollArea(self)
        self._scroll_area.setObjectName("GridForgeToolShelfScrollArea")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._content_widget = QWidget(self._scroll_area)
        self._content_widget.setObjectName("GridForgeToolShelfContent")
        self._layout = QVBoxLayout(self._content_widget)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(2)
        self._scroll_area.setWidget(self._content_widget)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._scroll_area)
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
            action_id = self._action_id_for_tool(definition.tool_id)
            button = self._buttons.get(definition.tool_id)
            if button is None:
                continue
            if router is not None:
                # An installed router is authoritative: a missing canonical
                # route must not fall through to a callback that bypasses
                # editor ownership and enabled-state checks.
                button.setEnabled(router.has(action_id) and router.is_enabled(action_id))
            elif self._activate is not None:
                # Standalone compatibility shelves may use a callback only
                # when no canonical router was supplied.
                button.setEnabled(True)
            else:
                # Never present an apparently actionable control without a
                # route. In particular, standalone fallback shelves must not
                # silently swallow clicks or create their own tool lifecycle.
                button.setEnabled(False)
                _LOG.warning(
                    "TOOL_SHELF_TOOL_INACTIVE tool_id=%s editor=%s reason=no_activation_route",
                    definition.tool_id,
                    self._editor_type or "unknown",
                )

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
        previous_category = None
        for definition in self._definitions.values():
            if definition.category != previous_category:
                if previous_category is not None:
                    separator = QFrame(self._content_widget)
                    separator.setFrameShape(QFrame.Shape.HLine)
                    separator.setFrameShadow(QFrame.Shadow.Plain)
                    separator.setObjectName("GridForgeToolShelfSeparator")
                    self._layout.addWidget(separator)
                category_label = QLabel(definition.category.title(), self._content_widget)
                category_label.setObjectName("GridForgeToolShelfCategory")
                self._layout.addWidget(category_label)
            previous_category = definition.category

            button = QToolButton(self._content_widget)
            button.setObjectName(f"GridForgeTool_{definition.tool_id}")
            button.setToolTip(
                f"{definition.display_name}"
                + (f"  [{definition.shortcuts[0]}]" if definition.shortcuts else "")
                + (f" — {definition.description}" if definition.description else "")
            )
            button.setStatusTip(button.toolTip())
            button.setText("" if self._compact_mode else definition.display_name)
            button.setCheckable(True)
            button.setAutoRaise(True)
            button.setIconSize(QSize(22, 22))
            button.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonIconOnly
                if self._compact_mode
                else Qt.ToolButtonStyle.ToolButtonTextBesideIcon
            )
            icon = None
            if self._icon_provider is not None:
                try:
                    icon = self._icon_provider(definition)
                except Exception as exc:
                    # A broken presentation provider must be visible in logs,
                    # but must never leave a compact icon-only button blank.
                    _LOG.warning(
                        "TOOL_ICON_RESOLUTION_FAILED tool_id=%s icon_id=%s editor=%s error=%s",
                        definition.tool_id,
                        definition.icon_id,
                        self._editor_type or "unknown",
                        exc,
                    )
            if icon is not None and not icon.isNull():
                button.setIcon(icon)
            else:
                # A missing provider/icon is not permission to show an empty
                # control. Use an ID-derived label, never an unrelated symbol.
                glyph = self._fallback_glyph(definition)
                button.setText(glyph if self._compact_mode else definition.display_name)
                if self._compact_mode:
                    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
                _LOG.warning(
                    "TOOL_ICON_FALLBACK_GLYPH tool_id=%s icon_id=%s editor=%s provider_available=%s",
                    definition.tool_id,
                    definition.icon_id,
                    self._editor_type or "unknown",
                    self._icon_provider is not None,
                )
            button.clicked.connect(lambda _checked=False, tool_id=definition.tool_id: self._activate_tool(tool_id))
            self._layout.addWidget(button)
            self._buttons[definition.tool_id] = button
        self._layout.addStretch(1)
        self.refresh_runtime_state()

    @staticmethod
    def _fallback_glyph(definition: ToolDefinition) -> str:
        """Return a legible, tool-specific fallback without inventing artwork."""
        value = definition.tool_id.replace("_", " ").replace(".", " ").strip()
        return value[:2].upper() if value else "?"

    def _action_id_for_tool(self, tool_id: str) -> str:
        """Resolve tool actions in the shelf editor namespace."""
        if self._editor_type:
            return f"tool.{self._editor_type}.{tool_id}"
        return f"tool.{tool_id}"

    def _activate_tool(self, tool_id: str) -> None:
        action_router = self._action_router
        action_id = self._action_id_for_tool(tool_id)
        try:
            if action_router is not None:
                if not action_router.has(action_id):
                    return
                action_router.dispatch(action_id)
            elif self._activate is not None:
                # Compatibility only for standalone shelves without a router.
                self._activate(tool_id)
        finally:
            # Button state is never authoritative; always reconcile from the
            # canonical ToolManager/Controller state after success or failure.
            self.refresh_runtime_state()

    @property
    def compact_mode(self) -> bool:
        return self._compact_mode

    def set_compact_mode(self, compact: bool) -> None:
        compact = bool(compact)
        if self._compact_mode == compact:
            return
        self._compact_mode = compact
        self.setMinimumWidth(44 if compact else 132)
        self._rebuild()

    def set_active_tool(self, tool_id: str | None) -> None:
        for current_id, button in self._buttons.items():
            button.setChecked(current_id == tool_id)


class ToolSettingsPanel(QWidget):
    """Typed presentation controls over the active tool's immutable settings schema."""

    def __init__(self, *, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context: object | None = None
        self._update_handler: Callable[..., ToolSettings] | None = None
        self._title = QLabel("No active tool", self)
        self._form = QFormLayout()
        self._controls: dict[str, QWidget] = {}
        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addLayout(self._form)
        self.setObjectName("GridForgeToolSettings")
        self.setVisible(False)

    def set_update_handler(self, handler: Callable[..., ToolSettings] | None) -> None:
        """Bind the UI/controller-owned update route; never store it in EditorContext."""
        if handler is not None and not callable(handler):
            raise TypeError("handler must be callable or None.")
        self._update_handler = handler
        self.set_context(self._context)

    def set_context(self, context: object | None) -> None:
        self._context = context
        while self._form.rowCount():
            self._form.removeRow(0)
        self._controls.clear()
        tool_id = getattr(context, "active_tool", None) if context is not None else None
        settings = getattr(context, "tool_settings", None) if context is not None else None
        self._title.setText(f"Tool: {tool_id or 'None'}")
        definitions = dict(getattr(settings, "definitions", {}) or {}) if settings is not None else {}
        values = dict(getattr(settings, "values", {}) or {}) if settings is not None else {}
        self.setVisible(bool(tool_id and definitions))
        if settings is None or not definitions:
            return
        for key, definition in sorted(definitions.items()):
            if not isinstance(definition, ToolSettingDefinition):
                continue
            value = values.get(key, definition.default)
            label = definition.label + (f" ({definition.unit})" if definition.unit else "")
            control = self._make_control(key, definition, value, settings)
            self._controls[key] = control
            self._form.addRow(QLabel(label, self), control)

    def _make_control(
        self, key: str, definition: ToolSettingDefinition, value: object, settings: ToolSettings
    ) -> QWidget:
        editable = bool(definition.editable and self._update_handler is not None)
        if definition.value_type == "bool":
            control = QCheckBox(self)
            control.setChecked(bool(value))
            control.setEnabled(editable)
            control.toggled.connect(
                lambda changed, k=key, s=settings: self._apply_change(k, changed, s)
            )
        elif definition.value_type == "choice":
            control = QComboBox(self)
            for choice in definition.choices:
                control.addItem(str(choice), choice)
            control.setCurrentIndex(max(0, control.findData(value)))
            control.setEnabled(editable)
            control.currentIndexChanged.connect(
                lambda index, widget=control, k=key, s=settings:
                    self._apply_change(k, widget.itemData(index), s) if index >= 0 else None
            )
        elif definition.value_type in {"int", "float"}:
            control = QDoubleSpinBox(self)
            control.setDecimals(0 if definition.value_type == "int" else 4)
            lower = definition.minimum if definition.minimum is not None else (-1_000_000_000 if definition.value_type == "int" else -1_000_000_000.0)
            upper = definition.maximum if definition.maximum is not None else (1_000_000_000 if definition.value_type == "int" else 1_000_000_000.0)
            control.setRange(float(lower), float(upper))
            if definition.step is not None:
                control.setSingleStep(float(definition.step))
            control.setValue(float(value))
            control.setEnabled(editable)
            control.valueChanged.connect(
                lambda changed, k=key, d=definition, s=settings:
                    self._apply_change(k, int(changed) if d.value_type == "int" else float(changed), s)
            )
        else:
            control = QLineEdit(self)
            control.setText(str(value))
            control.setReadOnly(not editable)
            control.editingFinished.connect(
                lambda widget=control, k=key, s=settings: self._apply_change(k, widget.text(), s)
            )
        control.setToolTip(
            "Editable tool interaction setting." if editable
            else "Read-only setting; no active update route is available."
        )
        if not definition.editable:
            control.setEnabled(False)
        return control

    def _apply_change(self, key: str, value: object, settings: ToolSettings) -> None:
        handler = self._update_handler
        if handler is None:
            self.set_context(self._context)
            return
        try:
            updated = handler(
                tool_id=settings.tool_id,
                expected_revision=settings.revision,
                changes={key: value},
            )
            if not isinstance(updated, ToolSettings):
                raise TypeError("Tool settings update route did not return ToolSettings.")
            context = self._context
            updater = getattr(context, "with_updates", None)
            self._context = updater(tool_settings=updated) if callable(updater) else context
            self.set_context(self._context)
        except Exception as exc:
            self._title.setToolTip(f"Setting was not applied: {type(exc).__name__}: {exc}")
            self.set_context(self._context)




__all__ = ["ToolShelf", "ToolSettingsPanel"]
