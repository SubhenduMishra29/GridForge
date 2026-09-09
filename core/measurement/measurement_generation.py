# ============================================================
# File: core/measurement/measurement_generation.py
# GridForge V2 — GF-AUD-204 Measurement Generation Boundary
# Author: Subhendu Mishra
# ============================================================

"""GridForge V2 measurement-generation transformation boundary.

This module consumes already-correlated analysis-domain quantities and
transforms them through authoritative physical measurement-source
characteristics before updating a logical ``MeasurementChannel``.

The boundary deliberately does not calculate power flow, line flow,
transformer flow, or short circuit quantities. It also does not resolve
network topology. Correlation is prepared before this boundary and a
Power Flow numerical index is obtained only from ``PowerFlowInput`` at
execution time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

from core.analysis.line_flow import LineFlowResult
from core.analysis.transformer_flow import TransformerFlowResult
from core.measurement.measurement_channel import MeasurementChannel
from core.solver.power_flow.result import PowerFlowResult
from core.solver.short_circuit.result import ShortCircuitResult


MeasurementQuantity: TypeAlias = (
    LineFlowResult
    | TransformerFlowResult
    | PowerFlowResult
    | ShortCircuitResult
)


@dataclass(frozen=True, slots=True)
class PreparedMeasurementContext:
    """Immutable, correlation-complete input to Measurement Generation.

    ``quantity`` retains one of the repository's existing analysis/result
    contracts. No generic electrical-quantity object is introduced.
    ``bus_index`` is intentionally absent because numerical indices are an
    execution-time concern of the numerical analysis boundary.
    """

    source_id: str
    source_terminal: str
    bus_id: str
    electrical_side: str | None
    quantity: MeasurementQuantity

    def __post_init__(self) -> None:
        for name in ("source_id", "source_terminal", "bus_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        if self.electrical_side is not None:
            if not isinstance(self.electrical_side, str) or not self.electrical_side.strip():
                raise ValueError("electrical_side must be None or a non-empty string.")
        if not isinstance(
            self.quantity,
            (LineFlowResult, TransformerFlowResult, PowerFlowResult, ShortCircuitResult),
        ):
            raise TypeError(
                "quantity must be an existing LineFlowResult, TransformerFlowResult, "
                "PowerFlowResult, or ShortCircuitResult."
            )


class UnsupportedMeasurementQuantity(ValueError):
    """Raised when an analysis quantity has no frozen measurement mapping."""


class MeasurementGeneration:
    """Transform prepared analysis quantities through physical source data."""

    _SHORT_CIRCUIT_KEYS = frozenset(
        {
            "fault_current",
            "fault_current_magnitude",
            "phase_currents",
            "phase_current_magnitudes",
            "sequence_currents",
            "sequence_current_magnitudes",
            "sequence_current_angles_deg",
            "ground_current",
            "ground_current_magnitude",
        }
    )

    def generate_current(
        self,
        context: PreparedMeasurementContext,
        source: Any,
        channel: MeasurementChannel,
    ) -> float | complex:
        """Consume a Line/Transformer current and apply authoritative CT data."""
        self._validate_source(context, source)
        self._validate_channel(channel)
        quantity = context.quantity

        if isinstance(quantity, LineFlowResult):
            raw = self._line_current(quantity, context)
        elif isinstance(quantity, TransformerFlowResult):
            raw = self._transformer_current(quantity, context)
        else:
            raise UnsupportedMeasurementQuantity(
                self._unsupported_message(context, "current")
            )

        value = raw / self._ratio(source, "current")
        value = self._apply_ct_polarity(value, source)
        channel.update(value, available=bool(getattr(source, "in_service", True)))
        return value

    def generate_voltage(
        self,
        context: PreparedMeasurementContext,
        source: Any,
        channel: MeasurementChannel,
        prepared_power_flow: Any,
    ) -> float:
        """Consume an existing Power Flow voltage using bus-id correlation."""
        self._validate_source(context, source)
        self._validate_channel(channel)
        if not isinstance(context.quantity, PowerFlowResult):
            raise UnsupportedMeasurementQuantity(
                self._unsupported_message(context, "power-flow voltage")
            )
        if prepared_power_flow is None or not hasattr(prepared_power_flow, "input"):
            raise TypeError("prepared_power_flow must expose a prepared input contract.")
        input_data = prepared_power_flow.input
        if not hasattr(input_data, "index_of"):
            raise TypeError("prepared_power_flow.input must expose index_of(bus_id).")

        index = input_data.index_of(context.bus_id)
        result = context.quantity
        if index >= len(result.voltage_magnitudes):
            raise KeyError(
                f"Power Flow result has no voltage for canonical bus_id {context.bus_id!r}."
            )

        value = result.voltage_magnitudes[index] / self._ratio(source, "voltage")
        channel.update(value, available=bool(getattr(source, "in_service", True)))
        return value

    def generate_short_circuit(
        self,
        context: PreparedMeasurementContext,
        source: Any,
        channel: MeasurementChannel,
        quantity_key: str,
    ) -> float | complex:
        """Consume an established short-circuit fault quantity at its fault location."""
        self._validate_source(context, source)
        self._validate_channel(channel)
        if not isinstance(context.quantity, ShortCircuitResult):
            raise UnsupportedMeasurementQuantity(
                self._unsupported_message(context, "short-circuit fault quantity")
            )

        root_key, member_key = self._split_short_circuit_key(quantity_key)
        if root_key not in self._SHORT_CIRCUIT_KEYS:
            raise UnsupportedMeasurementQuantity(
                f"Unsupported short-circuit mapping for source_id={context.source_id!r}, "
                f"source_terminal={context.source_terminal!r}, quantity family={quantity_key!r}: "
                "arbitrary branch current or calculated post-fault voltage is not established."
            )

        result = context.quantity
        if context.bus_id != result.fault_bus_id:
            raise UnsupportedMeasurementQuantity(
                f"Unsupported short-circuit mapping for source_id={context.source_id!r}, "
                f"source_terminal={context.source_terminal!r}: physical measurement source bus "
                f"{context.bus_id!r} does not correspond to fault location {result.fault_bus_id!r}."
            )
        if root_key not in result.values:
            raise UnsupportedMeasurementQuantity(
                f"Short-circuit quantity {root_key!r} is not present in the existing result for "
                f"source_id={context.source_id!r}, source_terminal={context.source_terminal!r}."
            )

        raw = result.values[root_key]
        if isinstance(raw, dict):
            if member_key is None:
                raise UnsupportedMeasurementQuantity(
                    f"Short-circuit quantity family {root_key!r} is aggregate; a specific existing "
                    "phase/sequence member is required by MeasurementChannel."
                )
            if member_key not in raw:
                raise UnsupportedMeasurementQuantity(
                    f"Short-circuit quantity {quantity_key!r} is not present in the existing result for "
                    f"source_id={context.source_id!r}, source_terminal={context.source_terminal!r}."
                )
            raw = raw[member_key]
        elif member_key is not None:
            raise UnsupportedMeasurementQuantity(
                f"Short-circuit quantity {quantity_key!r} does not identify an existing scalar result."
            )

        value = raw / self._ratio(source, "current")
        value = self._apply_ct_polarity(value, source)
        channel.update(value, available=bool(getattr(source, "in_service", True)))
        return value

    @staticmethod
    def _split_short_circuit_key(quantity_key: str) -> tuple[str, str | None]:
        if not isinstance(quantity_key, str) or not quantity_key.strip():
            raise ValueError("quantity_key must be a non-empty string.")
        normalized = quantity_key.strip()
        if "." not in normalized:
            return normalized, None
        root, member = normalized.split(".", 1)
        return root, member

    @staticmethod
    def _line_current(
        result: LineFlowResult,
        context: PreparedMeasurementContext,
    ) -> complex:
        side = MeasurementGeneration._side(context)
        expected_bus = result.from_bus if side == "from" else result.to_bus
        if context.bus_id != expected_bus:
            raise UnsupportedMeasurementQuantity(
                MeasurementGeneration._unsupported_message(context, "line current")
            )
        return result.current_from if side == "from" else result.current_to

    @staticmethod
    def _transformer_current(
        result: TransformerFlowResult,
        context: PreparedMeasurementContext,
    ) -> float:
        side = MeasurementGeneration._side(context)
        expected_bus = result.from_bus if side == "from" else result.to_bus
        if context.bus_id != expected_bus:
            raise UnsupportedMeasurementQuantity(
                MeasurementGeneration._unsupported_message(context, "transformer current")
            )
        return result.i_from_pu if side == "from" else result.i_to_pu

    @staticmethod
    def _side(context: PreparedMeasurementContext) -> str:
        if context.electrical_side not in {"from", "to"}:
            raise UnsupportedMeasurementQuantity(
                MeasurementGeneration._unsupported_message(context, "terminal current")
            )
        return context.electrical_side

    @staticmethod
    def _ratio(source: Any, family: str) -> float:
        attribute = "ratio" if family == "current" else "voltage_ratio"
        try:
            ratio = float(getattr(source, attribute))
        except (AttributeError, TypeError, ValueError) as exc:
            raise TypeError(
                f"Authoritative physical source must expose {attribute!r}."
            ) from exc
        if ratio <= 0.0:
            raise ValueError(f"Authoritative physical source {attribute} must be positive.")
        return ratio

    @staticmethod
    def _apply_ct_polarity(value: float | complex, source: Any) -> float | complex:
        polarity = getattr(source, "polarity", None)
        polarity_value = getattr(polarity, "value", polarity)
        if polarity_value == "P1_P2":
            return value
        if polarity_value == "P2_P1":
            return -value
        raise ValueError(
            "Authoritative CT source must expose a supported physical polarity convention."
        )

    @staticmethod
    def _validate_source(context: PreparedMeasurementContext, source: Any) -> None:
        if source is None or not hasattr(source, "id"):
            raise TypeError("authoritative measurement source must expose id.")
        if source.id != context.source_id:
            raise ValueError(
                f"Prepared source_id {context.source_id!r} does not match authoritative source id {source.id!r}."
            )
        terminals = getattr(source, "terminals", None)
        if terminals is not None:
            roles = {getattr(terminal, "role", None) for terminal in terminals}
            if context.source_terminal not in roles:
                raise UnsupportedMeasurementQuantity(
                    f"Prepared source_terminal={context.source_terminal!r} is not an authoritative "
                    f"terminal of source_id={context.source_id!r}."
                )

    @staticmethod
    def _validate_channel(channel: MeasurementChannel) -> None:
        if not isinstance(channel, MeasurementChannel):
            raise TypeError("channel must be a MeasurementChannel.")

    @staticmethod
    def _unsupported_message(
        context: PreparedMeasurementContext,
        family: str,
    ) -> str:
        return (
            f"Unsupported measurement quantity for source_id={context.source_id!r}, "
            f"source_terminal={context.source_terminal!r}, quantity family={family!r}, "
            f"bus_id={context.bus_id!r}."
        )


__all__ = [
    "MeasurementGeneration",
    "MeasurementQuantity",
    "PreparedMeasurementContext",
    "UnsupportedMeasurementQuantity",
]
