# ============================================================
# File: core/application/endpoint_reference.py
# GridForge V2 — Compatibility Re-export
# Author: Subhendu Mishra
# ============================================================

"""Compatibility import surface for the canonical Core endpoint identity.

The authoritative definitions live in ``core.model.endpoint_reference``.
Application code must import them from ``core.model``; this module exists
only to avoid breaking legacy external imports while the ownership boundary
is migrated.
"""

from __future__ import annotations

from core.model.endpoint_reference import (
    EndpointReference,
    EndpointReferenceKind,
    EquipmentType,
)

__all__ = [
    "EndpointReference",
    "EndpointReferenceKind",
    "EquipmentType",
]
