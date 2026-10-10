# ============================================================
# File: core/protection/function_catalog.py
# GridForge V2 — Protection Function Catalog
# Author: Subhendu Mishra
# ============================================================

"""Canonical catalog of supported and explicitly unsupported ANSI functions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from core.protection.distance import DistanceRelay
from core.protection.directional import DirectionalRelay
from core.protection.overcurrent import (
    EarthIECOvercurrentRelay,
    EarthInstantaneousOvercurrentRelay,
    IECOvercurrentRelay,
    InstantaneousOvercurrentRelay,
    NegativeSequenceOvercurrentRelay,
)
from core.protection.thermal import ThermalOverloadRelay
from core.protection.voltage import OverVoltageRelay, UnderVoltageRelay
from core.protection.input_contracts import (CONTRACT_50, CONTRACT_51, CONTRACT_50N, CONTRACT_51N, CONTRACT_27, CONTRACT_59, CONTRACT_46, CONTRACT_49, CONTRACT_67, CONTRACT_21)


class ProtectionFunctionStatus(str, Enum):
    """Implementation status of an ANSI protection function."""

    IMPLEMENTED = "IMPLEMENTED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


@dataclass(frozen=True, slots=True)
class ProtectionFunctionSpecification:
    """Immutable metadata for one canonical ANSI function code."""

    code: str
    name: str
    status: ProtectionFunctionStatus
    implementation: type[Any] | None = None
    input_contract: Any | None = None

    def __post_init__(self) -> None:
        code = self.code.strip().upper()
        name = self.name.strip()
        if not code:
            raise ValueError("Protection function code cannot be empty.")
        if not name:
            raise ValueError("Protection function name cannot be empty.")
        if self.status is ProtectionFunctionStatus.IMPLEMENTED and self.implementation is None:
            raise ValueError("Implemented protection functions require an implementation.")
        if self.status is ProtectionFunctionStatus.NOT_IMPLEMENTED and self.implementation is not None:
            raise ValueError("Unimplemented protection functions cannot advertise an implementation.")
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "name", name)


_SPECS = (
    ProtectionFunctionSpecification("50", "Instantaneous overcurrent", ProtectionFunctionStatus.IMPLEMENTED, InstantaneousOvercurrentRelay, CONTRACT_50),
    ProtectionFunctionSpecification("51", "Inverse-time overcurrent", ProtectionFunctionStatus.IMPLEMENTED, IECOvercurrentRelay, CONTRACT_51),
    ProtectionFunctionSpecification("50N", "Instantaneous earth-fault overcurrent", ProtectionFunctionStatus.IMPLEMENTED, EarthInstantaneousOvercurrentRelay, CONTRACT_50N),
    ProtectionFunctionSpecification("51N", "Inverse-time earth-fault overcurrent", ProtectionFunctionStatus.IMPLEMENTED, EarthIECOvercurrentRelay, CONTRACT_51N),
    ProtectionFunctionSpecification("27", "Undervoltage", ProtectionFunctionStatus.IMPLEMENTED, UnderVoltageRelay, CONTRACT_27),
    ProtectionFunctionSpecification("59", "Overvoltage", ProtectionFunctionStatus.IMPLEMENTED, OverVoltageRelay, CONTRACT_59),
    ProtectionFunctionSpecification("46", "Negative-sequence / phase-balance overcurrent", ProtectionFunctionStatus.IMPLEMENTED, NegativeSequenceOvercurrentRelay, CONTRACT_46),
    ProtectionFunctionSpecification("49", "Thermal overload", ProtectionFunctionStatus.IMPLEMENTED, ThermalOverloadRelay, CONTRACT_49),
    ProtectionFunctionSpecification("67", "Directional overcurrent", ProtectionFunctionStatus.IMPLEMENTED, DirectionalRelay, CONTRACT_67),
    ProtectionFunctionSpecification("87", "Differential protection", ProtectionFunctionStatus.NOT_IMPLEMENTED),
    ProtectionFunctionSpecification("21", "Distance protection", ProtectionFunctionStatus.IMPLEMENTED, DistanceRelay, CONTRACT_21),
)

_CATALOG: Mapping[str, ProtectionFunctionSpecification] = MappingProxyType({spec.code: spec for spec in _SPECS})


def list_protection_functions() -> tuple[str, ...]:
    return tuple(_CATALOG)


def get_protection_function(code: str) -> ProtectionFunctionSpecification:
    if not isinstance(code, str):
        raise TypeError("Protection function code must be a string.")
    normalized = code.strip().upper()
    if not normalized:
        raise ValueError("Protection function code cannot be empty.")
    try:
        return _CATALOG[normalized]
    except KeyError as exc:
        raise KeyError(f"Unknown protection function code: {normalized}") from exc


__all__ = [
    "ProtectionFunctionStatus",
    "ProtectionFunctionSpecification",
    "get_protection_function",
    "list_protection_functions",
]
