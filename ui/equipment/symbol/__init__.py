# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/symbol/__init__.py
#
# Purpose:
#     Public API boundary for the SLD symbol subsystem.
#
# Architectural Role:
#     Provides symbol definitions, registry and factory services
#     without coupling the symbol layer to Qt or rendering.
#
# Responsibilities:
#     - expose symbol classes;
#     - expose symbol registry;
#     - expose symbol factory.
#
# Does NOT:
#     - paint symbols;
#     - create QGraphicsItem objects;
#     - own the renderer lifecycle.
#
# ============================================================

"""
GridForge V2 — Equipment Symbol subsystem.
"""

from .symbol_base import SymbolBase
from .symbol_definition import SymbolDefinition
from .symbol_registry import SymbolRegistry
from .symbol_factory import SymbolFactory

__all__ = [
    "SymbolBase",
    "SymbolDefinition",
    "SymbolRegistry",
    "SymbolFactory",
]
