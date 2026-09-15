"""
GridForge V2 Protection Package
================================

Package
-------
core.protection

Purpose
-------
Public API for the GridForge V2 protection subsystem.

This package exposes stable foundational protection contracts and the
canonical ANSI function metadata catalog. Concrete protection-function
implementations remain in their dedicated subpackages.

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

Only stable protection contracts and function metadata are exported
here. Concrete protection functions remain available from their
dedicated modules.

The function catalog is metadata only. It does not instantiate or own
runtime protection elements and does not replace plugin registration.

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
from .protection_measurement_binding import ProtectionMeasurementBinding
from .function_catalog import (
    ProtectionFunctionSpecification,
    ProtectionFunctionStatus,
    get_protection_function,
    list_protection_functions,
)


__all__ = [
    "ProtectionContext",
    "ProtectionDecision",
    "RelayInput",
    "RelayBase",
    "ProtectionElement",
    "ProtectionElementState",
    "ProtectionSystem",
    "ProtectionMeasurementBinding",
    "ProtectionFunctionSpecification",
    "ProtectionFunctionStatus",
    "get_protection_function",
    "list_protection_functions",
]
