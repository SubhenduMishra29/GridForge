"""Transformer zero-sequence winding-path classification.

This module classifies externally available zero-sequence paths. It does
not calculate a transformer equivalent impedance or stamp Ybus. Those
operations require test-configuration, vector-group and core-return
contracts that must be explicit before a numerical equivalent is enabled.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

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
        raise ValueError(
            f"Transformer '{transformer_id}' has grounded-wye on both windings. "
            "Zero-sequence transfer is not enabled until vector-group, clock-number, "
            "winding-polarity and applicable Z0 test-configuration contracts are explicit."
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
    "classify_transformer_zero_sequence",
]
