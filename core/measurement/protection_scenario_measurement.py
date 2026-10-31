"""Detached Protection Study measurement samples from explicit fault contributions.

The terminal-current adapter consumes the exact equipment endpoint persisted
in the protection binding. The legacy Branch FROM/TO conversion remains
available for compatibility. Neither path updates live MeasurementChannel
state. Values use canonical CT-secondary amperes and retain instrument/channel
basis identity.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping

from core.measurement.measurement_channel import MeasurementChannel
from core.measurement.measurement_generation import (
    MeasurementGeneration,
    PreparedMeasurementContext,
)
from core.model import EndpointReference
from core.network import CTMeasurementAssociation
from core.protection.protection_measurement_binding import ProtectionMeasurementBinding
from core.solver.short_circuit.result import ContributionStatus, ShortCircuitResult


@dataclass(frozen=True, slots=True)
class ProtectionScenarioMeasurementSample:
    """Immutable secondary-side measurement produced for one study scenario."""

    scenario_id: str
    binding_id: str
    protection_element_id: str
    relay_input_id: str
    channel_id: str
    instrument_id: str
    quantity_key: str
    phase_or_sequence: str
    value: complex
    unit: str
    reference_basis_id: str
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        for name in (
            "scenario_id", "binding_id", "protection_element_id", "relay_input_id",
            "channel_id", "instrument_id", "quantity_key", "phase_or_sequence",
            "unit", "reference_basis_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())
        current = complex(self.value)
        if not isfinite(current.real) or not isfinite(current.imag):
            raise ValueError("Scenario measurement value must be finite.")
        object.__setattr__(self, "value", current)
        if self.unit != "A":
            raise ValueError("CT scenario current samples must use the canonical ampere unit A.")
        if not isinstance(self.provenance, Mapping):
            raise TypeError("provenance must be a mapping.")
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


class ProtectionScenarioMeasurementAdapter:
    """Convert explicitly bound terminal/Branch contributions into detached CT samples."""

    def __init__(self, generation: MeasurementGeneration | None = None) -> None:
        self._generation = generation or MeasurementGeneration()
        if not isinstance(self._generation, MeasurementGeneration):
            raise TypeError("generation must be a MeasurementGeneration.")

    def convert_physical_conductor_ct_sample(
        self,
        *,
        scenario_id: str,
        binding: ProtectionMeasurementBinding,
        result: ShortCircuitResult,
        instrument: Any,
        channel: MeasurementChannel,
        ct_association: CTMeasurementAssociation,
        conductor_id: str,
        positive_current_direction: str,
    ) -> ProtectionScenarioMeasurementSample:
        """Convert one explicitly configured physical conductor current to CT secondary A."""
        if not isinstance(binding, ProtectionMeasurementBinding):
            raise TypeError("binding must be a ProtectionMeasurementBinding.")
        if not isinstance(result, ShortCircuitResult):
            raise TypeError("result must be a ShortCircuitResult.")
        if not isinstance(channel, MeasurementChannel):
            raise TypeError("channel must be a MeasurementChannel.")
        if not isinstance(ct_association, CTMeasurementAssociation):
            raise TypeError("ct_association must be a CTMeasurementAssociation.")
        if binding.measurement_type.strip().lower() != "current":
            raise ValueError("Physical conductor adapter only accepts current bindings.")
        if binding.instrument_id != getattr(instrument, "id", None):
            raise ValueError("Binding instrument identity does not match the supplied CT.")
        if binding.channel_id != channel.id:
            raise ValueError("Binding channel identity does not match the supplied MeasurementChannel.")
        endpoint = binding.source_endpoint_reference
        if not isinstance(endpoint, EndpointReference) or not endpoint.is_terminal:
            raise ValueError("Physical conductor CT requires an explicit equipment-terminal endpoint.")
        if endpoint.object_id != binding.source_equipment_id or endpoint.terminal_role not in {"FROM", "TO"}:
            raise ValueError("Physical conductor CT endpoint must identify the configured Branch FROM/TO terminal.")
        if not isinstance(conductor_id, str) or not conductor_id.strip():
            raise ValueError("conductor_id must be explicit.")
        conductor_id = conductor_id.strip()
        expected_quantity = f"conductor_currents.{conductor_id}"
        if binding.result_quantity != expected_quantity:
            raise ValueError("Binding result_quantity must exactly identify the configured physical conductor record.")
        record_key = f"{endpoint.object_id}:{endpoint.terminal_role}:{conductor_id}"
        try:
            record = result.conductor_currents[record_key]
        except KeyError as exc:
            raise ValueError(f"Short-circuit result has no physical conductor-current record {record_key!r}.") from exc
        if record.phase_or_sequence != binding.phase_or_sequence.strip().upper():
            raise ValueError("Binding conductor role does not match the physical current record.")
        if record.equipment_id != endpoint.object_id or record.terminal_role != endpoint.terminal_role:
            raise ValueError("Physical current record identity does not match the configured terminal.")
        ct_side = ct_association.locate_measurement_endpoint(endpoint)
        ct_terminal = ct_association.p1_terminal_reference if ct_side == "P1_SIDE" else ct_association.p2_terminal_reference
        context = PreparedMeasurementContext(
            source_id=ct_association.ct_id,
            source_terminal=ct_terminal,
            bus_id=record.bus_id,
            electrical_side=ct_side,
            quantity=result,
        )
        value = self._generation.convert_short_circuit_conductor_current(
            context,
            instrument,
            channel,
            equipment_terminal_reference=endpoint,
            conductor_current=record,
            positive_current_direction=positive_current_direction,
            ct_association=ct_association,
        )
        ratio = float(getattr(instrument, "ratio"))
        if not isfinite(ratio) or ratio <= 0.0 or abs(ratio - binding.instrument_ratio) > max(1e-9, ratio * 1e-9):
            raise ValueError("Configured binding ratio does not match the authoritative CT ratio.")
        provenance = {
            "project_id": result.provenance.get("project_id"),
            "activation_generation": result.provenance.get("activation_generation"),
            "topology_revision": result.provenance.get("topology_revision"),
            "calculation_domain": result.provenance.get("calculation_domain"),
            "fault_bus_id": result.fault_bus_id,
            "equipment_id": endpoint.object_id,
            "equipment_terminal_role": endpoint.terminal_role,
            "conductor_id": conductor_id,
            "conductor_role": record.phase_or_sequence,
            "conductor_current_reference_direction": record.reference_direction,
            "conductor_current_units": record.current_units,
            "conductor_current_a": record.provenance.get("current_a"),
            "measurement_bus_id": record.bus_id,
            "ct_id": ct_association.ct_id,
            "ct_primary_side": ct_side,
            "ct_topology_revision": ct_association.topology_revision,
            "instrument_ratio": ratio,
            "ct_positive_current_direction": ct_association.positive_current_direction,
            "positive_current_direction": positive_current_direction,
        }
        measurement_point_id = binding.metadata.get("measurement_point_id")
        residual_source_mode = binding.metadata.get("residual_source_mode")
        if measurement_point_id is not None:
            provenance["measurement_point_id"] = measurement_point_id
        if residual_source_mode is not None:
            provenance["residual_source_mode"] = residual_source_mode
        basis_id = f"CT_SECONDARY_A:{ct_association.ct_id}:{channel.id}:{ratio:.12g}"
        return ProtectionScenarioMeasurementSample(
            scenario_id=scenario_id,
            binding_id=binding.binding_id,
            protection_element_id=binding.protection_element_id,
            relay_input_id=binding.relay_input_id,
            channel_id=channel.id,
            instrument_id=ct_association.ct_id,
            quantity_key=expected_quantity,
            phase_or_sequence=binding.phase_or_sequence,
            value=complex(value),
            unit="A",
            reference_basis_id=basis_id,
            provenance=provenance,
        )

    def convert_neutral_ct_sample(
        self,
        *,
        scenario_id: str,
        binding: ProtectionMeasurementBinding,
        result: ShortCircuitResult,
        instrument: Any,
        channel: MeasurementChannel,
        ct_association: CTMeasurementAssociation,
        construction: Any,
    ) -> ProtectionScenarioMeasurementSample:
        """Execute a direct Neutral CT from its configured physical neutral node."""
        endpoint = binding.source_endpoint_reference
        if construction.equipment_id != binding.source_equipment_id or construction.terminal_role != endpoint.terminal_role:
            raise ValueError("Neutral CT construction equipment/terminal does not match its measurement binding.")
        sample = self.convert_physical_conductor_ct_sample(
            scenario_id=scenario_id, binding=binding, result=result, instrument=instrument,
            channel=channel, ct_association=ct_association,
            conductor_id=construction.conductor_id,
            positive_current_direction=construction.positive_current_direction,
        )
        if sample.phase_or_sequence.strip().upper() != "N":
            raise ValueError("Neutral CT construction must resolve to an N conductor-current record.")
        if sample.provenance.get("physical_node_id") != construction.neutral_node_id:
            raise ValueError("Configured neutral_node_id does not match the solved physical conductor node.")
        provenance = dict(sample.provenance)
        point = binding.metadata.get("measurement_point_id")
        if not isinstance(point, str) or not point.strip():
            raise ValueError("Direct Neutral CT binding requires an explicit measurement_point_id.")
        provenance.update({
            "residual_source_mode": "NEUTRAL_CT",
            "measurement_point_id": point.strip(),
            "neutral_node_id": construction.neutral_node_id,
        })
        return ProtectionScenarioMeasurementSample(
            scenario_id=sample.scenario_id, binding_id=sample.binding_id,
            protection_element_id=sample.protection_element_id, relay_input_id=sample.relay_input_id,
            channel_id=sample.channel_id, instrument_id=sample.instrument_id,
            quantity_key=sample.quantity_key, phase_or_sequence="N", value=sample.value,
            unit=sample.unit, reference_basis_id=sample.reference_basis_id, provenance=provenance,
        )

    def convert_cbct_window_sample(
        self,
        *,
        scenario_id: str,
        binding: ProtectionMeasurementBinding,
        result: ShortCircuitResult,
        instrument: Any,
        channel: MeasurementChannel,
        ct_association: CTMeasurementAssociation,
        construction: Any,
    ) -> ProtectionScenarioMeasurementSample:
        """Sum only the explicitly enclosed, co-terminal CBCT conductor records."""
        conductors = tuple(getattr(construction, "conductors", ()))
        if not conductors or not getattr(construction, "window_id", None):
            raise ValueError("CBCT requires an explicit physical window and conductor membership.")
        endpoint = binding.source_endpoint_reference
        if not endpoint.is_terminal:
            raise ValueError("CBCT measurement binding must identify one equipment terminal.")
        if any(item.equipment_id != endpoint.object_id or item.terminal_role != endpoint.terminal_role for item in conductors):
            raise ValueError("Every CBCT enclosed conductor must belong to the same configured equipment terminal.")
        samples = []
        for item in conductors:
            member_binding = replace(
                binding,
                phase_or_sequence=item.phase_or_sequence,
                result_quantity=f"conductor_currents.{item.conductor_id}",
            )
            samples.append(self.convert_physical_conductor_ct_sample(
                scenario_id=scenario_id, binding=member_binding, result=result,
                instrument=instrument, channel=channel, ct_association=ct_association,
                conductor_id=item.conductor_id,
                positive_current_direction=item.positive_current_direction,
            ))
        if len({(x.provenance.get("topology_revision"), x.provenance.get("measurement_bus_id")) for x in samples}) != 1:
            raise ValueError("CBCT enclosed conductor records do not share one topology revision and measurement Bus.")
        point = binding.metadata.get("measurement_point_id")
        if not isinstance(point, str) or not point.strip():
            raise ValueError("CBCT binding requires an explicit measurement_point_id.")
        provenance = dict(samples[0].provenance)
        provenance.update({
            "residual_source_mode": "CBCT",
            "measurement_point_id": point.strip(),
            "cbct_window_id": construction.window_id,
            "cbct_enclosed_conductor_ids": tuple(item.conductor_id for item in conductors),
            "cbct_neutral_included": construction.neutral_included,
            "cbct_member_provenance": tuple(dict(sample.provenance) for sample in samples),
        })
        return ProtectionScenarioMeasurementSample(
            scenario_id=scenario_id, binding_id=binding.binding_id,
            protection_element_id=binding.protection_element_id, relay_input_id=binding.relay_input_id,
            channel_id=channel.id, instrument_id=ct_association.ct_id,
            quantity_key=f"conductor_currents.CBCT:{construction.window_id}",
            phase_or_sequence="RESIDUAL",
            value=complex(sum((sample.value for sample in samples), 0j)),
            unit="A", reference_basis_id=samples[0].reference_basis_id, provenance=provenance,
        )

    def convert_terminal_ct_sample(
        self,
        *,
        scenario_id: str,
        binding: ProtectionMeasurementBinding,
        result: ShortCircuitResult,
        instrument: Any,
        channel: MeasurementChannel,
        ct_association: CTMeasurementAssociation,
    ) -> ProtectionScenarioMeasurementSample:
        """Convert the exact configured equipment-terminal current without channel mutation."""
        if not isinstance(binding, ProtectionMeasurementBinding):
            raise TypeError("binding must be a ProtectionMeasurementBinding.")
        if not isinstance(result, ShortCircuitResult):
            raise TypeError("result must be a ShortCircuitResult.")
        if not isinstance(channel, MeasurementChannel):
            raise TypeError("channel must be a MeasurementChannel.")
        if not isinstance(ct_association, CTMeasurementAssociation):
            raise TypeError("ct_association must be a CTMeasurementAssociation.")
        if binding.measurement_type.strip().lower() != "current":
            raise ValueError("Terminal-current adapter only accepts current bindings.")
        if binding.instrument_id != getattr(instrument, "id", None):
            raise ValueError("Binding instrument identity does not match the supplied CT.")
        if binding.channel_id != channel.id:
            raise ValueError("Binding channel identity does not match the supplied MeasurementChannel.")
        endpoint = binding.source_endpoint_reference
        if not isinstance(endpoint, EndpointReference) or not endpoint.is_terminal:
            raise ValueError("This adapter requires an explicit equipment-terminal endpoint; Bus attachments are not terminal-current records.")
        if endpoint.object_id != binding.source_equipment_id:
            raise ValueError("Configured terminal endpoint does not match the source equipment identity.")
        parts = binding.result_quantity.split(".", 1)
        if len(parts) != 2 or parts[0] not in {"phase_currents", "sequence_currents"}:
            raise ValueError("Binding result_quantity must name an explicit phase_currents or sequence_currents member.")
        phase_member = {
            "A": "Ia", "B": "Ib", "C": "Ic",
            "POSITIVE_SEQUENCE": "I1",
            "NEGATIVE_SEQUENCE": "I2",
            "ZERO_SEQUENCE": "I0",
        }.get(binding.phase_or_sequence.strip().upper(), binding.phase_or_sequence)
        if parts[1] != phase_member:
            raise ValueError("Binding phase_or_sequence does not map to its result_quantity member.")
        ct_side = ct_association.locate_measurement_endpoint(endpoint)
        ct_terminal = ct_association.p1_terminal_reference if ct_side == "P1_SIDE" else ct_association.p2_terminal_reference
        terminal_key = f"{endpoint.object_id}:{endpoint.terminal_role}"
        try:
            terminal = result.terminal_currents[terminal_key]
        except KeyError as exc:
            raise ValueError(f"Short-circuit result has no terminal-current record for {terminal_key!r}.") from exc
        context = PreparedMeasurementContext(
            source_id=ct_association.ct_id,
            source_terminal=ct_terminal,
            bus_id=terminal.bus_id,
            electrical_side=ct_side,
            quantity=result,
        )
        value = self._generation.convert_short_circuit_terminal_current(
            context, instrument, channel,
            equipment_terminal_reference=endpoint,
            quantity_key=binding.result_quantity,
            ct_association=ct_association,
        )
        ratio = float(getattr(instrument, "ratio"))
        if not isfinite(ratio) or ratio <= 0.0 or abs(ratio - binding.instrument_ratio) > max(1e-9, ratio * 1e-9):
            raise ValueError("Configured binding ratio does not match the authoritative CT ratio.")
        provenance = {
            "project_id": result.provenance.get("project_id"),
            "activation_generation": result.provenance.get("activation_generation"),
            "topology_revision": result.provenance.get("topology_revision"),
            "fault_bus_id": result.fault_bus_id,
            "equipment_id": endpoint.object_id,
            "equipment_type": terminal.equipment_type,
            "equipment_terminal_role": endpoint.terminal_role,
            "terminal_current_reference_direction": terminal.reference_direction,
            "measurement_bus_id": terminal.bus_id,
            "ct_id": ct_association.ct_id,
            "ct_primary_side": ct_side,
            "ct_topology_revision": ct_association.topology_revision,
            "current_units": result.provenance.get("current_units"),
            "base_mva": result.provenance.get("base_mva"),
            "bus_voltage_base_kv": result.provenance.get("bus_voltage_bases_kv", {}).get(terminal.bus_id),
            "instrument_ratio": ratio,
            "ct_positive_current_direction": ct_association.positive_current_direction,
            "terminal_sequence_provenance": dict(terminal.sequence_provenance),
        }
        # Residual-current mode and measurement point are persisted binding
        # declarations, never inferred from CT location or channel phase.
        for metadata_key in ("measurement_point_id", "residual_source_mode"):
            declared = binding.metadata.get(metadata_key)
            if declared is not None:
                provenance[metadata_key] = declared
        basis_id = f"CT_SECONDARY_A:{ct_association.ct_id}:{channel.id}:{ratio:.12g}"
        return ProtectionScenarioMeasurementSample(
            scenario_id=scenario_id, binding_id=binding.binding_id,
            protection_element_id=binding.protection_element_id,
            relay_input_id=binding.relay_input_id, channel_id=channel.id,
            instrument_id=ct_association.ct_id, quantity_key=binding.result_quantity,
            phase_or_sequence=binding.phase_or_sequence, value=complex(value),
            unit="A", reference_basis_id=basis_id, provenance=provenance,
        )
    def convert_branch_ct_sample(
        self,
        *,
        scenario_id: str,
        binding: ProtectionMeasurementBinding,
        result: ShortCircuitResult,
        instrument: Any,
        channel: MeasurementChannel,
        ct_association: CTMeasurementAssociation,
    ) -> ProtectionScenarioMeasurementSample:
        """Convert one configured phase/sequence member without channel mutation."""
        if not isinstance(binding, ProtectionMeasurementBinding):
            raise TypeError("binding must be a ProtectionMeasurementBinding.")
        if not isinstance(result, ShortCircuitResult):
            raise TypeError("result must be a ShortCircuitResult.")
        if result.status.value != "COMPLETE" or not result.success:
            raise ValueError("Only a complete successful short-circuit result can feed a scenario sample.")
        if result.contribution_status is not ContributionStatus.COMPLETE:
            raise ValueError("Incomplete short-circuit contributions cannot feed protection samples.")
        if not isinstance(ct_association, CTMeasurementAssociation):
            raise TypeError("ct_association must be a CTMeasurementAssociation.")
        if not isinstance(channel, MeasurementChannel):
            raise TypeError("channel must be a MeasurementChannel.")
        if binding.measurement_type.strip().lower() != "current":
            raise ValueError("This adapter only accepts current measurement bindings.")
        if binding.instrument_id != getattr(instrument, "id", None):
            raise ValueError("Binding instrument identity does not match the supplied CT.")
        if binding.channel_id != channel.id:
            raise ValueError("Binding channel identity does not match the supplied MeasurementChannel.")
        if binding.source_equipment_id not in result.branch_currents:
            raise ValueError("Current adapter requires an explicit Branch contribution identity.")
        endpoint = binding.source_endpoint_reference
        if not isinstance(endpoint, EndpointReference) or not endpoint.is_terminal:
            raise ValueError("Branch CT measurement requires an explicit Branch terminal endpoint.")
        if endpoint.object_id != binding.source_equipment_id:
            raise ValueError("Branch terminal endpoint does not match the configured Branch identity.")
        side = binding.electrical_side.strip().lower()
        if side not in {"from", "to"} or endpoint.terminal_role != side.upper():
            raise ValueError("Branch CT binding must explicitly identify matching FROM or TO terminal side.")
        branch = result.branch_currents[binding.source_equipment_id]
        bus_id = branch.from_bus_id if side == "from" else branch.to_bus_id
        ct_side = ct_association.locate_measurement_endpoint(endpoint)
        ct_terminal = (
            ct_association.p1_terminal_reference
            if ct_side == "P1_SIDE"
            else ct_association.p2_terminal_reference
        )
        context = PreparedMeasurementContext(
            source_id=ct_association.ct_id,
            source_terminal=ct_terminal,
            bus_id=bus_id,
            electrical_side=side,
            quantity=result,
        )
        value = self._generation.convert_short_circuit_branch_current(
            context,
            instrument,
            channel,
            branch_id=binding.source_equipment_id,
            branch_terminal_reference=endpoint,
            quantity_key=binding.result_quantity,
            ct_association=ct_association,
        )
        quantity_parts = binding.result_quantity.split(".", 1)
        if len(quantity_parts) != 2 or quantity_parts[0] not in {"phase_currents", "sequence_currents"}:
            raise ValueError("Binding result_quantity must explicitly name a phase_currents or sequence_currents member.")
        phase_member = {
            "A": "Ia", "B": "Ib", "C": "Ic",
            "POSITIVE_SEQUENCE": "I1",
            "NEGATIVE_SEQUENCE": "I2",
            "ZERO_SEQUENCE": "I0",
        }.get(binding.phase_or_sequence.strip().upper(), binding.phase_or_sequence)
        if quantity_parts[1] != phase_member:
            raise ValueError("Binding phase_or_sequence does not map to its explicit result_quantity member.")
        ratio = float(getattr(instrument, "ratio"))
        if not isfinite(ratio) or ratio <= 0.0 or abs(ratio - binding.instrument_ratio) > max(1e-9, ratio * 1e-9):
            raise ValueError("Configured binding ratio does not match the authoritative CT ratio.")
        provenance = {
            "project_id": result.provenance.get("project_id"),
            "activation_generation": result.provenance.get("activation_generation"),
            "topology_revision": result.provenance.get("topology_revision"),
            "fault_bus_id": result.fault_bus_id,
            "branch_id": binding.source_equipment_id,
            "branch_side": side,
            "measurement_bus_id": bus_id,
            "ct_id": ct_association.ct_id,
            "ct_topology_revision": ct_association.topology_revision,
            "current_units": result.provenance.get("current_units"),
            "base_mva": result.provenance.get("base_mva"),
            "bus_voltage_base_kv": result.provenance.get("bus_voltage_bases_kv", {}).get(bus_id),
            "instrument_ratio": ratio,
            "ct_positive_current_direction": ct_association.positive_current_direction,
        }
        basis_id = f"CT_SECONDARY_A:{ct_association.ct_id}:{channel.id}:{ratio:.12g}"
        return ProtectionScenarioMeasurementSample(
            scenario_id=scenario_id,
            binding_id=binding.binding_id,
            protection_element_id=binding.protection_element_id,
            relay_input_id=binding.relay_input_id,
            channel_id=channel.id,
            instrument_id=ct_association.ct_id,
            quantity_key=binding.result_quantity,
            phase_or_sequence=binding.phase_or_sequence,
            value=complex(value),
            unit="A",
            reference_basis_id=basis_id,
            provenance=provenance,
        )


__all__ = [
    "ProtectionScenarioMeasurementSample",
    "ProtectionScenarioMeasurementAdapter",
]
