"""Build explicit transformer terminal multiports from Core model data.

The producer intentionally consumes a complete manufacturer/test-derived
terminal admittance matrix. It does not synthesize winding physics from
scalar r/x/b, rated MVA, vector-group names, or core labels.
"""
from __future__ import annotations

from core.model.transformer import Transformer
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
    if matrix is None:
        raise ValueError(
            f"Transformer {transformer.id!r} has no explicit complete terminal-domain admittance matrix. "
            "Scalar r/x/b and sequence test data are not substituted."
        )
    if transformer.phase_domain_multiport_tap_ratio is None or transformer.phase_domain_multiport_phase_shift_rad is None:
        raise ValueError(f"Transformer {transformer.id!r} lacks multiport tap/phase-shift provenance.")
    if transformer._phase_domain_multiport_tap_ratio != transformer.tap or transformer._phase_domain_multiport_phase_shift_rad != transformer.shift:
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
