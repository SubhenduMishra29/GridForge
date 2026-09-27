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

from .equipment_definition import EquipmentDefinition, EngineeringParameterDefinition



def _p(parameter_id: str, display_name: str | None = None, datatype: str = "float",
       unit: str | None = None, *, required: bool = False, default: object = None,
       editable: bool = True, derived: bool = False, choices: tuple[object, ...] = (),
       minimum: float | None = None, maximum: float | None = None) -> EngineeringParameterDefinition:
    return EngineeringParameterDefinition(
        parameter_id=parameter_id, display_name=display_name or parameter_id.replace("_", " ").title(),
        datatype=datatype, unit=unit, required_before_create=required, default_value=default,
        editable=editable, derived=derived, choices=choices, minimum=minimum, maximum=maximum,
    )


_CREATION_SCHEMAS: dict[str, tuple[EngineeringParameterDefinition, ...]] = {
    "bus": (_p("nominal_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("frequency_hz", unit="Hz", required=True, minimum=0.0),
            _p("in_service", "In service", "bool", required=True, default=True)),
    "line": (_p("resistance_ohm", unit="ohm", required=True),
             _p("reactance_ohm", unit="ohm", required=True),
             _p("rate_mva", unit="MVA", required=True, minimum=0.0),
             _p("shunt_susceptance_siemens", unit="S", default=0.0)),
    "cable": (_p("length_km", unit="km", required=True, minimum=0.0),
              _p("r1_ohm_per_km", unit="ohm/km", required=True),
              _p("x1_ohm_per_km", unit="ohm/km", required=True),
              _p("rated_voltage_kv", unit="kV", minimum=0.0),
              _p("rated_current_a", unit="A", minimum=0.0)),
    "transformer": (_p("r", "Resistance", required=True),
                    _p("x", "Reactance", required=True),
                    _p("b", "Susceptance", default=0.0),
                    _p("impedance_basis", "Impedance basis", "enum", required=True,
                       choices=("pu", "percent", "absolute")),
                    _p("impedance_base_voltage_kv", unit="kV", required=True, minimum=0.0),
                    _p("impedance_base_mva", unit="MVA", minimum=0.0),
                    _p("rate_mva", unit="MVA", minimum=0.0)),
    "switch": (_p("voltage_kv", unit="kV", required=True, minimum=0.0),
               _p("rated_current_a", unit="A", required=True, minimum=0.0)),
    "breaker": (_p("voltage_kv", unit="kV", required=True, minimum=0.0),
                _p("rated_current_a", unit="A", required=True, minimum=0.0)),
    "disconnector": (_p("voltage_kv", unit="kV", required=True, minimum=0.0),
                     _p("rated_current_a", unit="A", required=True, minimum=0.0)),
    "fuse": (_p("rated_current_a", unit="A", required=True, minimum=0.0),
             _p("voltage_kv", unit="kV", required=True, minimum=0.0)),
    "load": (_p("p", "Active power", unit="MW", required=True),
             _p("q", "Reactive power", unit="MVAr", required=True)),
    "generator": (_p("p", "Active power", unit="MW", required=True),
                  _p("q", "Reactive power", unit="MVAr", required=True),
                  _p("V_setpoint", "Voltage setpoint", unit="pu", required=True)),
    "synchronous_machine": (_p("p", "Active power", unit="MW", required=True),
                            _p("q", "Reactive power", unit="MVAr", required=True)),
    "motor": (_p("p", "Active power", unit="MW", required=True),
              _p("q", "Reactive power", unit="MVAr", required=True)),
    "shunt": (_p("q", "Reactive power", unit="MVAr", required=True),),
    "capacitor": (_p("q", "Reactive power", unit="MVAr", required=True),),
    "reactor": (_p("q", "Reactive power", unit="MVAr", required=True),),
    "solar": (_p("p", "Active power", unit="MW", required=True),
              _p("q", "Reactive power", unit="MVAr", required=True)),
    "battery": (_p("p", "Active power", unit="MW", required=True),
                _p("q", "Reactive power", unit="MVAr", required=True)),
    "grid": (_p("nominal_voltage_kv", unit="kV", required=True, minimum=0.0),
             _p("frequency_hz", unit="Hz", required=True, minimum=0.0)),
    "current_transformer": (_p("primary_rated_current_a", unit="A", required=True, minimum=0.0),
                            _p("secondary_rated_current_a", unit="A", required=True, minimum=0.0),
                            _p("burden_va", unit="VA", minimum=0.0),
                            _p("accuracy_class", "Accuracy class", "str"),
                            _p("frequency_hz", unit="Hz", required=True, minimum=0.0),
                            _p("polarity", "Polarity", "enum", required=True, choices=("P1_P2", "P2_P1"))),
    "potential_transformer": (_p("primary_voltage_kv", unit="kV", required=True, minimum=0.0),
                              _p("secondary_voltage_v", unit="V", required=True, minimum=0.0),
                              _p("accuracy_class", "Accuracy class", "str"),
                              _p("burden_va", unit="VA", minimum=0.0),
                              _p("phase_displacement_deg", unit="deg")),
    "cvt": (_p("rated_primary_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("rated_secondary_voltage_v", unit="V", required=True, minimum=0.0),
            _p("accuracy_class", "Accuracy class", "str"),
            _p("rated_burden_va", unit="VA", minimum=0.0),
            _p("frequency_hz", unit="Hz", required=True, minimum=0.0),
            _p("polarity", "Polarity", "enum", required=True, choices=("NORMAL", "REVERSED"))),
    "relay": (_p("relay_type", "Relay type", "str", required=True),),
}


def creation_schema_for(equipment_type: str) -> tuple[EngineeringParameterDefinition, ...]:
    try:
        return _CREATION_SCHEMAS[equipment_type]
    except KeyError as exc:
        raise KeyError(f"No canonical creation schema for {equipment_type!r}") from exc



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
            registry.register(
                EquipmentDefinition(
                    equipment_type=equipment_type,
                    display_name=display_name,
                    tool_id=equipment_type,
                    terminal_names=terminals,
                    category=category,
                    engineering_parameters=creation_schema_for(equipment_type),
                )
            )
        return registry

    # ========================================================
    # PRESENTATION CONTRACT
    # ========================================================

    def validate_symbol_anchors(self, symbol_registry: "SymbolRegistry") -> None:
        """Validate the canonical definition-to-symbol terminal contract."""
        from .symbol.symbol_registry import SymbolRegistry
        if not isinstance(symbol_registry, SymbolRegistry):
            raise TypeError("symbol_registry must be a SymbolRegistry")
        for definition in self._definitions.values():
            symbol = symbol_registry.require(definition.symbol_id)
            missing = [name for name in definition.terminal_names if not symbol.has_terminal_anchor(name)]
            orphaned = [name for name in symbol.terminal_anchors if name not in definition.terminal_names]
            if missing or orphaned:
                raise ValueError(
                    f"Equipment type {definition.equipment_type!r} and symbol {definition.symbol_id!r} "
                    f"have inconsistent connection anchors: missing={missing!r}, orphaned={orphaned!r}."
                )

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
