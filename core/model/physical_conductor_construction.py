"""Common Core contract for physical conductor construction inside equipment.

The contract describes installed conductor paths and their terminal mapping.
It deliberately does not own operating state: Breaker/Switch/Disconnector/Fuse
models remain authoritative for whether a declared path currently conducts.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping


_SUPPORTED_ROLES = frozenset({"A", "B", "C", "N", "PE", "SHIELD", "PILOT", "OTHER"})


@dataclass(frozen=True, slots=True)
class PhysicalConductorPath:
    """One installed internal conductor path between two equipment terminals."""

    conductor_role: str
    from_terminal_role: str = "from"
    to_terminal_role: str = "to"
    impedance_ohm: complex = 0j

    def __post_init__(self) -> None:
        role = str(self.conductor_role).strip().upper()
        if role not in _SUPPORTED_ROLES:
            raise ValueError(f"Unsupported physical conductor role {role!r}.")
        object.__setattr__(self, "conductor_role", role)
        for field in ("from_terminal_role", "to_terminal_role"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty terminal role.")
            object.__setattr__(self, field, value.strip())
        if self.from_terminal_role.casefold() == self.to_terminal_role.casefold():
            raise ValueError("A physical conductor path must join distinct terminal roles.")
        impedance = complex(self.impedance_ohm)
        if not math.isfinite(impedance.real) or not math.isfinite(impedance.imag) or impedance.real < 0:
            raise ValueError("Physical conductor path impedance must be finite with non-negative resistance.")
        object.__setattr__(self, "impedance_ohm", impedance)


@dataclass(frozen=True, slots=True)
class PhysicalConductorConstruction:
    """Immutable inventory of the internal physical conductor paths of equipment."""

    paths: tuple[PhysicalConductorPath, ...]

    def __post_init__(self) -> None:
        paths = tuple(self.paths)
        if not paths:
            raise ValueError("Physical conductor construction requires at least one path.")
        if any(not isinstance(path, PhysicalConductorPath) for path in paths):
            raise TypeError("paths must contain PhysicalConductorPath records.")
        keys = [(p.conductor_role, p.from_terminal_role.casefold(), p.to_terminal_role.casefold()) for p in paths]
        if len(keys) != len(set(keys)):
            raise ValueError("Physical conductor construction contains duplicate paths.")
        object.__setattr__(self, "paths", paths)

    @property
    def conductor_roles(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(path.conductor_role for path in self.paths))

    @classmethod
    def from_roles(
        cls,
        roles: Iterable[str],
        *,
        impedance_ohm: complex = 0j,
        from_terminal_role: str = "from",
        to_terminal_role: str = "to",
    ) -> "PhysicalConductorConstruction":
        if isinstance(roles, (str, bytes)):
            raise TypeError("roles must be an iterable of conductor-role values, not a string.")
        normalized = tuple(roles)
        if not normalized:
            raise ValueError("Physical conductor role inventory cannot be empty.")
        return cls(tuple(
            PhysicalConductorPath(
                conductor_role=str(role),
                from_terminal_role=from_terminal_role,
                to_terminal_role=to_terminal_role,
                impedance_ohm=impedance_ohm,
            )
            for role in normalized
        ))

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType({
            "paths": tuple({
                "conductor_role": path.conductor_role,
                "from_terminal_role": path.from_terminal_role,
                "to_terminal_role": path.to_terminal_role,
                "impedance_ohm": {"real": path.impedance_ohm.real, "imag": path.impedance_ohm.imag},
            } for path in self.paths)
        })


__all__ = ["PhysicalConductorPath", "PhysicalConductorConstruction"]
