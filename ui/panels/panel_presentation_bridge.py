# ============================================================
# File: ui/panels/panel_presentation_bridge.py
# GridForge V2 — Panel Presentation Bridge
# Author: Subhendu Mishra
# ============================================================
"""Translate logical panel lifecycle state into existing Qt presentation."""

from __future__ import annotations

from dataclasses import dataclass

from ui.plugins.panels_plugin import PanelsPlugin

from .panel_instance import PanelInstance


@dataclass(frozen=True, slots=True)
class PanelPresentationState:
    """Read-only presentation projection of logical PanelState."""

    panel_id: str
    visible: bool
    active: bool

    @classmethod
    def from_instance(cls, instance: PanelInstance) -> "PanelPresentationState":
        if not isinstance(instance, PanelInstance):
            raise TypeError("instance must be PanelInstance.")
        return cls(
            panel_id=instance.descriptor.panel_id,
            visible=instance.state.visible,
            active=instance.state.active,
        )


class PanelPresentationBridge:
    """Canonical logical-state -> QWidget synchronization boundary."""

    def __init__(self, panels_plugin: PanelsPlugin) -> None:
        if not isinstance(panels_plugin, PanelsPlugin):
            raise TypeError("panels_plugin must be PanelsPlugin.")
        self._panels_plugin = panels_plugin

    def sync(self, instance: PanelInstance) -> PanelPresentationState:
        """Apply logical lifecycle state without creating a second source of truth."""
        state = PanelPresentationState.from_instance(instance)
        dock = self._panels_plugin.get_dock(state.panel_id)
        widget = self._panels_plugin.get_panel(state.panel_id)
        if dock is not None:
            dock.setVisible(state.visible)
        if widget is not None:
            widget.setVisible(state.visible)
        return state


__all__ = ["PanelPresentationBridge", "PanelPresentationState"]
