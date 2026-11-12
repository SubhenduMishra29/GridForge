# ============================================================
# GridForge V2 — CT Secondary Measurement Channel Editor
# ============================================================

"""Engineer-facing CT secondary-channel authoring surface.

This widget stages presentation values only. It reads detached
MeasurementChannelReadModel snapshots and submits immutable commands
through Application.execute(); it never touches Core equipment or
MeasurementChannel objects directly.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4
from weakref import ref

from core.application.errors import ExecutionError
from core.application.events import MeasurementChannelChanged
from core.application.commands.measurement_commands import (
    CreateMeasurementChannelCommand,
    DeleteMeasurementChannelCommand,
    UpdateMeasurementChannelCommand,
)
from ui.core.qt import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CTSecondaryChannelEditor(QGroupBox):
    """Create, inspect, update and delete channels for one selected CT."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("CT Secondary Measurement Channels", parent)
        self.setObjectName("CTSecondaryChannelEditor")
        self._application: Any | None = None
        self._target_id: str | None = None
        self._refreshing = False
        self._channels_by_id: dict[str, Any] = {}
        self._samples_by_id: dict[str, Any] = {}
        self._event_callback: Any | None = None

        self._channel_selector = QComboBox(self)
        self._channel_selector.setObjectName("CTSecondaryChannelSelector")
        self._channel_selector.currentIndexChanged.connect(self._load_selected_channel)

        self._channel_id = QLineEdit(self)
        self._channel_id.setObjectName("CTSecondaryChannelId")
        self._channel_id.setPlaceholderText("Unique channel identity")

        self._name = QLineEdit(self)
        self._name.setObjectName("CTSecondaryChannelName")
        self._name.setPlaceholderText("Optional engineer-facing name")

        self._terminal = QComboBox(self)
        self._terminal.setObjectName("CTSecondaryTerminal")
        self._terminal.addItem("S1 — secondary winding terminal", "S1")
        self._terminal.addItem("S2 — secondary winding terminal", "S2")

        self._phase = QComboBox(self)
        self._phase.setObjectName("CTSecondaryChannelPhase")
        for phase in ("A", "B", "C", "N"):
            self._phase.addItem(phase, phase)

        self._nominal = self._number("CTSecondaryNominalValue", 5.0, 0.000001, 100000000.0, 6)
        self._scale = self._number("CTSecondaryScale", 1.0, 0.000001, 100000000.0, 9)
        self._polarity = QComboBox(self)
        self._polarity.setObjectName("CTSecondaryPolarity")
        self._polarity.addItem("+1.0 — normal", 1.0)
        self._polarity.addItem("-1.0 — reversed", -1.0)

        self._producer = QLineEdit(self)
        self._producer.setObjectName("CTSecondaryProducerId")
        self._producer.setPlaceholderText("Exact trusted producer identity")

        self._timestamp_domain = QLineEdit(self)
        self._timestamp_domain.setObjectName("CTSecondaryTimestampDomain")
        self._timestamp_domain.setPlaceholderText("Must match trusted Application clock domain")

        self._stale_after = self._number("CTSecondaryStaleAfter", 2.0, 0.001, 86400.0, 3)

        form = QFormLayout()
        form.addRow("Existing channel", self._channel_selector)
        form.addRow("Channel ID", self._channel_id)
        form.addRow("Name", self._name)
        form.addRow("Physical CT terminal", self._terminal)
        form.addRow("Signal / unit", QLabel("CURRENT / A", self))
        form.addRow("Phase", self._phase)
        form.addRow("Nominal secondary current (A)", self._nominal)
        form.addRow("Channel scale", self._scale)
        form.addRow("Polarity", self._polarity)
        form.addRow("Producer identity", self._producer)
        form.addRow("Timestamp domain", self._timestamp_domain)
        form.addRow("Stale after (seconds)", self._stale_after)

        self._status = QLabel(
            "Select a committed Current Transformer to author its S1/S2 channels.",
            self,
        )
        self._status.setObjectName("CTSecondaryChannelStatus")
        self._status.setWordWrap(True)

        self._new_button = QPushButton("New Channel", self)
        self._new_button.setObjectName("NewCTSecondaryChannel")
        self._create_button = QPushButton("Create Channel", self)
        self._create_button.setObjectName("CreateCTSecondaryChannel")
        self._update_button = QPushButton("Update Selected", self)
        self._update_button.setObjectName("UpdateCTSecondaryChannel")
        self._delete_button = QPushButton("Delete Selected", self)
        self._delete_button.setObjectName("DeleteCTSecondaryChannel")
        actions = QHBoxLayout()
        actions.addWidget(self._new_button)
        actions.addWidget(self._create_button)
        actions.addWidget(self._update_button)
        actions.addWidget(self._delete_button)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addLayout(actions)
        root.addWidget(self._status)

        self._new_button.clicked.connect(self._new_channel)
        self._create_button.clicked.connect(self._create_channel)
        self._update_button.clicked.connect(self._update_channel)
        self._delete_button.clicked.connect(self._delete_channel)
        self._set_enabled(False)
        self.hide()

    @staticmethod
    def _number(
        object_name: str,
        default: float,
        minimum: float,
        maximum: float,
        decimals: int,
    ) -> QDoubleSpinBox:
        control = QDoubleSpinBox()
        control.setObjectName(object_name)
        control.setRange(minimum, maximum)
        control.setDecimals(decimals)
        control.setValue(default)
        return control

    def bind_application(self, application: Any) -> None:
        if application is None or not callable(getattr(application, "execute", None)):
            raise TypeError("CT channel editor requires the canonical Application.execute() boundary.")
        if not callable(getattr(application, "read_measurement_channel_configurations", None)) or not callable(getattr(application, "read_measurement_channels", None)):
            raise TypeError("Application must expose detached channel configuration and telemetry read APIs.")
        previous_bus = getattr(self._application, "event_bus", None)
        if previous_bus is not None and self._event_callback is not None:
            previous_bus.unsubscribe(MeasurementChannelChanged, self._event_callback)
        self._application = application
        owner_ref = ref(self)

        def refresh_owner(event: MeasurementChannelChanged) -> None:
            owner = owner_ref()
            if owner is not None:
                owner._on_measurement_channel_changed(event)

        self._event_callback = refresh_owner
        application.event_bus.subscribe(MeasurementChannelChanged, refresh_owner)
        self._refresh_channels()

    def _on_measurement_channel_changed(self, event: MeasurementChannelChanged) -> None:
        payload = getattr(event, "payload", {})
        source_id = payload.get("source_id") if callable(getattr(payload, "get", None)) else None
        if self._target_id is not None and source_id in {None, self._target_id}:
            self._refresh_channels()

    def set_target(self, projection: Any | None) -> None:
        """Show only for a committed CurrentTransformer projection."""
        target_id = None
        if projection is not None and getattr(projection, "identity_kind", None) == "element":
            display_type = str(getattr(projection, "display_type", "")).strip().lower()
            attributes = getattr(projection, "attributes", {}) or {}
            equipment_type = str(attributes.get("equipment_type", "")).strip().lower()
            normalized = display_type.replace(" ", "_").replace("-", "_")
            if normalized in {"current_transformer", "currenttransformer", "ct"} or equipment_type == "current_transformer":
                candidate = str(getattr(projection, "object_id", "")).strip()
                target_id = candidate or None
        self._target_id = target_id
        self.setVisible(target_id is not None)
        self._refresh_channels()

    def _set_enabled(self, enabled: bool) -> None:
        for control in (
            self._channel_selector, self._channel_id, self._name, self._terminal,
            self._phase, self._nominal, self._scale, self._polarity,
            self._producer, self._timestamp_domain, self._stale_after,
        ):
            control.setEnabled(enabled)
        self._new_button.setEnabled(enabled)
        self._create_button.setEnabled(enabled)
        self._update_button.setEnabled(False)
        self._delete_button.setEnabled(False)

    def _refresh_channels(self) -> None:
        if self._application is None or self._target_id is None:
            self._channels_by_id = {}
            self._samples_by_id = {}
            self._set_enabled(False)
            self._refreshing = True
            try:
                self._channel_selector.clear()
            finally:
                self._refreshing = False
            return
        try:
            channels = tuple(
                item for item in self._application.read_measurement_channel_configurations()
                if item.source_id == self._target_id
                and item.source_terminal_reference.get("terminal_role") in {"S1", "S2"}
                and item.signal_type == "CURRENT"
            )
            samples = {
                item.channel_id: item
                for item in self._application.read_measurement_channels()
            }
        except (RuntimeError, TypeError, ValueError) as exc:
            self._channels_by_id = {}
            self._samples_by_id = {}
            self._refreshing = True
            try:
                self._channel_selector.clear()
            finally:
                self._refreshing = False
            self._status.setText(f"Measurement channels unavailable: {exc}")
            self._set_enabled(False)
            return

        self._channels_by_id = {item.channel_id: item for item in channels}
        self._samples_by_id = samples
        self._refreshing = True
        try:
            selected_id = self._channel_selector.currentData()
            self._channel_selector.clear()
            for channel in channels:
                label = (
                    f"{channel.channel_id} · {channel.source_terminal_reference.get('terminal_role')} · "
                    f"{channel.phase}"
                )
                self._channel_selector.addItem(label, channel.channel_id)
            selected_index = self._channel_selector.findData(selected_id)
            if selected_index >= 0:
                self._channel_selector.setCurrentIndex(selected_index)
            elif self._channel_selector.count():
                self._channel_selector.setCurrentIndex(0)
        finally:
            self._refreshing = False

        self._set_enabled(True)
        self._channel_id.setReadOnly(self._channel_selector.currentIndex() >= 0)
        self._update_button.setEnabled(self._channel_selector.currentIndex() >= 0)
        self._delete_button.setEnabled(self._channel_selector.currentIndex() >= 0)
        if channels:
            self._load_selected_channel()
        else:
            self._reset_definition()
            self._status.setText(
                f"CT {self._target_id}: no S1/S2 measurement channels are authored yet. "
                "A channel remains unavailable until a trusted producer publishes an authenticated sample."
            )

    def _load_selected_channel(self, *_args: Any) -> None:
        if self._refreshing or self._application is None:
            return
        channel_id = self._channel_selector.currentData()
        if not channel_id:
            self._channel_id.setReadOnly(False)
            self._update_button.setEnabled(False)
            self._delete_button.setEnabled(False)
            return
        channel = self._channels_by_id.get(str(channel_id))
        if channel is None:
            return
        self._channel_id.setText(channel.channel_id)
        self._channel_id.setReadOnly(True)
        self._name.setText(channel.name or "")
        self._terminal.setCurrentIndex(max(0, self._terminal.findData(channel.source_terminal_reference.get("terminal_role"))))
        self._phase.setCurrentIndex(max(0, self._phase.findData(channel.phase)))
        self._nominal.setValue(float(channel.nominal_value or 5.0))
        self._scale.setValue(float(channel.scale or 1.0))
        self._polarity.setCurrentIndex(max(0, self._polarity.findData(float(channel.polarity or 1.0))))
        self._producer.setText(channel.producer_id or "")
        self._producer.setReadOnly(True)
        self._timestamp_domain.setText(channel.timestamp_domain or "")
        self._timestamp_domain.setReadOnly(True)
        self._stale_after.setValue(float(channel.stale_after or 2.0))
        self._update_button.setEnabled(True)
        self._delete_button.setEnabled(True)
        sample = getattr(self, "_samples_by_id", {}).get(channel.channel_id)
        self._status.setText(
            f"{channel.channel_id} · {channel.source_terminal_reference.get('terminal_role')} · "
            + (
                f"{sample.quality} / {sample.validity} · "
                + ("live sample available" if sample.available else "awaiting trusted sample")
                if sample is not None else "sample telemetry unavailable"
            )
        )

    def _new_channel(self) -> None:
        self._refreshing = True
        try:
            self._channel_selector.setCurrentIndex(-1)
        finally:
            self._refreshing = False
        self._reset_definition()
        self._status.setText("Enter a new channel ID and explicit producer and timestamp identities, then create the S1/S2 channel.")

    def _reset_definition(self) -> None:
        self._channel_id.clear()
        self._channel_id.setReadOnly(False)
        self._name.clear()
        self._terminal.setCurrentIndex(0)
        self._phase.setCurrentIndex(max(0, self._phase.findData("A")))
        self._nominal.setValue(5.0)
        self._scale.setValue(1.0)
        self._polarity.setCurrentIndex(0)
        self._producer.clear()
        self._producer.setReadOnly(False)
        self._timestamp_domain.setText(
            str(getattr(self._application, "measurement_clock_domain", None) or "")
        )
        self._timestamp_domain.setReadOnly(True)
        self._stale_after.setValue(2.0)
        self._update_button.setEnabled(False)
        self._delete_button.setEnabled(False)

    def _definition(self) -> dict[str, Any]:
        if not self._target_id:
            raise RuntimeError("Select a committed Current Transformer first.")
        channel_id = self._channel_id.text().strip()
        producer_id = self._producer.text().strip()
        timestamp_domain = self._timestamp_domain.text().strip()
        if not channel_id:
            raise ValueError("Channel ID is required.")
        if not producer_id:
            raise ValueError("Producer identity is required; it is never inferred.")
        if not timestamp_domain:
            raise ValueError("A trusted Application measurement clock domain must be configured before authoring channels.")
        if self._application is not None and timestamp_domain != getattr(self._application, "measurement_clock_domain", None):
            raise ValueError("Channel timestamp domain must match the configured trusted Application clock domain.")
        terminal_role = str(self._terminal.currentData())
        return {
            "channel_id": channel_id,
            "name": self._name.text().strip(),
            "source": self._target_id,
            "source_terminal": {
                "kind": "terminal",
                "equipment_type": "ct",
                "object_id": self._target_id,
                "terminal_role": terminal_role,
            },
            "signal_type": "CURRENT",
            "phase": str(self._phase.currentData()),
            "unit": "A",
            "nominal_value": float(self._nominal.value()),
            "scale": float(self._scale.value()),
            "polarity": float(self._polarity.currentData()),
            "producer_id": producer_id,
            "timestamp_domain": timestamp_domain,
            "stale_after": float(self._stale_after.value()),
        }

    def _submit(self, command: Any, success_message: str) -> None:
        try:
            result = self._application.execute(command)
            if not getattr(result, "success", False):
                raise ValueError(getattr(result, "message", None) or "Application rejected the channel command.")
        except (ExecutionError, KeyError, RuntimeError, TypeError, ValueError) as exc:
            self._status.setText(f"Channel change rejected: {exc}")
            return
        self._status.setText(success_message)
        self._refresh_channels()

    def _create_channel(self) -> None:
        try:
            definition = self._definition()
            command = CreateMeasurementChannelCommand(definition=definition)
        except (TypeError, ValueError, RuntimeError) as exc:
            self._status.setText(f"Channel definition invalid: {exc}")
            return
        self._submit(command, f"Created CT secondary channel {definition['channel_id']}.")

    def _update_channel(self) -> None:
        channel_id = self._channel_selector.currentData()
        if not channel_id:
            self._status.setText("Select an existing channel to update.")
            return
        try:
            definition = self._definition()
            command = UpdateMeasurementChannelCommand(
                channel_id=str(channel_id),
                definition=definition,
            )
        except (TypeError, ValueError, RuntimeError) as exc:
            self._status.setText(f"Channel definition invalid: {exc}")
            return
        self._submit(command, f"Updated CT secondary channel {channel_id}.")

    def _delete_channel(self) -> None:
        channel_id = self._channel_selector.currentData()
        if not channel_id:
            self._status.setText("Select an existing channel to delete.")
            return
        self._submit(
            DeleteMeasurementChannelCommand(channel_id=str(channel_id)),
            f"Deleted CT secondary channel {channel_id}.",
        )


__all__ = ["CTSecondaryChannelEditor"]
