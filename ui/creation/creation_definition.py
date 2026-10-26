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
from types import MappingProxyType
from typing import Any, Mapping

from core.application.creation_schema import (
    ConditionalParameterRequirement,
    CreationDefinition,
    CreationTerminalRequirement,
    CreationTopologyRequirement,
    EngineeringParameterDefinition,
    _validate_parameter,
)


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
        # Endpoint-field mappings describe how connected endpoints are passed
        # to a Core create command; they do not make every mapped endpoint
        # mandatory. Required topology is declared explicitly per equipment type.
        topology_requirements=topology,
        terminal_requirements=_terminals(terminal_names, initial_endpoint_required=initial_endpoint_required),
        conditional_requirements=conditional,
        configuration_required=any(p.required_before_create for p in parameters),
    )


def creation_definition_for(equipment_type: str, terminal_names: tuple[str, ...]) -> CreationDefinition:
    common_endpoints = {"FROM": "endpoint_from", "TO": "endpoint_to"}
    switching_endpoints = {"from": "endpoint_from", "to": "endpoint_to"}
    # Required connection terminals are explicit per equipment family. They
    # are checked only at network commit, never during placement or editing.
    single_terminal_topology = (CreationTopologyRequirement("terminal", required=True),)
    branch_topology = (
        CreationTopologyRequirement("FROM", required=True),
        CreationTopologyRequirement("TO", required=True),
    )
    switching_topology = (
        CreationTopologyRequirement("from", required=True),
        CreationTopologyRequirement("to", required=True),
    )

    definitions: dict[str, CreationDefinition] = {
        # A Bus is a connection-attachment owner, not terminalized equipment.
        # Bus attachments are represented by canonical attachment IDs in the
        # network connectivity contract, never by a synthetic "bus" terminal.
        "bus": _definition("bus", "bus", (
            _p("nominal_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("frequency_hz", unit="Hz", required=True, minimum=0.0),
            _p("in_service", "In service", "bool", required=True, default=True),
        ), "model.create_bus", "bus_id"),
        "grid": _definition("grid", "grid", (
            _p("nominal_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("frequency_hz", unit="Hz", required=True, minimum=0.0),
        ), "model.create_grid", "grid_id", topology=single_terminal_topology, endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "generator": _definition("generator", "generator", (
            _p("p", "Active power", unit="MW", required=True),
            _p("q", "Reactive power", unit="MVAr", required=True),
            _p("V_setpoint", "Voltage setpoint", unit="pu", required=True),
        ), "model.create_generator", "generator_id", topology=single_terminal_topology, endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "load": _definition("load", "load", (
            _p("p", "Active power", unit="MW", required=True),
            _p("q", "Reactive power", unit="MVAr", required=True),
        ), "model.create_load", "load_id", topology=single_terminal_topology, endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "shunt": _definition("shunt", "shunt", (
            _p("g_pu", "Conductance", required=True),
            _p("b_pu", "Susceptance", required=True),
        ), "model.create_shunt", "shunt_id", topology=single_terminal_topology, endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "capacitor": _definition("capacitor", "capacitor", (
            _p("reactive_power_injection_mvar", "Reactive power", unit="MVAr", required=True),
        ), "model.create_capacitor", "capacitor_id", topology=single_terminal_topology, endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "reactor": _definition("reactor", "reactor", (
            _p("reactive_power_injection_mvar", "Reactive power", unit="MVAr", required=True),
        ), "model.create_reactor", "reactor_id", topology=single_terminal_topology, endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "solar": _definition("solar", "solar", (
            _p("p_mw", "Active power", unit="MW", required=True),
            _p("q_mvar", "Reactive power", unit="MVAr", required=True),
        ), "model.create_solar", "solar_id", topology=single_terminal_topology, endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "battery": _definition("battery", "battery", (
            _p("p_mw", "Active power", unit="MW", required=True),
            _p("q_mvar", "Reactive power", unit="MVAr", required=True),
            _p("energy_capacity_mwh", unit="MWh", required=True, minimum=0.0),
            _p("max_charge_mw", unit="MW", minimum=0.0),
            _p("max_discharge_mw", unit="MW", minimum=0.0),
            _p("soc", "State of charge", unit="pu", default=1.0, minimum=0.0, maximum=1.0),
        ), "model.create_battery", "battery_id", topology=single_terminal_topology, endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "motor": _definition("motor", "motor", (
            _p("rated_mva", unit="MVA", required=True, minimum=0.0),
            _p("rated_kv", unit="kV", required=True, minimum=0.0),
            _p("power_factor", minimum=0.0, maximum=1.0, default=0.9),
            _p("p", "Active power", unit="MW", required=True),
            _p("q", "Reactive power", unit="MVAr", required=True),
            _p("efficiency", minimum=0.0, maximum=1.0, default=1.0),
            _p("slip", default=0.0),
            _p("starting_current_pu", default=0.0),
        ), "model.create_motor", "motor_id", topology=single_terminal_topology, endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "synchronous_machine": _definition("synchronous_machine", "synchronous_machine", (
            _p("active_power_injection_mw", "Active power", unit="MW", required=True),
            _p("reactive_power_injection_mvar", "Reactive power", unit="MVAr", required=True),
            _p("rated_power_mva", unit="MVA", minimum=0.0),
            _p("rated_voltage_kv", unit="kV", minimum=0.0),
            _p("frequency_hz", unit="Hz", required=True, default=50.0, minimum=0.0),
        ), "model.create_synchronous_machine", "synchronous_machine_id", topology=single_terminal_topology, endpoint_mapping={"terminal": "endpoint"}, terminal_names=terminal_names),
        "line": _definition("line", "line", (
            _p("resistance_ohm", unit="ohm", required=True),
            _p("reactance_ohm", unit="ohm", required=True),
            _p("rate_mva", unit="MVA", required=True, minimum=0.0),
            _p("shunt_susceptance_siemens", unit="S", default=0.0),
            _p("name", "Name", "str", default=""),
        ), "model.create_line", "line_id", topology=branch_topology, endpoint_mapping=common_endpoints, terminal_names=terminal_names),
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
        ), "model.create_cable", "cable_id", topology=branch_topology, endpoint_mapping=common_endpoints, terminal_names=terminal_names),
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
        ), "model.create_transformer", "transformer_id", topology=branch_topology, endpoint_mapping=common_endpoints, terminal_names=terminal_names,
           conditional=(ConditionalParameterRequirement(
               "Transformer requires impedance_base_mva or rate_mva.",
               require_any=("impedance_base_mva", "rate_mva"),
           ),)),
        "switch": _definition("switch", "switch", (
            _p("rated_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("rated_current_a", unit="A", required=True, minimum=0.0),
        ), "model.create_switch", "switch_id", topology=switching_topology, endpoint_mapping={"from": "endpoint_a", "to": "endpoint_b"}, terminal_names=terminal_names),
        "breaker": _definition("breaker", "breaker", (
            _p("voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("current_a", unit="A", required=True, minimum=0.0),
            _p("interrupting_ka", unit="kA", required=True, minimum=0.0),
            _p("closed", "Closed", "bool", default=True),
            _p("in_service", "In service", "bool", default=True),
        ), "model.create_breaker", "breaker_id", topology=switching_topology, endpoint_mapping=switching_endpoints, terminal_names=terminal_names),
        "disconnector": _definition("disconnector", "disconnector", (
            _p("voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("rated_current_a", unit="A", required=True, minimum=0.0),
        ), "model.create_disconnector", "disconnector_id", topology=switching_topology, endpoint_mapping=switching_endpoints, terminal_names=terminal_names),
        "fuse": _definition("fuse", "fuse", (
            _p("rated_current_a", unit="A", required=True, minimum=0.0),
            _p("rated_voltage_v", unit="V", required=True, minimum=0.0),
        ), "model.create_fuse", "fuse_id", topology=switching_topology, endpoint_mapping=switching_endpoints, terminal_names=terminal_names),
        "current_transformer": _definition("current_transformer", "current_transformer", (
            _p("primary_rated_current_a", unit="A", required=True, minimum=0.0),
            _p("secondary_rated_current_a", unit="A", required=True, minimum=0.0),
            _p("burden_va", unit="VA", minimum=0.0),
            _p("accuracy_class", "Accuracy class", "str"),
            _p("frequency_hz", unit="Hz", required=True, minimum=0.0),
            _p("polarity", "Polarity", "enum", required=True, choices=("P1_P2", "P2_P1")),
        ), "model.create_current_transformer", "transformer_id", topology=(CreationTopologyRequirement("P1", required=True), CreationTopologyRequirement("P2", required=True)),
           # Primary terminals participate in the electrical DraftConnection
           # graph. Secondary terminals are measurement/protection interfaces
           # and are associated through measurement channels, not required to
           # be simple-wire endpoints during equipment creation.
           endpoint_mapping={"P1": "p1_endpoint", "P2": "p2_endpoint"},
           terminal_names=terminal_names),
        "potential_transformer": _definition("potential_transformer", "potential_transformer", (
            _p("primary_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("secondary_voltage_v", unit="V", required=True, minimum=0.0),
            _p("accuracy_class", "Accuracy class", "str"),
            _p("burden_va", unit="VA", minimum=0.0),
            _p("phase_displacement_deg", unit="deg"),
        ), "model.create_potential_transformer", "pt_id", topology=(CreationTopologyRequirement("primary_a", required=True), CreationTopologyRequirement("primary_b", required=True)),
           # Primary terminals belong to electrical topology. Secondary
           # terminals feed measurement channels and are not required to be
           # DraftConnection endpoints at equipment-creation commit.
           endpoint_mapping={"primary_a": "primary_a", "primary_b": "primary_b"},
           terminal_names=terminal_names),
        "cvt": _definition("cvt", "cvt", (
            _p("rated_primary_voltage_kv", unit="kV", required=True, minimum=0.0),
            _p("rated_secondary_voltage_v", unit="V", required=True, minimum=0.0),
            _p("accuracy_class", "Accuracy class", "str"),
            _p("rated_burden_va", unit="VA", minimum=0.0),
            _p("frequency_hz", unit="Hz", required=True, minimum=0.0),
            _p("polarity", "Polarity", "enum", required=True, choices=("NORMAL", "REVERSED")),
        ), "model.create_capacitive_voltage_transformer", "transformer_id", topology=(CreationTopologyRequirement("H1", required=True), CreationTopologyRequirement("H2", required=True)),
           # H1/H2 are the electrical primary-side endpoints. X1/X2 are
           # measurement-side terminals and are associated through the
           # measurement-channel boundary rather than required Simple Wires.
           endpoint_mapping={"H1": "h1_endpoint", "H2": "h2_endpoint"},
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
