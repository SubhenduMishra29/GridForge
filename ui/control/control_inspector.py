"""Read-model based Control Inspector.
Author: Subhendu Mishra

Persistent changes are routed through immutable Application commands.
"""

from __future__ import annotations

from uuid import uuid4
from typing import Any

from ui.core.qt import QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget, Qt
from core.application.commands.control_commands import (
    AddControlActionBinding,
    AddControlInterlock,
    UpdateControlComponent,
    SetControlSignalMapping,
)
from core.application.control_signal_mapping import (
    ControlSignalBinding, ControlSignalDestination, ControlSignalMapping, ControlSignalSource,
)


_ACTIONS = {
    "breaker": ("trip", "open", "close", "put_in_service", "take_out_of_service"),
    "switch": ("open", "close", "put_in_service", "take_out_of_service"),
    "disconnector": ("open", "close", "put_in_service", "take_out_of_service"),
    "fuse": ("trip", "blow", "reset", "put_in_service", "take_out_of_service"),
    "motor": ("start", "stop", "put_in_service", "take_out_of_service"),
}


class ControlInspector(QWidget):
    def __init__(self, *, application: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ControlInspector")
        self._application = application
        self._selected_id: str | None = None
        self._selected_type: str | None = None
        self._preset = 1.0
        self._mode = "ton"
        self._component_label = QLabel("Component: None", self)
        self._configuration_label = QLabel("", self)
        self._rung_label = QLabel("Rung: None", self)
        self._mode_label = QLabel("", self)
        self._apply = QPushButton("Apply Timer Configuration", self)
        self._apply.clicked.connect(lambda _checked=False: self._apply_configuration())
        self._preset_down = QPushButton("Preset -0.5", self)
        self._preset_up = QPushButton("Preset +0.5", self)
        self._preset_down.clicked.connect(lambda _checked=False: self._adjust_preset(-0.5))
        self._preset_up.clicked.connect(lambda _checked=False: self._adjust_preset(0.5))
        self._cycle_mode = QPushButton("Cycle TON / TOF / TP", self)
        self._cycle_mode.clicked.connect(lambda _checked=False: self._cycle_timer_mode())
        self._outputs = QListWidget(self)
        self._targets = QListWidget(self)
        self._actions = QListWidget(self)
        self._targets.currentItemChanged.connect(lambda *_: self._refresh_action_choices())
        self._bind_button = QPushButton("Create Action Binding", self)
        self._bind_button.clicked.connect(lambda _checked=False: self._create_action_binding())
        self._interlock_button = QPushButton("Create Interlock", self)
        self._interlock_button.clicked.connect(lambda _checked=False: self._create_interlock())
        self._signal_sources = QListWidget(self)
        self._signal_inputs = QListWidget(self)
        self._signal_actions = QListWidget(self)
        self._signal_bindings = QListWidget(self)
        self._signal_status = QLabel("Signal mapping: select a source, Control input and action binding.", self)
        self._add_signal_binding_button = QPushButton("Add / Update Engineering Signal Binding", self)
        self._add_signal_binding_button.clicked.connect(lambda _checked=False: self._add_signal_binding())
        self._remove_signal_binding_button = QPushButton("Remove Selected Signal Binding", self)
        self._remove_signal_binding_button.clicked.connect(lambda _checked=False: self._remove_signal_binding())

        root = QVBoxLayout(self)
        root.addWidget(QLabel("Control Inspector", self))
        root.addWidget(self._component_label)
        root.addWidget(self._configuration_label)
        root.addWidget(self._rung_label)
        root.addWidget(self._mode_label)
        controls = QHBoxLayout()
        controls.addWidget(self._preset_down)
        controls.addWidget(self._preset_up)
        root.addLayout(controls)
        root.addWidget(self._cycle_mode)
        root.addWidget(self._apply)
        root.addWidget(QLabel("Logic output", self))
        root.addWidget(self._outputs)
        root.addWidget(QLabel("Action target", self))
        root.addWidget(self._targets)
        root.addWidget(QLabel("Action", self))
        root.addWidget(self._actions)
        root.addWidget(self._bind_button)
        root.addWidget(self._interlock_button)
        root.addWidget(QLabel("Engineering signal source", self))
        root.addWidget(self._signal_sources)
        root.addWidget(QLabel("Selected Control component input", self))
        root.addWidget(self._signal_inputs)
        root.addWidget(QLabel("Control action / interlock destination", self))
        root.addWidget(self._signal_actions)
        root.addWidget(QLabel("Project engineering signal bindings", self))
        root.addWidget(self._signal_bindings)
        root.addWidget(self._add_signal_binding_button)
        root.addWidget(self._remove_signal_binding_button)
        root.addWidget(self._signal_status)
        self._set_enabled(False)

    def show_read_model(self, read_model: Any, component_id: str | None) -> None:
        self._selected_id = component_id
        component = next((c for c in read_model.components if c.component_id == component_id), None) if component_id else None
        if component is None:
            self._selected_type = None
            self._component_label.setText("Component: None")
            self._configuration_label.setText("")
            self._rung_label.setText("Rung: None")
            self._outputs.clear()
            self._targets.clear()
            self._actions.clear()
            self._refresh_signal_mapping_lists(read_model, None)
            self._set_enabled(False)
            return

        self._selected_type = component.component_type
        configuration = dict(component.configuration)
        self._preset = float(configuration.get("preset", 1.0))
        self._mode = str(configuration.get("mode", "ton")).lower()
        self._component_label.setText(f"Component: {component.component_id} ({component.component_type})")
        self._rung_label.setText(f"Rung: {component.rung_id or 'None'} | position={component.position}")
        self._configuration_label.setText(f"Configuration: {configuration}")
        self._outputs.clear()
        for output in component.outputs:
            self._outputs.addItem(output)
        self._targets.clear()
        try:
            network = self._application.read_network()
            for element in network.elements:
                target_type = str(element.element_type).lower()
                if target_type in _ACTIONS:
                    self._targets.addItem(f"{target_type}:{element.object_id}")
        except RuntimeError:
            pass
        self._refresh_action_choices()
        self._refresh_signal_mapping_lists(read_model, component)
        self._set_enabled(True)
        self._apply.setEnabled(
            component.component_type == "timer"
            and self._application.supports("control.update_component")
        )
        self._bind_button.setEnabled(
            bool(self._outputs.currentItem())
            and bool(self._targets.count())
            and self._application.supports("control.add_action_binding")
        )
        self._interlock_button.setEnabled(
            self._application.supports("control.add_interlock")
        )

    def show_rung(self, read_model: Any, rung_id: str | None) -> None:
        self._selected_id = None
        self._selected_type = None
        self._set_enabled(False)
        self._outputs.clear()
        self._targets.clear()
        self._actions.clear()
        rung = next((item for item in read_model.rungs if item.rung_id == rung_id), None) if rung_id else None
        if rung is None:
            self._rung_label.setText("Rung: None")
            self._configuration_label.setText("")
            self._refresh_signal_mapping_lists(read_model, None)
            return
        self._rung_label.setText(
            f"Rung: {rung.rung_id} | order={rung.order} | "
            f"{'enabled' if rung.enabled else 'disabled'} | components={len(rung.component_ids)}"
        )
        self._configuration_label.setText(f"Positions: {dict(rung.positions)}")
        self._refresh_signal_mapping_lists(read_model, None)

    def enter_control_interlock_mode(self, read_model: Any, component_id: str | None) -> None:
        self._selected_id = component_id
        self._selected_type = None
        component = next((item for item in read_model.components if item.component_id == component_id), None)
        self._component_label.setText(
            f"Control Interlock source: {component_id}" if component is not None else "Control Interlock source: select a logic component"
        )
        self._rung_label.setText("Rung: configuration mode")
        self._configuration_label.setText("Control Interlock: selected logic component is the gating input.")
        self._mode_label.setText("Control Interlock mode: distinct from LogicEngine interlocks.")
        self._targets.clear()
        self._actions.clear()
        self._set_enabled(False)
        self._interlock_button.setEnabled(self._application.supports("control.add_interlock"))

    def enter_action_binding_mode(self, read_model: Any, component_id: str | None) -> None:
        self._mode_label.setText("Action Binding mode: configure logic output -> equipment action.")
        self.show_read_model(read_model, component_id)
        self._mode_label.setText("Action Binding mode: configure logic output -> equipment action.")

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

    def _refresh_action_choices(self) -> None:
        self._actions.clear()
        item = self._targets.currentItem()
        if item is None:
            return
        target_type, _target_id = item.text().split(":", 1)
        for action in _ACTIONS.get(target_type, ()):
            self._actions.addItem(action)

    def _create_action_binding(self) -> None:
        if self._selected_id is None or not self._outputs.currentItem() or not self._targets.currentItem() or not self._actions.currentItem():
            return
        source_output = self._outputs.currentItem().text()
        target_type, target_id = self._targets.currentItem().text().split(":", 1)
        action = self._actions.currentItem().text()
        read_model = self._application.read_control()
        component = next(c for c in read_model.components if c.component_id == self._selected_id)
        self._application.execute(AddControlActionBinding(
            binding={
                "control_id": f"binding-{uuid4().hex[:12]}",
                "source_component": component.component_id,
                "source_output": source_output,
                "target_equipment_id": target_id,
                "target_equipment_type": target_type,
                "action_type": action,
                "reason": "Configured from Control Inspector",
            }
        ))

    def _create_interlock(self) -> None:
        if self._selected_id is None:
            return
        self._application.execute(AddControlInterlock(
            configuration={
                "interlock_id": f"interlock-{uuid4().hex[:12]}",
                "required_inputs": [self._selected_id],
            }
        ))

    def _refresh_signal_mapping_lists(self, read_model: Any, component: Any | None) -> None:
        self._signal_sources.clear()
        self._signal_inputs.clear()
        self._signal_actions.clear()
        self._signal_bindings.clear()
        try:
            network = self._application.read_network()
            for element in network.elements:
                for signal_name in element.attributes:
                    self._signal_sources.addItem(f"{element.element_type}:{element.object_id}.{signal_name}")
                    self._signal_sources.item(self._signal_sources.count() - 1).setData(
                        Qt.ItemDataRole.UserRole,
                        (str(element.element_type).lower(), str(element.object_id), str(signal_name)),
                    )
        except RuntimeError as exc:
            self._signal_status.setText(f"Signal mapping unavailable: {exc}")
        if component is not None:
            for input_name in component.inputs:
                type_name = str(component.input_signal_types.get(input_name, "")).strip().lower()
                self._signal_inputs.addItem(f"{component.component_id}.{input_name} [{type_name or 'any'}]")
                self._signal_inputs.item(self._signal_inputs.count() - 1).setData(
                    Qt.ItemDataRole.UserRole,
                    (str(component.component_id), str(input_name), type_name),
                )
        for action in getattr(read_model, "action_bindings", ()):
            self._signal_actions.addItem(f"{action.binding_id} → {action.target_type}:{action.target_id}")
            self._signal_actions.item(self._signal_actions.count() - 1).setData(
                Qt.ItemDataRole.UserRole, str(action.binding_id)
            )
        mapping = self._application.control_signal_mapping or ControlSignalMapping()
        for index, binding in enumerate(mapping.bindings):
            self._signal_bindings.addItem(
                f"{binding.source.element_type}:{binding.source.object_id}.{binding.source.signal} → "
                f"{binding.destination.component_id}.{binding.destination.input_name} "
                f"(action {binding.destination.control_id})"
            )
            self._signal_bindings.item(self._signal_bindings.count() - 1).setData(
                Qt.ItemDataRole.UserRole, index
            )
        self._add_signal_binding_button.setEnabled(
            self._signal_sources.count() > 0
            and self._signal_inputs.count() > 0
            and self._signal_actions.count() > 0
        )
        self._remove_signal_binding_button.setEnabled(self._signal_bindings.count() > 0)

    def _apply_signal_mapping(self, mapping: ControlSignalMapping) -> None:
        result = self._application.execute(SetControlSignalMapping(mapping=mapping.to_dict()))
        if not getattr(result, "success", False):
            message = getattr(result, "message", "Application rejected the signal mapping command.")
            self._signal_status.setText(f"Signal mapping rejected: {message}")
            return
        self._signal_status.setText(f"Signal mapping saved in project configuration ({len(mapping.bindings)} binding(s)).")
        read_model = self._application.read_control()
        selected = next((item for item in read_model.components if item.component_id == self._selected_id), None)
        self._refresh_signal_mapping_lists(read_model, selected)

    def _add_signal_binding(self) -> None:
        source_item = self._signal_sources.currentItem()
        input_item = self._signal_inputs.currentItem()
        action_item = self._signal_actions.currentItem()
        if source_item is None or input_item is None or action_item is None:
            self._signal_status.setText("Select a signal source, Control input and action binding.")
            return
        try:
            source_type, source_id, signal_name = source_item.data(Qt.ItemDataRole.UserRole)
            component_id, input_name, input_type_name = input_item.data(Qt.ItemDataRole.UserRole)
            action_id = str(action_item.data(Qt.ItemDataRole.UserRole))
            supported_types = {"bool": bool, "float": float, "int": int, "str": str}
            expected_type = supported_types.get(input_type_name)
            binding = ControlSignalBinding(
                source=ControlSignalSource(
                    domain="core", element_type=source_type, object_id=source_id,
                    signal=signal_name, expected_type=expected_type,
                ),
                destination=ControlSignalDestination(
                    control_id=action_id, component_id=component_id, input_name=input_name,
                ),
            )
            current = self._application.control_signal_mapping or ControlSignalMapping()
            retained = tuple(
                item for item in current.bindings
                if (item.destination.component_id, item.destination.input_name)
                != (component_id, input_name)
            )
            self._apply_signal_mapping(ControlSignalMapping(bindings=retained + (binding,)))
        except Exception as exc:
            self._signal_status.setText(f"Signal mapping error: {type(exc).__name__}: {exc}")

    def _remove_signal_binding(self) -> None:
        item = self._signal_bindings.currentItem()
        if item is None:
            self._signal_status.setText("Select a project signal binding to remove.")
            return
        try:
            index = int(item.data(Qt.ItemDataRole.UserRole))
            current = self._application.control_signal_mapping or ControlSignalMapping()
            if index < 0 or index >= len(current.bindings):
                raise ValueError("Selected signal binding is stale; refresh the inspector and retry.")
            removed = current.bindings[index]
            updated = ControlSignalMapping(
                bindings=tuple(binding for binding in current.bindings if binding != removed)
            )
            self._apply_signal_mapping(updated)
        except Exception as exc:
            self._signal_status.setText(f"Signal mapping error: {type(exc).__name__}: {exc}")

    def _set_enabled(self, enabled: bool) -> None:
        for widget in (
            self._preset_down, self._preset_up, self._cycle_mode,
            self._bind_button, self._interlock_button,
        ):
            widget.setEnabled(bool(enabled))


__all__ = ["ControlInspector"]
