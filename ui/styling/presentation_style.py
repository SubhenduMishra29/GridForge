# ============================================================
# File: ui/styling/presentation_style.py
# GridForge V2 — Engineering Graphics Presentation Style
# Author: Subhendu Mishra
# ============================================================
"""Canonical presentation-state styling for QGraphics projections."""

from __future__ import annotations

from enum import Enum

from ui.core.qt import QApplication, QBrush, QColor, QFont, QPen

from .style_tokens import DEFAULT_STYLE_TOKENS, StyleTokens


class VisualState(str, Enum):
    NORMAL = "normal"
    HOVER = "hover"
    SELECTED = "selected"
    ACTIVE = "active"
    PREVIEW = "preview"
    INVALID = "invalid"
    WARNING = "warning"
    DISABLED = "disabled"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


def _color(value: str) -> QColor:
    return QColor(value)


def resolve_style_tokens(tokens: StyleTokens | None = None) -> StyleTokens:
    """Resolve the canonical active presentation tokens.

    Explicit tokens are preferred. Otherwise the StyleManager-published
    immutable token set on QApplication is used, with the default theme as
    the deterministic fallback.
    """
    if tokens is not None:
        if not isinstance(tokens, StyleTokens):
            raise TypeError("tokens must be a StyleTokens instance.")
        return tokens
    application = QApplication.instance()
    if application is not None:
        active = application.property("gridforge.style_tokens")
        if isinstance(active, StyleTokens):
            return active
    return DEFAULT_STYLE_TOKENS


def token_color(name: str, tokens: StyleTokens | None = None) -> QColor:
    """Return a defensive QColor from the canonical active style tokens."""
    resolved = resolve_style_tokens(tokens)
    return _color(getattr(resolved, name))


def visual_pen(
    role: str,
    state: VisualState = VisualState.NORMAL,
    *,
    width: float = 1.8,
    tokens: StyleTokens | None = None,
) -> QPen:
    """Build the canonical pen for an engineering visual role/state."""
    role_token = {
        "symbol": "symbol_stroke",
        "bus": "engineering_bus",
        "connection": "engineering_connection",
        "line": "engineering_line",
        "cable": "engineering_cable",
        "terminal": "engineering_terminal",
        "protection": "engineering_protection",
        "control": "engineering_control",
        "measurement": "engineering_measurement",
    }.get(role, "symbol_stroke")
    state_token = {
        VisualState.SELECTED: "selection_border",
        VisualState.HOVER: "accent_focus",
        VisualState.ACTIVE: "accent_active",
        VisualState.PREVIEW: "symbol_preview",
        VisualState.INVALID: "state_invalid",
        VisualState.WARNING: "state_warning",
        VisualState.DISABLED: "symbol_disabled",
        VisualState.CONNECTED: role_token,
        VisualState.DISCONNECTED: "text_muted",
    }.get(state)
    color = token_color(state_token or role_token, tokens)
    pen = QPen(color)
    setter = getattr(pen, "setWidthF", None)
    if callable(setter):
        setter(float(width) + (0.7 if state == VisualState.SELECTED else 0.0))
    else:
        pen.setWidth(int(round(width + (0.7 if state == VisualState.SELECTED else 0.0))))
    if state == VisualState.PREVIEW:
        pen.setStyle(getattr(__import__("ui.core.qt", fromlist=["Qt"]).Qt.PenStyle, "DashLine"))
    return pen


def visual_brush(
    role: str,
    state: VisualState = VisualState.NORMAL,
    *,
    tokens: StyleTokens = DEFAULT_STYLE_TOKENS,
) -> QBrush:
    """Build the canonical engineering fill treatment."""
    if state == VisualState.INVALID:
        return QBrush(token_color("state_invalid", tokens))
    if state == VisualState.WARNING:
        return QBrush(token_color("state_warning", tokens))
    if state == VisualState.PREVIEW:
        brush = QBrush(token_color("symbol_preview", tokens))
        setter = getattr(brush, "setStyle", None)
        if callable(setter):
            setter(getattr(__import__("ui.core.qt", fromlist=["Qt"]).Qt.BrushStyle, "Dense4Pattern"))
        return brush
    if state == VisualState.SELECTED:
        return QBrush(token_color("selection_background", tokens))
    if role == "symbol":
        return QBrush(token_color("symbol_fill", tokens))
    return QBrush()


def visual_font(
    role: str = "engineering",
    *,
    tokens: StyleTokens = DEFAULT_STYLE_TOKENS,
) -> QFont:
    resolved = resolve_style_tokens(tokens)
    size = {"title": 12, "section": 10, "engineering": 9, "annotation": 8}.get(role, 9)
    font = QFont(resolved.font_family, size)
    if role in {"title", "section"}:
        font.setWeight(QFont.Weight.DemiBold)
    return font


__all__ = ["VisualState", "resolve_style_tokens", "token_color", "visual_pen", "visual_brush", "visual_font"]
