"""Canonical engineering-to-sequence-network preparation for short-circuit studies.

This module is the sole bridge from authoritative Network equipment to the
numerical SequenceNetwork representation.  It performs engineering-unit/base
conversion and builds detached positive-, negative-, and zero-sequence
impedance matrices.  It never mutates Core equipment.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from core.model.cable import Cable
from core.model.line import Line
from core.model.transformer import Transformer
from core.network.endpoint import resolve_terminal_bus
from core.solver.short_circuit.sequence_network import SequenceNetwork


class SequenceNetworkPreparation:
    """Build one sequence network from an authoritative Network."""

    def __init__(self, network: Any, *, base_mva: float | None = None) -> None:
        if network is None or not hasattr(network, "buses"):
            raise ValueError("Sequence preparation requires an authoritative Network.")
        if not network.buses:
            raise ValueError("Sequence preparation requires at least one Bus.")
        if base_mva is not None and (not np.isfinite(base_mva) or base_mva <= 0.0):
            raise ValueError("base_mva must be finite and greater than zero.")
        self.network = network
        self.base_mva = None if base_mva is None else float(base_mva)

    def prepare(self) -> SequenceNetwork:
        """Prepare detached sequence element data and Zbus matrices."""
        bus_ids = tuple(str(bus.id) for bus in self.network.buses)
        if len(set(bus_ids)) != len(bus_ids):
            raise ValueError("Network bus IDs must be unique for sequence preparation.")
        index = {bus: i for i, bus in enumerate(self.network.buses)}
        sequence = SequenceNetwork()
        branch_data: list[tuple[int, int, complex, complex | None, complex | None, str]] = []

        for element in self._branch_elements():
            if not bool(getattr(element, "in_service", True)):
                continue
            bus_a, bus_b = self._end_buses(element)
            if bus_a is None or bus_b is None or bus_a is bus_b:
                continue
            i, j = index[bus_a], index[bus_b]
            z1, z2, z0 = self._branch_sequence_impedances(element, bus_a)
            element_id = getattr(element, "id", element)
            sequence.add_element(element_id, z1, z2, z0)
            branch_data.append((i, j, z1, z2, z0, str(element_id)))

        for source in self.network.grids:
            if not bool(getattr(source, "in_service", True)):
                continue
            bus = self._single_bus(source)
            if bus is None:
                continue
            z1 = self._source_impedance(source, "z1_pu")
            z2 = self._source_impedance(source, "z2_pu")
            z0 = self._source_impedance(source, "z0_pu")
            element_id = getattr(source, "id", source)
            sequence.add_element(element_id, z1, z2, z0)
            branch_data.append((index[bus], index[bus], z1, z2, z0, str(element_id)))

        self._validate_rotating_machines()
        self._validate_unsupported_zero_sequence()

        for name, values in (("positive", sequence.positive), ("negative", sequence.negative), ("zero", sequence.zero)):
            if not values:
                raise ValueError(f"No {name}-sequence engineering data is available for the Network.")

        for name, position in (("positive", 2), ("negative", 3), ("zero", 4)):
            matrix = self._build_matrix(len(bus_ids), branch_data, position)
            sequence.set_matrix(name, matrix)

        return sequence

    def _branch_elements(self) -> list[Any]:
        result: list[Any] = []
        seen: set[int] = set()
        for collection_name in ("lines", "cables", "transformers"):
            for element in getattr(self.network, collection_name, ()):
                if id(element) not in seen:
                    seen.add(id(element))
                    result.append(element)
        return result

    @staticmethod
    def _end_buses(element: Any) -> tuple[Any | None, Any | None]:
        buses = []
        for terminal_name in ("from_terminal", "to_terminal"):
            terminal = getattr(element, terminal_name, None)
            buses.append(None if terminal is None else resolve_terminal_bus(terminal))
        return buses[0], buses[1]

    @staticmethod
    def _single_bus(element: Any) -> Any | None:
        terminal = getattr(element, "terminal", None)
        return None if terminal is None else resolve_terminal_bus(terminal)

    def _require_base(self) -> float:
        if self.base_mva is None:
            raise ValueError("base_mva is required when converting engineering impedances to study per-unit values.")
        return self.base_mva

    def _ohm_to_pu(self, z_ohm: complex, voltage_kv: float) -> complex:
        if voltage_kv <= 0.0:
            raise ValueError("A positive bus nominal voltage is required for engineering sequence conversion.")
        zbase = voltage_kv * voltage_kv / self._require_base()
        return complex(z_ohm) / zbase

    def _branch_sequence_impedances(self, element: Any, bus: Any) -> tuple[complex, complex, complex | None]:
        if isinstance(element, Cable):
            z1 = self._ohm_to_pu(complex(element.resistance_ohm, element.reactance_ohm), float(bus.nominal_voltage_kv))
            z0 = self._ohm_to_pu(complex(element.zero_sequence_resistance_ohm, element.zero_sequence_reactance_ohm), float(bus.nominal_voltage_kv))
            return z1, z1, z0

        if isinstance(element, Line):
            z1 = self._ohm_to_pu(element.series_impedance, float(bus.nominal_voltage_kv))
            return z1, z1, None

        if isinstance(element, Transformer):
            base_mva = element.impedance_base_mva
            base_kv = element.impedance_base_voltage_kv
            study_mva = self._require_base()
            study_kv = float(bus.nominal_voltage_kv)
            if study_kv <= 0.0:
                raise ValueError(f"Bus '{bus.id}' requires nominal_voltage_kv for transformer preparation.")
            scale = (study_mva / base_mva) * (base_kv / study_kv) ** 2
            if element.impedance_basis == "pu":
                z1 = complex(element.r, element.x) * scale
            else:
                z1 = self._ohm_to_pu(complex(element.r, element.x), study_kv)
            return z1, None, None

        raise ValueError(f"Unsupported sequence-network branch type: {type(element).__name__}.")

    @staticmethod
    def _source_impedance(source: Any, name: str) -> complex:
        value = getattr(source, name, None)
        if value is None:
            raise ValueError(f"Grid '{getattr(source, 'id', source)}' is missing required {name}.")
        try:
            result = complex(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Grid '{getattr(source, 'id', source)}' has invalid {name}.") from exc
        if not np.isfinite(result.real) or not np.isfinite(result.imag):
            raise ValueError(f"Grid '{getattr(source, 'id', source)}' has non-finite {name}.")
        if abs(result) == 0.0:
            raise ValueError(f"Grid '{getattr(source, 'id', source)}' {name} cannot be zero.")
        return result

    def _validate_rotating_machines(self) -> None:
        for collection_name in ("generators", "synchronous_machines", "motors"):
            for machine in getattr(self.network, collection_name, ()):
                if not bool(getattr(machine, "in_service", True)):
                    continue
                if self._single_bus(machine) is None:
                    continue
                missing = [name for name in ("z1_pu", "z2_pu", "z0_pu") if getattr(machine, name, None) is None]
                if missing:
                    raise ValueError(
                        f"{type(machine).__name__} '{getattr(machine, 'id', machine)}' is connected and in service "
                        f"but lacks explicit short-circuit sequence data: {', '.join(missing)}."
                    )

    def _validate_unsupported_zero_sequence(self) -> None:
        for transformer in getattr(self.network, "transformers", ()):
            if bool(getattr(transformer, "in_service", True)) and self._single_bus(transformer) is not None:
                raise ValueError(
                    f"Transformer '{getattr(transformer, 'id', transformer)}' lacks explicit Z2/Z0 and grounding/vector-group data."
                )
        for line in getattr(self.network, "lines", ()):
            if bool(getattr(line, "in_service", True)) and self._end_buses(line)[0] is not None:
                raise ValueError(
                    f"Line '{getattr(line, 'id', line)}' lacks explicit zero-sequence engineering data."
                )

    @staticmethod
    def _build_matrix(size: int, branches: list[tuple[int, int, complex, complex | None, complex | None, str]], position: int) -> np.ndarray:
        y = np.zeros((size, size), dtype=complex)
        for i, j, z1, z2, z0, _ in branches:
            z = (z1, z2, z0)[position - 2]
            if z is None:
                raise ValueError("Required sequence impedance is missing for a network element.")
            if abs(z) == 0.0:
                raise ValueError("Sequence branch impedance cannot be zero.")
            admittance = 1.0 / z
            if i == j:
                y[i, i] += admittance
            else:
                y[i, i] += admittance
                y[j, j] += admittance
                y[i, j] -= admittance
                y[j, i] -= admittance
        if np.any(np.abs(np.diag(y)) == 0.0):
            raise ValueError("Sequence network contains a bus without a connected source or branch.")
        try:
            return np.linalg.inv(y)
        except np.linalg.LinAlgError as exc:
            raise ValueError("Sequence network admittance matrix is singular; the prepared network is not solvable.") from exc


__all__ = ["SequenceNetworkPreparation"]
