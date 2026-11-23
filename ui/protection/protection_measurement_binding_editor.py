# Author: Subhendu Mishra
"""Explicit PT/CVT-to-RelayInput protection measurement binding editor."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from core.model import EndpointReference, EquipmentType
from core.protection.protection_measurement_binding import ProtectionMeasurementBinding
from core.application.commands.protection_configuration_commands import (
    CreateProtectionMeasurementBindingCommand,
)
from ui.core.qt import (
    QComboBox,
    QDoubleValidator,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QVBoxLayout,
)


class ProtectionMeasurementBindingEditor(QGroupBox):
    """Author explicit PT/CVT source-to-RelayInput associations through Application."""

    _SOURCE_TYPES = frozenset({"bus", "line", "cable"})
    _INSTRUMENT_TYPES = {
        "pt": "PT",
        "potential_transformer": "PT",
        "cvt": "CVT",
    }

    def __init__(self, *, application: Any, parent: Any | None = None) -> None:
        super().__init__("PT/CVT Protection Measurement Binding", parent)
        if application is None or not callable(getattr(application, "execute", None)):
            raise TypeError("Protection binding editor requires Application.execute().")
        self._application = application
        self._refreshing = False
        self._network_elements: dict[str, Any] = {}
        self._functions: dict[str, Any] = {}
        self._channels: dict[str, Any] = {}
        self._instruments: dict[str, Any] = {}

        self._element = QComboBox(self)
        self._element.setObjectName("ProtectionBindingElement")
        self._relay_input = QComboBox(self)
        self._relay_input.setObjectName("ProtectionBindingRelayInput")
        self._instrument = QComboBox(self)
        self._instrument.setObjectName("ProtectionBindingInstrument")
        self._channel = QComboBox(self)
        self._channel.setObjectName("ProtectionBindingChannel")
        self._source_endpoint = QComboBox(self)
        self._source_endpoint.setObjectName("ProtectionBindingSourceEndpoint")
        self._electrical_side = QComboBox(self)
        self._electrical_side.setObjectName("ProtectionBindingElectricalSide")
        self._phase = QComboBox(self)
        self._phase.setObjectName("ProtectionBindingPhase")
        self._result_quantity = QLineEdit(self)
        self._result_quantity.setObjectName("ProtectionBindingResultQuantity")
        self._result_quantity.setPlaceholderText("Exact result quantity key expected by the protection input")
        self._ratio = QLineEdit(self)
        self._ratio.setObjectName("ProtectionBindingInstrumentRatio")
        self._ratio.setValidator(QDoubleValidator(0.000000001, 1.0e15, 9, self))
        self._ratio.setPlaceholderText("Enter the physical instrument voltage ratio explicitly")
        self._ratio_reference = QLabel("Select a PT/CVT to inspect its authoritative model ratio.", self)
        self._status = QLabel("", self)
        self._status.setWordWrap(True)
        self._existing_bindings = QListWidget(self)
        self._existing_bindings.setObjectName("ProtectionMeasurementBindingInventory")
        self._create = QPushButton("Create Protection Measurement Binding", self)
        self._create.setObjectName("CreateProtectionMeasurementBinding")
        self._create.clicked.connect(self._create_binding)

        form = QFormLayout()
        form.addRow("Protection element", self._element)
        form.addRow("RelayInput", self._relay_input)
        form.addRow("Physical PT/CVT", self._instrument)
        form.addRow("Configured voltage channel", self._channel)
        form.addRow("Measured Bus / line endpoint", self._source_endpoint)
        form.addRow("Electrical side", self._electrical_side)
        form.addRow("Phase / sequence", self._phase)
        form.addRow("Result quantity key", self._result_quantity)
        form.addRow("Instrument ratio", self._ratio)
        form.addRow("Model ratio reference", self._ratio_reference)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._create)
        layout.addWidget(QLabel("Persisted physical measurement bindings", self))
        layout.addWidget(self._existing_bindings)
        layout.addWidget(self._status)

        self._element.currentIndexChanged.connect(self._refresh_inputs)
        self._relay_input.currentIndexChanged.connect(self._refresh_input_channel)
        self._instrument.currentIndexChanged.connect(self._refresh_ratio_reference)
        self._source_endpoint.currentIndexChanged.connect(self._refresh_side_choices)
        for control in (self._element, self._relay_input, self._instrument, self._channel, self._source_endpoint, self._electrical_side, self._phase):
            control.currentIndexChanged.connect(self._update_create_enabled)
        self._ratio.textChanged.connect(self._update_create_enabled)
        self._result_quantity.textChanged.connect(self._update_create_enabled)
        self.refresh()

    @staticmethod
    def _normalized_type(value: Any) -> str:
        return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")

    @classmethod
    def _instrument_kind(cls, element: Any) -> str | None:
        kind = cls._normalized_type(getattr(element, "element_type", ""))
        if kind in cls._INSTRUMENT_TYPES:
            return cls._INSTRUMENT_TYPES[kind]
        labels = getattr(element, "labels", {}) or {}
        for key in ("type", "equipment_type", "family"):
            candidate = cls._normalized_type(labels.get(key))
            if candidate in cls._INSTRUMENT_TYPES:
                return cls._INSTRUMENT_TYPES[candidate]
        return None

    def _add_placeholder(self, combo: QComboBox, label: str = "Select explicitly…") -> None:
        combo.clear()
        combo.addItem(label, None)

    def refresh(self) -> None:
        """Rebuild all choices from detached active-project Application read models."""
        self._refreshing = True
        try:
            self._add_placeholder(self._element)
            self._add_placeholder(self._relay_input)
            self._add_placeholder(self._instrument)
            self._add_placeholder(self._channel)
            self._add_placeholder(self._source_endpoint)
            self._add_placeholder(self._electrical_side)
            self._add_placeholder(self._phase)
            self._network_elements = {}
            self._functions = {}
            self._channels = {}
            self._instruments = {}
            try:
                network = self._application.read_network()
                functions = self._application.read_protection_function_configurations()
                channel_configs = self._application.read_measurement_channel_configurations()
            except (RuntimeError, AttributeError) as exc:
                self._status.setText(f"Binding editor unavailable: {exc}")
                self._create.setEnabled(False)
                return

            self._network_elements = {str(item.object_id): item for item in network.elements}
            self._channels = {str(item.channel_id): item for item in channel_configs}
            self._instruments = {
                object_id: item for object_id, item in self._network_elements.items()
                if self._instrument_kind(item) in {"PT", "CVT"}
            }
            for configuration in sorted(functions, key=lambda item: (str(item.relay_id), str(item.element_id))):
                eligible = False
                for channel_id in configuration.input_channel_ids.values():
                    channel = self._channels.get(str(channel_id))
                    instrument = self._instruments.get(str(getattr(channel, "source_id", ""))) if channel else None
                    if (
                        channel is not None
                        and str(channel.signal_type).strip().lower() == "voltage"
                        and instrument is not None
                    ):
                        eligible = True
                        break
                if eligible:
                    self._functions[str(configuration.element_id)] = configuration
                    self._element.addItem(
                        f"{configuration.function_code} | {configuration.element_id} | Relay {configuration.relay_id}",
                        str(configuration.element_id),
                    )

            self._populate_source_endpoints(network)
            if self._element.count() > 1:
                self._refresh_inputs()
            else:
                self._status.setText(
                    "No configured protection RelayInput is currently backed by a PT/CVT voltage channel. "
                    "Configure the function input and PT/CVT secondary channel first."
                )
                self._create.setEnabled(False)
            self._refresh_existing_bindings()
        finally:
            self._refreshing = False

    def _populate_source_endpoints(self, network: Any) -> None:
        self._add_placeholder(self._source_endpoint)
        roles_by_type = getattr(self._application, "TERMINAL_ROLES_BY_TYPE", {})
        for element in sorted(network.elements, key=lambda item: (str(item.element_type), str(item.object_id))):
            kind = self._normalized_type(element.element_type)
            if kind == "bus":
                for slot in range(9):
                    endpoint = EndpointReference.bus(
                        bus_id=str(element.object_id),
                        attachment_id=f"attachment-{slot}",
                    )
                    self._source_endpoint.addItem(
                        f"BUS {element.object_id} | attachment-{slot}", endpoint
                    )
                continue
            if kind not in self._SOURCE_TYPES:
                continue
            try:
                equipment_type = EquipmentType(kind)
            except (TypeError, ValueError):
                continue
            for role in roles_by_type.get(kind, ()):
                endpoint = EndpointReference.terminal(
                    equipment_type=equipment_type,
                    equipment_id=str(element.object_id),
                    terminal_role=str(role),
                )
                self._source_endpoint.addItem(
                    f"{kind.upper()} {element.object_id} | {role}", endpoint
                )

    def _refresh_inputs(self, *_: Any) -> None:
        if self._refreshing:
            return
        self._refreshing = True
        try:
            self._add_placeholder(self._relay_input)
            self._add_placeholder(self._channel)
            self._add_placeholder(self._instrument)
            self._add_placeholder(self._phase)
            element_id = self._element.currentData()
            configuration = self._functions.get(str(element_id)) if element_id else None
            if configuration is None:
                return
            for input_name, channel_id in sorted(configuration.input_channel_ids.items()):
                channel = self._channels.get(str(channel_id))
                instrument = self._instruments.get(str(getattr(channel, "source_id", ""))) if channel else None
                if (
                    channel is None
                    or str(channel.signal_type).strip().lower() != "voltage"
                    or instrument is None
                ):
                    continue
                self._relay_input.addItem(str(input_name), (str(input_name), str(channel_id)))
            self._create.setEnabled(False)
            self._status.setText("Select a RelayInput, its configured channel, and the physical PT/CVT explicitly.")
        finally:
            self._refreshing = False

    def _refresh_input_channel(self, *_: Any) -> None:
        if self._refreshing:
            return
        self._refreshing = True
        try:
            self._add_placeholder(self._channel)
            self._add_placeholder(self._instrument)
            self._add_placeholder(self._phase)
            selection = self._relay_input.currentData()
            if not selection:
                self._create.setEnabled(False)
                return
            _, channel_id = selection
            channel = self._channels.get(str(channel_id))
            if channel is None:
                self._create.setEnabled(False)
                return
            self._channel.addItem(
                f"{channel.channel_id} | {channel.name} | {channel.signal_type} / {channel.unit}",
                str(channel.channel_id),
            )
            instrument_id = str(channel.source_id or "")
            instrument = self._instruments.get(instrument_id)
            if instrument is not None:
                self._instrument.addItem(
                    f"{self._instrument_kind(instrument)} | {instrument_id}",
                    instrument_id,
                )
            self._phase.addItem(str(channel.phase), str(channel.phase))
            self._create.setEnabled(False)
            self._refresh_ratio_reference()
            self._status.setText(
                "Channel and physical instrument are identified from the configured source; "
                "select each explicitly and enter the exact phase and ratio."
            )
        finally:
            self._refreshing = False

    def _refresh_ratio_reference(self, *_: Any) -> None:
        instrument_id = self._instrument.currentData()
        instrument = self._instruments.get(str(instrument_id)) if instrument_id else None
        if instrument is None:
            self._ratio_reference.setText("Select a PT/CVT to inspect its authoritative model ratio.")
            return
        ratio = instrument.attributes.get("voltage_ratio")
        self._ratio_reference.setText(
            "Authoritative model voltage ratio: "
            + (str(ratio) if ratio is not None else "not exposed — Application validation will reject unavailable ratio")
        )

    def _refresh_side_choices(self, *_: Any) -> None:
        if self._refreshing:
            return
        endpoint = self._source_endpoint.currentData()
        self._add_placeholder(self._electrical_side)
        if endpoint is None:
            return
        if endpoint.is_bus:
            self._electrical_side.addItem("Bus side", "bus")
        elif endpoint.terminal_role == "FROM":
            self._electrical_side.addItem("From side", "from")
        elif endpoint.terminal_role == "TO":
            self._electrical_side.addItem("To side", "to")
        else:
            self._electrical_side.addItem("Equipment terminal side", "equipment")

    def _update_create_enabled(self, *_: Any) -> None:
        if self._refreshing:
            return
        complete = all((
            self._element.currentData(), self._relay_input.currentData(),
            self._instrument.currentData(), self._channel.currentData(),
            self._source_endpoint.currentData(), self._electrical_side.currentData(),
            self._phase.currentData(), self._result_quantity.text().strip(),
            self._ratio.text().strip(),
        ))
        self._create.setEnabled(bool(complete))

    def _create_binding(self) -> None:
        element_id = self._element.currentData()
        input_selection = self._relay_input.currentData()
        instrument_id = self._instrument.currentData()
        channel_id = self._channel.currentData()
        endpoint = self._source_endpoint.currentData()
        electrical_side = self._electrical_side.currentData()
        phase = self._phase.currentData()
        result_quantity = self._result_quantity.text().strip()
        ratio_text = self._ratio.text().strip()
        if not all((element_id, input_selection, instrument_id, channel_id, endpoint, electrical_side, phase, result_quantity, ratio_text)):
            self._status.setText("Every binding field is explicit and required; complete all selections and numeric entries.")
            return
        try:
            ratio = float(ratio_text)
            if ratio <= 0:
                raise ValueError("Instrument ratio must be positive.")
            channel = self._channels[str(channel_id)]
            instrument = self._instruments[str(instrument_id)]
            if str(channel.source_id) != str(instrument_id):
                raise ValueError("Selected channel is not sourced by the selected physical PT/CVT.")
            if str(channel.phase).strip().upper() != str(phase).strip().upper():
                raise ValueError("Selected phase/sequence does not match the configured physical channel.")
            binding = ProtectionMeasurementBinding(
                binding_id=str(uuid4()),
                protection_element_id=str(element_id),
                source_equipment_id=str(endpoint.object_id),
                source_endpoint_reference=endpoint,
                electrical_side=str(electrical_side),
                measurement_type="voltage",
                phase_or_sequence=str(phase),
                result_quantity=result_quantity,
                instrument_id=str(instrument_id),
                instrument_ratio=ratio,
                channel_id=str(channel_id),
                relay_input_id=str(input_selection[0]),
            )
            result = self._application.execute(
                CreateProtectionMeasurementBindingCommand(binding=binding)
            )
        except Exception as exc:
            self._status.setText(f"Binding rejected: {exc}")
            return
        if not getattr(result, "success", False):
            self._status.setText(
                getattr(result, "message", "Application rejected the protection measurement binding.")
            )
            return
        self._ratio.clear()
        self._result_quantity.clear()
        self.refresh()
        self._status.setText(
            getattr(result, "message", "Protection measurement binding created and validated.")
        )

    def _refresh_existing_bindings(self) -> None:
        try:
            bindings = self._application.read_protection_measurement_bindings()
        except (RuntimeError, AttributeError):
            return
        self._existing_bindings.clear()
        for binding in bindings:
            endpoint = dict(binding.source_endpoint_reference)
            endpoint_label = ":".join(str(endpoint.get(key, "")) for key in ("kind", "object_id", "terminal_role", "attachment_id") if endpoint.get(key) is not None)
            self._existing_bindings.addItem(
                f"{binding.binding_id} | {binding.protection_element_id}:{binding.relay_input_id} | "
                f"{binding.instrument_id} | {binding.channel_id} | {binding.phase_or_sequence} | {endpoint_label}"
            )


__all__ = ["ProtectionMeasurementBindingEditor"]
