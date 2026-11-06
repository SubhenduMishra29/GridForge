"""Numerical Zbus/Thevenin services for prepared short-circuit data."""

from __future__ import annotations

from typing import Any

import numpy as np


class ImpedanceMatrix:
    """Compute Zbus from a prepared numerical Ybus matrix.

    No Network, Bus, or other Core object is retained. ``bus_ids`` is copied
    only as immutable numerical index metadata.
    """

    def __init__(self, ybus: Any, bus_ids: tuple[Any, ...] | list[Any]) -> None:
        self.bus_ids = tuple(bus_ids)
        if not self.bus_ids:
            raise ValueError("bus_ids cannot be empty.")
        self.Zbus: np.ndarray | None = None
        self._ybus_shape: tuple[int, int] | None = None
        self._ybus = self._to_dense_matrix(ybus, "Ybus")
        if self._ybus.shape != (len(self.bus_ids), len(self.bus_ids)):
            raise ValueError("Ybus dimension does not match bus_ids.")

    @staticmethod
    def _to_dense_matrix(matrix: Any, name: str) -> np.ndarray:
        if matrix is None:
            raise ValueError(f"{name} cannot be None.")
        try:
            result = np.asarray(matrix.toarray() if hasattr(matrix, "toarray") else matrix, dtype=complex)
        except Exception as exc:
            raise ValueError(f"{name} could not be converted to a numerical matrix.") from exc
        if result.ndim != 2 or result.shape[0] != result.shape[1]:
            raise ValueError(f"{name} must be a square two-dimensional matrix.")
        if not np.all(np.isfinite(result.real)) or not np.all(np.isfinite(result.imag)):
            raise ValueError(f"{name} contains NaN or infinite values.")
        return result.copy()

    def build(self) -> np.ndarray:
        try:
            Zbus = np.linalg.inv(self._ybus)
        except np.linalg.LinAlgError as exc:
            raise RuntimeError("Ybus is singular. Cannot calculate Zbus.") from exc
        except Exception as exc:
            raise RuntimeError(f"Unexpected Zbus calculation failure: {exc}") from exc
        Zbus = np.asarray(Zbus, dtype=complex)
        if not np.all(np.isfinite(Zbus.real)) or not np.all(np.isfinite(Zbus.imag)):
            raise RuntimeError("Zbus calculation produced NaN or infinite values.")
        self.Zbus = Zbus
        self._ybus_shape = Zbus.shape
        return Zbus.copy()

    def _ensure_built(self) -> np.ndarray:
        return self.Zbus if self.Zbus is not None else self.build()

    def _validate_bus_index(self, bus_index: int, name: str = "bus_index") -> int:
        if isinstance(bus_index, bool) or not isinstance(bus_index, (int, np.integer)):
            raise TypeError(f"{name} must be an integer.")
        index = int(bus_index)
        if not 0 <= index < len(self.bus_ids):
            raise IndexError(f"{name} out of range: {index}. Valid range is 0 to {len(self.bus_ids) - 1}.")
        return index

    def get_thevenin_impedance(self, bus_index: int) -> complex:
        index = self._validate_bus_index(bus_index)
        return complex(self._ensure_built()[index, index])

    def get_transfer_impedance(self, from_bus: int, to_bus: int) -> complex:
        i = self._validate_bus_index(from_bus, "from_bus")
        j = self._validate_bus_index(to_bus, "to_bus")
        return complex(self._ensure_built()[i, j])

    def get_zbus(self, copy: bool = True) -> np.ndarray:
        Zbus = self._ensure_built()
        return Zbus.copy() if copy else Zbus

    def invalidate(self) -> None:
        self.Zbus = None
        self._ybus_shape = None

    def summary(self) -> dict:
        return {
            "component": "ImpedanceMatrix",
            "version": "2.0",
            "status": "BUILT" if self.Zbus is not None else "NOT_BUILT",
            "size": None if self.Zbus is None else self.Zbus.shape,
            "dtype": None if self.Zbus is None else str(self.Zbus.dtype),
            "backend": "numpy",
            "network_ybus_shape": self._ybus_shape,
        }

    def __repr__(self) -> str:
        status = "built" if self.Zbus is not None else "not_built"
        return f"ImpedanceMatrix(buses={len(self.bus_ids)}, status={status})"


__all__ = ["ImpedanceMatrix"]
