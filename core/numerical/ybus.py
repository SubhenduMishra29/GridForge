# ============================================================
# File: core/numerical/ybus.py
# GridForge V2 — Numerical Y-Bus
# Author: Subhendu Mishra
# ============================================================

"""Numerical Y-bus construction from detached PU preparation data.

Author: Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix


@dataclass(frozen=True)
class YBus:
    """Immutable numerical Y-bus representation."""

    matrix: csr_matrix
    bus_ids: tuple[str, ...]
    topology_revision: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.matrix, csr_matrix):
            raise TypeError("YBus.matrix must be a scipy.sparse.csr_matrix.")
        if self.matrix.ndim != 2:
            raise ValueError("YBus matrix must be two-dimensional.")
        rows, columns = self.matrix.shape
        if rows != columns:
            raise ValueError("YBus matrix must be square.")
        if rows != len(self.bus_ids):
            raise ValueError("YBus matrix dimension must match bus_ids length.")
        if self.matrix.dtype.kind != "c":
            raise TypeError("YBus matrix must use a complex dtype.")
        if len(set(self.bus_ids)) != len(self.bus_ids):
            raise ValueError("YBus bus_ids must be unique.")

    @property
    def shape(self) -> tuple[int, int]:
        return self.matrix.shape

    @property
    def nnz(self) -> int:
        return self.matrix.nnz

    def index_of(self, bus_id: str) -> int:
        try:
            return self.bus_ids.index(bus_id)
        except ValueError as exc:
            raise KeyError(f"Bus '{bus_id}' is not present in this YBus.") from exc

    def __getitem__(self, key: Any) -> Any:
        return self.matrix[key]

    def tocsr(self) -> csr_matrix:
        return self.matrix

    def toarray(self) -> np.ndarray:
        return self.matrix.toarray()

    def copy(self) -> "YBus":
        return YBus(
            matrix=self.matrix.copy(),
            bus_ids=self.bus_ids,
            topology_revision=self.topology_revision,
        )


class YBusBuilder:
    """Build YBus from a detached prepared PU snapshot.

    This class deliberately has no Network dependency. It does not resolve
    terminals, inspect live model objects, select bases, infer units, or
    reinterpret engineering quantities.
    """

    def __init__(self) -> None:
        pass

    def build(self, prepared: Any) -> YBus:
        """Build YBus using only prepared bus IDs and PU branch data."""
        if prepared is None:
            raise ValueError("YBusBuilder requires a prepared Power Flow snapshot.")

        bus_ids = tuple(str(value) for value in getattr(prepared, "bus_ids", ()))
        if not bus_ids:
            raise ValueError("Prepared Power Flow must contain bus_ids.")
        if len(set(bus_ids)) != len(bus_ids):
            raise ValueError("Prepared Power Flow bus_ids must be unique.")

        matrix = lil_matrix((len(bus_ids), len(bus_ids)), dtype=np.complex128)
        index = {bus_id: position for position, bus_id in enumerate(bus_ids)}

        for branch in getattr(prepared, "branches", ()):
            if getattr(branch, "in_service", True):
                self._stamp_branch(matrix, index, branch)

        for transformer in getattr(prepared, "transformers", ()):
            if getattr(transformer, "in_service", True):
                self._stamp_transformer(matrix, index, transformer)

        for shunt in getattr(prepared, "shunts", ()):
            if getattr(shunt, "in_service", True):
                self._stamp_shunt(matrix, index, shunt)

        return YBus(
            matrix=matrix.tocsr(),
            bus_ids=bus_ids,
            topology_revision=getattr(prepared, "topology_revision", None),
        )

    @staticmethod
    def _bus_index(index: dict[str, int], bus_id: str, element: Any) -> int:
        try:
            return index[str(bus_id)]
        except KeyError as exc:
            raise ValueError(
                f"Prepared element '{getattr(element, 'branch_id', getattr(element, 'shunt_id', element))}' "
                f"references unknown bus '{bus_id}'."
            ) from exc

    def _stamp_branch(self, matrix: lil_matrix, index: dict[str, int], branch: Any) -> None:
        i = self._bus_index(index, branch.from_bus_id, branch)
        j = self._bus_index(index, branch.to_bus_id, branch)
        z = complex(float(branch.r_pu), float(branch.x_pu))
        if z == 0.0 + 0.0j:
            raise ValueError(f"Prepared branch '{branch.branch_id}' has zero series impedance.")
        y_series = 1.0 / z
        b_pu = self._finite_float(branch.b_pu, branch, "b_pu")
        y_shunt_half = 1j * b_pu / 2.0
        matrix[i, i] += y_series + y_shunt_half
        matrix[j, j] += y_series + y_shunt_half
        matrix[i, j] -= y_series
        matrix[j, i] -= y_series

    def _stamp_transformer(self, matrix: lil_matrix, index: dict[str, int], transformer: Any) -> None:
        i = self._bus_index(index, transformer.from_bus_id, transformer)
        j = self._bus_index(index, transformer.to_bus_id, transformer)
        z = complex(float(transformer.r_pu), float(transformer.x_pu))
        if z == 0.0 + 0.0j:
            raise ValueError(f"Prepared transformer '{transformer.branch_id}' has zero series impedance.")
        y_series = 1.0 / z
        tap = self._finite_float(transformer.tap, transformer, "tap")
        if tap <= 0.0:
            raise ValueError(f"Prepared transformer '{transformer.branch_id}' has non-positive tap.")
        shift = self._finite_float(transformer.shift, transformer, "shift")
        b_pu = self._finite_float(transformer.b_pu, transformer, "b_pu")
        complex_tap = tap * np.exp(1j * shift)
        matrix[i, i] += y_series / abs(complex_tap) ** 2
        matrix[i, j] -= y_series / np.conj(complex_tap)
        matrix[j, i] -= y_series / complex_tap
        matrix[j, j] += y_series
        y_shunt_half = 1j * b_pu / 2.0
        matrix[i, i] += y_shunt_half
        matrix[j, j] += y_shunt_half

    def _stamp_shunt(self, matrix: lil_matrix, index: dict[str, int], shunt: Any) -> None:
        i = self._bus_index(index, shunt.bus_id, shunt)
        conductance = self._finite_float(shunt.g_pu, shunt, "g_pu")
        susceptance = self._finite_float(shunt.b_pu, shunt, "b_pu")
        matrix[i, i] += complex(conductance, susceptance)

    @staticmethod
    def _finite_float(value: Any, element: Any, parameter: str) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Prepared element '{getattr(element, 'branch_id', getattr(element, 'shunt_id', element))}' "
                f"has invalid '{parameter}'."
            ) from exc
        if not np.isfinite(result):
            raise ValueError(
                f"Prepared element '{getattr(element, 'branch_id', getattr(element, 'shunt_id', element))}' "
                f"has non-finite '{parameter}'."
            )
        return result


__all__ = ["YBus", "YBusBuilder"]
