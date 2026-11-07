"""Opaque, immutable ANSI 67 measurement-cycle snapshot contract.

Only the active ProtectionRuntime issuance path creates accepted instances.
The issuer capability is carried by the snapshot and checked against the
capability attached to the Application-created ProtectionContext.
"""
from __future__ import annotations

from dataclasses import dataclass

_DIRECTIONAL_SNAPSHOT_SEAL = object()

@dataclass(frozen=True, slots=True)
class _AuthoritativeDirectionalSnapshot:
    _seal: object
    _issuer: object
    element_id: str
    voltage_value: complex
    current_value: complex
    voltage_angle: float
    current_angle: float
    voltage_channel_id: str
    current_channel_id: str
    voltage_channel_identity: int
    current_channel_identity: int
    sample_timestamp: float
    project_id: str
    activation_generation: int
    configuration_identity: int
    runtime_identity: int

__all__ = []
