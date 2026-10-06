# ============================================================
# File: ui/creation/creation_definition.py
# GridForge V2 — Canonical equipment creation contracts
# Author: Subhendu Mishra
# ============================================================
"""Declarative creation contracts for registered equipment types.

This module is the single creation-schema authority.  It describes
engineering parameters, topology/terminal acquisition, preview support,
and the immutable Application command contract.  It contains no Core
mutation and no UI lifecycle state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from ui.equipment.equipment_definition import EngineeringParameterDefinition


@dataclass(frozen=True, slots=True)
class CreationTerminalRequirement:
    """Declarative acquisition requirement for one canonical Core terminal."""

    terminal_name: str
    required: bool = False
    cardinality: str = "single"
    allowed_connection_types: tuple[str, ...] = ()
    acquisition_state: str = "required"
    initial_endpoint_required: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.terminal_name, str) or not self.terminal_name.strip():
            raise ValueError("terminal_name must be non-empty.")
        if self.cardinality not in {"single", "pair", "multiple"}:
            raise ValueError("cardinality must be single, pair, or multiple.")
        if self.acquisition_state not in {"required", "optional", "acquired", "pending"}:
            raise ValueError("acquisition_state must be required, optional, acquired, or pending.")
        object.__setattr__(self, "terminal_name", self.terminal_name.strip())
        object.__setattr__(self, "allowed_connection_types", tuple(self.allowed_connection_types))


@dataclass(frozen=True, slots=True)
class CreationTopologyRequirement:
    """Declarative endpoint/topology acquisition requirement."""

    name: str
    required: bool = False
    cardinality: str = "single"
    allowed_connection_types: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("topology requirement name must be non-empty.")
        if self.cardinality not in {"single", "pair", "multiple"}:
            raise ValueError("cardinality must be single, pair, or multiple.")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "allowed_connection_types", tuple(self.allowed_connection_types))


@dataclass(frozen=True, slots=True)
class ConditionalParameterRequirement:
    """Declarative conditional completeness rule."""

    label: str
    require_any: tuple[str, ...] = ()
    require_all: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.require_any and not self.require_all:
            raise ValueError("A conditional requirement must name parameters.")
        object.__setattr__(self, "require_any", tuple(self.require_any))
        object.__setattr__(self, "require_all", tuple(self.require_all))


@dataclass(frozen=True, slots=True)
class CreationDefinition:
    """Immutable canonical creation contract for one equipment type."""

    equipment_type: str
    tool_id: str
    parameter_definitions: tuple[EngineeringParameterDefinition, ...]
    command_type: str
    id_field: str
    parameter_mapping: Mapping[str, str] = field(default_factory=dict)
    endpoint_mapping: Mapping[str, str] = field(default_factory=dict)
    topology_requirements: tuple[CreationTopologyRequirement, ...] = ()
    terminal_requirements: tuple[CreationTerminalRequirement, ...] = ()
    conditional_requirements: tuple[ConditionalParameterRequirement, ...] = ()
    placement_required: bool = True
    preview_supported: bool = True
    configuration_required: bool = False

    def __post_init__(self) -> None:
        if not self.equipment_type.strip() or not self.tool_id.strip():
            raise ValueError("CreationDefinition identities must be non-empty.")
        if not isinstance(self.command_type, str) or not self.command_type.strip():
            raise TypeError("command_type must be a non-empty Application command type.")
        if not self.id_field.strip():
            raise ValueError("id_field must be non-empty.")
        parameters = tuple(self.parameter_definitions)
        ids = [item.parameter_id for item in parameters]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate creation parameter in {self.equipment_type!r}.")
        mapping = dict(self.parameter_mapping)
        for parameter_id in ids:
            mapping.setdefault(parameter_id, parameter_id)
        unknown = set(mapping) - set(ids)
        if unknown:
            raise ValueError(f"Command mapping references unknown parameters: {sorted(unknown)!r}")
        object.__setattr__(self, "equipment_type", self.equipment_type.strip())
        object.__setattr__(self, "tool_id", self.tool_id.strip())
        object.__setattr__(self, "id_field", self.id_field.strip())
        object.__setattr__(self, "command_type", self.command_type.strip())
        object.__setattr__(self, "parameter_definitions", parameters)
        object.__setattr__(self, "parameter_mapping", mapping)
        object.__setattr__(self, "endpoint_mapping", dict(self.endpoint_mapping))
        object.__setattr__(self, "topology_requirements", tuple(self.topology_requirements))
        object.__setattr__(self, "terminal_requirements", tuple(self.terminal_requirements))
        object.__setattr__(self, "conditional_requirements", tuple(self.conditional_requirements))

    @property
    def required_parameters(self) -> tuple[EngineeringParameterDefinition, ...]:
        return tuple(p for p in self.parameter_definitions if p.required_before_create)

    @property
    def optional_parameters(self) -> tuple[EngineeringParameterDefinition, ...]:
        return tuple(p for p in self.parameter_definitions if not p.required_before_create)

    @property
    def default_values(self) -> Mapping[str, Any]:
        return {p.parameter_id: p.default_value for p in self.parameter_definitions if p.default_value is not None}

    def parameter(self, parameter_id: str) -> EngineeringParameterDefinition:
        for parameter in self.parameter_definitions:
            if parameter.parameter_id == parameter_id:
                return parameter
        raise KeyError(parameter_id)

    def validate_values(self, values: Mapping[str, Any]) -> tuple[str, ...]:
        errors: list[str] = []
        for parameter in self.parameter_definitions:
            value = values.get(parameter.parameter_id)
            if parameter.required_before_create and value is None:
                errors.append(f"{parameter.display_name} is required.")
                continue
            if value is None:
                continue
            try:
                _validate_parameter(parameter, value)
            except (TypeError, ValueError) as exc:
                errors.append(f"{parameter.display_name}: {exc}")
        for conditional in self.conditional_requirements:
            if conditional.require_any and not any(values.get(key) is not None for key in conditional.require_any):
                errors.append(conditional.label)
            if conditional.require_all and not all(values.get(key) is not None for key in conditional.require_all):
                errors.append(conditional.label)
        return tuple(errors)


def _validate_parameter(definition: EngineeringParameterDefinition, value: Any) -> None:
    unit = None
    if isinstance(value, Mapping):
        unit = value.get("unit")
        value = value.get("value")
    if unit is not None and definition.unit is not None and str(unit).strip() != str(definition.unit).strip():
        raise ValueError(f"unit must be {definition.unit!r}")
    datatype = definition.datatype.strip().lower()
    if datatype in {"float", "number"}:
        if isinstance(value, bool):
            raise TypeError("must be numeric")
        numeric = float(value)
        if definition.minimum is not None and numeric < definition.minimum:
            raise ValueError(f"must be >= {definition.minimum}")
        if definition.maximum is not None and numeric > definition.maximum:
            raise ValueError(f"must be <= {definition.maximum}")
    elif datatype in {"int", "integer"}:
        if isinstance(value, bool) or int(value) != value:
            raise TypeError("must be an integer")
        numeric = int(value)
        if definition.minimum is not None and numeric < definition.minimum:
            raise ValueError(f"must be >= {definition.minimum}")
        if definition.maximum is not None and numeric > definition.maximum:
            raise ValueError(f"must be <= {definition.maximum}")
    elif datatype in {"bool", "boolean"}:
        if not isinstance(value, bool):
            raise TypeError("must be boolean")
    elif datatype == "enum":
        if str(value) not in tuple(str(choice) for choice in definition.choices):
            raise ValueError(f"must be one of {tuple(definition.choices)!r}")
    elif datatype in {"str", "string"}:
        if not isinstance(value, str):
            raise TypeError("must be text")
    rules = dict(definition.validation)
    if rules.get("non_empty") and (value is None or (isinstance(value, str) and not value.strip())):
        raise ValueError("must not be empty")
    if rules.get("nonzero") and value == 0:
        raise ValueError("must be non-zero")
    if "allowed_values" in rules and value not in tuple(rules["allowed_values"]):
        raise ValueError(f"must be one of {tuple(rules['allowed_values'])!r}")


def _p(parameter_id: str, display_name: str | None = None, datatype: str = "float",
       unit: str | None = None, *, required: bool = False, default: Any = None,
       editable: bool = True, derived: bool = False, choices: tuple[Any, ...] = (),
       minimum: float | None = None, maximum: float | None = None,
       validation: Mapping[str, Any] | None = None) -> EngineeringParameterDefinition:
    return EngineeringParameterDefinition(
        parameter_id=parameter_id,
        display_name=display_name or parameter_id.replace("_", " ").title(),
        datatype=datatype,
        unit=unit,
        required_before_create=required,
        default_value=default,
        editable=editable,
        derived=derived,
        choices=choices,
        minimum=minimum,
        maximum=maximum,
        validation={} if validation is None else dict(validation),
    )


def _terminals(names: tuple[str, ...], *, required: bool = True, initial_endpoint_required: bool = False) -> tuple[CreationTerminalRequirement, ...]:
    return tuple(
        CreationTerminalRequirement(
            name,
            required=required,
            cardinality="single",
            allowed_connection_types=("electrical",),
            acquisition_state="required",
            initial_endpoint_required=initial_endpoint_required,
        )
        for name in names
    )


def _definition(
    equipment_type: str,
    tool_id: str,
    parameters: tuple[EngineeringParameterDefinition, ...],
    command_type: str,
    id_field: str,
    *,
    topology: tuple[CreationTopologyRequirement, ...] = (),
    endpoint_mapping: Mapping[str, str] | None = None,
    parameter_mapping: Mapping[str, str] = {},
    terminal_names: tuple[str, ...] = (),
    conditional: tuple[ConditionalParameterRequirement, ...] = (),
    initial_endpoint_required: bool = False,
) -> CreationDefinition:
    return CreationDefinition(
        equipment_type=equipment_type,
        tool_id=tool_id,
        parameter_definitions=parameters,
        command_type=command_type,
        id_field=id_field,
        parameter_mapping=parameter_mapping,
        endpoint_mapping=endpoint_mapping or {},
        topology_requirements=topology,
        terminal_requirements=_terminals(terminal_names, initial_endpoint_required=initial_endpoint_required),
        conditional_requirements=conditional,
        configuration_required=any(p.required_before_create for p in parameters),
    )


def creation_definition_for(equipment_type: str, terminal_names: tuple[str, ...]) -> CreationDefinition:
    endpoint_pair = (
        CreationTopologyRequirement("FROM", required=True),
        CreationTopologyRequirement("TO", required=True),
    )
    common_endpoints = {"FROM": "endpoint_from", "TO": "endpoint_to"}
    switching_endpoints = {"from": "endpoint_from", "to": "endpoint_to"}

    definitions: dict[str, CreationDefinition] = {
        "bus": _definition("bus", "bus", (
            _p("nominal_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("frequency_hz", unit="Hz", required=True, minimum=0.0),
            _p("in_service", "In service", "bool", required=True, default=True),
        ), "model.create_bus", "bus_id"),
        "grid": _definition("grid", "grid", (
            _p("nominal_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("frequency_hz", unit="Hz", required=True, minimum=0.0),
        ), "model.create_grid", "grid_id", endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "generator": _definition("generator", "generator", (
            _p("p", "Active power", unit="MW", required=True),
            _p("q", "Reactive power", unit="MVAr", required=True),
            _p("V_setpoint", "Voltage setpoint", unit="pu", required=True),
        ), "model.create_generator", "generator_id", endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "load": _definition("load", "load", (
            _p("p", "Active power", unit="MW", required=True),
            _p("q", "Reactive power", unit="MVAr", required=True),
        ), "model.create_load", "load_id", endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "shunt": _definition("shunt", "shunt", (
            _p("g_pu", "Conductance", required=True),
            _p("b_pu", "Susceptance", required=True),
        ), "model.create_shunt", "shunt_id", endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "capacitor": _definition("capacitor", "capacitor", (
            _p("reactive_power_injection_mvar", "Reactive power", unit="MVAr", required=True),
        ), "model.create_capacitor", "capacitor_id", endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "reactor": _definition("reactor", "reactor", (
            _p("reactive_power_injection_mvar", "Reactive power", unit="MVAr", required=True),
        ), "model.create_reactor", "reactor_id", endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "solar": _definition("solar", "solar", (
            _p("p_mw", "Active power", unit="MW", required=True),
            _p("q_mvar", "Reactive power", unit="MVAr", required=True),
        ), "model.create_solar", "solar_id", endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "battery": _definition("battery", "battery", (
            _p("p_mw", "Active power", unit="MW", required=True),
            _p("q_mvar", "Reactive power", unit="MVAr", required=True),
            _p("energy_capacity_mwh", unit="MWh", required=True, minimum=0.0),
            _p("max_charge_mw", unit="MW", minimum=0.0),
            _p("max_discharge_mw", unit="MW", minimum=0.0),
            _p("soc", "State of charge", unit="pu", default=1.0, minimum=0.0, maximum=1.0),
        ), "model.create_battery", "battery_id", endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "motor": _definition("motor", "motor", (
            _p("rated_mva", unit="MVA", required=True, minimum=0.0),
            _p("rated_kv", unit="kV", required=True, minimum=0.0),
            _p("power_factor", minimum=0.0, maximum=1.0, default=0.9),
            _p("p", "Active power", unit="MW", required=True),
            _p("q", "Reactive power", unit="MVAr", required=True),
            _p("efficiency", minimum=0.0, maximum=1.0, default=1.0),
            _p("slip", default=0.0),
            _p("starting_current_pu", default=0.0),
        ), "model.create_motor", "motor_id", endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "synchronous_machine": _definition("synchronous_machine", "synchronous_machine", (
            _p("active_power_injection_mw", "Active power", unit="MW", required=True),
            _p("reactive_power_injection_mvar", "Reactive power", unit="MVAr", required=True),
            _p("rated_power_mva", unit="MVA", minimum=0.0),
            _p("rated_voltage_kv", unit="kV", minimum=0.0),
            _p("frequency_hz", unit="Hz", required=True, default=50.0, minimum=0.0),
        ), "model.create_synchronous_machine", "synchronous_machine_id", endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "line": _definition("line", "line", (
            _p("resistance_ohm", unit="ohm", required=True),
            _p("reactance_ohm", unit="ohm", required=True),
            _p("rate_mva", unit="MVA", required=True, minimum=0.0),
            _p("shunt_susceptance_siemens", unit="S", default=0.0),
            _p("name", "Name", "str", default=""),
        ), "model.create_line", "line_id", endpoint_mapping=common_endpoints, terminal_names=terminal_names),
        "cable": _definition("cable", "cable", (
            _p("length_km", unit="km", required=True, minimum=0.0),
            _p("r1_ohm_per_km", unit="ohm/km", required=True),
            _p("x1_ohm_per_km", unit="ohm/km", required=True),
            _p("b1_us_per_km", unit="uS/km", default=0.0),
            _p("r0_ohm_per_km", unit="ohm/km", minimum=0.0),
            _p("x0_ohm_per_km", unit="ohm/km", minimum=0.0),
            _p("b0_us_per_km", unit="uS/km", minimum=0.0),
            _p("rated_voltage_kv", unit="kV", minimum=0.0),
            _p("rated_current_a", unit="A", minimum=0.0),
            _p("name", "Name", "str", default=""),
        ), "model.create_cable", "cable_id", endpoint_mapping=common_endpoints, terminal_names=terminal_names),
        "transformer": _definition("transformer", "transformer", (
            _p("r", "Resistance", required=True),
            _p("x", "Reactance", required=True),
            _p("b", "Susceptance", default=0.0),
            _p("impedance_basis", "Impedance basis", "enum", required=True, choices=("pu", "engineering")),
            _p("impedance_base_voltage_kv", unit="kV", required=True, minimum=0.0, validation={"nonzero": True}),
            _p("impedance_base_mva", unit="MVA", minimum=0.0, validation={"nonzero": True}),
            _p("rate_mva", unit="MVA", minimum=0.0, validation={"nonzero": True}),
            _p("tap", "Tap", default=1.0),
            _p("shift", "Phase shift", unit="deg", default=0.0),
            _p("name", "Name", "str", default=""),
        ), "model.create_transformer", "transformer_id", endpoint_mapping=common_endpoints, terminal_names=terminal_names,
           conditional=(ConditionalParameterRequirement(
               "Transformer requires impedance_base_mva or rate_mva.",
               require_any=("impedance_base_mva", "rate_mva"),
           ),)),
        "switch": _definition("switch", "switch", (
            _p("rated_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("rated_current_a", unit="A", required=True, minimum=0.0),
        ), "model.create_switch", "switch_id", endpoint_mapping={"from": "endpoint_a", "to": "endpoint_b"}, terminal_names=terminal_names),
        "breaker": _definition("breaker", "breaker", (
            _p("voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("current_a", unit="A", required=True, minimum=0.0),
            _p("interrupting_ka", unit="kA", required=True, minimum=0.0),
            _p("closed", "Closed", "bool", default=True),
            _p("in_service", "In service", "bool", default=True),
        ), "model.create_breaker", "breaker_id", endpoint_mapping=switching_endpoints, terminal_names=terminal_names),
        "disconnector": _definition("disconnector", "disconnector", (
            _p("voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("rated_current_a", unit="A", required=True, minimum=0.0),
        ), "model.create_disconnector", "disconnector_id", endpoint_mapping=switching_endpoints, terminal_names=terminal_names),
        "fuse": _definition("fuse", "fuse", (
            _p("rated_current_a", unit="A", required=True, minimum=0.0),
            _p("rated_voltage_v", unit="V", required=True, minimum=0.0),
        ), "model.create_fuse", "fuse_id", endpoint_mapping=switching_endpoints, terminal_names=terminal_names),
        "current_transformer": _definition("current_transformer", "current_transformer", (
            _p("primary_rated_current_a", unit="A", required=True, minimum=0.0),
            _p("secondary_rated_current_a", unit="A", required=True, minimum=0.0),
            _p("burden_va", unit="VA", minimum=0.0),
            _p("accuracy_class", "Accuracy class", "str"),
            _p("frequency_hz", unit="Hz", required=True, minimum=0.0),
            _p("polarity", "Polarity", "enum", required=True, choices=("P1_P2", "P2_P1")),
        ), "model.create_current_transformer", "transformer_id",
           endpoint_mapping={"P1": "p1_endpoint", "P2": "p2_endpoint", "S1": "s1_endpoint", "S2": "s2_endpoint"},
           terminal_names=terminal_names),
        "potential_transformer": _definition("potential_transformer", "potential_transformer", (
            _p("primary_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("secondary_voltage_v", unit="V", required=True, minimum=0.0),
            _p("accuracy_class", "Accuracy class", "str"),
            _p("burden_va", unit="VA", minimum=0.0),
            _p("phase_displacement_deg", unit="deg"),
        ), "model.create_potential_transformer", "pt_id",
           endpoint_mapping={"primary_a": "primary_a", "primary_b": "primary_b", "secondary_a": "secondary_a", "secondary_b": "secondary_b"},
           terminal_names=terminal_names),
        "cvt": _definition("cvt", "cvt", (
            _p("rated_primary_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("rated_secondary_voltage_v", unit="V", required=True, minimum=0.0),
            _p("accuracy_class", "Accuracy class", "str"),
            _p("rated_burden_va", unit="VA", minimum=0.0),
            _p("frequency_hz", unit="Hz", required=True, minimum=0.0),
            _p("polarity", "Polarity", "enum", required=True, choices=("NORMAL", "REVERSED")),
        ), "model.create_capacitive_voltage_transformer", "transformer_id",
           endpoint_mapping={"H1": "h1_endpoint", "H2": "h2_endpoint", "X1": "x1_endpoint", "X2": "x2_endpoint"},
           terminal_names=terminal_names),
        "relay": _definition("relay", "relay", (
            _p("relay_type", "Relay type", "str", required=True),
        ), "model.create_relay", "relay_id"),
    }
    try:
        definition = definitions[equipment_type]
    except KeyError as exc:
        raise KeyError(f"No canonical creation definition for {equipment_type!r}") from exc
    return definition


__all__ = [
    "ConditionalParameterRequirement",
    "CreationDefinition",
    "CreationTerminalRequirement",
    "CreationTopologyRequirement",
    "creation_definition_for",
]
