"""
GridForge V2 Protection Package
================================

Package
-------
core.protection

Purpose
-------
Public API for the GridForge V2 protection subsystem.

This package exposes only the stable foundational protection
contracts. Concrete protection-function implementations remain in
their dedicated subpackages.

Architectural Boundary
----------------------

The protection package consumes authoritative state from other
GridForge subsystems and produces structured protection decisions.

It does not:

    * own physical Relay definitions;
    * own CT/PT/CVT definitions;
    * own MeasurementChannel state;
    * calculate network electrical quantities;
    * calculate fault currents;
    * build Y-bus;
    * perform load flow;
    * perform short-circuit analysis;
    * operate physical breakers;
    * contain GUI state;
    * perform persistence or file I/O.

Public API Policy
-----------------

Only stable protection contracts are exported here.

Concrete protection functions are intentionally NOT re-exported from
this package. They remain available from their dedicated modules:

    core.protection.overcurrent
    core.protection.directional
    core.protection.distance
    core.protection.coordination

This prevents ``core.protection`` from becoming a concrete-function
registry and preserves the intended plugin architecture.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
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


__all__ = [
    "ProtectionContext",
    "ProtectionDecision",
    "RelayInput",
    "RelayBase",
    "ProtectionElement",
    "ProtectionElementState",
    "ProtectionSystem",
]
