"""Immutable sequence-network data prepared for short-circuit execution.

The snapshot is deliberately detached from ``SequenceNetwork``.  It contains
only defensive, immutable copies of sequence element impedances and optional
sequence impedance matrices, so numerical execution cannot observe later
mutations of the preparation container.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np


ComplexMatrix = tuple[tuple[complex, ...], ...]


def _freeze_mapping(values: Mapping[Any, complex | None]) -> Mapping[Any, complex | None]:
    return MappingProxyType(dict(values))


def _freeze_matrix(matrix: np.ndarray | None) -> ComplexMatrix | None:
    if matrix is None:
        return None
    array = np.asarray(matrix, dtype=complex)
    return tuple(tuple(complex(value) for value in row) for row in array.tolist())


def _matrix_from_snapshot(matrix: ComplexMatrix) -> np.ndarray:
    return np.asarray(matrix, dtype=complex)


@dataclass(frozen=True, slots=True)
class SequenceNetworkSnapshot:
    """Immutable execution snapshot of a prepared sequence network."""

    positive: Mapping[Any, complex | None]
    negative: Mapping[Any, complex | None]
    zero: Mapping[Any, complex | None]
    positive_matrix: ComplexMatrix | None = None
    negative_matrix: ComplexMatrix | None = None
    zero_matrix: ComplexMatrix | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "positive", _freeze_mapping(self.positive))
        object.__setattr__(self, "negative", _freeze_mapping(self.negative))
        object.__setattr__(self, "zero", _freeze_mapping(self.zero))
        object.__setattr__(self, "positive_matrix", _freeze_matrix(self.positive_matrix))
        object.__setattr__(self, "negative_matrix", _freeze_matrix(self.negative_matrix))
        object.__setattr__(self, "zero_matrix", _freeze_matrix(self.zero_matrix))

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
        data = getattr(self, self._normalize_sequence(sequence))
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
                raise IndexError(f"{name} index {index} is outside the valid matrix range.")
        return complex(matrix[int(from_bus), int(to_bus)])
