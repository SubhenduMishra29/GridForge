"""Immutable sequence-network data prepared for short-circuit execution.

The snapshot is deliberately detached from ``SequenceNetwork``. It contains
only defensive, immutable copies of sequence element impedances, sequence
impedance matrices, and optional prepared topology/source metadata required for
engineering current interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

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

    def __post_init__(self) -> None:
        for name in ("branch_id", "from_bus_id", "to_bus_id", "equipment_type"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty engineering identifier.")
        for name in ("from_bus_index", "to_bus_index"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer.")
        if self.from_bus_id == self.to_bus_id or self.from_bus_index == self.to_bus_index:
            raise ValueError("A branch snapshot requires distinct endpoints.")
        for name in ("positive", "negative", "zero"):
            value = getattr(self, name)
            if value is not None:
                value = complex(value)
                if not np.isfinite(value.real) or not np.isfinite(value.imag) or abs(value) == 0.0:
                    raise ValueError(f"{name}-sequence branch impedance must be finite and non-zero.")
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
    "SequenceNetworkSnapshot",
]
