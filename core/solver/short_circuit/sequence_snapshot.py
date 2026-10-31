"""Immutable sequence-network data prepared for short-circuit execution.

The snapshot is deliberately detached from ``SequenceNetwork``. It contains
only defensive, immutable copies of sequence element impedances, sequence
impedance matrices, and optional prepared topology/source metadata required for
engineering current interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from core.network.physical_conductor_topology import PhysicalConductorTopologySnapshot

import numpy as np


ComplexMatrix = tuple[tuple[complex, ...], ...]


def _freeze_mapping(values: Mapping[Any, Any]) -> Mapping[Any, Any]:
    return MappingProxyType(dict(values))


def _freeze_matrix(matrix: Any) -> ComplexMatrix | None:
    if matrix is None:
        return None
    array = np.asarray(matrix, dtype=complex)
    if array.ndim != 2 or array.shape[0] != array.shape[1] or array.size == 0:
        raise ValueError("Sequence matrix must be a non-empty square matrix.")
    return tuple(tuple(complex(value) for value in row) for row in array.tolist())


def _matrix_from_snapshot(matrix: ComplexMatrix) -> np.ndarray:
    return np.asarray(matrix, dtype=complex)


@dataclass(frozen=True, slots=True)
class SequenceBranchSnapshot:
    """Prepared branch identity and sequence impedances."""

    branch_id: str
    from_bus_id: str
    to_bus_id: str
    from_bus_index: int
    to_bus_index: int
    positive: complex
    negative: complex | None
    zero: complex | None
    equipment_type: str
    from_terminal_role: str = "FROM"
    to_terminal_role: str = "TO"
    tap_ratio: float = 1.0
    phase_shift_rad: float = 0.0

    def __post_init__(self) -> None:
        for name in ("branch_id", "from_bus_id", "to_bus_id", "equipment_type", "from_terminal_role", "to_terminal_role"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty engineering identifier.")
        for name in ("from_bus_index", "to_bus_index"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer.")
        if self.from_bus_id == self.to_bus_id or self.from_bus_index == self.to_bus_index:
            raise ValueError("A branch snapshot requires distinct endpoints.")
        if self.from_terminal_role == self.to_terminal_role:
            raise ValueError("A branch snapshot requires distinct terminal roles.")
        tap_ratio = float(self.tap_ratio)
        phase_shift_rad = float(self.phase_shift_rad)
        if not np.isfinite(tap_ratio) or tap_ratio <= 0.0:
            raise ValueError("tap_ratio must be finite and greater than zero.")
        if not np.isfinite(phase_shift_rad):
            raise ValueError("phase_shift_rad must be finite.")
        object.__setattr__(self, "tap_ratio", tap_ratio)
        object.__setattr__(self, "phase_shift_rad", phase_shift_rad)
        for name in ("positive", "negative", "zero"):
            value = getattr(self, name)
            if value is not None:
                value = complex(value)
                if not np.isfinite(value.real) or not np.isfinite(value.imag) or abs(value) == 0.0:
                    raise ValueError(f"{name}-sequence branch impedance must be finite and non-zero.")
                object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class SequenceTransformerZeroShuntSnapshot:
    """Detached grounded-wye transformer zero-sequence shunt and terminal provenance."""

    transformer_id: str
    bus_id: str
    bus_index: int
    terminal_role: str
    grounded_winding_side: str
    impedance_pu: complex
    transformer_z0_ohm: complex
    neutral_3zn_ohm: complex
    total_impedance_ohm: complex
    base_mva: float
    base_voltage_kv: float
    core_construction: str
    zero_sequence_test_basis: str
    test_energized_winding: str
    test_other_winding_condition: str
    test_neutral_return_included: bool

    def __post_init__(self) -> None:
        for name in ("transformer_id", "bus_id", "terminal_role", "grounded_winding_side",
                     "core_construction", "zero_sequence_test_basis", "test_energized_winding",
                     "test_other_winding_condition"):
            value = str(getattr(self, name)).strip()
            if not value:
                raise ValueError(f"{name} must be a non-empty provenance value.")
            object.__setattr__(self, name, value)
        if self.terminal_role not in {"FROM", "TO"}:
            raise ValueError("Transformer zero-sequence shunt terminal_role must be FROM or TO.")
        if self.grounded_winding_side not in {"HV", "LV"}:
            raise ValueError("grounded_winding_side must be HV or LV.")
        if type(self.test_neutral_return_included) is not bool:
            raise TypeError("test_neutral_return_included must be a boolean.")
        if isinstance(self.bus_index, bool) or not isinstance(self.bus_index, int) or self.bus_index < 0:
            raise ValueError("Transformer shunt bus_index must be a non-negative integer.")
        for name in ("impedance_pu", "transformer_z0_ohm", "neutral_3zn_ohm", "total_impedance_ohm"):
            value = complex(getattr(self, name))
            if not np.isfinite(value.real) or not np.isfinite(value.imag):
                raise ValueError(f"{name} must be finite.")
            if name == "impedance_pu" and abs(value) == 0.0:
                raise ValueError("Transformer zero-sequence shunt impedance_pu must be non-zero.")
            object.__setattr__(self, name, value)
        for name in ("base_mva", "base_voltage_kv"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive.")
            object.__setattr__(self, name, value)




@dataclass(frozen=True, slots=True)
class SequenceTransformerZeroTwoBusSnapshot:
    """Detached Yg-Yg two-terminal zero-sequence T-equivalent stamp."""

    transformer_id: str
    hv_bus_id: str
    lv_bus_id: str
    hv_bus_index: int
    lv_bus_index: int
    hv_terminal_role: str
    lv_terminal_role: str
    y_hh_pu: complex
    y_hl_pu: complex
    y_ll_pu: complex
    hv_neutral_3zn_ohm: complex
    lv_neutral_3zn_ohm: complex
    lv_neutral_3zn_hv_referred_ohm: complex
    base_mva: float
    test_mva_base: float
    hv_base_voltage_kv: float
    lv_base_voltage_kv: float
    test_hv_open_circuit_z0_ohm: complex
    test_lv_open_circuit_z0_hv_referred_ohm: complex
    test_hv_short_circuit_z0_ohm: complex
    test_source_reference: str
    core_construction: str
    zero_sequence_test_basis: str

    def __post_init__(self) -> None:
        for name in ("transformer_id", "hv_bus_id", "lv_bus_id", "test_source_reference", "core_construction", "zero_sequence_test_basis"):
            value = str(getattr(self, name)).strip()
            if not value:
                raise ValueError(f"{name} must be a non-empty provenance value.")
            object.__setattr__(self, name, value)
        if self.hv_bus_id == self.lv_bus_id:
            raise ValueError("Yg-Yg zero-sequence snapshot requires distinct HV/LV Buses.")
        if self.hv_terminal_role not in {"FROM", "TO"} or self.lv_terminal_role not in {"FROM", "TO"} or self.hv_terminal_role == self.lv_terminal_role:
            raise ValueError("Yg-Yg snapshot requires distinct canonical HV/LV terminal roles.")
        for name in ("hv_bus_index", "lv_bus_index"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer.")
        if self.hv_bus_index == self.lv_bus_index:
            raise ValueError("Yg-Yg snapshot requires distinct HV/LV Bus indices.")
        for name in ("y_hh_pu", "y_hl_pu", "y_ll_pu", "hv_neutral_3zn_ohm", "lv_neutral_3zn_ohm",
                     "lv_neutral_3zn_hv_referred_ohm", "test_hv_open_circuit_z0_ohm",
                     "test_lv_open_circuit_z0_hv_referred_ohm", "test_hv_short_circuit_z0_ohm"):
            value = complex(getattr(self, name))
            if not np.isfinite(value.real) or not np.isfinite(value.imag):
                raise ValueError(f"{name} must be finite.")
            object.__setattr__(self, name, value)
        for name in ("base_mva", "test_mva_base", "hv_base_voltage_kv", "lv_base_voltage_kv"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive.")
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class SequenceSourceSnapshot:
    """Prepared source identity, bus, sequence impedances and internal voltage."""

    source_id: str
    source_type: str
    bus_id: str
    bus_index: int
    positive: complex
    negative: complex | None
    zero: complex | None
    internal_voltage: complex

    def __post_init__(self) -> None:
        for name in ("source_id", "source_type", "bus_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty engineering identifier.")
        if isinstance(self.bus_index, bool) or not isinstance(self.bus_index, int) or self.bus_index < 0:
            raise ValueError("bus_index must be a non-negative integer.")
        voltage = complex(self.internal_voltage)
        if not np.isfinite(voltage.real) or not np.isfinite(voltage.imag):
            raise ValueError("internal_voltage must be finite.")
        object.__setattr__(self, "internal_voltage", voltage)
        for name in ("positive", "negative", "zero"):
            value = getattr(self, name)
            if value is not None:
                value = complex(value)
                if not np.isfinite(value.real) or not np.isfinite(value.imag) or abs(value) == 0.0:
                    raise ValueError(f"{name}-sequence source impedance must be finite and non-zero.")
                object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class SequenceNetworkSnapshot:
    """Immutable execution snapshot of a prepared sequence network."""

    positive: Mapping[Any, complex | None]
    negative: Mapping[Any, complex | None]
    zero: Mapping[Any, complex | None]
    positive_matrix: ComplexMatrix | None = None
    negative_matrix: ComplexMatrix | None = None
    zero_matrix: ComplexMatrix | None = None
    bus_ids: tuple[str, ...] = ()
    branches: tuple[SequenceBranchSnapshot, ...] = ()
    sources: tuple[SequenceSourceSnapshot, ...] = ()
    unavailable_bus_indices: Mapping[str, tuple[int, ...]] = field(default_factory=dict)
    transformer_zero_shunts: tuple[SequenceTransformerZeroShuntSnapshot, ...] = ()
    transformer_zero_two_bus_stamps: tuple[SequenceTransformerZeroTwoBusSnapshot, ...] = ()
    physical_conductor_topology: PhysicalConductorTopologySnapshot | None = None
    physical_conductor_impedances: Any | None = None
    physical_conductor_impedance_diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "positive", _freeze_mapping(self.positive))
        object.__setattr__(self, "negative", _freeze_mapping(self.negative))
        object.__setattr__(self, "zero", _freeze_mapping(self.zero))
        object.__setattr__(self, "positive_matrix", _freeze_matrix(self.positive_matrix))
        object.__setattr__(self, "negative_matrix", _freeze_matrix(self.negative_matrix))
        object.__setattr__(self, "zero_matrix", _freeze_matrix(self.zero_matrix))
        object.__setattr__(self, "bus_ids", tuple(str(bus_id) for bus_id in self.bus_ids))
        if self.bus_ids and len(set(self.bus_ids)) != len(self.bus_ids):
            raise ValueError("Sequence snapshot bus IDs must be unique.")
        object.__setattr__(self, "branches", tuple(self.branches))
        object.__setattr__(self, "sources", tuple(self.sources))
        shunts = tuple(self.transformer_zero_shunts)
        seen_transformers: set[str] = set()
        for shunt in shunts:
            if not isinstance(shunt, SequenceTransformerZeroShuntSnapshot):
                raise TypeError("transformer_zero_shunts must contain SequenceTransformerZeroShuntSnapshot records.")
            if shunt.transformer_id in seen_transformers:
                raise ValueError("A transformer may have only one supported grounded-side zero-sequence shunt.")
            seen_transformers.add(shunt.transformer_id)
            if self.bus_ids:
                if shunt.bus_index >= len(self.bus_ids) or self.bus_ids[shunt.bus_index] != shunt.bus_id:
                    raise ValueError("Transformer shunt Bus identity does not match bus_ids.")
        object.__setattr__(self, "transformer_zero_shunts", shunts)
        two_bus_stamps = tuple(self.transformer_zero_two_bus_stamps)
        seen_two_bus: set[str] = set()
        for stamp in two_bus_stamps:
            if not isinstance(stamp, SequenceTransformerZeroTwoBusSnapshot):
                raise TypeError("transformer_zero_two_bus_stamps must contain SequenceTransformerZeroTwoBusSnapshot records.")
            if stamp.transformer_id in seen_two_bus or stamp.transformer_id in seen_transformers:
                raise ValueError("A transformer cannot have both one-sided and two-sided zero-sequence equivalents.")
            seen_two_bus.add(stamp.transformer_id)
            if self.bus_ids:
                if stamp.hv_bus_index >= len(self.bus_ids) or stamp.lv_bus_index >= len(self.bus_ids):
                    raise ValueError("Yg-Yg transformer Bus index is outside bus_ids.")
                if self.bus_ids[stamp.hv_bus_index] != stamp.hv_bus_id or self.bus_ids[stamp.lv_bus_index] != stamp.lv_bus_id:
                    raise ValueError("Yg-Yg transformer Bus identity does not match bus_ids.")
        object.__setattr__(self, "transformer_zero_two_bus_stamps", two_bus_stamps)
        conductor_topology = self.physical_conductor_topology
        if conductor_topology is not None:
            if not isinstance(conductor_topology, PhysicalConductorTopologySnapshot):
                raise TypeError("physical_conductor_topology must be a PhysicalConductorTopologySnapshot.")
            if conductor_topology.topology_revision < 0:
                raise ValueError("Physical conductor topology revision must be non-negative.")
            if conductor_topology.branches and not self.bus_ids:
                raise ValueError("Sequence snapshot requires canonical bus_ids when physical conductor topology is present.")
            if self.bus_ids:
                for item in conductor_topology.branches:
                    for bus_id in (item.from_bus_id, item.to_bus_id):
                        if bus_id is not None and bus_id not in self.bus_ids:
                            raise ValueError("Physical conductor branch references a Bus outside the sequence snapshot.")
        conductor_diagnostics = tuple(str(item) for item in self.physical_conductor_impedance_diagnostics)
        conductor_impedances = self.physical_conductor_impedances
        if conductor_impedances is None and conductor_topology is not None and any(item.in_service for item in conductor_topology.branches) and not conductor_diagnostics:
            conductor_diagnostics = ("UNAVAILABLE: physical conductor impedance snapshot was not prepared.",)
        object.__setattr__(self, "physical_conductor_impedance_diagnostics", conductor_diagnostics)
        if conductor_impedances is not None:
            if not all(hasattr(conductor_impedances, name) for name in ("project_id", "activation_generation", "topology_revision", "branches")):
                raise TypeError("physical_conductor_impedances must satisfy the detached impedance snapshot contract.")
            if conductor_topology is None:
                raise ValueError("Physical conductor impedance snapshot requires its topology snapshot.")
            if (conductor_impedances.project_id, conductor_impedances.activation_generation, conductor_impedances.topology_revision) != (conductor_topology.project_id, conductor_topology.activation_generation, conductor_topology.topology_revision):
                raise ValueError("Physical conductor impedance and topology provenance do not match.")
            expected_ids = {item.equipment_id for item in conductor_topology.branches if item.in_service}
            actual_ids = {item.equipment_id for item in conductor_impedances.branches}
            if expected_ids != actual_ids:
                raise ValueError("Physical conductor impedance coverage does not match active conductor-equipped branches.")
        unavailable: dict[str, tuple[int, ...]] = {}
        for sequence in ("positive", "negative", "zero"):
            raw_indices = tuple(self.unavailable_bus_indices.get(sequence, ()))
            if any(
                isinstance(index, bool) or not isinstance(index, (int, np.integer))
                for index in raw_indices
            ):
                raise TypeError(f"{sequence}-sequence unavailable Bus indices must be integers.")
            indices = tuple(sorted(set(int(index) for index in raw_indices)))
            if any(index < 0 or (self.bus_ids and index >= len(self.bus_ids)) for index in indices):
                raise ValueError(f"{sequence}-sequence unavailable Bus index is outside bus_ids.")
            unavailable[sequence] = indices
        if self.bus_ids:
            for sequence in ("positive", "negative", "zero"):
                matrix = getattr(self, f"{sequence}_matrix")
                if matrix is not None and len(matrix) != len(self.bus_ids):
                    raise ValueError(f"{sequence}-sequence matrix dimensions must match bus_ids.")
        unknown_sequences = set(self.unavailable_bus_indices) - {"positive", "negative", "zero"}
        if unknown_sequences:
            raise ValueError(f"Unsupported unavailable sequence metadata: {sorted(unknown_sequences)}.")
        object.__setattr__(self, "unavailable_bus_indices", _freeze_mapping(unavailable))
        for record in self.branches:
            if not isinstance(record, SequenceBranchSnapshot):
                raise TypeError("branches must contain SequenceBranchSnapshot records.")
        for record in self.sources:
            if not isinstance(record, SequenceSourceSnapshot):
                raise TypeError("sources must contain SequenceSourceSnapshot records.")
        if self.bus_ids:
            size = len(self.bus_ids)
            for branch in self.branches:
                if branch.from_bus_index >= size or branch.to_bus_index >= size:
                    raise ValueError("Branch snapshot bus index is outside bus_ids.")
                if self.bus_ids[branch.from_bus_index] != branch.from_bus_id or self.bus_ids[branch.to_bus_index] != branch.to_bus_id:
                    raise ValueError("Branch snapshot bus identity does not match bus_ids.")
            for source in self.sources:
                if source.bus_index >= size or self.bus_ids[source.bus_index] != source.bus_id:
                    raise ValueError("Source snapshot bus identity does not match bus_ids.")

    @classmethod
    def from_sequence_network(cls, sequence_network: Any, *, bus_ids: tuple[str, ...] = (), branches: tuple[SequenceBranchSnapshot, ...] = (), sources: tuple[SequenceSourceSnapshot, ...] = ()) -> "SequenceNetworkSnapshot":
        """Detach all supported sequence data from a preparation container."""
        if sequence_network is None:
            raise ValueError("Sequence network cannot be None.")
        return cls(
            positive=dict(getattr(sequence_network, "positive", {})),
            negative=dict(getattr(sequence_network, "negative", {})),
            zero=dict(getattr(sequence_network, "zero", {})),
            positive_matrix=sequence_network.get_matrix("positive") if sequence_network.has_matrix("positive") else None,
            negative_matrix=sequence_network.get_matrix("negative") if sequence_network.has_matrix("negative") else None,
            zero_matrix=sequence_network.get_matrix("zero") if sequence_network.has_matrix("zero") else None,
            bus_ids=bus_ids,
            branches=branches,
            sources=sources,
            unavailable_bus_indices=dict(getattr(sequence_network, "unavailable_bus_indices", {})),
            physical_conductor_topology=getattr(sequence_network, "physical_conductor_topology", None),
            physical_conductor_impedances=getattr(sequence_network, "physical_conductor_impedances", None),
            physical_conductor_impedance_diagnostics=tuple(getattr(sequence_network, "physical_conductor_impedance_diagnostics", ())),
            transformer_zero_two_bus_stamps=tuple(
                SequenceTransformerZeroTwoBusSnapshot(
                    transformer_id=str(item.transformer_id),
                    hv_bus_id=str(item.hv_bus_id), lv_bus_id=str(item.lv_bus_id),
                    hv_bus_index=int(item.hv_bus_index), lv_bus_index=int(item.lv_bus_index),
                    hv_terminal_role=str(item.hv_terminal_role), lv_terminal_role=str(item.lv_terminal_role),
                    y_hh_pu=complex(item.y_hh_pu), y_hl_pu=complex(item.y_hl_pu), y_ll_pu=complex(item.y_ll_pu),
                    hv_neutral_3zn_ohm=complex(item.hv_neutral_3zn_ohm),
                    lv_neutral_3zn_ohm=complex(item.lv_neutral_3zn_ohm),
                    lv_neutral_3zn_hv_referred_ohm=complex(item.lv_neutral_3zn_hv_referred_ohm),
                    base_mva=float(item.base_mva), test_mva_base=float(item.test_data.test_mva_base), hv_base_voltage_kv=float(item.hv_base_voltage_kv),
                    lv_base_voltage_kv=float(item.lv_base_voltage_kv),
                    test_hv_open_circuit_z0_ohm=complex(item.test_data.hv_open_circuit_z0_ohm),
                    test_lv_open_circuit_z0_hv_referred_ohm=complex(item.test_data.lv_open_circuit_z0_hv_referred_ohm),
                    test_hv_short_circuit_z0_ohm=complex(item.test_data.hv_short_circuit_z0_ohm),
                    test_source_reference=str(item.test_data.source_reference),
                    core_construction=str(getattr(item.core_construction, "value", item.core_construction)),
                    zero_sequence_test_basis=str(getattr(item.zero_sequence_test_basis, "value", item.zero_sequence_test_basis)),
                )
                for item in getattr(sequence_network, "transformer_zero_sequence_two_bus_stamps", ())
            ),
            transformer_zero_shunts=tuple(
                SequenceTransformerZeroShuntSnapshot(
                    transformer_id=str(item.transformer_id),
                    bus_id=str(item.bus_id),
                    bus_index=tuple(str(value) for value in bus_ids).index(str(item.bus_id)),
                    terminal_role=str(item.terminal_role).strip().upper(),
                    grounded_winding_side=str(item.grounded_winding_side).strip().upper(),
                    impedance_pu=complex(item.impedance_pu),
                    transformer_z0_ohm=complex(item.transformer_z0_ohm),
                    neutral_3zn_ohm=complex(item.neutral_3zn_ohm),
                    total_impedance_ohm=complex(item.total_impedance_ohm),
                    base_mva=float(item.base_mva),
                    base_voltage_kv=float(item.base_voltage_kv),
                    core_construction=str(getattr(item.core_construction, "value", item.core_construction)),
                    zero_sequence_test_basis=str(getattr(item.zero_sequence_test_basis, "value", item.zero_sequence_test_basis)),
                    test_energized_winding=str(getattr(item.test_configuration.energized_winding, "value", item.test_configuration.energized_winding)),
                    test_other_winding_condition=str(getattr(item.test_configuration.other_winding_condition, "value", item.test_configuration.other_winding_condition)),
                    test_neutral_return_included=item.test_configuration.neutral_return_included,
                )
                for item in getattr(sequence_network, "transformer_zero_sequence_shunts", ())
            ),
        )

    @staticmethod
    def _normalize_sequence(sequence: str) -> str:
        aliases = {
            "positive": "positive", "z1": "positive", "1": "positive",
            "negative": "negative", "z2": "negative", "2": "negative",
            "zero": "zero", "z0": "zero", "0": "zero",
        }
        if not isinstance(sequence, str):
            raise TypeError("sequence must be a string.")
        key = sequence.strip().lower()
        if key not in aliases:
            raise ValueError("Invalid sequence. Expected 'positive', 'negative', or 'zero'.")
        return aliases[key]

    def get_impedance(self, element_id: Any, sequence: str) -> complex:
        sequence = self._normalize_sequence(sequence)
        data = getattr(self, sequence)
        if element_id not in data:
            raise KeyError(f"No {sequence}-sequence impedance registered for element {element_id!r}.")
        value = data[element_id]
        if value is None:
            raise ValueError(f"Zero-sequence impedance is unavailable for element {element_id!r}.")
        return complex(value)

    def total_impedance(self, elements, sequence: str = "positive") -> complex:
        """Return the legacy series equivalent from frozen element data."""
        total = complex(0.0, 0.0)
        for element_id in elements:
            total += self.get_impedance(element_id, sequence)
        return total

    def get_matrix(self, sequence: str) -> np.ndarray:
        """Return a defensive numerical copy of a frozen sequence matrix."""
        sequence = self._normalize_sequence(sequence)
        matrix = getattr(self, f"{sequence}_matrix")
        if matrix is None:
            raise ValueError(f"{sequence.capitalize()}-sequence impedance matrix has not been configured.")
        return _matrix_from_snapshot(matrix)

    def has_matrix(self, sequence: str) -> bool:
        return getattr(self, f"{self._normalize_sequence(sequence)}_matrix") is not None

    def is_bus_available(self, sequence: str, bus_index: int) -> bool:
        normalized = self._normalize_sequence(sequence)
        if isinstance(bus_index, bool) or not isinstance(bus_index, (int, np.integer)):
            raise TypeError("Bus index must be an integer.")
        index = int(bus_index)
        if self.bus_ids and not 0 <= index < len(self.bus_ids):
            raise IndexError("Bus index is outside bus_ids.")
        return index not in self.unavailable_bus_indices.get(normalized, ())

    def get_driving_point_impedance(self, sequence: str, bus_index: int) -> complex:
        matrix = self.get_matrix(sequence)
        if isinstance(bus_index, bool) or not isinstance(bus_index, (int, np.integer)):
            raise TypeError("Bus index must be an integer.")
        index = int(bus_index)
        if not 0 <= index < matrix.shape[0]:
            raise IndexError(f"Bus index {index} is outside the valid range 0 to {matrix.shape[0] - 1}.")
        return complex(matrix[index, index])

    def get_transfer_impedance(self, sequence: str, from_bus: int, to_bus: int) -> complex:
        matrix = self.get_matrix(sequence)
        for name, index in (("from_bus", from_bus), ("to_bus", to_bus)):
            if isinstance(index, bool) or not isinstance(index, (int, np.integer)):
                raise TypeError(f"{name} must be an integer.")
            if not 0 <= int(index) < matrix.shape[0]:
                raise IndexError(f"{name} index is outside the valid matrix range.")
        return complex(matrix[int(from_bus), int(to_bus)])


__all__ = [
    "SequenceBranchSnapshot",
    "SequenceSourceSnapshot",
    "SequenceTransformerZeroShuntSnapshot",
    "SequenceNetworkSnapshot",
]
