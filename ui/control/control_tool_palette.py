"""Capability-driven Control/Ladder tool palette.

The palette is presentation-only. A descriptor is shown only when its
Application command contract is registered by the existing Application.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

from ui.core.qt import QVBoxLayout, QPushButton, QLabel, QWidget


@dataclass(frozen=True, slots=True)
class ControlToolDescriptor:
    tool_id: str
    display_name: str
    category: str
    icon: str
    command_type: str
    component_type: str | None = None


class ControlToolPalette(QWidget):
    """Register and expose only executable Control engineering tools."""

    def __init__(self, *, application: Any, on_selected: Callable[[ControlToolDescriptor], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if application is None:
            raise ValueError("application is required.")
        if not callable(on_selected):
            raise TypeError("on_selected must be callable.")
        self._application = application
        self._on_selected = on_selected
        self._buttons: dict[str, QPushButton] = {}
        self._descriptors = self._available_descriptors()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Control Tools", self))
        categories: dict[str, list[ControlToolDescriptor]] = {}
        for descriptor in self._descriptors:
            categories.setdefault(descriptor.category, []).append(descriptor)
        for category, descriptors in categories.items():
            layout.addWidget(QLabel(category, self))
            for descriptor in descriptors:
                button = QPushButton(descriptor.display_name, self)
                button.setToolTip(descriptor.icon)
                button.clicked.connect(lambda _checked=False, d=descriptor: self._on_selected(d))
                layout.addWidget(button)
                self._buttons[descriptor.tool_id] = button
        layout.addStretch(1)

    @property
    def descriptors(self) -> tuple[ControlToolDescriptor, ...]:
        return self._descriptors

    def _available_descriptors(self) -> tuple[ControlToolDescriptor, ...]:
        candidates = (
            ControlToolDescriptor("contact.no", "Normally Open Contact", "Contacts", "[ ]", "control.add_component", "normally_open_contact"),
            ControlToolDescriptor("contact.nc", "Normally Closed Contact", "Contacts", "[/]", "control.add_component", "normally_closed_contact"),
            ControlToolDescriptor("coil", "Coil", "Outputs", "( )", "control.add_component", "coil"),
            ControlToolDescriptor("set", "Set", "Outputs", "(S)", "control.add_component", "set_coil"),
            ControlToolDescriptor("reset", "Reset", "Outputs", "(R)", "control.add_component", "reset_coil"),
            ControlToolDescriptor("timer", "Timer", "Timing", "[TON]", "control.add_component", "timer"),
            ControlToolDescriptor("latch", "Latch", "Logic", "[L]", "control.add_component", "latch"),
            ControlToolDescriptor("and", "AND", "Logic", "[AND]", "control.add_component", "and_gate"),
            ControlToolDescriptor("or", "OR", "Logic", "[OR]", "control.add_component", "or_gate"),
            ControlToolDescriptor("not", "NOT", "Logic", "[NOT]", "control.add_component", "not_gate"),
            ControlToolDescriptor("interlock", "Interlock", "Control", "[ILK]", "control.add_component", "interlock"),
            ControlToolDescriptor("action_binding", "Action Binding", "Control", "=>", "control.add_action_binding"),
        )
        return tuple(
            descriptor
            for descriptor in candidates
            if self._application.supports(descriptor.command_type)
        )


__all__ = ["ControlToolDescriptor", "ControlToolPalette"]
