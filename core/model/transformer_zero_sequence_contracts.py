"""Explicit transformer vector-group and zero-sequence test contracts.

These contracts record nameplate phase displacement, winding polarity and
zero-sequence test connection. They are configuration evidence only: they do
not calculate a transformer zero-sequence equivalent or enable a Ybus stamp.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TransformerVectorGroupConnection(str, Enum):
    """IEC vector-group winding connection pair, HV then LV."""

    YY = "Yy"
    YD = "Yd"
    DY = "Dy"
    DD = "Dd"


class TransformerWindingPolarity(str, Enum):
    """Declared winding dot/polarity relationship."""

    NORMAL = "NORMAL"
    REVERSED = "REVERSED"


class ZeroSequenceTestEnergizedWinding(str, Enum):
    HV = "HV"
    LV = "LV"


class ZeroSequenceTestOtherWindingCondition(str, Enum):
    """Explicit condition of the non-energized winding during the Z0 test."""

    OPEN_CIRCUIT = "OPEN_CIRCUIT"
    SHORT_CIRCUITED = "SHORT_CIRCUITED"
    DELTA_CLOSED = "DELTA_CLOSED"


@dataclass(frozen=True, slots=True)
class TransformerZeroSequenceTestConfiguration:
    """Declared physical connection used to obtain the transformer Z0 data.

    The configuration is intentionally independent of the Z0 numeric value.
    A measured/manufacturer Z0 value is not applicable to a study winding pair
    unless its test connection is explicitly represented and checked.
    """

    energized_winding: ZeroSequenceTestEnergizedWinding
    other_winding_condition: ZeroSequenceTestOtherWindingCondition
    neutral_return_included: bool

    def __post_init__(self) -> None:
        try:
            energized = (
                self.energized_winding
                if isinstance(self.energized_winding, ZeroSequenceTestEnergizedWinding)
                else ZeroSequenceTestEnergizedWinding(str(self.energized_winding).strip().upper())
            )
            condition = (
                self.other_winding_condition
                if isinstance(self.other_winding_condition, ZeroSequenceTestOtherWindingCondition)
                else ZeroSequenceTestOtherWindingCondition(str(self.other_winding_condition).strip().upper())
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid transformer zero-sequence test winding configuration.") from exc
        if not isinstance(self.neutral_return_included, bool):
            raise TypeError("neutral_return_included must be an explicit bool.")
        object.__setattr__(self, "energized_winding", energized)
        object.__setattr__(self, "other_winding_condition", condition)


@dataclass(frozen=True, slots=True)
class TransformerVectorGroupConfiguration:
    """Explicit nameplate vector group, clock number and winding polarity.

    IEC clock notation is retained literally: clock_number * 30 degrees is
    the declared LV displacement relative to HV. Polarity metadata is not
    silently folded into or added to that displacement; any discrepancy
    between nameplate vector group and physical polarity is an input error
    requiring engineering reconciliation.
    """

    connection: TransformerVectorGroupConnection
    clock_number: int
    hv_polarity: TransformerWindingPolarity
    lv_polarity: TransformerWindingPolarity

    def __post_init__(self) -> None:
        try:
            connection = (
                self.connection
                if isinstance(self.connection, TransformerVectorGroupConnection)
                else TransformerVectorGroupConnection(str(self.connection).strip())
            )
            hv = (
                self.hv_polarity
                if isinstance(self.hv_polarity, TransformerWindingPolarity)
                else TransformerWindingPolarity(str(self.hv_polarity).strip().upper())
            )
            lv = (
                self.lv_polarity
                if isinstance(self.lv_polarity, TransformerWindingPolarity)
                else TransformerWindingPolarity(str(self.lv_polarity).strip().upper())
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid transformer vector-group or winding-polarity declaration.") from exc
        if isinstance(self.clock_number, bool) or not isinstance(self.clock_number, int):
            raise TypeError("clock_number must be an integer from 0 through 11.")
        if not 0 <= self.clock_number <= 11:
            raise ValueError("clock_number must be an integer from 0 through 11.")
        object.__setattr__(self, "connection", connection)
        object.__setattr__(self, "hv_polarity", hv)
        object.__setattr__(self, "lv_polarity", lv)

    @property
    def phase_displacement_deg(self) -> int:
        """IEC clock displacement: LV relative to HV, in 30-degree steps."""
        return self.clock_number * 30

    def validate_winding_connections(self, hv_connection: object, lv_connection: object) -> None:
        """Reject vector-group notation inconsistent with declared windings."""
        from core.model.transformer import TransformerWindingConnection

        expected = {
            "Y": TransformerWindingConnection.WYE_GROUNDED,
            "D": TransformerWindingConnection.DELTA,
        }
        # Both grounded and ungrounded star windings use Y vector notation.
        actual_hv = "Y" if hv_connection in {
            TransformerWindingConnection.WYE_GROUNDED,
            TransformerWindingConnection.WYE_UNGROUNDED,
        } else "D" if hv_connection is TransformerWindingConnection.DELTA else None
        actual_lv = "Y" if lv_connection in {
            TransformerWindingConnection.WYE_GROUNDED,
            TransformerWindingConnection.WYE_UNGROUNDED,
        } else "D" if lv_connection is TransformerWindingConnection.DELTA else None
        notation = self.connection.value
        if actual_hv != notation[0] or actual_lv != notation[1]:
            raise ValueError(
                "Transformer vector-group connection notation does not match "
                "the configured HV/LV winding connections."
            )


def validate_zero_sequence_test_applicability(
    *,
    test: TransformerZeroSequenceTestConfiguration,
    reference_winding: str,
    hv_connection: object,
    lv_connection: object,
) -> None:
    """Validate test-side/reference-side and delta-closure consistency.

    This is an applicability gate, not a numerical Z0 conversion. The test
    neutral return remains separately declared and must not be silently
    combined with the stored transformer Z0; the model's neutral 3Zn remains
    a distinct network contribution.
    """
    from core.model.transformer import TransformerWindingConnection

    reference = str(reference_winding).strip().upper()
    if reference not in {"HV", "LV"}:
        raise ValueError("Z0 impedance reference winding must be HV or LV.")
    if test.energized_winding.value != reference:
        raise ValueError(
            "Zero-sequence test energized winding must match the declared Z0 reference winding."
        )
    other_connection = lv_connection if reference == "HV" else hv_connection
    if test.other_winding_condition is ZeroSequenceTestOtherWindingCondition.DELTA_CLOSED:
        if other_connection is not TransformerWindingConnection.DELTA:
            raise ValueError("DELTA_CLOSED test condition requires a delta-connected non-energized winding.")
    elif other_connection is TransformerWindingConnection.DELTA:
        raise ValueError(
            "A delta-connected non-energized winding requires an explicit DELTA_CLOSED test condition."
        )


__all__ = [
    "TransformerVectorGroupConnection",
    "TransformerWindingPolarity",
    "ZeroSequenceTestEnergizedWinding",
    "ZeroSequenceTestOtherWindingCondition",
    "TransformerVectorGroupConfiguration",
    "TransformerZeroSequenceTestConfiguration",
    "validate_zero_sequence_test_applicability",
]
