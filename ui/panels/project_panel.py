# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/project_panel.py
#
# Author:
#     Subhendu Mishra
#
# Purpose:
#     Presentation-only project/document hierarchy panel.
#
# Responsibilities:
#     - Own panel-local lifecycle state.
#     - Hold externally supplied projected hierarchy data.
#     - Present Project / Document structure to the user.
#     - Provide a stable presentation boundary for future intents.
#
# Architectural boundary:
#     This panel does not own Project, Document, SLDDocument, Core,
#     persistence, commands, workspace layout, selection authority,
#     or Qt docking/realization.
#
#     Read path:
#         Project / Document state
#             -> Projection / ViewState
#             -> ProjectPanel.set_hierarchy()
#             -> presentation
#
#     Write path (future actions):
#         user intent
#             -> command / application boundary
#             -> authoritative Project / Document state
#             -> event
#             -> Projection / ViewState
#             -> ProjectPanel
#
#     The panel must never mutate the supplied hierarchy directly.
# ============================================================

from __future__ import annotations

from typing import Any

from .panel_base import PanelBase


class ProjectPanel(PanelBase):
    """Logical project/document hierarchy panel.

    The panel is deliberately Qt-independent.  Workspace and docking
    realization belong to the workspace/presentation shell, while project
    and document authority belongs outside the panel.
    """

    _PANEL_ID = "project"
    _TITLE = "Project Explorer"

    def __init__(self) -> None:
        self._created = False
        self._visible = False
        self._active = False
        self._hierarchy: Any | None = None

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
    # Project/document presentation data
    # --------------------------------------------------------

    @property
    def hierarchy(self) -> Any | None:
        """Return the current externally-owned projected hierarchy.

        This is presentation input only.  The panel does not own or mutate
        the underlying Project, Document, SLDDocument, or Core state.
        """
        return self._hierarchy

    def set_hierarchy(self, hierarchy: Any | None) -> None:
        """Set the projected project/document hierarchy.

        The supplied object should normally be a Projection/ViewState
        representation.  Ownership remains with the caller.
        """
        self._hierarchy = hierarchy

    def clear_hierarchy(self) -> None:
        """Clear the current project/document presentation data."""
        self._hierarchy = None

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
        self._hierarchy = None
        self._active = False
        self._visible = False
        self._created = False

    def reset(self) -> None:
        """Reset transient presentation state without destroying the panel."""
        self._hierarchy = None
        self._active = False
