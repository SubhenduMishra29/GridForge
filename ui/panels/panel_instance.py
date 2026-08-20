# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/panel_instance.py
#
# Purpose:
#     Represents a runtime instance of a registered panel.
#
# Architectural Role:
#     Couples a PanelBase implementation with persistent panel
#     state without coupling the panel to Qt docking.
#
# Responsibilities:
#     - lifecycle state;
#     - panel object;
#     - visibility;
#     - activation;
#     - destruction.
#
# Does NOT:
#     - create QDockWidget;
#     - directly alter MainWindow.
#
# ============================================================

"""
GridForge V2 — Panel Instance.
"""

from __future__ import annotations

from .panel_base import PanelBase
from .panel_descriptor import PanelDescriptor
from .panel_state import PanelState


class PanelInstance:
    """
    Runtime instance of a registered panel.
    """

    def __init__(
        self,
        descriptor: PanelDescriptor,
        panel: PanelBase,
    ) -> None:
        if descriptor is None:
            raise ValueError(
                "descriptor must not be None"
            )

        if panel is None:
            raise ValueError(
                "panel must not be None"
            )

        if panel.panel_id != descriptor.panel_id:
            raise ValueError(
                "Panel ID does not match descriptor"
            )

        self._descriptor = descriptor
        self._panel = panel

        self._state = PanelState(
            visible=descriptor.visible_by_default,
            area=descriptor.area,
        )

        self._created = False
        self._destroyed = False

    @property
    def descriptor(self) -> PanelDescriptor:
        return self._descriptor

    @property
    def panel(self) -> PanelBase:
        return self._panel

    @property
    def state(self) -> PanelState:
        return self._state

    @property
    def created(self) -> bool:
        return self._created

    @property
    def destroyed(self) -> bool:
        return self._destroyed

    def create(self) -> None:
        if self._destroyed:
            raise RuntimeError(
                "Cannot create a destroyed panel"
            )

        if self._created:
            return

        self._panel.on_create()
        self._created = True

        if self._state.visible:
            self._panel.on_show()

    def show(self) -> None:
        self.create()

        if not self._state.visible:
            self._state.show()
            self._panel.on_show()

    def hide(self) -> None:
        if not self._created:
            return

        if self._state.visible:
            self._state.hide()
            self._panel.on_hide()

    def activate(self) -> None:
        self.create()

        self._state.activate()
        self._panel.on_activate()

    def deactivate(self) -> None:
        if not self._created:
            return

        if self._state.active:
            self._state.deactivate()
            self._panel.on_deactivate()

    def reset(self) -> None:
        self._panel.reset()

    def destroy(self) -> None:
        if self._destroyed:
            return

        if self._created:
            self._panel.on_destroy()

        self._created = False
        self._destroyed = True
