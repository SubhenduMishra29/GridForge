# `ui/panels/panel_base.py`

# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/panel_base.py
#
# Purpose:
#     Defines the logical contract for a GridForge V2 panel.
#
# Architectural Role:
#     Provides a toolkit-independent panel interface.
#
# Responsibilities:
#     - panel identity;
#     - lifecycle;
#     - visibility state;
#     - activation;
#     - reset behavior.
#
# Does NOT:
#     - create QDockWidget;
#     - directly manipulate MainWindow;
#     - own Core state.
#
# ============================================================

"""
GridForge V2 — Panel Base Contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class PanelBase(ABC):
    """
    Abstract logical panel contract.

    Concrete panels implement their own domain-specific behavior while
    the workspace manages lifecycle and visibility.
    """

    @property
    @abstractmethod
    def panel_id(self) -> str:
        """
        Stable unique panel identifier.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def title(self) -> str:
        """
        Human-readable panel title.
        """
        raise NotImplementedError

    def on_create(self) -> None:
        """
        Called when the panel instance is created.

        Default implementation intentionally does nothing.
        """

    def on_show(self) -> None:
        """
        Called when the panel becomes visible.
        """

    def on_hide(self) -> None:
        """
        Called when the panel becomes hidden.
        """

    def on_activate(self) -> None:
        """
        Called when the panel becomes active.
        """

    def on_deactivate(self) -> None:
        """
        Called when the panel loses activation.
        """

    def on_destroy(self) -> None:
        """
        Called before the panel instance is destroyed.
        """

    def reset(self) -> None:
        """
        Reset panel-specific transient state.

        Concrete panels may override this.
        """
