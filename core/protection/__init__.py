"""Public API for the GridForge V2 protection subsystem."""

from .context import ProtectionContext
from .decision import ProtectionDecision
from .relay_input import RelayInput
from .relay_base import RelayBase
from .protection_element import ProtectionElement, ProtectionElementState
from .protection_system import ProtectionSystem
from .protection_measurement_binding import ProtectionMeasurementBinding
from .factory import ProtectionFactory
from .function_catalog import (
    ProtectionFunctionSpecification,
    ProtectionFunctionStatus,
    get_protection_function,
    list_protection_functions,
)

__all__ = [
    "ProtectionContext", "ProtectionDecision", "RelayInput", "RelayBase",
    "ProtectionElement", "ProtectionElementState", "ProtectionSystem",
    "ProtectionMeasurementBinding", "ProtectionFactory",
    "ProtectionFunctionSpecification", "ProtectionFunctionStatus",
    "get_protection_function", "list_protection_functions",
]
