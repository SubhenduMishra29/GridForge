# ============================================================
# File: ui/equipment/terminal_contract.py
# GridForge V2 — Cross-layer terminal contract reconciliation
# Author: Subhendu Mishra
# ============================================================

"""Declarative, Qt-free reconciliation for GridForge terminal roles.

This module does not own terminal identity. It validates the existing
EquipmentDefinition, CreationDefinition, SymbolDefinition and Core
Terminal.role authorities. EndpointReference remains the only
cross-boundary endpoint identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from .equipment_definition import EquipmentDefinition
    from ui.creation.creation_definition import CreationDefinition
    from .symbol.symbol_definition import SymbolDefinition


@dataclass(frozen=True, slots=True)
class TerminalContract:
    """Immutable derived contract for one declared terminal role."""

    terminal_role: str
    cardinality: str = "single"
    domain: str = "electrical"
    anchor_required: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.terminal_role, str) or not self.terminal_role.strip():
            raise ValueError("terminal_role must be a non-empty string.")
        if self.cardinality not in {"single", "pair", "multiple"}:
            raise ValueError("Unsupported terminal cardinality.")
        if not isinstance(self.domain, str) or not self.domain.strip():
            raise ValueError("terminal domain must be non-empty.")
        object.__setattr__(self, "terminal_role", self.terminal_role.strip())
        object.__setattr__(self, "domain", self.domain.strip())


@dataclass(frozen=True, slots=True)
class TerminalContractReport:
    """Immutable result of one equipment-family reconciliation."""

    equipment_type: str
    declared_roles: tuple[str, ...]
    creation_roles: tuple[str, ...]
    symbol_roles: tuple[str, ...]
    core_roles: tuple[str, ...] | None
    contracts: tuple[TerminalContract, ...]
    errors: tuple[str, ...]

    @property
    def is_match(self) -> bool:
        return not self.errors


def reconcile_terminal_contract(
    definition: "EquipmentDefinition",
    *,
    creation_definition: "CreationDefinition | None" = None,
    symbol_definition: "SymbolDefinition | None" = None,
    core_roles: Iterable[str] | None = None,
) -> TerminalContractReport:
    """Reconcile all existing terminal-role representations.

    core_roles is supplied by the Core audit boundary. This function
    never creates or stores Core terminals and never becomes a registry.
    """

    if definition is None:
        raise ValueError("definition must not be None.")

    declared_roles = tuple(definition.terminal_names)
    errors: list[str] = []

    creation = creation_definition or getattr(definition, "creation_definition", None)
    creation_roles = (
        tuple(req.terminal_name for req in creation.terminal_requirements)
        if creation is not None
        else ()
    )

    if creation is None and declared_roles:
        errors.append("Missing CreationDefinition for declared terminal roles.")
    elif creation is not None and creation_roles != declared_roles:
        errors.append(
            "CreationDefinition terminal roles do not exactly match "
            "EquipmentDefinition.terminal_names."
        )

    symbol_roles = (
        tuple(symbol_definition.terminal_anchors.keys())
        if symbol_definition is not None
        else ()
    )

    if symbol_definition is not None:
        missing = [role for role in declared_roles if role not in symbol_roles]
        orphaned = [role for role in symbol_roles if role not in declared_roles]
        if missing:
            errors.append(f"Missing symbol anchors: {missing!r}.")
        if orphaned:
            errors.append(f"Orphaned symbol anchors: {orphaned!r}.")
    elif declared_roles:
        errors.append("Missing SymbolDefinition for declared terminal roles.")

    normalized_core_roles: tuple[str, ...] | None = None
    if core_roles is not None:
        normalized_core_roles = tuple(core_roles)
        if len(normalized_core_roles) != len(set(normalized_core_roles)):
            errors.append("Core equipment owns duplicate terminal roles.")
        if normalized_core_roles != declared_roles:
            errors.append(
                "Core Terminal.role values do not exactly match "
                "EquipmentDefinition.terminal_names."
            )

    requirements = {
        req.terminal_name: req
        for req in (creation.terminal_requirements if creation is not None else ())
    }
    contracts = tuple(
        TerminalContract(
            terminal_role=role,
            cardinality=requirements.get(role).cardinality if role in requirements else "single",
            domain=(
                "electrical"
                if not requirements.get(role) or not requirements[role].allowed_connection_types
                else "|".join(requirements[role].allowed_connection_types)
            ),
            anchor_required=True,
        )
        for role in declared_roles
    )

    return TerminalContractReport(
        equipment_type=definition.equipment_type,
        declared_roles=declared_roles,
        creation_roles=creation_roles,
        symbol_roles=symbol_roles,
        core_roles=normalized_core_roles,
        contracts=contracts,
        errors=tuple(errors),
    )


def reconcile_role_sets(
    *,
    equipment_type: str,
    definition_roles: Iterable[str],
    creation_roles: Iterable[str],
    symbol_roles: Iterable[str],
    core_roles: Iterable[str],
) -> TerminalContractReport:
    """Reconcile role sets for a static audit without Core object construction."""

    declared = tuple(definition_roles)
    creation = tuple(creation_roles)
    symbol = tuple(symbol_roles)
    core = tuple(core_roles)
    errors: list[str] = []

    if creation != declared:
        errors.append("Creation roles do not match declared roles.")
    if symbol != declared:
        errors.append("Symbol anchor roles do not match declared roles.")
    if core != declared:
        errors.append("Core terminal roles do not match declared roles.")
    if len(core) != len(set(core)):
        errors.append("Core equipment owns duplicate terminal roles.")

    contracts = tuple(TerminalContract(role) for role in declared)
    return TerminalContractReport(
        equipment_type=equipment_type,
        declared_roles=declared,
        creation_roles=creation,
        symbol_roles=symbol,
        core_roles=core,
        contracts=contracts,
        errors=tuple(errors),
    )


__all__ = [
    "TerminalContract",
    "TerminalContractReport",
    "reconcile_terminal_contract",
    "reconcile_role_sets",
]
