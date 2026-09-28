"""Engineer-facing Protection workspace over the canonical Application read boundary."""

from __future__ import annotations

from typing import Any

from core.application.events import ElementCreated, ElementRemoved, ElementUpdated, NetworkChanged, ProjectClosed, ProjectLoaded
from ui.core.qt import QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget


class ProtectionWorkspace(QWidget):
    """Read-only Protection workspace; all domain state remains Application/Core owned."""

    workspace_id = "protection"
    _EVENT_TYPES = (ElementCreated, ElementRemoved, ElementUpdated, NetworkChanged, ProjectLoaded, ProjectClosed)

    def __init__(self, *, application: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if application is None:
            raise ValueError("application is required.")
        self._application = application
        self._subscriptions: list[tuple[type, Any]] = []
        self._relay_list = QListWidget(self)
        self._details = QLabel("Select a relay.", self)
        self._details.setWordWrap(True)
        refresh = QPushButton("Refresh Protection", self)
        refresh.clicked.connect(lambda _checked=False: self.refresh())
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Protection Engineering", self))
        layout.addWidget(refresh)
        layout.addWidget(self._relay_list, 1)
        layout.addWidget(self._details)
        self._relay_list.currentRowChanged.connect(self._selection_changed)
        for event_type in self._EVENT_TYPES:
            application.event_bus.subscribe(event_type, self._on_application_event)
            self._subscriptions.append((event_type, self._on_application_event))
        self.refresh()

    def refresh(self) -> None:
        self._relay_list.clear()
        try:
            protection = self._application.read_protection()
        except RuntimeError:
            self._details.setText("Protection: no active project/read boundary.")
            return
        for relay in protection.relays:
            status = "TRIPPED" if relay.tripped else "PICKED UP" if relay.picked_up else "READY"
            self._relay_list.addItem(f"{relay.name} [{relay.relay_type}] — {status}")
        self._details.setText(
            f"Protection read boundary: {len(protection.relays)} relay(s). "
            "Relay identity and state are sourced from ProtectionReadService."
        )

    def _selection_changed(self, row: int) -> None:
        try:
            protection = self._application.read_protection()
        except RuntimeError:
            return
        if row < 0 or row >= len(protection.relays):
            return
        relay = protection.relays[row]
        self._details.setText(
            f"Relay: {relay.name}\n"
            f"ID: {relay.object_id}\n"
            f"Type: {relay.relay_type}\n"
            f"Function: {relay.function_type}\n"
            f"In service: {relay.in_service}\n"
            f"Enabled: {relay.enabled}\n"
            f"Blocked: {relay.blocked}\n"
            f"Picked up: {relay.picked_up}\n"
            f"Tripped: {relay.tripped}\n"
            f"Measurement inputs: {len(relay.input_channel_bindings)}"
        )

    def _on_application_event(self, _event: Any) -> None:
        self.refresh()

    def dispose(self) -> None:
        for event_type, handler in tuple(self._subscriptions):
            self._application.event_bus.unsubscribe(event_type, handler)
        self._subscriptions.clear()


__all__ = ["ProtectionWorkspace"]
