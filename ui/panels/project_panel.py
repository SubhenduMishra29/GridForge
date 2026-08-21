# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/project_panel.py
#
# Purpose:
#     Project / network hierarchy panel.
#
# Architectural boundary:
#     Logical panel only. Docking and Workspace placement belong
#     to the Workspace / realization layer.
# ============================================================

from __future__ import annotations

from .panel_base import PanelBase


class ProjectPanel(PanelBase):
    """
    Project and network hierarchy panel.

    The panel owns only its presentation-level transient state.
    The authoritative project/network model remains outside the
    panel.
    """

    _PANEL_ID = "project"
    _TITLE = "Project Explorer"

    def __init__(self) -> None:
        self._created = False
        self._visible = False
        self._active = False

    @property
    def panel_id(self) -> str:
        """Return the stable panel identifier."""
        return self._PANEL_ID

    @property
    def title(self) -> str:
        """Return the human-readable panel title."""
        return self._TITLE

    @property
    def is_created(self) -> bool:
        """Return whether the panel lifecycle has started."""
        return self._created

    @property
    def is_visible(self) -> bool:
        """Return the current logical visibility state."""
        return self._visible

    @property
    def is_active(self) -> bool:
        """Return the current logical activation state."""
        return self._active

    def on_create(self) -> None:
        """Initialize panel-local transient state."""
        self._created = True

    def on_show(self) -> None:
        """Mark the panel logically visible."""
        self._visible = True

    def on_hide(self) -> None:
        """Mark the panel logically hidden."""
        self._visible = False

    def on_activate(self) -> None:
        """Mark the panel logically active."""
        self._active = True

    def on_deactivate(self) -> None:
        """Mark the panel logically inactive."""
        self._active = False

    def on_destroy(self) -> None:
        """Release panel-local lifecycle state."""
        self._active = False
        self._visible = False
        self._created = False

    def reset(self) -> None:
        """Reset transient panel state."""
        self._active = False
