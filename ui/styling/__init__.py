# ============================================================
# File: ui/styling/__init__.py
# GridForge V2 — UI Styling Package
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 UI Styling
=======================

The `ui.styling` package contains presentation-level styling
infrastructure for the GridForge graphical interface.

The styling subsystem is presentation infrastructure only. It does not own
application state, engineering state, Core models, network topology,
controllers, commands, tools, selection, canvas behavior, renderers,
plugins, or engineering calculations.
"""

from __future__ import annotations

from .theme import DEFAULT_THEME, Theme
from .style_manager import (
    StyleManager,
    StyleManagerError,
    StylesheetApplyError,
    StylesheetLoadError,
)

__all__ = [
    "DEFAULT_THEME",
    "Theme",
    "StyleManager",
    "StyleManagerError",
    "StylesheetApplyError",
    "StylesheetLoadError",
]
