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

Public API
----------
Theme and StyleManager provide application-level theme configuration.
StyleTokens and the presentation helpers provide the canonical token and
visual-state styling API. `palette_visual_pen` is the palette-specific
contrast helper; `visual_pen` remains the canonical engineering/canvas
pen helper.
"""

from __future__ import annotations

from .theme import DEFAULT_THEME, Theme
from .style_manager import (
    StyleManager,
    StyleManagerError,
    StylesheetApplyError,
    StylesheetLoadError,
)
from .style_tokens import DEFAULT_STYLE_TOKENS, StyleTokens
from .presentation_style import (
    PresentationState,
    VisualState,
    palette_visual_pen,
    resolve_style_tokens,
    token_color,
    visual_brush,
    visual_font,
    visual_pen,
)

__all__ = [
    "DEFAULT_THEME",
    "Theme",
    "StyleManager",
    "StyleManagerError",
    "StylesheetApplyError",
    "StylesheetLoadError",
    "DEFAULT_STYLE_TOKENS",
    "StyleTokens",
    "PresentationState",
    "VisualState",
    "resolve_style_tokens",
    "token_color",
    "visual_pen",
    "palette_visual_pen",
    "visual_brush",
    "visual_font",
]
