# ============================================================
# File: ui/styling/theme.py
# GridForge V2 — UI Theme Infrastructure
# Author: Subhendu Mishra
# ============================================================
"""Immutable presentation theme definition for GridForge V2."""

from __future__ import annotations

from dataclasses import dataclass, field

from .style_tokens import DEFAULT_STYLE_TOKENS, StyleTokens


@dataclass(frozen=True, slots=True)
class Theme:
    """Presentation-only theme; it contains no Qt or engineering state."""

    name: str
    application_background: str
    panel_background: str
    canvas_background: str
    foreground: str
    secondary_foreground: str
    disabled_foreground: str
    accent: str
    border: str
    selection: str
    toolbar_background: str
    statusbar_background: str
    font_family: str
    font_size: int
    tokens: StyleTokens = field(default_factory=lambda: DEFAULT_STYLE_TOKENS)

    def __post_init__(self) -> None:
        for name in (
            "name", "application_background", "panel_background",
            "canvas_background", "foreground", "secondary_foreground",
            "disabled_foreground", "accent", "border", "selection",
            "toolbar_background", "statusbar_background", "font_family",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        if isinstance(self.font_size, bool) or not isinstance(self.font_size, int) or self.font_size <= 0:
            raise ValueError("font_size must be a positive integer.")
        if not isinstance(self.tokens, StyleTokens):
            raise TypeError("tokens must be a StyleTokens instance.")

    def get_state(self) -> dict[str, object]:
        """Return presentation diagnostics without exposing mutable state."""
        return {
            "name": self.name,
            "application_background": self.application_background,
            "panel_background": self.panel_background,
            "canvas_background": self.canvas_background,
            "foreground": self.foreground,
            "secondary_foreground": self.secondary_foreground,
            "disabled_foreground": self.disabled_foreground,
            "accent": self.accent,
            "border": self.border,
            "selection": self.selection,
            "toolbar_background": self.toolbar_background,
            "statusbar_background": self.statusbar_background,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "tokens": self.tokens.__dict__ if hasattr(self.tokens, "__dict__") else {
                field_name: getattr(self.tokens, field_name)
                for field_name in self.tokens.__dataclass_fields__
            },
        }


DEFAULT_THEME = Theme(
    name="GridForge Engineering Dark",
    application_background=DEFAULT_STYLE_TOKENS.window_background,
    panel_background=DEFAULT_STYLE_TOKENS.panel_background,
    canvas_background=DEFAULT_STYLE_TOKENS.canvas_background,
    foreground=DEFAULT_STYLE_TOKENS.text_primary,
    secondary_foreground=DEFAULT_STYLE_TOKENS.text_secondary,
    disabled_foreground=DEFAULT_STYLE_TOKENS.text_disabled,
    accent=DEFAULT_STYLE_TOKENS.accent_primary,
    border=DEFAULT_STYLE_TOKENS.panel_border,
    selection=DEFAULT_STYLE_TOKENS.selection_background,
    toolbar_background=DEFAULT_STYLE_TOKENS.panel_surface,
    statusbar_background=DEFAULT_STYLE_TOKENS.window_background,
    font_family=DEFAULT_STYLE_TOKENS.font_family,
    font_size=DEFAULT_STYLE_TOKENS.font_size_pt,
    tokens=DEFAULT_STYLE_TOKENS,
)

__all__ = ["DEFAULT_THEME", "Theme"]
