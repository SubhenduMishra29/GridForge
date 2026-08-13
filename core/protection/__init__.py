"""
GridForge V2 Protection Package
================================

Package
-------
core.protection

Purpose
-------
Public API for the GridForge V2 protection subsystem.

Architectural Position
----------------------

    Physical Relay
          |
          v
    ProtectionElement
          |
          v
       RelayBase
          |
          +------------------+
          |                  |
          v                  v
     RelayInput      ProtectionContext
          |                  |
          +--------+---------+
                   |
                   v
          ProtectionDecision
                   |
                   v
          ProtectionSystem
                   |
                   v
       Protection Scheme /
        Output Execution
                   |
                   v
            BreakerManager

Public Contracts
----------------

ProtectionContext
    Immutable execution-time context supplied to protection
    functions.

ProtectionDecision
    Immutable structured result produced by one protection-function
    evaluation.

RelayInput
    Protection-facing binding to an authoritative MeasurementChannel.

RelayBase
    Abstract executable protection-function contract.

ProtectionElement
    Composition object connecting one protection function to an
    authoritative physical Relay.

ProtectionElementState
    Runtime orchestration state of a ProtectionElement.

ProtectionSystem
    System-level registration and orchestration of protection
    elements.

Architectural Boundary
----------------------

This package does NOT:

    * own physical Relay definitions;
    * own CT/PT/CVT definitions;
    * own MeasurementChannel state;
    * calculate network electrical quantities;
    * calculate fault currents;
    * build Ybus;
    * perform load flow;
    * perform short-circuit analysis;
    * operate physical breakers;
    * contain GUI state;
    * perform persistence/file I/O.

The protection subsystem consumes authoritative state from other
GridForge subsystems and produces structured protection decisions.

Public API Policy
-----------------

Only stable protection contracts are exported from this package.

Concrete protection-function implementations should normally live in
their dedicated modules and should not be imported here merely for
convenience.

This prevents ``core.protection`` from becoming a registry of every
protection-function plugin and preserves the plugin architecture.

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
