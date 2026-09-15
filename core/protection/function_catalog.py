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
)
from core.protection.voltage import OverVoltageRelay, UnderVoltageRelay


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
    ProtectionFunctionSpecification("50", "Instantaneous overcurrent", ProtectionFunctionStatus.IMPLEMENTED, InstantaneousOvercurrentRelay),
    ProtectionFunctionSpecification("51", "Inverse-time overcurrent", ProtectionFunctionStatus.IMPLEMENTED, IECOvercurrentRelay),
    ProtectionFunctionSpecification("50N", "Instantaneous earth-fault overcurrent", ProtectionFunctionStatus.IMPLEMENTED, EarthInstantaneousOvercurrentRelay),
    ProtectionFunctionSpecification("51N", "Inverse-time earth-fault overcurrent", ProtectionFunctionStatus.IMPLEMENTED, EarthIECOvercurrentRelay),
    ProtectionFunctionSpecification("27", "Undervoltage", ProtectionFunctionStatus.IMPLEMENTED, UnderVoltageRelay),
    ProtectionFunctionSpecification("59", "Overvoltage", ProtectionFunctionStatus.IMPLEMENTED, OverVoltageRelay),
    ProtectionFunctionSpecification("46", "Negative-sequence / phase-balance overcurrent", ProtectionFunctionStatus.NOT_IMPLEMENTED),
    ProtectionFunctionSpecification("49", "Thermal overload", ProtectionFunctionStatus.NOT_IMPLEMENTED),
    ProtectionFunctionSpecification("67", "Directional overcurrent", ProtectionFunctionStatus.IMPLEMENTED, DirectionalRelay),
    ProtectionFunctionSpecification("87", "Differential protection", ProtectionFunctionStatus.NOT_IMPLEMENTED),
    ProtectionFunctionSpecification("21", "Distance protection", ProtectionFunctionStatus.IMPLEMENTED, DistanceRelay),
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
