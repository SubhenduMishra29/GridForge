"""Detached numerical preparation for Short-Circuit studies."""

from __future__ import annotations

import cmath
import math
from typing import Any, Optional

from core.solver.short_circuit.fault_types import FaultType
from core.solver.short_circuit.input import ShortCircuitInput
from core.solver.short_circuit.sequence_snapshot import (
    SequenceBranchSnapshot,
    SequenceNetworkSnapshot,
    SequenceSourceSnapshot,
)
from .sequence_network_preparation import SequenceNetworkPreparation
from core.network.topology_snapshot import TopologySnapshot
from core.model.transformer import Transformer


class ShortCircuitPreparation:
    """Prepare a detached Short-Circuit numerical problem from Core.

    The Network and sequence-network inputs are retained only for the duration
    of ``prepare`` and are released afterwards so the preparation object cannot
    become a long-lived holder of live Core state.
    """

    def __init__(self, network: Any, sequence_network: Optional[Any] = None, *, base_mva: float | None = None) -> None:
        if network is None or not hasattr(network, "buses"):
            raise ValueError("Short Circuit preparation requires a Network with buses.")
        if len(network.buses) == 0:
            raise ValueError("Short Circuit preparation requires at least one bus.")
        self._network = network
        self._sequence_network = sequence_network
        self.base_mva = base_mva
        self._topology_snapshot = None

    def prepare(self, fault_type: FaultType, fault_bus: Any, Zf: complex = 0.0, *, elements: Any | None = None, topology_snapshot: TopologySnapshot | None = None) -> ShortCircuitInput:
        network = self._network
        if topology_snapshot is None:
            network.rebuild_topology()
            topology_snapshot = network.topology_snapshot
            if topology_snapshot is None:
                raise ValueError('Short Circuit requires a canonical TopologySnapshot.')
        self._topology_snapshot = topology_snapshot
        if network is None:
            raise RuntimeError("Short Circuit preparation has already been consumed.")
        try:
            normalized_type = FaultType.from_value(fault_type)
            bus_ids = tuple(topology_snapshot.bus_ids)
            if not bus_ids:
                raise ValueError("TopologySnapshot must contain at least one Bus for Short Circuit preparation.")
            if len(set(bus_ids)) != len(bus_ids):
                raise ValueError("TopologySnapshot bus IDs must be unique for Short Circuit preparation.")
            bus_index = self._resolve_fault_bus_index(fault_bus, bus_ids)
            prefault_voltages = tuple(
                self._prepare_prefault_voltage(network, bus_id)
                for bus_id in bus_ids
            )
            prefault_voltage = prefault_voltages[bus_index]
            snapshot = self._prepare_sequence_snapshot(network, normalized_type, bus_ids, topology_snapshot)
            required_sequences = (
                ("positive", "negative")
                if normalized_type is FaultType.LINE_LINE
                else ("positive", "negative", "zero")
                if normalized_type.is_unbalanced
                else ("positive",)
            )
            unavailable_at_fault = tuple(
                sequence for sequence in required_sequences
                if not snapshot.is_bus_available(sequence, bus_index)
            )
            if unavailable_at_fault:
                raise ValueError(
                    f"Fault Bus '{bus_ids[bus_index]}' belongs to an ungrounded or "
                    f"numerically unavailable sequence-network component for: "
                    f"{', '.join(unavailable_at_fault)} sequence. No earth-return "
                    "path is declared for this component."
                )

            positive_matrix = snapshot.get_matrix("positive")
            zbus = tuple(tuple(complex(value) for value in row) for row in positive_matrix.tolist())
            thevenin_impedance = complex(positive_matrix[bus_index, bus_index])

            if elements is None:
                sequence_elements = tuple(str(element_id) for element_id in snapshot.positive.keys())
            else:
                sequence_elements = tuple(str(getattr(element, "id", element)) for element in elements)
            if normalized_type.is_unbalanced:
                for name in required_sequences:
                    if not snapshot.has_matrix(name):
                        raise ValueError(f"{name.capitalize()}-sequence matrix is required for this unsymmetrical fault study.")
                if not sequence_elements:
                    raise ValueError("At least one sequence-network element is required for an unsymmetrical fault study.")

            voltage_bases: dict[str, float] = {}
            for bus_id in bus_ids:
                bus = network.get_by_identity(bus_id)
                nominal_kv = getattr(bus, "nominal_voltage_kv", None)
                if nominal_kv is None:
                    continue
                try:
                    nominal_kv = float(nominal_kv)
                except (TypeError, ValueError):
                    continue
                if math.isfinite(nominal_kv) and nominal_kv > 0.0:
                    voltage_bases[bus_id] = nominal_kv

            return ShortCircuitInput(
                fault_type=normalized_type,
                fault_bus_index=bus_index,
                fault_bus_id=bus_ids[bus_index],
                prefault_voltage=prefault_voltage,
                fault_impedance=complex(Zf),
                bus_ids=bus_ids,
                thevenin_impedance=thevenin_impedance,
                zbus=zbus,
                sequence_snapshot=snapshot,
                sequence_elements=sequence_elements,
                prefault_voltages=prefault_voltages,
                project_id=topology_snapshot.project_id,
                activation_generation=topology_snapshot.activation_generation,
                topology_revision=topology_snapshot.topology_revision,
                base_mva=self.base_mva,
                bus_voltage_bases_kv=voltage_bases,
            )
        finally:
            self._network = None
            self._sequence_network = None

    def _prepare_sequence_snapshot(self, network: Any, fault_type: FaultType, bus_ids: tuple[str, ...], topology_snapshot: TopologySnapshot | None = None) -> SequenceNetworkSnapshot:
        if self._sequence_network is not None:
            sequence_network = self._sequence_network
            requires_tap_aware_matrix = any(
                isinstance(element, Transformer)
                and (
                    not math.isclose(float(getattr(element, "tap", 1.0)), 1.0, rel_tol=0.0, abs_tol=1e-12)
                    or not math.isclose(float(getattr(element, "shift", 0.0)), 0.0, rel_tol=0.0, abs_tol=1e-12)
                )
                for element in self._branch_elements(network)
                if bool(getattr(element, "in_service", True))
            )
            if requires_tap_aware_matrix and getattr(sequence_network, "transformer_tap_convention", None) != "FROM_SIDE_COMPLEX_TAP_V1":
                raise ValueError(
                    "An externally supplied sequence network cannot be used with a non-unity transformer tap/phase shift "
                    "unless it declares the canonical FROM_SIDE_COMPLEX_TAP_V1 stamping convention."
                )
        else:
            required = (
                ("positive", "negative")
                if fault_type is FaultType.LINE_LINE
                else ("positive", "negative", "zero")
                if fault_type.is_unbalanced
                else ("positive",)
            )
            sequence_network = SequenceNetworkPreparation(network, base_mva=self.base_mva, topology_snapshot=topology_snapshot).prepare(required)
        return SequenceNetworkSnapshot.from_sequence_network(
            sequence_network,
            bus_ids=bus_ids,
            branches=self._prepare_branch_snapshots(network, sequence_network, bus_ids),
            sources=self._prepare_source_snapshots(network, sequence_network, bus_ids),
        )

    def _prepare_branch_snapshots(self, network: Any, sequence_network: Any, bus_ids: tuple[str, ...]) -> tuple[SequenceBranchSnapshot, ...]:
        index = {bus_id: position for position, bus_id in enumerate(bus_ids)}
        records: list[SequenceBranchSnapshot] = []
        seen: set[str] = set()
        for element in self._branch_elements(network):
            if not bool(getattr(element, "in_service", True)):
                continue
            bus_a, bus_b = self._end_buses(element)
            if bus_a is None or bus_b is None or bus_a is bus_b:
                continue
            from_id = str(getattr(bus_a, "id", bus_a))
            to_id = str(getattr(bus_b, "id", bus_b))
            branch_id = str(getattr(element, "id", element))
            if branch_id in seen:
                continue
            positive = self._sequence_value(sequence_network, branch_id, element, "positive")
            if positive is None:
                continue
            negative = self._sequence_value(sequence_network, branch_id, element, "negative")
            zero = self._sequence_value(sequence_network, branch_id, element, "zero")
            records.append(
                SequenceBranchSnapshot(
                    branch_id=branch_id,
                    from_bus_id=from_id,
                    to_bus_id=to_id,
                    from_bus_index=index[from_id],
                    to_bus_index=index[to_id],
                    positive=positive,
                    negative=negative,
                    zero=zero,
                    equipment_type=type(element).__name__,
                    from_terminal_role=str(getattr(element.from_terminal, "role", "FROM")),
                    to_terminal_role=str(getattr(element.to_terminal, "role", "TO")),
                    tap_ratio=float(getattr(element, "tap", 1.0)),
                    phase_shift_rad=float(getattr(element, "shift", 0.0)),
                )
            )
            seen.add(branch_id)
        return tuple(records)

    def _prepare_source_snapshots(self, network: Any, sequence_network: Any, bus_ids: tuple[str, ...]) -> tuple[SequenceSourceSnapshot, ...]:
        index = {bus_id: position for position, bus_id in enumerate(bus_ids)}
        records: list[SequenceSourceSnapshot] = []
        for source in self._source_elements(network):
            if not bool(getattr(source, "in_service", True)):
                continue
            bus = self._single_bus(source)
            if bus is None:
                continue
            bus_id = str(getattr(bus, "id", bus))
            source_id = str(getattr(source, "id", source))
            positive = self._sequence_value(sequence_network, source_id, source, "positive")
            internal_voltage = self._source_internal_voltage(source)
            if positive is None or internal_voltage is None:
                continue
            records.append(
                SequenceSourceSnapshot(
                    source_id=source_id,
                    source_type=type(source).__name__,
                    bus_id=bus_id,
                    bus_index=index[bus_id],
                    positive=positive,
                    negative=self._sequence_value(sequence_network, source_id, source, "negative"),
                    zero=self._sequence_value(sequence_network, source_id, source, "zero"),
                    internal_voltage=internal_voltage,
                )
            )
        return tuple(records)

    @staticmethod
    def _sequence_value(sequence_network: Any, element_id: str, element: Any, sequence: str) -> complex | None:
        data = getattr(sequence_network, sequence, {})
        value = data.get(element_id)
        if value is None:
            original_id = getattr(element, "id", None)
            value = data.get(original_id)
        return None if value is None else complex(value)

    @staticmethod
    def _source_internal_voltage(source: Any) -> complex | None:
        explicit = getattr(source, "internal_voltage", None)
        if explicit is not None:
            value = complex(explicit)
            if math.isfinite(value.real) and math.isfinite(value.imag):
                return value
            return None
        magnitude = getattr(source, "voltage_pu", None)
        angle_deg = getattr(source, "angle_deg", None)
        if magnitude is None:
            return None
        try:
            magnitude = float(magnitude)
            angle = 0.0 if angle_deg is None else math.radians(float(angle_deg))
        except (TypeError, ValueError):
            return None
        if not math.isfinite(magnitude) or not math.isfinite(angle) or magnitude <= 0.0:
            return None
        return magnitude * cmath.exp(1j * angle)

    @staticmethod
    def _source_elements(network: Any) -> list[Any]:
        result: list[Any] = []
        for collection_name in ("grids", "generators", "synchronous_machines", "motors"):
            result.extend(getattr(network, collection_name, ()) or ())
        return result

    @staticmethod
    def _branch_elements(network: Any) -> list[Any]:
        result: list[Any] = []
        seen: set[int] = set()
        for collection_name in ("lines", "cables", "transformers"):
            for element in getattr(network, collection_name, ()) or ():
                if id(element) not in seen:
                    seen.add(id(element))
                    result.append(element)
        return result

    def _end_buses(self, element: Any) -> tuple[Any | None, Any | None]:
        records = {(r.equipment_id, r.terminal_role): r.bus_id for r in self._topology_snapshot.equipment_bus_attachments}
        from_id = records.get((str(element.id), getattr(element.from_terminal, 'role', '')))
        to_id = records.get((str(element.id), getattr(element.to_terminal, 'role', '')))
        return (self._network.get_by_identity(from_id) if from_id else None, self._network.get_by_identity(to_id) if to_id else None)

    def _single_bus(self, element: Any) -> Any | None:
        role = getattr(getattr(element, 'terminal', None), 'role', '')
        bus_id = next((r.bus_id for r in self._topology_snapshot.equipment_bus_attachments if r.equipment_id == str(element.id) and r.terminal_role == role), None)
        return self._network.get_by_identity(bus_id) if bus_id else None

    @staticmethod
    def _prepare_prefault_voltage(network: Any, bus_id: str) -> complex:
        bus = network.get_by_identity(bus_id)
        try:
            magnitude = float(bus.V)
            angle = float(bus.theta)
        except (AttributeError, TypeError, ValueError):
            magnitude = float(getattr(bus, "voltage_pu", 1.0))
            angle = math.radians(float(getattr(bus, "angle_deg", 0.0)))
        if not math.isfinite(magnitude) or not math.isfinite(angle) or magnitude < 0.0:
            raise ValueError("Bus prefault voltage state must contain finite, non-negative values.")
        return magnitude * cmath.exp(1j * angle)

    @staticmethod
    def _resolve_fault_bus_index(fault_bus: Any, bus_ids: tuple[str, ...]) -> int:
        candidate = str(getattr(fault_bus, "id", fault_bus))
        try:
            return bus_ids.index(candidate)
        except ValueError as exc:
            raise ValueError(f"Fault bus '{fault_bus}' was not found in the Network.") from exc


__all__ = ["ShortCircuitPreparation"]
