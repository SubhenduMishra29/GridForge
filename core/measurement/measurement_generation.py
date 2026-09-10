"""GridForge V2 measurement-generation transformation boundary.

Author: Subhendu Mishra

The canonical conversion chain is:

    numerical PU quantity
        -> engineering physical quantity
        -> CT/PT/CVT ratio
        -> secondary measurement channel

MeasurementGeneration is the sole conversion boundary. MeasurementChannel
stores the logical signal and its authoritative source reference; it does not
re-interpret instrument ratios.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, TypeAlias

from core.analysis.line_flow import LineFlowResult
from core.analysis.transformer_flow import TransformerFlowResult
from core.measurement.measurement_channel import MeasurementChannel, MeasurementSignalType
from core.solver.power_flow.result import PowerFlowResult
from core.solver.short_circuit.result import ShortCircuitResult


MeasurementQuantity: TypeAlias = (
    LineFlowResult | TransformerFlowResult | PowerFlowResult | ShortCircuitResult
)


@dataclass(frozen=True, slots=True)
class PreparedMeasurementContext:
    """Immutable correlation-complete input to Measurement Generation."""

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
        if self.electrical_side is not None and (
            not isinstance(self.electrical_side, str) or not self.electrical_side.strip()
        ):
            raise ValueError("electrical_side must be None or a non-empty string.")
        if not isinstance(
            self.quantity,
            (LineFlowResult, TransformerFlowResult, PowerFlowResult, ShortCircuitResult),
        ):
            raise TypeError("quantity must be an existing analysis/result contract.")


class UnsupportedMeasurementQuantity(ValueError):
    """Raised when an analysis quantity has no established measurement mapping."""


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
        *,
        prepared_power_flow: Any,
    ) -> float | complex:
        """Convert PU current -> physical primary A -> CT secondary A."""
        self._validate_source(context, source)
        self._validate_channel(channel, MeasurementSignalType.CURRENT)
        quantity = context.quantity
        if isinstance(quantity, LineFlowResult):
            raw = self._line_current(quantity, context)
        elif isinstance(quantity, TransformerFlowResult):
            raw = self._transformer_current(quantity, context)
        else:
            raise UnsupportedMeasurementQuantity(self._unsupported_message(context, "current"))

        base_current_a = self._current_base_a(prepared_power_flow, context.bus_id)
        primary_current_a = raw * base_current_a
        value = primary_current_a / self._ratio(source, "current")
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
        """Convert PU voltage -> physical primary kV -> PT/CVT secondary V."""
        self._validate_source(context, source)
        self._validate_channel(channel, MeasurementSignalType.VOLTAGE)
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
            raise KeyError(f"Power Flow result has no voltage for canonical bus_id {context.bus_id!r}.")

        base_voltage_kv = self._voltage_base_kv(prepared_power_flow, context.bus_id)
        primary_voltage_kv = result.voltage_magnitudes[index] * base_voltage_kv
        value = primary_voltage_kv * 1000.0 / self._ratio(source, "voltage")
        channel.update(value, available=bool(getattr(source, "in_service", True)))
        return value

    def generate_short_circuit(
        self,
        context: PreparedMeasurementContext,
        source: Any,
        channel: MeasurementChannel,
        quantity_key: str,
        *,
        prepared_power_flow: Any,
    ) -> float | complex:
        """Convert PU short-circuit current -> primary A -> CT secondary A.

        The short-circuit solver result is numerical PU data because its fault
        current is produced from PU prefault voltage and PU fault impedance.
        Applying a CT ratio directly to that value is therefore prohibited.
        """
        self._validate_source(context, source)
        self._validate_channel(channel, MeasurementSignalType.CURRENT)
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
                    f"Short-circuit quantity family {root_key!r} is aggregate; a specific "
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
        primary_current_a = raw * self._current_base_a(prepared_power_flow, context.bus_id)
        value = primary_current_a / self._ratio(source, "current")
        value = self._apply_ct_polarity(value, source)
        channel.update(value, available=bool(getattr(source, "in_service", True)))
        return value

    @staticmethod
    def _current_base_a(prepared_power_flow: Any, bus_id: str) -> float:
        if prepared_power_flow is None:
            raise TypeError("prepared_power_flow is required for PU current conversion.")
        try:
            base_mva = float(prepared_power_flow.base_mva)
            voltage_kv = float(prepared_power_flow.bus_voltage_bases[bus_id])
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Prepared Power Flow must declare base_mva and voltage base for bus {bus_id!r}."
            ) from exc
        if base_mva <= 0.0 or voltage_kv <= 0.0:
            raise ValueError("Power Flow base MVA and bus voltage base must be positive.")
        return base_mva * 1000.0 / (sqrt(3.0) * voltage_kv)

    @staticmethod
    def _voltage_base_kv(prepared_power_flow: Any, bus_id: str) -> float:
        try:
            voltage_kv = float(prepared_power_flow.bus_voltage_bases[bus_id])
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Prepared Power Flow must declare a voltage base for bus {bus_id!r}."
            ) from exc
        if voltage_kv <= 0.0:
            raise ValueError("Bus voltage base must be positive.")
        return voltage_kv

    @staticmethod
    def _split_short_circuit_key(quantity_key: str) -> tuple[str, str | None]:
        if not isinstance(quantity_key, str) or not quantity_key.strip():
            raise ValueError("quantity_key must be a non-empty string.")
        normalized = quantity_key.strip()
        if "." not in normalized:
            return normalized, None
        return tuple(normalized.split(".", 1))  # type: ignore[return-value]

    @staticmethod
    def _line_current(result: LineFlowResult, context: PreparedMeasurementContext) -> complex:
        side = MeasurementGeneration._side(context)
        expected_bus = result.from_bus if side == "from" else result.to_bus
        if context.bus_id != expected_bus:
            raise UnsupportedMeasurementQuantity(
                MeasurementGeneration._unsupported_message(context, "line current")
            )
        return result.current_from if side == "from" else result.current_to

    @staticmethod
    def _transformer_current(result: TransformerFlowResult, context: PreparedMeasurementContext) -> float:
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
            raise TypeError(f"Authoritative physical source must expose {attribute!r}.") from exc
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
        raise ValueError("Authoritative CT source must expose a supported physical polarity convention.")

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
    def _validate_channel(channel: MeasurementChannel, expected: MeasurementSignalType) -> None:
        if not isinstance(channel, MeasurementChannel):
            raise TypeError("channel must be a MeasurementChannel.")
        if channel.signal_type is not expected:
            raise ValueError(
                f"MeasurementChannel signal_type must be {expected.value!r} for this conversion."
            )

    @staticmethod
    def _unsupported_message(context: PreparedMeasurementContext, family: str) -> str:
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
