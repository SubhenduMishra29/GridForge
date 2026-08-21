# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/properties_panel.py
#
# Purpose:
#     Selected-object properties panel.
#
# Architectural boundary:
#     Logical panel only. The authoritative selected object and
#     electrical model remain outside the panel.
# ============================================================

from __future__ import annotations

from typing import Any

from .panel_base import PanelBase


class PropertiesPanel(PanelBase):
    """
    Properties inspector panel.

    The panel stores only the currently inspected presentation
    target. It does not own the underlying electrical object.
    """

    _PANEL_ID = "properties"
    _TITLE = "Properties"

    def __init__(self) -> None:
        self._created = False
        self._visible = False
        self._active = False
        self._target: Any | None = None

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

    @property
    def target(self) -> Any | None:
        """Return the current inspection target."""
        return self._target

    def set_target(
        self,
        target: Any | None,
    ) -> None:
        """
        Set the object currently being inspected.

        The panel stores only a reference; it does not become the
        owner of the target.
        """

        self._target = target

    def clear_target(self) -> None:
        """Clear the current inspection target."""
        self._target = None

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
        self._target = None
        self._active = False
        self._visible = False
        self._created = False

    def reset(self) -> None:
        """Reset the transient inspection target."""
        self._target = None
        self._active = False

