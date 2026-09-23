# ============================================================
# GridForge V2 — Built-in SLD Symbol Catalogue
# Author: Subhendu Mishra
# ============================================================
"""Built-in renderer-neutral symbol definitions."""

from __future__ import annotations

from .symbol_definition import SymbolDefinition
from .symbol_registry import SymbolRegistry


_BUILTIN_SYMBOLS: tuple[tuple[str, str, tuple[str, ...], tuple[dict, ...], dict[str, tuple[float, float]]], ...] = (
    ("bus", "Bus", ("terminal",), ({"kind": "line", "x1": -24, "y1": 0, "x2": 24, "y2": 0},), {"terminal": (-24.0, 0.0)}),
    ("line", "Line", ("from", "to"), ({"kind": "line", "x1": -24, "y1": 0, "x2": 24, "y2": 0},), {"from": (-24.0, 0.0), "to": (24.0, 0.0)}),
    ("cable", "Cable", ("from", "to"), ({"kind": "line", "x1": -24, "y1": 0, "x2": 24, "y2": 0},), {"from": (-24.0, 0.0), "to": (24.0, 0.0)}),
    ("transformer", "Transformer", ("from", "to"), ({"kind": "circle", "cx": -8, "cy": 0, "r": 10}, {"kind": "circle", "cx": 8, "cy": 0, "r": 10}), {"from": (-24.0, 0.0), "to": (24.0, 0.0)}),
    ("switch", "Switch", ("from", "to"), ({"kind": "line", "x1": -24, "y1": 0, "x2": 0, "y2": -12},), {"from": (-24.0, 0.0), "to": (24.0, 0.0)}),
    ("breaker", "Breaker", ("from", "to"), ({"kind": "rect", "x": -10, "y": -10, "width": 20, "height": 20},), {"from": (-24.0, 0.0), "to": (24.0, 0.0)}),
    ("disconnector", "Disconnector", ("from", "to"), ({"kind": "line", "x1": -24, "y1": 0, "x2": 0, "y2": -12},), {"from": (-24.0, 0.0), "to": (24.0, 0.0)}),
    ("fuse", "Fuse", ("from", "to"), ({"kind": "rect", "x": -8, "y": -6, "width": 16, "height": 12},), {"from": (-24.0, 0.0), "to": (24.0, 0.0)}),
    ("load", "Load", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 12},), {"terminal": (-24.0, 0.0)}),
    ("generator", "Generator", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 14},), {"terminal": (-24.0, 0.0)}),
    ("synchronous_machine", "Synchronous Machine", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 14},), {"terminal": (-24.0, 0.0)}),
    ("motor", "Motor", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 12},), {"terminal": (-24.0, 0.0)}),
    ("shunt", "Shunt", ("terminal",), ({"kind": "line", "x1": -12, "y1": 0, "x2": 12, "y2": 0},), {"terminal": (-24.0, 0.0)}),
    ("capacitor", "Capacitor", ("terminal",), ({"kind": "line", "x1": -5, "y1": -12, "x2": -5, "y2": 12}, {"kind": "line", "x1": 5, "y1": -12, "x2": 5, "y2": 12}), {"terminal": (-24.0, 0.0)}),
    ("reactor", "Reactor", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 10},), {"terminal": (-24.0, 0.0)}),
    ("solar", "Solar", ("terminal",), ({"kind": "rect", "x": -14, "y": -10, "width": 28, "height": 20},), {"terminal": (-24.0, 0.0)}),
    ("battery", "Battery", ("terminal",), ({"kind": "rect", "x": -10, "y": -14, "width": 20, "height": 28},), {"terminal": (-24.0, 0.0)}),
    ("grid", "Grid", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 14},), {"terminal": (-24.0, 0.0)}),
    ("current_transformer", "Current Transformer", ("P1", "P2", "S1", "S2"), ({"kind": "circle", "cx": 0, "cy": 0, "r": 12},), {"P1": (-24.0, -10.0), "P2": (-24.0, 10.0), "S1": (24.0, -10.0), "S2": (24.0, 10.0)}),
    ("potential_transformer", "Potential Transformer", ("primary_a", "primary_b", "secondary_a", "secondary_b"), ({"kind": "circle", "cx": 0, "cy": 0, "r": 12},), {"primary_a": (-24.0, -10.0), "primary_b": (-24.0, 10.0), "secondary_a": (24.0, -10.0), "secondary_b": (24.0, 10.0)}),
    ("cvt", "Capacitive Voltage Transformer", ("H1", "H2", "X1", "X2"), ({"kind": "circle", "cx": 0, "cy": 0, "r": 12},), {"H1": (-24.0, -10.0), "H2": (-24.0, 10.0), "X1": (24.0, -10.0), "X2": (24.0, 10.0)}),
    ("relay", "Relay", (), ({"kind": "rect", "x": -12, "y": -10, "width": 24, "height": 20},), {}),
)


def register_builtin_symbols(registry: SymbolRegistry) -> None:
    """Register every supported built-in symbol with explicit terminal anchors."""
    if not isinstance(registry, SymbolRegistry):
        raise TypeError("registry must be a SymbolRegistry")
    for symbol_id, display_name, terminals, primitives, anchors in _BUILTIN_SYMBOLS:
        registry.register(
            SymbolDefinition(
                symbol_id=symbol_id,
                display_name=display_name,
                width=48.0,
                height=32.0,
                terminal_anchors=anchors,
                primitives=primitives,
            )
        )


__all__ = ["register_builtin_symbols"]
