"""
GridForge V2 Protection Decision Compatibility Module.

The canonical ProtectionDecision implementation is defined in:

    core.protection.decision

This module is retained temporarily as a compatibility import path
for existing GridForge code.
"""

from __future__ import annotations

from core.protection.decision import ProtectionDecision


__all__ = [
    "ProtectionDecision",
]
