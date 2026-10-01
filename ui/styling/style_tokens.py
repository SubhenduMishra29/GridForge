# ============================================================
# File: ui/styling/style_tokens.py
# GridForge V2 — Canonical UI Style Tokens
# Author: Subhendu Mishra
# ============================================================
"""Semantic presentation tokens shared by widgets and graphics projections."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StyleTokens:
    """Immutable semantic visual vocabulary for the presentation layer."""

    window_background: str = "#171A1F"
    panel_background: str = "#20242A"
    panel_surface: str = "#262B32"
    canvas_background: str = "#FFFFFF"
    editor_background: str = "#171A1F"
    editor_foreground: str = "#E7ECF2"
    editor_border: str = "#46515D"
    list_background: str = "#171A1F"
    list_foreground: str = "#E7ECF2"
    panel_border: str = "#39414B"
    separator: str = "#303740"

    text_primary: str = "#E7ECF2"
    text_secondary: str = "#AAB4C0"
    text_muted: str = "#7D8996"
    text_disabled: str = "#5B6570"
    text_inverse: str = "#101419"
    table_background: str = "#171A1F"
    table_alternate_background: str = "#20242A"

    accent_primary: str = "#5BA7FF"
    accent_active: str = "#79BAFF"
    accent_focus: str = "#8AC4FF"
    selection_background: str = "#24527D"
    selection_border: str = "#6CB4FF"
    hover_background: str = "#2E353E"
    pressed_background: str = "#1D4568"

    state_valid: str = "#55B889"
    state_warning: str = "#D6A84B"
    state_invalid: str = "#E06B6B"
    state_info: str = "#61A9D9"
    state_placement: str = "#A87BFF"
    state_disabled: str = "#5B6570"

    engineering_bus: str = "#E6C35A"
    engineering_connection: str = "#AEB8C4"
    engineering_line: str = "#7DB7E8"
    engineering_cable: str = "#B58BE8"
    engineering_terminal: str = "#6CC5A0"
    engineering_protection: str = "#E08A72"
    engineering_control: str = "#7CC4C9"
    engineering_measurement: str = "#B5A7E8"

    # Generic SLD symbols are rendered on the authoritative white canvas.\n    # Keep the shared stroke token dark enough for line/circle-only symbols;\n    # Bus uses its separate engineering_bus role and is intentionally unchanged.\n    symbol_stroke: str = "#26313B"
    symbol_fill: str = "#222830"
    symbol_disabled: str = "#68737F"
    symbol_preview: str = "#A87BFF"

    canvas_grid_minor: str = "#1B2128"
    canvas_grid_major: str = "#27303A"
    canvas_snap: str = "#79BAFF"

    font_family: str = "Segoe UI"
    font_size_pt: int = 10


DEFAULT_STYLE_TOKENS = StyleTokens()

__all__ = ["StyleTokens", "DEFAULT_STYLE_TOKENS"]
