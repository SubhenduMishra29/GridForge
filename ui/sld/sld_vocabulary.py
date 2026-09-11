# ============================================================
# File: ui/sld/sld_vocabulary.py
# GridForge V2 — Canonical SLD Semantic Vocabulary
# Author: Subhendu Mishra
# ============================================================
"""Canonical SLD semantic names and producer aliases.

The vocabulary is UI-owned. It does not import or traverse Core equipment
models. Application read-model producers may retain their collection-oriented
names while the SLD boundary resolves them to stable semantic names.
"""

from __future__ import annotations


# Frozen semantic vocabulary for the SLD projection boundary.
SLD_SEMANTIC_TYPES = (
    "BUS",
    "LINE",
    "CABLE",
    "TRANSFORMER",
    "SWITCH",
    "BREAKER",
    "DISCONNECTOR",
    "FUSE",
    "LOAD",
    "GENERATOR",
    "SYNCHRONOUS_MACHINE",
    "MOTOR",
    "SHUNT",
    "CAPACITOR",
    "REACTOR",
    "SOLAR",
    "BATTERY",
    "GRID",
    "CT",
    "PT",
    "CVT",
    "RELAY",
)

SLD_SUPPORTED_TYPES = frozenset(SLD_SEMANTIC_TYPES)

_PRODUCER_ALIASES = {
    "buses": "BUS",
    "lines": "LINE",
    "cables": "CABLE",
    "transformers": "TRANSFORMER",
    "switches": "SWITCH",
    "breakers": "BREAKER",
    "disconnectors": "DISCONNECTOR",
    "fuses": "FUSE",
    "loads": "LOAD",
    "generators": "GENERATOR",
    "synchronous_machines": "SYNCHRONOUS_MACHINE",
    "motors": "MOTOR",
    "shunts": "SHUNT",
    "capacitors": "CAPACITOR",
    "reactors": "REACTOR",
    "solar": "SOLAR",
    "batteries": "BATTERY",
    "grids": "GRID",
    "current_transformers": "CT",
    "potential_transformers": "PT",
    "capacitive_voltage_transformers": "CVT",
    "CT": "CT",
    "PT": "PT",
    "CVT": "CVT",
    "RELAY": "RELAY",
}


def semantic_type(element_type: str) -> str:
    """Resolve one Application producer type to a canonical SLD semantic type."""
    if not isinstance(element_type, str) or not element_type.strip():
        raise ValueError("element_type must be a non-empty string")
    key = element_type.strip()
    value = _PRODUCER_ALIASES.get(key)
    if value is None:
        value = _PRODUCER_ALIASES.get(key.lower())
    if value is None or value not in SLD_SUPPORTED_TYPES:
        raise ValueError(f"Unsupported SLD semantic type: {element_type!r}")
    return value


__all__ = ["SLD_SEMANTIC_TYPES", "SLD_SUPPORTED_TYPES", "semantic_type"]
