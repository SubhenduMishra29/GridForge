# ============================================================
# GridForge V2 — Built-in SLD Symbol Catalogue
# Author: Subhendu Mishra
# ============================================================
"""Built-in renderer-neutral symbol definitions.

The catalogue contains presentation metadata only. Equipment identity and
symbol selection remain owned by EquipmentDefinition and SymbolRegistry.
"""

from __future__ import annotations

from .symbol_definition import SymbolDefinition
from .symbol_registry import SymbolRegistry


_BUILTIN_SYMBOLS: tuple[tuple[str, str, tuple[str, ...], tuple[dict, ...]], ...] = (
    ("bus", "Bus", ("terminal",), ({"kind": "line", "x1": -24, "y1": 0, "x2": 24, "y2": 0},)),
    ("line", "Line", ("from", "to"), ({"kind": "line", "x1": -24, "y1": 0, "x2": 24, "y2": 0},)),
    ("cable", "Cable", ("from", "to"), ({"kind": "line", "x1": -24, "y1": 0, "x2": 24, "y2": 0},)),
    ("transformer", "Transformer", ("from", "to"), ({"kind": "circle", "cx": -8, "cy": 0, "r": 10}, {"kind": "circle", "cx": 8, "cy": 0, "r": 10})),
    ("switch", "Switch", ("from", "to"), ({"kind": "line", "x1": -24, "y1": 0, "x2": 0, "y2": -12},)),
    ("breaker", "Breaker", ("from", "to"), ({"kind": "rect", "x": -10, "y": -10, "width": 20, "height": 20},)),
    ("disconnector", "Disconnector", ("from", "to"), ({"kind": "line", "x1": -24, "y1": 0, "x2": 0, "y2": -12},)),
    ("fuse", "Fuse", ("from", "to"), ({"kind": "rect", "x": -8, "y": -6, "width": 16, "height": 12},)),
    ("load", "Load", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 12},)),
    ("generator", "Generator", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 14},)),
    ("synchronous_machine", "Synchronous Machine", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 14},)),
    ("motor", "Motor", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 12},)),
    ("shunt", "Shunt", ("terminal",), ({"kind": "line", "x1": -12, "y1": 0, "x2": 12, "y2": 0},)),
    ("capacitor", "Capacitor", ("terminal",), ({"kind": "line", "x1": -5, "y1": -12, "x2": -5, "y2": 12}, {"kind": "line", "x1": 5, "y1": -12, "x2": 5, "y2": 12})),
    ("reactor", "Reactor", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 10},)),
    ("solar", "Solar", ("terminal",), ({"kind": "rect", "x": -14, "y": -10, "width": 28, "height": 20},)),
    ("battery", "Battery", ("terminal",), ({"kind": "rect", "x": -10, "y": -14, "width": 20, "height": 28},)),
    ("grid", "Grid", ("terminal",), ({"kind": "circle", "cx": 0, "cy": 0, "r": 14},)),
    ("current_transformer", "Current Transformer", ("primary", "secondary"), ({"kind": "circle", "cx": 0, "cy": 0, "r": 12},)),
    ("potential_transformer", "Potential Transformer", ("primary", "secondary"), ({"kind": "circle", "cx": 0, "cy": 0, "r": 12},)),
    ("cvt", "Capacitive Voltage Transformer", ("primary", "secondary"), ({"kind": "circle", "cx": 0, "cy": 0, "r": 12},)),
    ("relay", "Relay", (), ({"kind": "rect", "x": -12, "y": -10, "width": 24, "height": 20},)),
)


def register_builtin_symbols(registry: SymbolRegistry) -> None:
    """Register the complete built-in catalogue into the supplied registry."""
    if not isinstance(registry, SymbolRegistry):
        raise TypeError("registry must be a SymbolRegistry")
    for symbol_id, display_name, terminals, primitives in _BUILTIN_SYMBOLS:
        anchors = {}
        if len(terminals) == 1:
            anchors[terminals[0]] = (-24.0, 0.0)
        elif len(terminals) >= 2:
            anchors[terminals[0]] = (-24.0, 0.0)
            anchors[terminals[1]] = (24.0, 0.0)
        registry.register(SymbolDefinition(symbol_id=symbol_id, display_name=display_name, width=48.0, height=32.0, terminal_anchors=anchors, primitives=primitives))


__all__ = ["register_builtin_symbols"]
