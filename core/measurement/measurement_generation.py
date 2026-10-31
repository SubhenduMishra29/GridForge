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
from typing import Any, Mapping, TypeAlias

from core.analysis.line_flow import LineFlowResult
from core.analysis.transformer_flow import TransformerFlowResult
from core.model import EndpointReference
from core.network import CTMeasurementAssociation
from core.measurement.measurement_channel import MeasurementChannel, MeasurementSignalType
from core.solver.power_flow.result import PowerFlowResult
from core.solver.short_circuit.result import ContributionStatus, ShortCircuitResult, ShortCircuitConductorCurrent


MeasurementQuantity: TypeAlias = (
    LineFlowResult | TransformerFlowResult | PowerFlowResult | ShortCircuitResult
)


@dataclass(frozen=True, slots=True)
class PreparedMeasurementContext:
    """Immutable correlation-complete input to Measurement Generation."""

    source_id: str
    source_terminal: EndpointReference
    bus_id: str
    electrical_side: str | None
    quantity: MeasurementQuantity

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be a non-empty string.")
        if not isinstance(self.source_terminal, EndpointReference) or not self.source_terminal.is_terminal:
            raise TypeError("source_terminal must be a terminal EndpointReference.")
        if self.source_terminal.equipment_id != self.source_id.strip():
            raise ValueError("source_terminal equipment identity must match source_id.")
        if not isinstance(self.bus_id, str) or not self.bus_id.strip():
            raise ValueError("bus_id must be a non-empty string.")
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
        self._validate_source(context, source, expected_types=frozenset({'CT'}))
        self._validate_channel(channel, MeasurementSignalType.CURRENT, source)
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
        self._validate_source(context, source, expected_types=frozenset({'PT', 'CVT'}))
        self._validate_channel(channel, MeasurementSignalType.VOLTAGE, source)
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
        self._validate_source(context, source, expected_types=frozenset({'CT'}))
        self._validate_channel(channel, MeasurementSignalType.CURRENT, source)
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
        raw = result.values.get(root_key)
        if raw is None:
            if root_key == "phase_currents":
                raw = result.phase_currents
            elif root_key == "sequence_currents":
                raw = result.sequence_currents
            elif root_key == "fault_current":
                raw = result.fault_current
        if raw is None:
            raise UnsupportedMeasurementQuantity(
                f"Short-circuit quantity {root_key!r} is not present in the existing result for "
                f"source_id={context.source_id!r}, source_terminal={context.source_terminal!r}."
            )
        if isinstance(raw, Mapping):
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

    def convert_short_circuit_branch_current(
        self,
        context: PreparedMeasurementContext,
        source: Any,
        channel: MeasurementChannel,
        *,
        branch_id: str,
        branch_terminal_reference: EndpointReference,
        quantity_key: str,
        ct_association: CTMeasurementAssociation,
    ) -> float | complex:
        '''Convert one explicitly oriented branch-current result to CT secondary A.

        This is a pure conversion: it never updates the supplied
        MeasurementChannel. The configured Branch terminal and FROM/TO side
        are matched against the CT's separate P1/P2 SimpleWire components.
        No feeder, zone, or CT association is inferred from graphical layout.
        '''
        self._validate_source(context, source, expected_types=frozenset({"CT"}))
        self._validate_channel(channel, MeasurementSignalType.CURRENT, source)
        if not isinstance(context.quantity, ShortCircuitResult):
            raise UnsupportedMeasurementQuantity(
                self._unsupported_message(context, "short-circuit branch current")
            )
        if not isinstance(ct_association, CTMeasurementAssociation):
            raise TypeError("ct_association must be the canonical resolved CTMeasurementAssociation.")
        if ct_association.ct_id != context.source_id:
            raise ValueError("Resolved CT association identity does not match the configured measurement source.")
        if not ct_association.in_service:
            raise UnsupportedMeasurementQuantity("CT association is out of service.")
        channel_source = getattr(channel, "source", None)
        if getattr(channel_source, "id", None) != source.id:
            raise UnsupportedMeasurementQuantity(
                "MeasurementChannel physical source does not match the configured CT instrument."
            )
        if getattr(channel, "source_terminal", None) not in {
            ct_association.s1_terminal_reference,
            ct_association.s2_terminal_reference,
        }:
            raise UnsupportedMeasurementQuantity(
                "MeasurementChannel must reference the configured CT S1 or S2 secondary terminal."
            )
        terminal_role = context.source_terminal.terminal_role
        expected_ct_terminal = {
            "P1": ct_association.p1_terminal_reference,
            "P2": ct_association.p2_terminal_reference,
        }.get(terminal_role)
        if expected_ct_terminal != context.source_terminal:
            raise UnsupportedMeasurementQuantity(
                f"CT source terminal {terminal_role!r} does not match the resolved CT association."
            )
        polarity = getattr(getattr(source, "polarity", None), "value", getattr(source, "polarity", None))
        expected_polarity_direction = {
            "P1_P2": "P1_TO_P2",
            "P2_P1": "P2_TO_P1",
        }.get(polarity)
        if expected_polarity_direction != ct_association.positive_current_direction:
            raise UnsupportedMeasurementQuantity(
                "Physical CT polarity does not match the resolved CT association snapshot."
            )
        if not isinstance(branch_terminal_reference, EndpointReference) or not branch_terminal_reference.is_terminal:
            raise TypeError("branch_terminal_reference must be the explicitly configured Branch terminal.")
        if branch_terminal_reference.object_id != branch_id:
            raise ValueError("Branch terminal reference identity does not match branch_id.")
        result = context.quantity
        if not result.success or result.status.value != "COMPLETE":
            raise UnsupportedMeasurementQuantity("Short-circuit scenario is not complete.")
        if result.contribution_status.value != "COMPLETE":
            raise UnsupportedMeasurementQuantity(
                "Short-circuit branch contributions are incomplete; CT conversion is blocked."
            )
        if result.provenance.get("current_units") != "per_unit":
            raise UnsupportedMeasurementQuantity(
                "Short-circuit result does not declare per-unit branch-current provenance."
            )
        if ct_association.topology_revision != result.provenance.get("topology_revision"):
            raise UnsupportedMeasurementQuantity(
                "CT association topology revision does not match the short-circuit scenario snapshot."
            )
        try:
            branch = result.branch_currents[branch_id]
        except KeyError as exc:
            raise UnsupportedMeasurementQuantity(
                f"Short-circuit result has no branch-current contribution for {branch_id!r}."
            ) from exc
        side = self._side(context)
        if branch_terminal_reference.terminal_role != side.upper():
            raise UnsupportedMeasurementQuantity(
                "Configured Branch terminal reference must match the explicit FROM/TO measurement side."
            )
        try:
            branch_current_direction = ct_association.branch_current_direction(
                branch_terminal_reference, side
            )
        except (TypeError, ValueError) as exc:
            raise UnsupportedMeasurementQuantity(str(exc)) from exc

        expected_bus = branch.from_bus_id if side == "from" else branch.to_bus_id
        if context.bus_id != expected_bus:
            raise UnsupportedMeasurementQuantity(
                f"CT measurement Bus {context.bus_id!r} does not match branch {branch_id!r} "
                f"{side}-side Bus {expected_bus!r}."
            )
        root_key, member_key = self._split_short_circuit_key(quantity_key)
        if root_key == "phase_currents":
            if member_key is None or member_key not in branch.phase_currents:
                raise UnsupportedMeasurementQuantity(f"Branch current quantity {quantity_key!r} is unavailable.")
            raw_pu = branch.phase_currents[member_key]
        elif root_key == "sequence_currents":
            if member_key is None or member_key not in branch.sequence_currents:
                raise UnsupportedMeasurementQuantity(f"Branch current quantity {quantity_key!r} is unavailable.")
            raw_pu = branch.sequence_currents[member_key]
        else:
            raise UnsupportedMeasurementQuantity(
                "Branch CT conversion requires an explicit phase_currents.<phase> or sequence_currents.<sequence> member."
            )

        try:
            base_mva = float(result.provenance["base_mva"])
            voltage_kv = float(result.provenance["bus_voltage_bases_kv"][context.bus_id])
        except (KeyError, TypeError, ValueError) as exc:
            raise UnsupportedMeasurementQuantity(
                f"Short-circuit result lacks a valid MVA/voltage base for Bus {context.bus_id!r}."
            ) from exc
        if not isfinite(base_mva) or base_mva <= 0.0 or not isfinite(voltage_kv) or voltage_kv <= 0.0:
            raise UnsupportedMeasurementQuantity("Short-circuit study bases must be finite and positive.")
        primary_current_a = raw_pu * (base_mva * 1000.0 / (sqrt(3.0) * voltage_kv))
        oriented_primary_current_a = primary_current_a * branch_current_direction
        return self._apply_ct_polarity(oriented_primary_current_a, source) / self._ratio(source, "current")

    def convert_short_circuit_conductor_current(
        self,
        context: PreparedMeasurementContext,
        source: Any,
        channel: MeasurementChannel,
        *,
        equipment_terminal_reference: EndpointReference,
        conductor_current: ShortCircuitConductorCurrent,
        positive_current_direction: str,
        ct_association: CTMeasurementAssociation,
    ) -> float | complex:
        """Convert one physical conductor-current record to CT secondary amperes."""
        self._validate_source(context, source, expected_types=frozenset({"CT"}))
        self._validate_channel(channel, MeasurementSignalType.CURRENT, source)
        result = context.quantity
        if not isinstance(result, ShortCircuitResult):
            raise UnsupportedMeasurementQuantity(self._unsupported_message(context, "physical conductor current"))
        if not isinstance(conductor_current, ShortCircuitConductorCurrent):
            raise TypeError("conductor_current must be a ShortCircuitConductorCurrent.")
        if not isinstance(ct_association, CTMeasurementAssociation) or ct_association.ct_id != context.source_id:
            raise TypeError("ct_association must be the canonical association for the configured CT.")
        if not ct_association.in_service:
            raise UnsupportedMeasurementQuantity("CT association is out of service.")
        if getattr(getattr(channel, "source", None), "id", None) != source.id:
            raise UnsupportedMeasurementQuantity("MeasurementChannel physical source does not match the configured CT.")
        if channel.source_terminal not in {ct_association.s1_terminal_reference, ct_association.s2_terminal_reference}:
            raise UnsupportedMeasurementQuantity("MeasurementChannel must reference the configured CT S1 or S2 terminal.")
        expected_ct_terminal = {"P1": ct_association.p1_terminal_reference, "P2": ct_association.p2_terminal_reference}.get(context.source_terminal.terminal_role)
        if expected_ct_terminal != context.source_terminal:
            raise UnsupportedMeasurementQuantity("CT source terminal does not match the resolved P1/P2 association.")
        polarity = getattr(getattr(source, "polarity", None), "value", getattr(source, "polarity", None))
        expected_direction = {"P1_P2": "P1_TO_P2", "P2_P1": "P2_TO_P1"}.get(polarity)
        if expected_direction != ct_association.positive_current_direction:
            raise UnsupportedMeasurementQuantity("Physical CT polarity does not match the resolved association.")
        if not isinstance(equipment_terminal_reference, EndpointReference) or not equipment_terminal_reference.is_terminal:
            raise TypeError("equipment_terminal_reference must be an explicit equipment terminal.")
        if not result.success or result.status.value != "COMPLETE":
            raise UnsupportedMeasurementQuantity("Short-circuit scenario is not complete.")
        if result.conductor_current_status not in {ContributionStatus.COMPLETE, ContributionStatus.PARTIAL}:
            raise UnsupportedMeasurementQuantity("Physical conductor-current records are unavailable or failed.")
        if ct_association.topology_revision != result.provenance.get("topology_revision"):
            raise UnsupportedMeasurementQuantity("CT association topology revision does not match the scenario snapshot.")
        if conductor_current.topology_revision != ct_association.topology_revision:
            raise UnsupportedMeasurementQuantity("Physical conductor-current topology revision is stale.")
        if conductor_current.equipment_id != equipment_terminal_reference.object_id:
            raise UnsupportedMeasurementQuantity("Physical conductor-current equipment identity does not match the configured endpoint.")
        if conductor_current.terminal_role != equipment_terminal_reference.terminal_role:
            raise UnsupportedMeasurementQuantity("Physical conductor-current terminal role does not match the configured endpoint.")
        if conductor_current.bus_id != context.bus_id:
            raise UnsupportedMeasurementQuantity("Prepared measurement Bus does not match the physical conductor-current record.")
        if conductor_current.current_units != "per_unit" or conductor_current.reference_direction != "INTO_EQUIPMENT":
            raise UnsupportedMeasurementQuantity("Physical conductor-current units or reference direction are unsupported.")
        try:
            ct_side = ct_association.locate_measurement_endpoint(equipment_terminal_reference)
        except (TypeError, ValueError) as exc:
            raise UnsupportedMeasurementQuantity(str(exc)) from exc
        direction = str(positive_current_direction).strip().upper()
        if direction not in {"INTO_EQUIPMENT", "OUT_OF_EQUIPMENT"}:
            raise UnsupportedMeasurementQuantity("Physical conductor CT direction must be explicitly INTO_EQUIPMENT or OUT_OF_EQUIPMENT.")
        base_mva, voltage_kv = conductor_current.base_mva, conductor_current.voltage_base_kv
        if not isfinite(base_mva) or base_mva <= 0.0 or not isfinite(voltage_kv) or voltage_kv <= 0.0:
            raise UnsupportedMeasurementQuantity("Physical conductor-current base values are invalid.")
        primary_current_a = complex(conductor_current.current) * (base_mva * 1000.0 / (sqrt(3.0) * voltage_kv))
        if direction == "OUT_OF_EQUIPMENT":
            primary_current_a = -primary_current_a
        ct_reference_current_a = -primary_current_a if ct_side == "P1_SIDE" else primary_current_a
        return self._apply_ct_polarity(ct_reference_current_a, source) / self._ratio(source, "current")

    def convert_short_circuit_terminal_current(
        self,
        context: PreparedMeasurementContext,
        source: Any,
        channel: MeasurementChannel,
        *,
        equipment_terminal_reference: EndpointReference,
        quantity_key: str,
        ct_association: CTMeasurementAssociation,
    ) -> float | complex:
        """Convert an explicit equipment-terminal PU current into CT secondary A.

        Terminal current is positive into equipment. The configured endpoint
        must lie on exactly one CT primary SimpleWire component. P1-side
        endpoints retain the terminal sign; P2-side endpoints reverse it.
        """
        self._validate_source(context, source, expected_types=frozenset({"CT"}))
        self._validate_channel(channel, MeasurementSignalType.CURRENT, source)
        result = context.quantity
        if not isinstance(result, ShortCircuitResult):
            raise UnsupportedMeasurementQuantity(self._unsupported_message(context, "short-circuit terminal current"))
        if not isinstance(ct_association, CTMeasurementAssociation) or ct_association.ct_id != context.source_id:
            raise TypeError("ct_association must be the canonical association for the configured CT.")
        if not ct_association.in_service:
            raise UnsupportedMeasurementQuantity("CT association is out of service.")
        if getattr(getattr(channel, "source", None), "id", None) != source.id:
            raise UnsupportedMeasurementQuantity("MeasurementChannel physical source does not match the configured CT.")
        if getattr(channel, "source_terminal", None) not in {ct_association.s1_terminal_reference, ct_association.s2_terminal_reference}:
            raise UnsupportedMeasurementQuantity("MeasurementChannel must reference the configured CT S1 or S2 terminal.")
        expected_ct_terminal = {
            "P1": ct_association.p1_terminal_reference,
            "P2": ct_association.p2_terminal_reference,
        }.get(context.source_terminal.terminal_role)
        if expected_ct_terminal != context.source_terminal:
            raise UnsupportedMeasurementQuantity("CT source terminal does not match the resolved P1/P2 association.")
        polarity = getattr(getattr(source, "polarity", None), "value", getattr(source, "polarity", None))
        expected_direction = {"P1_P2": "P1_TO_P2", "P2_P1": "P2_TO_P1"}.get(polarity)
        if expected_direction != ct_association.positive_current_direction:
            raise UnsupportedMeasurementQuantity("Physical CT polarity does not match the resolved association.")
        if not isinstance(equipment_terminal_reference, EndpointReference) or not equipment_terminal_reference.is_terminal:
            raise TypeError("equipment_terminal_reference must be an explicit equipment terminal EndpointReference.")
        if equipment_terminal_reference.object_id == ct_association.ct_id:
            raise ValueError("A CT cannot be its own measured equipment terminal.")
        if not result.success or result.status.value != "COMPLETE":
            raise UnsupportedMeasurementQuantity("Short-circuit scenario is not complete.")
        if result.terminal_current_status not in {ContributionStatus.COMPLETE, ContributionStatus.PARTIAL}:
            raise UnsupportedMeasurementQuantity("Short-circuit terminal-current records are unavailable or failed.")
        if result.provenance.get("current_units") != "per_unit":
            raise UnsupportedMeasurementQuantity("Short-circuit result does not declare per-unit terminal-current provenance.")
        if ct_association.topology_revision != result.provenance.get("topology_revision"):
            raise UnsupportedMeasurementQuantity("CT association topology revision does not match the scenario snapshot.")
        try:
            ct_side = ct_association.locate_measurement_endpoint(equipment_terminal_reference)
        except (TypeError, ValueError) as exc:
            raise UnsupportedMeasurementQuantity(str(exc)) from exc
        terminal_key = f"{equipment_terminal_reference.object_id}:{equipment_terminal_reference.terminal_role}"
        try:
            terminal = result.terminal_currents[terminal_key]
        except KeyError as exc:
            raise UnsupportedMeasurementQuantity(f"No terminal-current record exists for {terminal_key!r}.") from exc
        if terminal.equipment_id != equipment_terminal_reference.object_id or terminal.terminal_role != equipment_terminal_reference.terminal_role:
            raise UnsupportedMeasurementQuantity("Terminal-current record identity does not match the configured endpoint.")
        if terminal.reference_direction != "INTO_EQUIPMENT" or terminal.current_units != "per_unit":
            raise UnsupportedMeasurementQuantity("Terminal-current reference direction or units are unsupported.")
        if terminal.bus_id != context.bus_id:
            raise UnsupportedMeasurementQuantity("Prepared measurement Bus does not match the terminal-current record Bus.")
        root_key, member_key = self._split_short_circuit_key(quantity_key)
        if member_key is None:
            raise UnsupportedMeasurementQuantity("Terminal CT conversion requires an explicit phase/sequence member.")
        if root_key == "phase_currents":
            values = terminal.phase_currents
        elif root_key == "sequence_currents":
            values = terminal.sequence_currents
        else:
            raise UnsupportedMeasurementQuantity("Terminal CT conversion accepts phase_currents or sequence_currents only.")
        if member_key not in values:
            raise UnsupportedMeasurementQuantity(f"Terminal-current quantity {quantity_key!r} is unavailable.")
        try:
            base_mva = float(result.provenance["base_mva"])
            voltage_kv = float(result.provenance["bus_voltage_bases_kv"][context.bus_id])
        except (KeyError, TypeError, ValueError) as exc:
            raise UnsupportedMeasurementQuantity("Short-circuit result lacks a valid MVA/voltage base for the measured Bus.") from exc
        if not isfinite(base_mva) or base_mva <= 0.0 or not isfinite(voltage_kv) or voltage_kv <= 0.0:
            raise UnsupportedMeasurementQuantity("Short-circuit study bases must be finite and positive.")
        primary_current_a = complex(values[member_key]) * (base_mva * 1000.0 / (sqrt(3.0) * voltage_kv))
        ct_reference_current_a = -primary_current_a if ct_side == "P1_SIDE" else primary_current_a
        return self._apply_ct_polarity(ct_reference_current_a, source) / self._ratio(source, "current")
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
    def _validate_source(
        context: PreparedMeasurementContext,
        source: Any,
        *,
        expected_types: frozenset[str],
    ) -> None:
        if source is None or not hasattr(source, "id"):
            raise TypeError("authoritative measurement source must expose id.")
        if source.id != context.source_id:
            raise ValueError(
                f"Prepared source_id {context.source_id!r} does not match authoritative source id {source.id!r}."
            )

        source_type = str(
            getattr(source, "element_type", type(source).__name__)
        ).strip().upper()
        if source_type not in expected_types:
            raise UnsupportedMeasurementQuantity(
                f"Measurement source {context.source_id!r} has type {source_type!r}; "
                f"expected one of {sorted(expected_types)!r}."
            )

        terminals = getattr(source, "terminals", None)
        if terminals is not None:
            roles = {getattr(terminal, "role", None) for terminal in terminals}
            terminal_role = context.source_terminal.terminal_role
            if terminal_role not in roles:
                raise UnsupportedMeasurementQuantity(
                    f"Prepared source_terminal={terminal_role!r} is not an authoritative "
                    f"terminal of source_id={context.source_id!r}."
                )

            # Measurement generation converts primary-side network quantities
            # through the instrument ratio. A secondary terminal is not a
            # valid source for that conversion, even if it belongs to the
            # correct instrument and appears in its terminal list.
            primary_roles = {
                "CT": frozenset({"P1", "P2"}),
                "PT": frozenset({"primary_a", "primary_b"}),
                "CVT": frozenset({"H1", "H2"}),
            }[source_type]
            if terminal_role not in primary_roles:
                raise UnsupportedMeasurementQuantity(
                    f"Measurement generation requires a primary-side terminal for "
                    f"{source_type} source {context.source_id!r}; received {terminal_role!r}."
                )

    @staticmethod
    def _validate_channel(
        channel: MeasurementChannel,
        expected: MeasurementSignalType,
        source: Any,
    ) -> None:
        if not isinstance(channel, MeasurementChannel):
            raise TypeError("channel must be a MeasurementChannel.")
        if channel.signal_type is not expected:
            raise ValueError(
                f"MeasurementChannel signal_type must be {expected.value!r} for this conversion."
            )
        if channel.source_id != getattr(source, "id", None):
            raise ValueError("MeasurementChannel source must be the same physical instrument used for generation.")
        source_type = str(getattr(source, "element_type", type(source).__name__)).strip().upper()
        secondary_roles = {
            "CT": frozenset({"S1", "S2"}),
            "PT": frozenset({"secondary_a", "secondary_b"}),
            "CVT": frozenset({"X1", "X2"}),
        }
        if source_type not in secondary_roles:
            raise UnsupportedMeasurementQuantity(
                f"Measurement generation does not support a secondary-terminal contract for {source_type!r}."
            )
        terminal_reference = channel.source_terminal
        if not isinstance(terminal_reference, EndpointReference) or not terminal_reference.is_terminal:
            raise ValueError("MeasurementChannel must identify its physical secondary terminal.")
        if terminal_reference.equipment_id != source.id:
            raise ValueError("MeasurementChannel secondary terminal must belong to its physical source instrument.")
        if terminal_reference.terminal_role not in secondary_roles[source_type]:
            raise ValueError(
                f"{source_type} measurement channel must originate from a configured secondary terminal; "
                f"received {terminal_reference.terminal_role!r}."
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
