# ============================================================
# Author: Subhendu Mishra
# GridForge V2
# ============================================================
# File:
#     ui/equipment/equipment_registry.py
#
# Purpose:
#     Registry of available SLD equipment definitions.
#
# Architectural Role:
#     Provides one authoritative UI-side lookup mechanism for
#     equipment TYPE definitions.
#
# Responsibilities:
#     - register equipment definitions;
#     - remove definitions;
#     - look up definitions;
#     - test equipment availability;
#     - enumerate available equipment types.
#
# Does NOT:
#     - create equipment instances;
#     - create QGraphicsItems;
#     - render symbols;
#     - maintain document instances;
#     - perform electrical calculations;
#     - validate electrical topology.
#
# ============================================================

"""
GridForge V2 — Equipment Registry.

Qt-independent registry of available SLD equipment definitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Iterable, Optional

if TYPE_CHECKING:
    from .symbol.symbol_registry import SymbolRegistry

from .equipment_definition import EquipmentDefinition
from ui.creation.creation_definition import creation_definition_for
from .terminal_contract import reconcile_terminal_contract





class EquipmentRegistry:
    """
    Registry containing available equipment type definitions.

    EquipmentRegistry owns TYPE metadata only.

    It does not own runtime equipment instances. Those belong to
    EquipmentManager.
    """

    def __init__(self) -> None:
        self._definitions: Dict[
            str,
            EquipmentDefinition,
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        definition: EquipmentDefinition,
    ) -> None:
        """
        Register one equipment definition.

        Duplicate equipment types are rejected.
        """

        if definition is None:
            raise ValueError(
                "definition must not be None"
            )

        if not isinstance(
            definition,
            EquipmentDefinition,
        ):
            raise TypeError(
                "definition must be an "
                "EquipmentDefinition instance"
            )

        equipment_type = definition.equipment_type

        if equipment_type in self._definitions:
            raise ValueError(
                f"Equipment type already registered: "
                f"{equipment_type}"
            )

        self._definitions[
            equipment_type
        ] = definition

    # ========================================================
    # REMOVAL
    # ========================================================

    def unregister(
        self,
        equipment_type: str,
    ) -> EquipmentDefinition:
        """
        Remove and return an equipment definition.

        Raises:
            KeyError:
                If the equipment type is not registered.
        """

        definition = self._definitions.pop(
            equipment_type,
            None,
        )

        if definition is None:
            raise KeyError(
                equipment_type
            )

        return definition

    # ========================================================
    # LOOKUP
    # ========================================================

    def get(
        self,
        equipment_type: str,
    ) -> Optional[EquipmentDefinition]:
        """
        Return a definition or None when absent.
        """

        return self._definitions.get(
            equipment_type
        )

    def require(
        self,
        equipment_type: str,
    ) -> EquipmentDefinition:
        """
        Return a registered definition.

        Raises:
            KeyError:
                If the equipment type is unknown.
        """

        definition = self.get(
            equipment_type
        )

        if definition is None:
            raise KeyError(
                f"Unknown equipment type: "
                f"{equipment_type}"
            )

        return definition

    def contains(
        self,
        equipment_type: str,
    ) -> bool:
        """
        Return whether an equipment type is registered.
        """

        return equipment_type in self._definitions

    # ========================================================
    # ENUMERATION
    # ========================================================

    def definitions(
        self,
    ) -> Iterable[EquipmentDefinition]:
        """
        Return a stable snapshot of all definitions.
        """

        return tuple(
            self._definitions.values()
        )

    def equipment_types(
        self,
    ) -> tuple[str, ...]:
        """
        Return all registered equipment type identifiers.
        """

        return tuple(
            self._definitions.keys()
        )

    # ========================================================
    # CANONICAL CATALOGUE PROJECTION
    # ========================================================

    def catalogue(self) -> tuple[EquipmentDefinition, ...]:
        """Return the project-independent equipment catalogue snapshot."""
        return tuple(self._definitions.values())

    def tool_id_for(self, equipment_type: str) -> str:
        """Resolve the canonical ToolManager identity for an equipment type."""
        return self.require(equipment_type).tool_id

    @classmethod
    def create_default(cls) -> "EquipmentRegistry":
        """Compose the built-in engineering equipment catalogue once."""
        registry = cls()
        definitions = (
            ("bus", "Bus", ("terminal",), "network"),
            ("line", "Line", ("from", "to"), "branch"),
            ("cable", "Cable", ("from", "to"), "branch"),
            ("transformer", "Transformer", ("from", "to"), "branch"),
            ("switch", "Switch", ("from", "to"), "switching"),
            ("breaker", "Breaker", ("from", "to"), "switching"),
            ("disconnector", "Disconnector", ("from", "to"), "switching"),
            ("fuse", "Fuse", ("from", "to"), "switching"),
            ("load", "Load", ("terminal",), "load"),
            ("generator", "Generator", ("terminal",), "generation"),
            ("synchronous_machine", "Synchronous Machine", ("terminal",), "generation"),
            ("motor", "Motor", ("terminal",), "load"),
            ("shunt", "Shunt", ("terminal",), "shunt"),
            ("capacitor", "Capacitor", ("terminal",), "shunt"),
            ("reactor", "Reactor", ("terminal",), "shunt"),
            ("solar", "Solar", ("terminal",), "generation"),
            ("battery", "Battery", ("terminal",), "storage"),
            ("grid", "Grid", ("terminal",), "source"),
            ("current_transformer", "Current Transformer", ("P1", "P2", "S1", "S2"), "measurement"),
            ("potential_transformer", "Potential Transformer", ("primary_a", "primary_b", "secondary_a", "secondary_b"), "measurement"),
            ("cvt", "Capacitive Voltage Transformer", ("H1", "H2", "X1", "X2"), "measurement"),
            ("relay", "Relay", (), "protection"),
        )
        for equipment_type, display_name, terminals, category in definitions:
            creation_definition = creation_definition_for(equipment_type, terminals)
            registry.register(
                EquipmentDefinition(
                    equipment_type=equipment_type,
                    display_name=display_name,
                    tool_id=equipment_type,
                    terminal_names=terminals,
                    category=category,
                    engineering_parameters=creation_definition.parameter_definitions,
                    creation_definition=creation_definition,
                )
            )
        return registry

    def validate_creation_contracts(self) -> tuple[str, ...]:
        """Return static creation-contract inconsistencies for this catalogue."""
        from ui.creation.command_factory import verify_creation_contracts
        return verify_creation_contracts(self.catalogue())

    # ========================================================
    # PRESENTATION CONTRACT
    # ========================================================

    def validate_symbol_anchors(self, symbol_registry: "SymbolRegistry") -> None:
        """Validate symbol anchors and the complete presentation terminal contract."""
        self.validate_terminal_contracts(symbol_registry)

    def validate_terminal_contracts(
        self,
        symbol_registry: "SymbolRegistry",
        *,
        core_roles_by_type: Mapping[str, tuple[str, ...]] | None = None,
    ) -> tuple[object, ...]:
        """Reconcile definition, creation, symbol and optional Core roles.

        The returned reports are derived diagnostics; this registry does not
        become a Core terminal authority.
        """
        from .symbol.symbol_registry import SymbolRegistry
        if not isinstance(symbol_registry, SymbolRegistry):
            raise TypeError("symbol_registry must be a SymbolRegistry")
        reports = []
        for definition in self._definitions.values():
            symbol = symbol_registry.require(definition.symbol_id)
            report = reconcile_terminal_contract(
                definition,
                creation_definition=definition.creation_definition,
                symbol_definition=symbol,
                core_roles=None if core_roles_by_type is None else core_roles_by_type.get(definition.equipment_type),
            )
            if report.errors:
                raise ValueError(
                    f"Terminal contract mismatch for {definition.equipment_type!r}: "
                    + " ".join(report.errors)
                )
            reports.append(report)
        return tuple(reports)

    # ========================================================
    # COLLECTION MANAGEMENT
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all equipment type definitions.
        """

        self._definitions.clear()

    # ========================================================
    # PROTOCOL HELPERS
    # ========================================================

    def __len__(
        self,
    ) -> int:
        return len(
            self._definitions
        )

    def __contains__(
        self,
        equipment_type: str,
    ) -> bool:
        return self.contains(
            equipment_type
        )
