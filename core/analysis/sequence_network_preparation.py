"""Canonical engineering-to-sequence-network preparation for short-circuit studies."""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np

from core.model.cable import Cable
from core.model.line import Line
from core.model.transformer import Transformer
from core.network.endpoint import resolve_terminal_bus
from core.solver.short_circuit.sequence_network import SequenceNetwork


class SequenceNetworkPreparation:
    """Build sequence-network data from an authoritative Network."""

    def __init__(self, network: Any, *, base_mva: float | None = None) -> None:
        if network is None or not hasattr(network, "buses"):
            raise ValueError("Sequence preparation requires an authoritative Network.")
        if not network.buses:
            raise ValueError("Sequence preparation requires at least one Bus.")
        if base_mva is not None and (not np.isfinite(base_mva) or base_mva <= 0.0):
            raise ValueError("base_mva must be finite and greater than zero.")
        self.network = network
        self.base_mva = None if base_mva is None else float(base_mva)

    def prepare(self, sequences: Iterable[str] = ("positive", "negative", "zero")) -> SequenceNetwork:
        """Prepare the requested sequence networks without mutating Core."""
        requested = tuple(self._normalize_sequence(value) for value in sequences)
        if not requested:
            raise ValueError("At least one sequence is required.")
        bus_ids = tuple(str(bus.id) for bus in self.network.buses)
        if len(set(bus_ids)) != len(bus_ids):
            raise ValueError("Network bus IDs must be unique for sequence preparation.")
        index = {bus: i for i, bus in enumerate(self.network.buses)}
        sequence = SequenceNetwork()
        branch_data: list[tuple[int, int, dict[str, complex | None], str]] = []

        for element in self._branch_elements():
            if not bool(getattr(element, "in_service", True)):
                continue
            bus_a, bus_b = self._end_buses(element)
            if bus_a is None or bus_b is None or bus_a is bus_b:
                continue
            data = self._branch_sequence_impedances(element, bus_a)
            element_id = getattr(element, "id", element)
            for name in requested:
                if data[name] is None:
                    raise ValueError(f"{type(element).__name__} '{element_id}' lacks explicit {name}-sequence engineering data.")
            sequence.add_element(element_id, data["positive"], data["negative"], data["zero"])
            branch_data.append((index[bus_a], index[bus_b], data, str(element_id)))

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
            branch_data.append((index[bus], index[bus], data, str(element_id)))

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
                branch_data.append((index[bus], index[bus], data, str(element_id)))

        for name in requested:
            sequence.set_matrix(name, self._build_matrix(len(bus_ids), branch_data, name))
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

    @staticmethod
    def _end_buses(element: Any) -> tuple[Any | None, Any | None]:
        terminals = (getattr(element, "from_terminal", None), getattr(element, "to_terminal", None))
        return tuple(None if terminal is None else resolve_terminal_bus(terminal) for terminal in terminals)  # type: ignore[return-value]

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
            return {"positive": z1, "negative": z1, "zero": None}
        if isinstance(element, Transformer):
            study_kv = voltage
            if study_kv <= 0.0:
                raise ValueError(f"Bus '{bus.id}' requires nominal_voltage_kv for transformer preparation.")
            scale = (self._require_base() / element.impedance_base_mva) * (element.impedance_base_voltage_kv / study_kv) ** 2
            z1 = complex(element.r, element.x) * scale if element.impedance_basis == "pu" else self._ohm_to_pu(complex(element.r, element.x), study_kv)
            return {"positive": z1, "negative": None, "zero": None}
        raise ValueError(f"Unsupported sequence-network branch type: {type(element).__name__}.")

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
    def _build_matrix(size: int, branches: list[tuple[int, int, dict[str, complex | None], str]], sequence: str) -> np.ndarray:
        y = np.zeros((size, size), dtype=complex)
        for i, j, data, element_id in branches:
            z = data[sequence]
            if z is None:
                raise ValueError(f"Element '{element_id}' lacks {sequence}-sequence impedance.")
            if abs(z) == 0.0:
                raise ValueError(f"Element '{element_id}' has zero {sequence}-sequence impedance.")
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
