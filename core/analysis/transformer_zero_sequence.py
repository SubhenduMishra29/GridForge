"""Transformer zero-sequence winding-path classification.

This module classifies externally available zero-sequence paths and builds
the explicitly supported one-sided grounded-wye return shunt. It does not
model a general two-winding zero-sequence transfer equivalent.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

from core.model.transformer import (
    TransformerCoreConstruction,
    TransformerWindingConnection,
)


class TransformerZeroSequencePath(str, Enum):
    """Externally visible zero-sequence path topology."""

    GROUNDED_WYE_SIDE_RETURN = "GROUNDED_WYE_SIDE_RETURN"
    NO_EXTERNAL_ZERO_SEQUENCE_PATH = "NO_EXTERNAL_ZERO_SEQUENCE_PATH"


@dataclass(frozen=True, slots=True)
class TransformerZeroSequenceTopology:
    """Immutable topology classification; not a numerical network stamp."""

    transformer_id: str
    path: TransformerZeroSequencePath
    grounded_winding_sides: tuple[str, ...]
    externally_blocked_winding_sides: tuple[str, ...]
    core_construction: TransformerCoreConstruction | None
    internal_delta_circulation_possible: bool
    requires_neutral_3zn: bool
    requires_applicable_test_configuration: bool
    numerical_equivalent_available: bool = False



@dataclass(frozen=True, slots=True)
class TransformerZeroSequenceShunt:
    """Grounded-wye-side zero-sequence shunt, referred to its bus voltage base.

    This is a one-sided return equivalent, not an HV-LV series branch.
    Transformer test Z0 excludes neutral return; neutral_3zn_ohm is added
    exactly once and retained separately for provenance.
    """

    transformer_id: str
    bus_id: str
    grounded_winding_side: str
    transformer_z0_ohm: complex
    neutral_3zn_ohm: complex
    total_impedance_ohm: complex
    base_mva: float
    base_voltage_kv: float
    impedance_pu: complex
    core_construction: TransformerCoreConstruction
    zero_sequence_test_basis: str
    test_configuration: Any


def build_transformer_zero_sequence_shunt(
    transformer: Any,
    grounded_bus: Any,
    *,
    base_mva: float,
) -> TransformerZeroSequenceShunt | None:
    """Build the validated one-sided grounded-wye return equivalent.

    A delta opposite winding requires DELTA_CLOSED in the Z0 test. An
    ungrounded-wye opposite winding requires OPEN_CIRCUIT. Short-circuit
    test configurations are not treated as this one-sided equivalent.
    Core construction is provenance only; no empirical multiplier applies.
    """
    if grounded_bus is None:
        raise ValueError("A resolved grounded-wye Bus is required for transformer Z0 preparation.")
    if isinstance(base_mva, bool) or not np.isfinite(base_mva) or base_mva <= 0.0:
        raise ValueError("base_mva must be finite and greater than zero.")

    topology = classify_transformer_zero_sequence(transformer)
    if topology.path is TransformerZeroSequencePath.NO_EXTERNAL_ZERO_SEQUENCE_PATH:
        return None
    if len(topology.grounded_winding_sides) != 1:
        raise ValueError("Only a single grounded-wye winding return can be represented by this equivalent.")

    side = topology.grounded_winding_sides[0]
    opposite = transformer.lv_winding_connection if side == "HV" else transformer.hv_winding_connection
    test = transformer.zero_sequence_test_configuration
    if opposite is TransformerWindingConnection.DELTA:
        expected_condition = "DELTA_CLOSED"
    elif opposite is TransformerWindingConnection.WYE_UNGROUNDED:
        expected_condition = "OPEN_CIRCUIT"
    else:
        raise ValueError("Unsupported opposite-winding condition for a one-sided grounded-wye return.")
    if test.other_winding_condition.value != expected_condition:
        raise ValueError(
            f"Transformer '{transformer.id}' one-sided Z0 test requires "
            f"other_winding_condition={expected_condition}."
        )

    neutral = (
        transformer.hv_neutral_grounding_impedance_ohm
        if side == "HV"
        else transformer.lv_neutral_grounding_impedance_ohm
    )
    if neutral is None:
        raise ValueError(f"Transformer '{transformer.id}' grounded {side} neutral impedance is unavailable.")

    z0 = complex(transformer.zero_sequence_resistance_ohm, transformer.zero_sequence_reactance_ohm)
    neutral_3zn = 3.0 * complex(neutral)
    total = z0 + neutral_3zn
    for label, value in (("Z0", z0), ("3Zn", neutral_3zn), ("Z0 + 3Zn", total)):
        if not np.isfinite(value.real) or not np.isfinite(value.imag):
            raise ValueError(f"Transformer '{transformer.id}' {label} must be finite.")
    if abs(total) == 0.0:
        raise ValueError(f"Transformer '{transformer.id}' grounded-wye return impedance is zero.")

    voltage_kv = float(getattr(grounded_bus, "nominal_voltage_kv", 0.0))
    if not np.isfinite(voltage_kv) or voltage_kv <= 0.0:
        raise ValueError(
            f"Grounded {side} Bus '{getattr(grounded_bus, 'id', '')}' requires a positive nominal voltage."
        )
    z_base = voltage_kv * voltage_kv / float(base_mva)
    impedance_pu = total / z_base
    if not np.isfinite(impedance_pu.real) or not np.isfinite(impedance_pu.imag) or abs(impedance_pu) == 0.0:
        raise ValueError(f"Transformer '{transformer.id}' produced an invalid per-unit zero-sequence shunt.")

    return TransformerZeroSequenceShunt(
        transformer_id=str(transformer.id),
        bus_id=str(grounded_bus.id),
        grounded_winding_side=side,
        transformer_z0_ohm=z0,
        neutral_3zn_ohm=neutral_3zn,
        total_impedance_ohm=total,
        base_mva=float(base_mva),
        base_voltage_kv=voltage_kv,
        impedance_pu=impedance_pu,
        core_construction=topology.core_construction,
        zero_sequence_test_basis=str(transformer.zero_sequence_test_basis),
        test_configuration=test,
    )

def classify_transformer_zero_sequence(
    transformer: Any,
) -> TransformerZeroSequenceTopology:
    """Classify winding connectivity while refusing unsupported transfer.

    One grounded-wye winding creates a candidate grounded-side return path.
    Its Z0 must be referred to that grounded winding. Neutral impedance is
    deliberately excluded from the stored Z0 and must later contribute 3Zn.

    Two grounded-wye windings require an explicit vector-group/clock and
    winding-polarity contract before transfer can be represented. The
    current Transformer model does not yet carry that contract, so this
    case fails closed rather than assuming zero-sequence transfer.

    Delta-delta and ungrounded-wye combinations have no external grounded
    neutral path in this two-winding model. Delta circulation is reported
    as an internal possibility, never exposed as a bus zero-sequence path.
    """
    if transformer is None:
        raise ValueError("Transformer is required for zero-sequence topology classification.")

    transformer_id = str(getattr(transformer, "id", "")).strip()
    if not transformer_id:
        raise ValueError("Transformer identity is required for zero-sequence topology classification.")

    hv = getattr(transformer, "hv_winding_connection", None)
    lv = getattr(transformer, "lv_winding_connection", None)
    if hv is None or lv is None:
        raise ValueError(
            f"Transformer '{transformer_id}' requires explicit HV and LV winding connections."
        )

    grounded = tuple(
        side for side, connection in (("HV", hv), ("LV", lv))
        if connection is TransformerWindingConnection.WYE_GROUNDED
    )
    blocked = tuple(
        side for side, connection in (("HV", hv), ("LV", lv))
        if connection is not TransformerWindingConnection.WYE_GROUNDED
    )
    delta_present = (
        hv is TransformerWindingConnection.DELTA
        or lv is TransformerWindingConnection.DELTA
    )

    if len(grounded) == 0:
        return TransformerZeroSequenceTopology(
            transformer_id=transformer_id,
            path=TransformerZeroSequencePath.NO_EXTERNAL_ZERO_SEQUENCE_PATH,
            grounded_winding_sides=(),
            externally_blocked_winding_sides=("HV", "LV"),
            core_construction=getattr(transformer, "core_construction", None),
            internal_delta_circulation_possible=delta_present,
            requires_neutral_3zn=False,
            requires_applicable_test_configuration=False,
        )

    if len(grounded) == 2:
        vector_group = getattr(transformer, "vector_group_configuration", None)
        test_configuration = getattr(transformer, "zero_sequence_test_configuration", None)
        reference = getattr(transformer, "impedance_reference_winding", None)
        if vector_group is None or test_configuration is None:
            raise ValueError(
                f"Transformer '{transformer_id}' has grounded-wye on both windings and requires "
                "explicit vector-group and zero-sequence test-configuration contracts."
            )
        vector_group.validate_winding_connections(hv, lv)
        from core.model.transformer_zero_sequence_contracts import validate_zero_sequence_test_applicability
        validate_zero_sequence_test_applicability(
            test=test_configuration, reference_winding=reference,
            hv_connection=hv, lv_connection=lv,
        )
        raise ValueError(
            f"Transformer '{transformer_id}' has validated winding contracts, but grounded-wye "
            "to grounded-wye zero-sequence transfer remains numerically unavailable until its "
            "core/test-derived two-winding equivalent is implemented."
        )

    grounded_side = grounded[0]
    reference = getattr(transformer, "impedance_reference_winding", None)
    z0r = getattr(transformer, "zero_sequence_resistance_ohm", None)
    z0x = getattr(transformer, "zero_sequence_reactance_ohm", None)
    core = getattr(transformer, "core_construction", None)
    test_basis = getattr(transformer, "zero_sequence_test_basis", None)
    if z0r is None or z0x is None:
        raise ValueError(
            f"Transformer '{transformer_id}' requires explicit Z0 resistance and reactance "
            f"for the {grounded_side} grounded-wye return path."
        )
    if reference != grounded_side:
        raise ValueError(
            f"Transformer '{transformer_id}' Z0 reference winding must be {grounded_side} "
            "for a one-sided grounded-wye return equivalent."
        )
    if core is None or test_basis is None:
        raise ValueError(
            f"Transformer '{transformer_id}' requires explicit core construction and "
            "zero-sequence test-data provenance."
        )
    vector_group = getattr(transformer, "vector_group_configuration", None)
    test_configuration = getattr(transformer, "zero_sequence_test_configuration", None)
    if vector_group is None or test_configuration is None:
        raise ValueError(
            f"Transformer '{transformer_id}' requires explicit vector-group and "
            "zero-sequence test-configuration contracts."
        )
    vector_group.validate_winding_connections(hv, lv)
    from core.model.transformer_zero_sequence_contracts import validate_zero_sequence_test_applicability
    validate_zero_sequence_test_applicability(
        test=test_configuration, reference_winding=reference,
        hv_connection=hv, lv_connection=lv,
    )

    return TransformerZeroSequenceTopology(
        transformer_id=transformer_id,
        path=TransformerZeroSequencePath.GROUNDED_WYE_SIDE_RETURN,
        grounded_winding_sides=grounded,
        externally_blocked_winding_sides=blocked,
        core_construction=core,
        internal_delta_circulation_possible=delta_present,
        requires_neutral_3zn=True,
        requires_applicable_test_configuration=True,
    )


__all__ = [
    "TransformerZeroSequencePath",
    "TransformerZeroSequenceTopology",
    "TransformerZeroSequenceShunt",
    "build_transformer_zero_sequence_shunt",
    "classify_transformer_zero_sequence",
]
