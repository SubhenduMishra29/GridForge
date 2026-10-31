"""Fail-closed source primitive preparation for the physical phase-domain solver.

Only canonical, in-service Grid and Generator models with complete explicit
sequence construction data are admitted. Per-unit impedances are converted
from their declared equipment bases to SI ohms before symmetrical-component
transformation. No load-flow or nameplate quantity is used as a substitute.
"""
from __future__ import annotations

import cmath
import math
from typing import Any

from core.model.generator import Generator
from core.model.grid import Grid
from core.network.phase_domain_conductor_network import (
    PhaseDomainConductorNetwork,
    PhaseDomainNodeKind,
)
from core.solver.short_circuit.phase_domain_solver import PhaseDomainMultiConductorSource


def _finite_complex(value: Any, name: str) -> complex:
    try:
        result = complex(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite complex impedance.") from exc
    if not math.isfinite(result.real) or not math.isfinite(result.imag):
        raise ValueError(f"{name} must be finite.")
    if result.real <= 0.0:
        raise ValueError(f"{name} must have strictly positive resistance for a passive source primitive.")
    return result


def _sequence_to_phase(z0: complex, z1: complex, z2: complex) -> tuple[tuple[complex, ...], ...]:
    a = cmath.exp(2j * math.pi / 3.0)
    transform = (
        (1.0 + 0j, 1.0 + 0j, 1.0 + 0j),
        (1.0 + 0j, a * a, a),
        (1.0 + 0j, a, a * a),
    )
    inverse = tuple(
        tuple(transform[j][i].conjugate() / 3.0 for j in range(3))
        for i in range(3)
    )
    sequence = (z0, z1, z2)
    return tuple(
        tuple(
            sum(transform[i][k] * sequence[k] * inverse[k][j] for k in range(3))
            for j in range(3)
        )
        for i in range(3)
    )


def prepare_phase_domain_source_equivalents(
    network: Any,
    graph: PhaseDomainConductorNetwork,
) -> tuple[PhaseDomainMultiConductorSource, ...]:
    """Derive ABC source primitives from registered Grid/Generator models.

    A source must have one canonical terminal, exactly one A/B/C graph node
    for that terminal, an endpoint Bus with a matching declared impedance
    voltage base, and complete Z0/Z1/Z2 plus explicit source voltage data.
    A Grid's Z0 must include its external grounding contribution. A
    Generator's Z0 is machine-only; 3*Zn is added from its explicit neutral
    grounding impedance.
    """
    if not isinstance(graph, PhaseDomainConductorNetwork):
        raise TypeError("graph must be PhaseDomainConductorNetwork.")
    nodes = tuple(
        node for node in graph.nodes
        if node.kind is PhaseDomainNodeKind.EQUIPMENT_TERMINAL
    )
    equipment_ids = sorted({node.equipment_id for node in nodes if node.equipment_id})
    sources: list[PhaseDomainMultiConductorSource] = []
    for equipment_id in equipment_ids:
        equipment = network.get_by_identity(equipment_id)
        if equipment is None or str(getattr(equipment, "id", "")) != equipment_id:
            raise ValueError(f"Phase-domain source {equipment_id!r} is not a canonical registered Network object.")
        if getattr(equipment, "in_service", None) is not True:
            continue
        if not isinstance(equipment, (Grid, Generator)):
            if str(getattr(equipment, "element_type", "")).lower() == "motor" and getattr(equipment, "running", False):
                raise ValueError(f"Running Motor {equipment_id!r} has no validated phase-domain source decay model; automatic source preparation fails closed.")
            continue
        terminals = tuple(getattr(equipment, "terminals", ()) or ())
        if len(terminals) != 1 or terminals[0].owner is not equipment or terminals[0].role != "terminal":
            raise ValueError(f"Source {equipment_id!r} must expose exactly one canonical owned terminal.")
        endpoint = terminals[0].endpoint
        bus_id = str(getattr(endpoint, "id", ""))
        if not bus_id:
            raise ValueError(f"Source {equipment_id!r} terminal must resolve directly to a canonical Bus.")
        base_mva = getattr(equipment, "impedance_base_mva", None)
        base_kv = getattr(equipment, "impedance_base_voltage_kv", None)
        if base_mva is None or base_kv is None:
            raise ValueError(f"Source {equipment_id!r} requires explicit impedance MVA and voltage bases.")
        base_mva, base_kv = float(base_mva), float(base_kv)
        if not math.isfinite(base_mva) or base_mva <= 0.0 or not math.isfinite(base_kv) or base_kv <= 0.0:
            raise ValueError(f"Source {equipment_id!r} has invalid impedance bases.")
        bus = network.get_by_identity(bus_id)
        bus_kv = getattr(bus, "nominal_voltage_kv", None)
        if bus is None or bus_kv is None or not math.isclose(float(bus_kv), base_kv, rel_tol=1e-8, abs_tol=1e-8):
            raise ValueError(f"Source {equipment_id!r} impedance voltage base must equal its terminal Bus nominal voltage.")
        if isinstance(equipment, Grid):
            if equipment.grounded is not True:
                raise ValueError(f"Grid source {equipment_id!r} is not explicitly grounded; zero-sequence source return is unavailable.")
            z1_pu, z2_pu, z0_pu = equipment.z1_pu, equipment.z2_pu, equipment.z0_pu
            voltage_pu, angle_deg = equipment.voltage_pu, equipment.angle_deg
            if any(value is None for value in (z1_pu, z2_pu, z0_pu)):
                raise ValueError(f"Grid source {equipment_id!r} requires explicit Z1, Z2 and Z0; short-circuit MVA alone is insufficient.")
            internal_voltage_pu = float(voltage_pu)
        else:
            if equipment.neutral_grounded is not True:
                raise ValueError(f"Generator source {equipment_id!r} neutral is not explicitly grounded; zero-sequence source return is unavailable.")
            z1_pu, z2_pu, z0_pu = equipment.z1_subtransient_pu, equipment.z2_pu, equipment.z0_pu
            internal_voltage_pu = equipment.short_circuit_internal_voltage_pu
            angle_deg = equipment.short_circuit_internal_angle_deg
            if any(value is None for value in (z1_pu, z2_pu, z0_pu, internal_voltage_pu)):
                raise ValueError(f"Generator source {equipment_id!r} requires explicit subtransient Z1, Z2, Z0 and internal voltage.")
        z_base = (base_kv * 1000.0) ** 2 / (base_mva * 1.0e6)
        z1 = _finite_complex(z1_pu, f"{equipment_id}.Z1") * z_base
        z2 = _finite_complex(z2_pu, f"{equipment_id}.Z2") * z_base
        z0 = _finite_complex(z0_pu, f"{equipment_id}.Z0") * z_base
        if isinstance(equipment, Generator):
            zn = equipment.neutral_grounding_impedance_ohm
            if zn is None:
                raise ValueError(f"Grounded Generator {equipment_id!r} requires explicit neutral grounding impedance (0j for solid grounding).")
            zn = complex(zn)
            if not math.isfinite(zn.real) or not math.isfinite(zn.imag) or zn.real < 0.0:
                raise ValueError(f"Generator {equipment_id!r} neutral grounding impedance is invalid.")
            z0 += 3.0 * zn
        zabc = _sequence_to_phase(z0, z1, z2)
        phase_nodes: dict[str, str] = {}
        for phase in ("A", "B", "C"):
            matches = [
                node for node in nodes
                if node.equipment_id == equipment_id
                and node.terminal_role == "terminal"
                and node.conductor_role == phase
            ]
            if len(matches) != 1:
                raise ValueError(f"Source {equipment_id!r} requires exactly one terminal graph node for phase {phase}; found {len(matches)}.")
            phase_nodes[phase] = matches[0].node_id
        if any(node.equipment_id != equipment_id or node.terminal_role != "terminal" for node in nodes if node.node_id in phase_nodes.values()):
            raise ValueError(f"Source {equipment_id!r} graph nodes do not match its canonical terminal.")
        if internal_voltage_pu is None or not math.isfinite(float(internal_voltage_pu)) or float(internal_voltage_pu) <= 0.0:
            raise ValueError(f"Source {equipment_id!r} internal voltage magnitude must be finite and positive.")
        angle = math.radians(float(angle_deg))
        phase_voltage_base = base_kv * 1000.0 / math.sqrt(3.0)
        phase_angles = (0.0, -2.0 * math.pi / 3.0, 2.0 * math.pi / 3.0)
        voltages = tuple(
            phase_voltage_base * float(internal_voltage_pu) * cmath.exp(1j * (angle + offset))
            for offset in phase_angles
        )
        sources.append(PhaseDomainMultiConductorSource(
            source_id=equipment_id,
            node_ids=tuple(phase_nodes[phase] for phase in ("A", "B", "C")),
            internal_voltage_v=voltages,
            impedance_matrix_ohm=zabc,
        ))
    if not sources:
        raise ValueError("No supported in-service Grid/Generator source with complete explicit phase-domain construction data was found.")
    return tuple(sources)


__all__ = ["prepare_phase_domain_source_equivalents"]
