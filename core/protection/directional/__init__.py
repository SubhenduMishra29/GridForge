"""
GridForge Directional Protection
================================

Directional protection domain API.

Provides:
    DirectionalRelay
    DirectionalProtectionSettings
    AuthoritativeDirectionalSnapshot
    create_authoritative_directional_snapshot

The snapshot factory creates immutable, Core-sealed phasor records after
Application has validated project-scoped measurement-channel provenance.
"""

from core.protection.directional.directional_relay import (
    AuthoritativeDirectionalSnapshot,
    DirectionalProtectionSettings,
    DirectionalRelay,
    create_authoritative_directional_snapshot,
)

__all__ = [
    "AuthoritativeDirectionalSnapshot",
    "create_authoritative_directional_snapshot",
    "DirectionalProtectionSettings",
    "DirectionalRelay",
]
