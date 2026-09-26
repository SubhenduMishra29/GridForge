"""Read-model based Control Inspector.

Persistent changes are routed through immutable Application commands.
"""

from __future__ import annotations

from typing import Any

from ui.core.qt import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from core.application.commands.control_commands import UpdateControlComponent


class ControlInspector(QWidget):
    def __init__(self, *, application: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._application = application
        self._selected_id: str | None = None
        self._selected_type: str | None = None
        self._preset = 1.0
        self._mode = "ton"
        self._component_label = QLabel("None", self)
        self._configuration_label = QLabel("", self)
        self._apply = QPushButton("Apply Timer Configuration", self)
        self._apply.clicked.connect(self._apply_configuration)
        self._preset_down = QPushButton("Preset -0.5", self)
        self._preset_up = QPushButton("Preset +0.5", self)
        self._preset_down.clicked.connect(lambda: self._adjust_preset(-0.5))
        self._preset_up.clicked.connect(lambda: self._adjust_preset(0.5))
        self._cycle_mode = QPushButton("Cycle TON / TOF / TP", self)
        self._cycle_mode.clicked.connect(self._cycle_timer_mode)
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Control Inspector", self))
        root.addWidget(self._component_label)
        root.addWidget(self._configuration_label)
        controls = QHBoxLayout()
        controls.addWidget(self._preset_down)
        controls.addWidget(self._preset_up)
        root.addLayout(controls)
        root.addWidget(self._cycle_mode)
        root.addWidget(self._apply)
        self._set_enabled(False)

    def show_read_model(self, read_model: Any, component_id: str | None) -> None:
        self._selected_id = component_id
        component = next((c for c in read_model.components if c.component_id == component_id), None) if component_id else None
        if component is None:
            self._selected_type = None
            self._component_label.setText("Component: None")
            self._configuration_label.setText("")
            self._set_enabled(False)
            return
        self._selected_type = component.component_type
        configuration = dict(component.configuration)
        self._preset = float(configuration.get("preset", 1.0))
        self._mode = str(configuration.get("mode", "ton")).lower()
        self._component_label.setText(f"Component: {component.component_id} ({component.component_type})")
        self._configuration_label.setText(f"Configuration: {configuration}")
        self._set_enabled(
            component.component_type == "timer"
            and self._application.supports("control.update_component")
        )

    def _adjust_preset(self, delta: float) -> None:
        self._preset = max(0.0, self._preset + delta)
        self._configuration_label.setText(f"Timer preset: {self._preset:g}; mode: {self._mode}")

    def _cycle_timer_mode(self) -> None:
        modes = ("ton", "tof", "tp")
        self._mode = modes[(modes.index(self._mode) + 1) % len(modes)]
        self._configuration_label.setText(f"Timer preset: {self._preset:g}; mode: {self._mode}")

    def _apply_configuration(self) -> None:
        if self._selected_id is None or self._selected_type != "timer":
            return
        self._application.execute(UpdateControlComponent(
            component_id=self._selected_id,
            component_type="timer",
            configuration={"preset": self._preset, "mode": self._mode},
        ))

    def _set_enabled(self, enabled: bool) -> None:
        for widget in (
            self._apply, self._preset_down, self._preset_up, self._cycle_mode,
        ):
            widget.setEnabled(bool(enabled))


__all__ = ["ControlInspector"]
