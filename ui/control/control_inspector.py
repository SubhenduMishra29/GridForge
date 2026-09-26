"""Read-model based Control Inspector.

Persistent changes are routed through immutable Application commands.
"""

from __future__ import annotations

from typing import Any
from ui.core.qt import QFormLayout, QLineEdit, QLabel, QPushButton, QComboBox, QWidget
from core.application.commands.control_commands import UpdateControlComponent


class ControlInspector(QWidget):
    def __init__(self, *, application: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._application = application
        self._selected_id: str | None = None
        self._selected_type: str | None = None
        self._preset = QLineEdit(self)
        self._mode = QComboBox(self)
        self._mode.addItems(["ton", "tof", "tp"])
        self._apply = QPushButton("Apply", self)
        self._apply.clicked.connect(self._apply_configuration)
        self._form = QFormLayout(self)
        self._form.addRow(QLabel("Component", self), QLabel("None", self))
        self._form.addRow(QLabel("Preset", self), self._preset)
        self._form.addRow(QLabel("Timer Mode", self), self._mode)
        self._form.addRow(self._apply)
        self._apply.setEnabled(False)

    def show_read_model(self, read_model: Any, component_id: str | None) -> None:
        self._selected_id = component_id
        component = next((c for c in read_model.components if c.component_id == component_id), None) if component_id else None
        if component is None:
            self._selected_type = None
            self._preset.setText("")
            self._apply.setEnabled(False)
            return
        self._selected_type = component.component_type
        self._preset.setText(str(component.configuration.get("preset", "")))
        mode = str(component.configuration.get("mode", "ton")).lower()
        index = max(0, self._mode.findText(mode))
        self._mode.setCurrentIndex(index)
        self._apply.setEnabled(component.component_type == "timer" and self._application.supports("control.update_component"))

    def _apply_configuration(self) -> None:
        if self._selected_id is None or self._selected_type != "timer":
            return
        try:
            preset = float(self._preset.text())
        except ValueError as exc:
            raise ValueError("Timer preset must be numeric.") from exc
        self._application.execute(UpdateControlComponent(
            component_id=self._selected_id,
            component_type="timer",
            configuration={"preset": preset, "mode": self._mode.currentText()},
        ))


__all__ = ["ControlInspector"]
