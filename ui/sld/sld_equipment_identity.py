# ============================================================
# GridForge V2 — SLD Equipment Identity Boundary
# Author: Subhendu Mishra
# ============================================================
"""Resolve canonical SLD semantics to EquipmentRegistry identities.

Ordinary identities intentionally follow the canonical lowercase equipment
identifier. Instrument abbreviations are the only explicit vocabulary bridge.
"""

from __future__ import annotations

from .sld_vocabulary import semantic_type


_INSTRUMENT_EQUIPMENT_TYPES = {
    "CT": "current_transformer",
    "PT": "potential_transformer",
    "CVT": "cvt",
}


def equipment_type_for_semantic(element_type: str) -> str:
    """Return the EquipmentRegistry identity for an SLD semantic value."""
    canonical = semantic_type(element_type)
    return _INSTRUMENT_EQUIPMENT_TYPES.get(canonical, canonical.lower())


__all__ = ["equipment_type_for_semantic"]
