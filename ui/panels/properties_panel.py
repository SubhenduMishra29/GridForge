# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/properties_panel.py
#
# Author:
#     Subhendu Mishra
#
# Purpose:
#     Presentation-only properties inspector panel.
#
# Responsibilities:
#     - Own the logical inspection target for this panel.
#     - Expose panel lifecycle state through PanelBase.
#     - Accept already-projected inspection data without owning it.
#     - Provide a stable place for future property-edit intents.
#
# Architectural boundary:
#     This panel is a Presentation-layer component.
#     It does not own Core electrical truth, SLDDocument truth,
#     persistence, commands, tools, selection authority, or Qt
#     widget realization.
#
#     Read path:
#         Core/Application event
#             -> Projection / ViewState
#             -> PropertiesPanel.set_target()
#             -> presentation
#
#     Write path (future edits):
#         user intent
#             -> command / application boundary
#             -> Core or authoritative document state
#             -> event
#             -> Projection / ViewState
#             -> PropertiesPanel
#
#     The panel must never mutate the inspected target directly.
# ============================================================

from __future__ import annotations

from typing import Any

from .panel_base import PanelBase


class PropertiesPanel(PanelBase):
    """Logical properties-inspector panel.

    ``PropertiesPanel`` deliberately contains no Qt widgets.  The panel
    lifecycle is logical and is realized by the presentation shell.

    The inspection target is treated as externally owned presentation
    data.  Holding a reference does not transfer ownership and does not
    authorize mutation of the underlying Core or document object.
    """

    _PANEL_ID = "properties"
    _TITLE = "Properties"

    def __init__(self) -> None:
        self._created = False
        self._visible = False
        self._active = False
        self._target: Any | None = None

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    @property
    def panel_id(self) -> str:
        """Return the stable logical panel identifier."""
        return self._PANEL_ID

    @property
    def title(self) -> str:
        """Return the human-readable panel title."""
        return self._TITLE

    # --------------------------------------------------------
    # Lifecycle state
    # --------------------------------------------------------

    @property
    def is_created(self) -> bool:
        """Return whether logical panel creation has completed."""
        return self._created

    @property
    def is_visible(self) -> bool:
        """Return whether the panel is logically visible."""
        return self._visible

    @property
    def is_active(self) -> bool:
        """Return whether the panel is logically active."""
        return self._active

    # --------------------------------------------------------
    # Inspection target
    # --------------------------------------------------------

    @property
    def target(self) -> Any | None:
        """Return the current externally-owned inspection target.

        The returned object is presentation input only.  Callers must not
        use the panel as a route for direct domain mutation.
        """
        return self._target

    def set_target(self, target: Any | None) -> None:
        """Set the current inspection target.

        ``target`` should normally be a projected/ViewState-compatible
        representation.  The panel does not copy, mutate, or take
        ownership of it.
        """
        self._target = target

    def clear_target(self) -> None:
        """Clear the current inspection target."""
        self._target = None

    # --------------------------------------------------------
    # Lifecycle hooks
    # --------------------------------------------------------

    def on_create(self) -> None:
        """Initialize panel-local logical state."""
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
        """Release panel-local transient state."""
        self._target = None
        self._active = False
        self._visible = False
        self._created = False

    def reset(self) -> None:
        """Reset transient inspection state without destroying the panel."""
        self._target = None
        self._active = False
