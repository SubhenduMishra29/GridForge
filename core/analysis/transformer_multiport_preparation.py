"""Build explicit transformer terminal multiports from Core model data.

The producer intentionally consumes a complete manufacturer/test-derived
terminal admittance matrix. It does not synthesize winding physics from
scalar r/x/b, rated MVA, vector-group names, or core labels.
"""
from __future__ import annotations

from core.model.transformer import Transformer
from core.model.transformer_zero_sequence_multiport_evidence import validate_transformer_zero_sequence_multiport_evidence
from core.solver.short_circuit.phase_domain_solver import PhaseDomainTransformerMultiport
from core.network.phase_domain_conductor_network import PhaseDomainConductorNetwork, PhaseDomainNodeKind


def prepare_transformer_phase_domain_multiport(
    transformer: Transformer,
    graph: PhaseDomainConductorNetwork,
) -> PhaseDomainTransformerMultiport:
    """Resolve the transformer's explicit winding terminal nodes and build its solver primitive."""
    if not isinstance(transformer, Transformer):
        raise TypeError("transformer must be a Core Transformer.")
    if not isinstance(graph, PhaseDomainConductorNetwork):
        raise TypeError("graph must be PhaseDomainConductorNetwork.")
    if not transformer.in_service:
        raise ValueError(f"Transformer {transformer.id!r} is out of service.")
    construction = transformer.physical_conductor_construction
    if construction is None:
        raise ValueError(f"Transformer {transformer.id!r} lacks explicit HV/LV winding construction.")
    matrix = transformer.phase_domain_terminal_admittance_siemens
    if construction.vector_group is None:
        raise ValueError(f"Transformer {transformer.id!r} requires explicit vector-group configuration for its multiport.")
    if construction.core_construction is None:
        raise ValueError(f"Transformer {transformer.id!r} requires explicit core construction for zero-sequence coverage assessment.")
    if matrix is None:
        raise ValueError(
            f"Transformer {transformer.id!r} has no explicit complete terminal-domain admittance matrix. "
            "Scalar r/x/b and sequence test data are not substituted."
        )
    if transformer.phase_domain_multiport_tap_ratio is None or transformer.phase_domain_multiport_phase_shift_rad is None:
        raise ValueError(f"Transformer {transformer.id!r} lacks multiport tap/phase-shift provenance.")
    if transformer.phase_domain_multiport_tap_ratio != transformer.tap or transformer.phase_domain_multiport_phase_shift_rad != transformer.shift:
        raise ValueError(f"Transformer {transformer.id!r} multiport matrix is stale after tap or phase-shift change.")

    ordered = []
    labels = []
    for winding in (construction.hv, construction.lv):
        for role in winding.phase_roles:
            matches = tuple(
                node for node in graph.nodes
                if node.kind is PhaseDomainNodeKind.EQUIPMENT_TERMINAL
                and node.equipment_id == transformer.id
                and node.terminal_role.casefold() == winding.terminal_role.casefold()
                and node.conductor_role == role
            )
            if len(matches) != 1:
                raise ValueError(
                    f"Transformer {transformer.id!r} requires exactly one {winding.winding} "
                    f"{role} terminal conductor node; found {len(matches)}."
                )
            ordered.append(matches[0].node_id)
            labels.append(f"{winding.winding}:{role}")
        if winding.neutral_terminal_role is not None:
            matches = tuple(
                node for node in graph.nodes
                if node.kind is PhaseDomainNodeKind.EQUIPMENT_TERMINAL
                and node.equipment_id == transformer.id
                and node.terminal_role.casefold() == winding.neutral_terminal_role.casefold()
                and node.conductor_role == "N"
            )
            if len(matches) != 1:
                raise ValueError(
                    f"Transformer {transformer.id!r} requires exactly one {winding.winding} "
                    f"neutral terminal conductor node; found {len(matches)}."
                )
            ordered.append(matches[0].node_id)
            labels.append(f"{winding.winding}:N")

    for winding in (construction.hv, construction.lv):
        if winding.neutral_terminal_role is None:
            continue
        neutral_node_id = next(
            node_id for node_id, label in zip(ordered, labels)
            if label == f"{winding.winding}:N"
        )
        grounding_edges = tuple(
            edge for edge in graph.connections
            if edge.in_service
            and edge.kind.value == "GROUND_ELECTRODE"
            and edge.source_reference == transformer.id
            and neutral_node_id in {edge.from_node_id, edge.to_node_id}
        )
        if len(grounding_edges) != 1:
            raise ValueError(
                f"Transformer {transformer.id!r} {winding.winding} neutral requires exactly "
                "one source-referenced physical GROUND_ELECTRODE connection."
            )
        edge = grounding_edges[0]
        if edge.impedance_ohm != winding.neutral_grounding_impedance_ohm:
            raise ValueError(
                f"Transformer {transformer.id!r} {winding.winding} neutral electrode "
                "impedance does not match the winding construction."
            )
        earth_node_id = edge.to_node_id if edge.from_node_id == neutral_node_id else edge.from_node_id
        if not graph.earth_reachable(earth_node_id):
            raise ValueError(
                f"Transformer {transformer.id!r} {winding.winding} neutral earth node "
                "has no explicit path to EARTH_REFERENCE."
            )
        return_edges = tuple(
            item for item in graph.connections
            if item.in_service
            and item.kind.value == "EARTH_RETURN"
            and item.source_reference == f"TRANSFORMER-EARTH-RETURN:{transformer.id}:{winding.winding}"
            and earth_node_id in {item.from_node_id, item.to_node_id}
        )
        if len(return_edges) != 1 or return_edges[0].impedance_ohm != winding.earth_return_impedance_ohm:
            raise ValueError(
                f"Transformer {transformer.id!r} {winding.winding} requires exactly one "
                "matching explicit earth-return impedance path."
            )

    delta_windings = tuple(
        winding.winding
        for winding in (construction.hv, construction.lv)
        if winding.connection == "DELTA"
    )
    validate_transformer_zero_sequence_multiport_evidence(
        transformer.zero_sequence_multiport_evidence,
        matrix=matrix,
        terminal_labels=labels,
        core_construction=construction.core_construction,
        delta_windings=delta_windings,
    )

    if len(matrix) != len(ordered):
        raise ValueError(
            f"Transformer {transformer.id!r} terminal admittance dimension {len(matrix)} "
            f"does not match explicit winding terminal inventory {len(ordered)}."
        )
    return PhaseDomainTransformerMultiport(
        transformer_id=transformer.id,
        node_ids=tuple(ordered),
        terminal_labels=tuple(labels),
        admittance_siemens=matrix,
    )


__all__ = ["prepare_transformer_phase_domain_multiport"]
