"""
GridForge V2 Protection Package
================================

Public API for the GridForge V2 protection subsystem.

Protection owns protection contracts and evaluation orchestration. It does
not calculate network quantities or mutate breakers/network topology.
"""

from .context import ProtectionContext
from .decision import ProtectionDecision
from .relay_input import RelayInput
from .relay_base import RelayBase
from .protection_element import (
    ProtectionElement,
    ProtectionElementState,
)
from .protection_system import ProtectionSystem
from .protection_measurement_binding import ProtectionMeasurementBinding


__all__ = [
    "ProtectionContext",
    "ProtectionDecision",
    "RelayInput",
    "RelayBase",
    "ProtectionElement",
    "ProtectionElementState",
    "ProtectionSystem",
    "ProtectionMeasurementBinding",
]
