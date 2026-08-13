"""
GridForge V2 Protection Package.

Package
-------
core.protection

Purpose
-------
Provides the protection-domain execution framework for GridForge V2.

Architectural Boundary
----------------------

    core.model
        |
        | physical equipment
        v
    Relay / Breaker
        |
        v
    core.measurement
        |
        | MeasurementChannel
        v
    core.protection
        |
        +-- RelayInput
        +-- RelayBase
        +-- ProtectionContext
        +-- ProtectionDecision
        |
        +-- protection functions
        +-- protection schemes
        +-- protection zones
        +-- protection outputs
        +-- coordination

The protection package contains executable protection-domain
abstractions.

Physical equipment models remain outside this package.

MeasurementChannel remains authoritative in:

    core.measurement.measurement_channel

Design Principles
-----------------

* Protection functions consume measurement channels through RelayInput.
* Protection functions derive from RelayBase.
* Protection functions return ProtectionDecision objects.
* ProtectionContext supplies evaluation-time execution information.
* Protection functions must not directly operate breakers.
* Physical relay/device identity remains authoritative in the model
  layer.
* Measurement state remains authoritative in the measurement layer.
* GUI and persistence concerns remain outside this package.
"""

from __future__ import annotations

from core.protection.context import ProtectionContext
from core.protection.decision import ProtectionDecision
from core.protection.relay_base import RelayBase
from core.protection.relay_input import RelayInput


__all__ = [
    "ProtectionContext",
    "ProtectionDecision",
    "RelayBase",
    "RelayInput",
]
