# ============================================================
# GridForge V2 — Built-in SLD Symbol Catalogue
# Author: Subhendu Mishra
# ============================================================
"""Canonical renderer-neutral engineering symbol definitions."""

from __future__ import annotations

from .symbol_definition import SymbolDefinition
from .symbol_registry import SymbolRegistry


_BUILTIN_SYMBOLS = (
    ("bus", "Bus", ("terminal",), (
        {"kind": "line", "x1": -28, "y1": 0, "x2": 28, "y2": 0},
    ), {"terminal": (-28.0, 0.0)}),
    ("line", "Line", ("FROM", "TO"), (
        {"kind": "line", "x1": -28, "y1": 0, "x2": 28, "y2": 0},
    ), {"FROM": (-28.0, 0.0), "TO": (28.0, 0.0)}),
    ("cable", "Cable", ("FROM", "TO"), (
        {"kind": "line", "x1": -28, "y1": 0, "x2": 28, "y2": 0},
        {"kind": "line", "x1": -18, "y1": -3, "x2": -10, "y2": 3},
        {"kind": "line", "x1": -10, "y1": -3, "x2": -2, "y2": 3},
        {"kind": "line", "x1": -2, "y1": -3, "x2": 6, "y2": 3},
    ), {"FROM": (-28.0, 0.0), "TO": (28.0, 0.0)}),
    ("transformer", "Transformer", ("FROM", "TO"), (
        {"kind": "line", "x1": -28, "y1": 0, "x2": -12, "y2": 0},
        {"kind": "circle", "cx": -6, "cy": 0, "r": 10},
        {"kind": "circle", "cx": 10, "cy": 0, "r": 10},
        {"kind": "line", "x1": 20, "y1": 0, "x2": 28, "y2": 0},
    ), {"FROM": (-28.0, 0.0), "TO": (28.0, 0.0)}),
    ("switch", "Switch", ("from", "to"), (
        {"kind": "line", "x1": -28, "y1": 0, "x2": -4, "y2": 0},
        {"kind": "line", "x1": -4, "y1": 0, "x2": 12, "y2": -11},
        {"kind": "line", "x1": 12, "y1": -11, "x2": 28, "y2": -11},
    ), {"from": (-28.0, 0.0), "to": (28.0, -11.0)}),
    ("breaker", "Breaker", ("from", "to"), (
        {"kind": "line", "x1": -28, "y1": 0, "x2": -10, "y2": 0},
        {"kind": "rect", "x": -10, "y": -9, "width": 20, "height": 18},
        {"kind": "line", "x1": 10, "y1": 0, "x2": 28, "y2": 0},
    ), {"from": (-28.0, 0.0), "to": (28.0, 0.0)}),
    ("disconnector", "Disconnector", ("from", "to"), (
        {"kind": "line", "x1": -28, "y1": 0, "x2": -8, "y2": 0},
        {"kind": "line", "x1": -8, "y1": 0, "x2": 10, "y2": -11},
        {"kind": "line", "x1": 10, "y1": -11, "x2": 28, "y2": -11},
    ), {"from": (-28.0, 0.0), "to": (28.0, -11.0)}),
    ("fuse", "Fuse", ("from", "to"), (
        {"kind": "line", "x1": -28, "y1": 0, "x2": -8, "y2": 0},
        {"kind": "rect", "x": -8, "y": -5, "width": 16, "height": 10},
        {"kind": "line", "x1": 8, "y1": 0, "x2": 28, "y2": 0},
    ), {"from": (-28.0, 0.0), "to": (28.0, 0.0)}),
    ("load", "Load", ("terminal",), (
        {"kind": "circle", "cx": 0, "cy": 0, "r": 12},
        {"kind": "line", "x1": -7, "y1": 7, "x2": 7, "y2": -7},
    ), {"terminal": (-28.0, 0.0)}),
    ("generator", "Generator", ("terminal",), (
        {"kind": "circle", "cx": 0, "cy": 0, "r": 14},
        {"kind": "text", "x": -10, "y": -9, "width": 20, "height": 18, "text": "G"},
    ), {"terminal": (-28.0, 0.0)}),
    ("synchronous_machine", "Synchronous Machine", ("terminal",), (
        {"kind": "circle", "cx": 0, "cy": 0, "r": 14},
        {"kind": "text", "x": -10, "y": -9, "width": 20, "height": 18, "text": "M"},
    ), {"terminal": (-28.0, 0.0)}),
    ("motor", "Motor", ("terminal",), (
        {"kind": "circle", "cx": 0, "cy": 0, "r": 12},
        {"kind": "text", "x": -8, "y": -8, "width": 16, "height": 16, "text": "M"},
    ), {"terminal": (-28.0, 0.0)}),
    ("shunt", "Shunt", ("terminal",), (
        {"kind": "line", "x1": -12, "y1": 0, "x2": 12, "y2": 0},
        {"kind": "line", "x1": -7, "y1": 0, "x2": -7, "y2": 12},
        {"kind": "line", "x1": 7, "y1": 0, "x2": 7, "y2": 12},
    ), {"terminal": (-28.0, 0.0)}),
    ("capacitor", "Capacitor", ("terminal",), (
        {"kind": "line", "x1": -6, "y1": -11, "x2": -6, "y2": 11},
        {"kind": "line", "x1": 6, "y1": -11, "x2": 6, "y2": 11},
        {"kind": "line", "x1": -28, "y1": 0, "x2": -6, "y2": 0},
    ), {"terminal": (-28.0, 0.0)}),
    ("reactor", "Reactor", ("terminal",), (
        {"kind": "circle", "cx": -7, "cy": 0, "r": 6},
        {"kind": "circle", "cx": 7, "cy": 0, "r": 6},
        {"kind": "line", "x1": -28, "y1": 0, "x2": -13, "y2": 0},
        {"kind": "line", "x1": 13, "y1": 0, "x2": 28, "y2": 0},
    ), {"terminal": (-28.0, 0.0)}),
    ("solar", "Solar", ("terminal",), (
        {"kind": "rect", "x": -13, "y": -10, "width": 26, "height": 20},
        {"kind": "line", "x1": -13, "y1": -3, "x2": 13, "y2": -3},
        {"kind": "line", "x1": -13, "y1": 3, "x2": 13, "y2": 3},
        {"kind": "line", "x1": 0, "y1": -10, "x2": 0, "y2": 10},
    ), {"terminal": (-28.0, 0.0)}),
    ("battery", "Battery", ("terminal",), (
        {"kind": "line", "x1": -5, "y1": -12, "x2": -5, "y2": 12},
        {"kind": "line", "x1": 5, "y1": -7, "x2": 5, "y2": 7},
        {"kind": "line", "x1": -28, "y1": 0, "x2": -5, "y2": 0},
        {"kind": "line", "x1": 5, "y1": 0, "x2": 28, "y2": 0},
    ), {"terminal": (-28.0, 0.0)}),
    ("grid", "Grid", ("terminal",), (
        {"kind": "circle", "cx": 0, "cy": 0, "r": 14},
        {"kind": "text", "x": -9, "y": -8, "width": 18, "height": 16, "text": "G"},
    ), {"terminal": (-28.0, 0.0)}),
    ("current_transformer", "Current Transformer", ("P1", "P2", "S1", "S2"), (
        {"kind": "circle", "cx": 0, "cy": 0, "r": 12},
        {"kind": "line", "x1": -28, "y1": -10, "x2": -12, "y2": -10},
        {"kind": "line", "x1": -28, "y1": 10, "x2": -12, "y2": 10},
        {"kind": "line", "x1": 12, "y1": -10, "x2": 28, "y2": -10},
        {"kind": "line", "x1": 12, "y1": 10, "x2": 28, "y2": 10},
    ), {"P1": (-28.0, -10.0), "P2": (-28.0, 10.0), "S1": (28.0, -10.0), "S2": (28.0, 10.0)}),
    ("potential_transformer", "Potential Transformer", ("primary_a", "primary_b", "secondary_a", "secondary_b"), (
        {"kind": "circle", "cx": 0, "cy": 0, "r": 12},
        {"kind": "text", "x": -10, "y": -8, "width": 20, "height": 16, "text": "PT"},
        {"kind": "line", "x1": -28, "y1": -10, "x2": -12, "y2": -10},
        {"kind": "line", "x1": -28, "y1": 10, "x2": -12, "y2": 10},
        {"kind": "line", "x1": 12, "y1": -10, "x2": 28, "y2": -10},
        {"kind": "line", "x1": 12, "y1": 10, "x2": 28, "y2": 10},
    ), {"primary_a": (-28.0, -10.0), "primary_b": (-28.0, 10.0), "secondary_a": (28.0, -10.0), "secondary_b": (28.0, 10.0)}),
    ("cvt", "Capacitive Voltage Transformer", ("H1", "H2", "X1", "X2"), (
        {"kind": "circle", "cx": 0, "cy": 0, "r": 12},
        {"kind": "line", "x1": -6, "y1": -12, "x2": -6, "y2": 12},
        {"kind": "line", "x1": 6, "y1": -12, "x2": 6, "y2": 12},
        {"kind": "line", "x1": -28, "y1": -10, "x2": -12, "y2": -10},
        {"kind": "line", "x1": -28, "y1": 10, "x2": -12, "y2": 10},
        {"kind": "line", "x1": 12, "y1": -10, "x2": 28, "y2": -10},
        {"kind": "line", "x1": 12, "y1": 10, "x2": 28, "y2": 10},
    ), {"H1": (-28.0, -10.0), "H2": (-28.0, 10.0), "X1": (28.0, -10.0), "X2": (28.0, 10.0)}),
    ("relay", "Relay", (), (
        {"kind": "circle", "cx": 0, "cy": 0, "r": 14},
        {"kind": "text", "x": -12, "y": -8, "width": 24, "height": 16, "text": "50/51"},
    ), {}),
)


def register_builtin_symbols(registry: SymbolRegistry) -> None:
    """Register every canonical symbol definition."""
    if not isinstance(registry, SymbolRegistry):
        raise TypeError("registry must be a SymbolRegistry")
    for symbol_id, display_name, terminals, primitives, anchors in _BUILTIN_SYMBOLS:
        registry.register(
            SymbolDefinition(
                symbol_id=symbol_id,
                display_name=display_name,
                width=56.0,
                height=40.0,
                terminal_anchors=anchors,
                primitives=primitives,
            )
        )


__all__ = ["register_builtin_symbols"]
