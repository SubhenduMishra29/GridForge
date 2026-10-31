"""Canonical engineering-to-sequence-network preparation for short-circuit studies."""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np

from core.model.cable import Cable
from core.model.line import Line
from core.model.transformer import Transformer
from core.analysis.transformer_zero_sequence import (
    TransformerZeroSequenceShunt,
    build_transformer_zero_sequence_shunt,
)
from core.network.topology_snapshot import TopologySnapshot
from core.solver.short_circuit.sequence_network import SequenceNetwork


class SequenceNetworkPreparation:
    """Build sequence-network data from an authoritative Network."""

    def __init__(self, network: Any, *, base_mva: float | None = None, topology_snapshot: TopologySnapshot | None = None) -> None:
        if network is None or not hasattr(network, "buses"):
            raise ValueError("Sequence preparation requires an authoritative Network.")
        if not network.buses:
            raise ValueError("Sequence preparation requires at least one Bus.")
        if base_mva is not None and (not np.isfinite(base_mva) or base_mva <= 0.0):
            raise ValueError("base_mva must be finite and greater than zero.")
        self.network = network
        self.base_mva = None if base_mva is None else float(base_mva)
        self.topology_snapshot = topology_snapshot
        if self.topology_snapshot is None:
            self.network.rebuild_topology()
            self.topology_snapshot = self.network.topology_snapshot
            if self.topology_snapshot is None:
                raise ValueError('Sequence preparation requires a canonical TopologySnapshot.')

    def prepare(self, sequences: Iterable[str] = ("positive", "negative", "zero")) -> SequenceNetwork:
        """Prepare the requested sequence networks without mutating Core."""
        requested = tuple(self._normalize_sequence(value) for value in sequences)
        if not requested:
            raise ValueError("At least one sequence is required.")
        bus_ids = tuple(self.topology_snapshot.bus_ids)
        if not bus_ids:
            raise ValueError("TopologySnapshot must contain at least one Bus for sequence preparation.")
        if len(set(bus_ids)) != len(bus_ids):
            raise ValueError("TopologySnapshot bus IDs must be unique for sequence preparation.")
        index = {bus_id: i for i, bus_id in enumerate(bus_ids)}
        sequence = SequenceNetwork()
        branch_data: list[tuple[int, int, dict[str, complex | None], str, complex]] = []
        transformer_zero_shunts: list[tuple[int, TransformerZeroSequenceShunt]] = []

        for element in self._branch_elements():
            if not bool(getattr(element, "in_service", True)):
                continue
            bus_a, bus_b = self._end_buses(element)
            if bus_a is None or bus_b is None or bus_a is bus_b:
                continue
            data = self._branch_sequence_impedances(element, bus_a)
            element_id = getattr(element, "id", element)
            if isinstance(element, Transformer) and "zero" in requested:
                def terminal_role_value(terminal: Any) -> str:
                    role = getattr(terminal, "role", "")
                    return str(getattr(role, "value", role)).strip().upper()

                terminal_bus_by_role = {
                    terminal_role_value(element.from_terminal): bus_a,
                    terminal_role_value(element.to_terminal): bus_b,
                }
                from core.analysis.transformer_zero_sequence import (
                    TransformerZeroSequencePath,
                    classify_transformer_zero_sequence,
                )
                topology = classify_transformer_zero_sequence(element)
                if topology.path is TransformerZeroSequencePath.GROUNDED_WYE_SIDE_RETURN:
                    side = topology.grounded_winding_sides[0]
                    terminal_role = element.hv_terminal_role if side == "HV" else element.lv_terminal_role
                    grounded_bus = terminal_bus_by_role.get(str(terminal_role))
                    if grounded_bus is None:
                        raise ValueError(
                            f"Transformer '{element_id}' grounded {side} terminal does not resolve "
                            "to a Bus through the canonical topology snapshot."
                        )
                    equivalent = build_transformer_zero_sequence_shunt(
                        element, grounded_bus, base_mva=self._require_base()
                    )
                    if equivalent is None:
                        raise ValueError(f"Transformer '{element_id}' grounded-wye return equivalent was unexpectedly unavailable.")
                    transformer_zero_shunts.append((index[str(grounded_bus.id)], equivalent))
            for name in requested:
                if data[name] is None and not isinstance(element, Transformer):
                    raise ValueError(f"{type(element).__name__} '{element_id}' lacks explicit {name}-sequence engineering data.")
            sequence.add_element(element_id, data["positive"], data["negative"], data["zero"])
            from_id = str(bus_a.id)
            to_id = str(bus_b.id)
            branch_data.append((index[from_id], index[to_id], data, str(element_id), self._branch_complex_tap(element)))

        for source in self.network.grids:
            if not bool(getattr(source, "in_service", True)):
                continue
            bus = self._single_bus(source)
            if bus is None:
                continue
            data = {"positive": self._source_impedance(source, "z1_pu"), "negative": self._source_impedance(source, "z2_pu"), "zero": self._source_impedance(source, "z0_pu")}
            for name in requested:
                if data[name] is None:
                    raise ValueError(f"Grid '{getattr(source, 'id', source)}' is missing required {name}-sequence impedance.")
            element_id = getattr(source, "id", source)
            sequence.add_element(element_id, data["positive"], data["negative"], data["zero"])
            bus_id = str(bus.id)
            branch_data.append((index[bus_id], index[bus_id], data, str(element_id), 1.0 + 0.0j))

        for collection_name in ("generators", "synchronous_machines", "motors"):
            for machine in getattr(self.network, collection_name, ()):
                if not bool(getattr(machine, "in_service", True)):
                    continue
                bus = self._single_bus(machine)
                if bus is None:
                    continue
                names = {"positive": "z1_pu", "negative": "z2_pu", "zero": "z0_pu"}
                data = {name: self._source_impedance(machine, names[name]) for name in requested}
                for name in requested:
                    if data[name] is None:
                        raise ValueError(f"{type(machine).__name__} '{getattr(machine, 'id', machine)}' lacks explicit {name}-sequence impedance.")
                element_id = getattr(machine, "id", machine)
                sequence.add_element(element_id, data["positive"], data.get("negative"), data.get("zero"))
                bus_id = str(bus.id)
                branch_data.append((index[bus_id], index[bus_id], data, str(element_id), 1.0 + 0.0j))

        for name in requested:
            shunt_stamps = (
                [(bus_index, equivalent.impedance_pu) for bus_index, equivalent in transformer_zero_shunts]
                if name == "zero" else []
            )
            sequence.set_matrix(
                name,
                self._build_matrix(len(bus_ids), branch_data, name, shunt_stamps=shunt_stamps),
            )
        sequence.transformer_zero_sequence_shunts = tuple(
            equivalent for _, equivalent in transformer_zero_shunts
        )
        # Detached preparation can verify that this matrix uses the same
        # from-side complex-tap convention as transformer terminal results.
        sequence.transformer_tap_convention = "FROM_SIDE_COMPLEX_TAP_V1"
        return sequence

    @staticmethod
    def _normalize_sequence(value: str) -> str:
        aliases = {"positive": "positive", "z1": "positive", "1": "positive", "negative": "negative", "z2": "negative", "2": "negative", "zero": "zero", "z0": "zero", "0": "zero"}
        if not isinstance(value, str) or value.strip().lower() not in aliases:
            raise ValueError("Invalid sequence. Expected positive, negative, or zero.")
        return aliases[value.strip().lower()]

    def _branch_elements(self) -> list[Any]:
        result: list[Any] = []
        seen: set[int] = set()
        for collection_name in ("lines", "cables", "transformers"):
            for element in getattr(self.network, collection_name, ()):
                if id(element) not in seen:
                    seen.add(id(element))
                    result.append(element)
        return result

    def _end_buses(self, element: Any) -> tuple[Any | None, Any | None]:
        records = {
            (r.equipment_id, r.terminal_role): r.bus_id
            for r in self.topology_snapshot.equipment_bus_attachments
        }
        from_id = records.get((str(element.id), getattr(element.from_terminal, 'role', '')))
        to_id = records.get((str(element.id), getattr(element.to_terminal, 'role', '')))
        return (
            self.network.get_by_identity(from_id) if from_id else None,
            self.network.get_by_identity(to_id) if to_id else None,
        )

    def _single_bus(self, element: Any) -> Any | None:
        role = getattr(getattr(element, 'terminal', None), 'role', '')
        bus_id = next((r.bus_id for r in self.topology_snapshot.equipment_bus_attachments if r.equipment_id == str(element.id) and r.terminal_role == role), None)
        return self.network.get_by_identity(bus_id) if bus_id else None

    def _require_base(self) -> float:
        if self.base_mva is None:
            raise ValueError("base_mva is required when converting engineering impedances to study per-unit values.")
        return self.base_mva

    def _ohm_to_pu(self, z_ohm: complex, voltage_kv: float) -> complex:
        if voltage_kv <= 0.0:
            raise ValueError("A positive nominal voltage is required for engineering sequence conversion.")
        return complex(z_ohm) / (voltage_kv * voltage_kv / self._require_base())

    def _branch_sequence_impedances(self, element: Any, bus: Any) -> dict[str, complex | None]:
        voltage = float(bus.nominal_voltage_kv)
        if isinstance(element, Cable):
            z1 = self._ohm_to_pu(complex(element.resistance_ohm, element.reactance_ohm), voltage)
            z0 = self._ohm_to_pu(complex(element.zero_sequence_resistance_ohm, element.zero_sequence_reactance_ohm), voltage)
            return {"positive": z1, "negative": z1, "zero": z0}
        if isinstance(element, Line):
            z1 = self._ohm_to_pu(element.series_impedance, voltage)
            zero_r = getattr(element, "zero_sequence_resistance_ohm", None)
            zero_x = getattr(element, "zero_sequence_reactance_ohm", None)
            if (zero_r is None) != (zero_x is None):
                raise ValueError(
                    f"Line '{element.id}' must declare both zero-sequence resistance and reactance."
                )
            z0 = None if zero_r is None else self._ohm_to_pu(complex(float(zero_r), float(zero_x)), voltage)
            if z0 == 0.0 + 0.0j:
                raise ValueError(f"Line '{element.id}' has zero zero-sequence impedance; an explicit non-zero Z0 is required.")
            return {"positive": z1, "negative": z1, "zero": z0}
        if isinstance(element, Transformer):
            study_kv = voltage
            if study_kv <= 0.0:
                raise ValueError(f"Bus '{bus.id}' requires nominal_voltage_kv for transformer preparation.")
            scale = (self._require_base() / element.impedance_base_mva) * (element.impedance_base_voltage_kv / study_kv) ** 2
            z1 = complex(element.r, element.x) * scale if element.impedance_basis == "pu" else self._ohm_to_pu(complex(element.r, element.x), study_kv)
            # For a passive, static two-winding transformer, the negative-
            # sequence series impedance equals the positive-sequence value.
            # The phase-shifting tap reverses its angle in the negative-
            # sequence network. Zero sequence remains unavailable until
            # winding connection and neutral grounding are modelled.
            return {"positive": z1, "negative": z1, "zero": None}
        raise ValueError(f"Unsupported sequence-network branch type: {type(element).__name__}.")

    @staticmethod
    def _branch_complex_tap(element: Any) -> complex:
        """Return the explicit from-side complex tap used by the two-port primitive."""
        tap = float(getattr(element, "tap", 1.0))
        shift = float(getattr(element, "shift", 0.0))
        if not np.isfinite(tap) or tap <= 0.0:
            raise ValueError(f"Branch '{getattr(element, 'id', element)}' has an invalid tap ratio.")
        if not np.isfinite(shift):
            raise ValueError(f"Branch '{getattr(element, 'id', element)}' has an invalid phase shift.")
        return complex(tap * np.cos(shift), tap * np.sin(shift))

    @staticmethod
    def _source_impedance(source: Any, name: str) -> complex | None:
        value = getattr(source, name, None)
        if value is None:
            return None
        result = complex(value)
        if not np.isfinite(result.real) or not np.isfinite(result.imag) or abs(result) == 0.0:
            raise ValueError(f"'{getattr(source, 'id', source)}' has invalid {name}.")
        return result

    @staticmethod
    def _build_matrix(
        size: int,
        branches: list[tuple[int, int, dict[str, complex | None], str, complex]],
        sequence: str,
        *,
        shunt_stamps: list[tuple[int, complex]] | None = None,
    ) -> np.ndarray:
        """Stamp scalar sources, series/tap branches and explicit bus shunts into Ybus."""
        y = np.zeros((size, size), dtype=complex)
        for i, j, data, element_id, tap in branches:
            # Negative-sequence phase displacement is opposite to the
            # positive-sequence displacement for a phase-shifting transformer.
            sequence_tap = tap.conjugate() if sequence == "negative" else tap
            z = data[sequence]
            if z is None:
                # A transformer one-sided return is a grounded-Bus shunt,
                # never an artificial HV-LV zero-sequence series branch.
                if sequence == "zero":
                    continue
                raise ValueError(f"Element '{element_id}' lacks {sequence}-sequence impedance.")
            if abs(z) == 0.0:
                raise ValueError(f"Element '{element_id}' has zero {sequence}-sequence impedance.")
            admittance = 1.0 / z
            if i == j:
                y[i, i] += admittance
            else:
                if not np.isfinite(sequence_tap.real) or not np.isfinite(sequence_tap.imag) or abs(sequence_tap) == 0.0:
                    raise ValueError(f"Element '{element_id}' has an invalid complex tap.")
                # Standard from-side off-nominal tap convention.
                y[i, i] += admittance / (abs(sequence_tap) ** 2)
                y[i, j] -= admittance / sequence_tap.conjugate()
                y[j, i] -= admittance / sequence_tap
                y[j, j] += admittance
        for bus_index, impedance_pu in shunt_stamps or ():
            if not 0 <= bus_index < size:
                raise ValueError("Zero-sequence shunt Bus index is outside the prepared topology.")
            impedance = complex(impedance_pu)
            if (
                not np.isfinite(impedance.real)
                or not np.isfinite(impedance.imag)
                or abs(impedance) == 0.0
            ):
                raise ValueError("Transformer zero-sequence shunt impedance must be finite and non-zero.")
            y[bus_index, bus_index] += 1.0 / impedance
        if np.any(np.abs(np.diag(y)) == 0.0):
            raise ValueError("Sequence network contains a bus without a connected source, branch or shunt.")
        try:
            return np.linalg.inv(y)
        except np.linalg.LinAlgError as exc:
            raise ValueError("Sequence network admittance matrix is singular; the prepared network is not solvable.") from exc


__all__ = ["SequenceNetworkPreparation"]
