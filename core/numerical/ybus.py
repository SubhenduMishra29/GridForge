# ============================================================
# File: core/numerical/ybus.py
# GridForge V2 — Numerical Y-Bus
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Numerical Y-bus construction.

Location:
    core/numerical/ybus.py

Architecture:
    Model
      ↓
    Network
      ↓
    Numerical
      ├── consumes authoritative BusIndex
      └── constructs derived Y-bus
      ↓
    Solver

Ownership:
    Network owns:
        - canonical electrical models;
        - equipment membership;
        - terminal relationships;
        - topology;
        - authoritative BusIndex.

    Numerical owns:
        - numerical matrix construction;
        - derived Y-bus representation.

    Solver owns:
        - numerical solution algorithms.

YBusBuilder is a read-only consumer of Network.

The builder requires Network.index to already be valid.
It never rebuilds, invalidates, or mutates Network state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix

from core.network.endpoint import resolve_terminal_bus


@dataclass(frozen=True)
class YBus:
    """
    Immutable numerical Y-bus representation.

    The matrix ordering is defined by the authoritative Network
    BusIndex used during construction.
    """

    matrix: csr_matrix
    bus_ids: tuple[str, ...]
    topology_revision: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.matrix, csr_matrix):
            raise TypeError(
                "YBus.matrix must be a scipy.sparse.csr_matrix."
            )

        if self.matrix.ndim != 2:
            raise ValueError(
                "YBus matrix must be two-dimensional."
            )

        rows, columns = self.matrix.shape

        if rows != columns:
            raise ValueError(
                "YBus matrix must be square."
            )

        if rows != len(self.bus_ids):
            raise ValueError(
                "YBus matrix dimension must match bus_ids length."
            )

        if self.matrix.dtype.kind != "c":
            raise TypeError(
                "YBus matrix must use a complex dtype."
            )

        if len(set(self.bus_ids)) != len(self.bus_ids):
            raise ValueError(
                "YBus bus_ids must be unique."
            )

    @property
    def shape(self) -> tuple[int, int]:
        """Return the Y-bus matrix shape."""
        return self.matrix.shape

    @property
    def nnz(self) -> int:
        """Return the number of stored non-zero values."""
        return self.matrix.nnz

    def index_of(self, bus_id: str) -> int:
        """Return the numerical index of a bus."""
        try:
            return self.bus_ids.index(bus_id)
        except ValueError as exc:
            raise KeyError(
                f"Bus '{bus_id}' is not present in this YBus."
            ) from exc

    def __getitem__(self, key: Any) -> Any:
        """Allow matrix-style indexing."""
        return self.matrix[key]

    def tocsr(self) -> csr_matrix:
        """Return the sparse CSR matrix."""
        return self.matrix

    def toarray(self) -> np.ndarray:
        """Return a dense matrix representation."""
        return self.matrix.toarray()

    def copy(self) -> "YBus":
        """Return an independent copy."""
        return YBus(
            matrix=self.matrix.copy(),
            bus_ids=self.bus_ids,
            topology_revision=self.topology_revision,
        )


class YBusBuilder:
    """
    Construct a YBus from an authoritative Network.

    The Network remains the source of electrical membership,
    connectivity, and bus ordering.

    This builder performs read-only numerical interpretation.
    """

    def __init__(self, network: Any) -> None:
        if network is None:
            raise ValueError(
                "YBusBuilder requires a Network."
            )

        self._network = network

    def build(self) -> YBus:
        """
        Build YBus from the current Network state.

        The Network is never mutated.
        """

        buses = tuple(self._network.buses)

        if not buses:
            raise ValueError(
                "Cannot build Y-bus for a Network with no buses."
            )

        self._require_valid_index(buses)

        matrix = lil_matrix(
            (len(buses), len(buses)),
            dtype=np.complex128,
        )

        self._stamp_branches(
            matrix=matrix,
            branches=getattr(self._network, "lines", ()),
            label="Line",
        )

        self._stamp_branches(
            matrix=matrix,
            branches=getattr(self._network, "cables", ()),
            label="Cable",
        )

        self._stamp_transformers(
            matrix=matrix,
            transformers=getattr(
                self._network,
                "transformers",
                (),
            ),
        )

        self._stamp_shunts(
            matrix=matrix,
            shunts=getattr(
                self._network,
                "shunts",
                (),
            ),
        )

        return YBus(
            matrix=matrix.tocsr(),
            bus_ids=tuple(
                str(bus.id)
                for bus in buses
            ),
            topology_revision=getattr(
                self._network,
                "topology_revision",
                None,
            ),
        )

    # ============================================================
    # NETWORK INDEX CONTRACT
    # ============================================================

    def _require_valid_index(
        self,
        buses: tuple[Any, ...],
    ) -> None:
        """
        Validate the authoritative Network BusIndex.

        This method validates only. It never rebuilds the index.
        """

        index = getattr(
            self._network,
            "index",
            None,
        )

        if index is None:
            raise AttributeError(
                "Network must provide an authoritative BusIndex."
            )

        if getattr(index, "valid", False) is not True:
            raise RuntimeError(
                "Network BusIndex is invalid or not prepared."
            )

        mapping = getattr(
            index,
            "mapping",
            None,
        )

        if mapping is None:
            raise AttributeError(
                "Network BusIndex must provide a mapping."
            )

        expected_ids = {
            bus.id
            for bus in buses
        }

        if set(mapping) != expected_ids:
            raise RuntimeError(
                "Network BusIndex does not match "
                "current Network bus membership."
            )

        expected_positions = set(range(len(buses)))

        if set(mapping.values()) != expected_positions:
            raise RuntimeError(
                "Network BusIndex does not provide "
                "a complete numerical ordering."
            )

    def _bus_index(
        self,
        bus: Any,
    ) -> int:
        """Return the authoritative numerical index of a Bus."""

        bus_id = getattr(bus, "id", None)

        if bus_id is None:
            raise ValueError(
                "Resolved endpoint does not provide a bus id."
            )

        mapping = self._network.index.mapping

        try:
            return mapping[bus_id]
        except KeyError as exc:
            raise ValueError(
                f"Bus '{bus_id}' is not present "
                "in the Network BusIndex."
            ) from exc

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @staticmethod
    def _is_in_service(
        element: Any,
    ) -> bool:
        """Return whether an electrical element is in service."""

        return bool(
            getattr(
                element,
                "in_service",
                True,
            )
        )

    # ============================================================
    # ENDPOINT RESOLUTION
    # ============================================================

    @staticmethod
    def _resolve_branch_bus(
        branch: Any,
        terminal_name: str,
    ) -> Any:
        """
        Resolve a branch terminal to its authoritative Bus.
        """

        try:
            terminal = getattr(
                branch,
                terminal_name,
            )
        except AttributeError as exc:
            raise ValueError(
                f"Element '{getattr(branch, 'id', branch)}' "
                f"does not provide '{terminal_name}'."
            ) from exc

        try:
            bus = resolve_terminal_bus(terminal)
        except Exception as exc:
            raise ValueError(
                f"Element '{getattr(branch, 'id', branch)}' "
                f"has an unresolved '{terminal_name}'."
            ) from exc

        if bus is None:
            raise ValueError(
                f"Element '{getattr(branch, 'id', branch)}' "
                f"has an unresolved '{terminal_name}'."
            )

        return bus

    @staticmethod
    def _resolve_shunt_bus(
        shunt: Any,
    ) -> Any:
        """
        Resolve the Shunt's authoritative Bus.

        Frozen model contract:

            shunt.terminal
                ↓
            resolve_terminal_bus()
                ↓
            Bus
        """

        try:
            terminal = shunt.terminal
            bus = resolve_terminal_bus(terminal)
        except Exception as exc:
            raise ValueError(
                f"Shunt '{getattr(shunt, 'id', shunt)}' "
                "does not resolve to a Bus."
            ) from exc

        if bus is None:
            raise ValueError(
                f"Shunt '{getattr(shunt, 'id', shunt)}' "
                "does not resolve to a Bus."
            )

        return bus

    # ============================================================
    # STANDARD BRANCH STAMPING
    # ============================================================

    def _stamp_branches(
        self,
        matrix: lil_matrix,
        branches: Any,
        label: str,
    ) -> None:
        """
        Stamp all in-service standard two-terminal branches.

        Used for Lines and Cables.
        """

        for branch in branches:
            if not self._is_in_service(branch):
                continue

            self._stamp_branch(
                matrix=matrix,
                branch=branch,
                label=label,
            )

    def _stamp_branch(
        self,
        matrix: lil_matrix,
        branch: Any,
        label: str,
    ) -> None:
        """
        Stamp a standard pi-equivalent branch.

        Required model contract:

            from_terminal
            to_terminal
            series_admittance
            b
        """

        from_bus = self._resolve_branch_bus(
            branch,
            "from_terminal",
        )

        to_bus = self._resolve_branch_bus(
            branch,
            "to_terminal",
        )

        i = self._bus_index(from_bus)
        j = self._bus_index(to_bus)

        y_series = self._finite_complex(
            getattr(
                branch,
                "series_admittance",
            ),
            branch,
            label,
            "series_admittance",
        )

        b_total = self._finite_float(
            getattr(
                branch,
                "b",
                0.0,
            ),
            branch,
            label,
            "b",
        )

        y_shunt_half = (
            1j * b_total / 2.0
        )

        matrix[i, i] += (
            y_series + y_shunt_half
        )
        matrix[j, j] += (
            y_series + y_shunt_half
        )

        matrix[i, j] -= y_series
        matrix[j, i] -= y_series

    # ============================================================
    # TRANSFORMER STAMPING
    # ============================================================

    def _stamp_transformers(
        self,
        matrix: lil_matrix,
        transformers: Any,
    ) -> None:
        """Stamp all in-service transformers."""

        for transformer in transformers:
            if not self._is_in_service(transformer):
                continue

            self._stamp_transformer(
                matrix=matrix,
                transformer=transformer,
            )

    def _stamp_transformer(
        self,
        matrix: lil_matrix,
        transformer: Any,
    ) -> None:
        """
        Stamp an off-nominal transformer.

        Branch contract:

            series_admittance
            b

        Transformer contract:

            tap
            shift
        """

        from_bus = self._resolve_branch_bus(
            transformer,
            "from_terminal",
        )

        to_bus = self._resolve_branch_bus(
            transformer,
            "to_terminal",
        )

        i = self._bus_index(from_bus)
        j = self._bus_index(to_bus)

        y_series = self._finite_complex(
            getattr(
                transformer,
                "series_admittance",
            ),
            transformer,
            "Transformer",
            "series_admittance",
        )

        tap = self._finite_float(
            getattr(
                transformer,
                "tap",
            ),
            transformer,
            "Transformer",
            "tap",
        )

        if tap <= 0.0:
            raise ValueError(
                f"Transformer "
                f"'{getattr(transformer, 'id', transformer)}' "
                "must have a positive tap ratio."
            )

        shift = self._finite_float(
            getattr(
                transformer,
                "shift",
            ),
            transformer,
            "Transformer",
            "shift",
        )

        b_total = self._finite_float(
            getattr(
                transformer,
                "b",
                0.0,
            ),
            transformer,
            "Transformer",
            "b",
        )

        complex_tap = (
            tap * np.exp(1j * shift)
        )

        matrix[i, i] += (
            y_series / abs(complex_tap) ** 2
        )

        matrix[i, j] -= (
            y_series / np.conj(complex_tap)
        )

        matrix[j, i] -= (
            y_series / complex_tap
        )

        matrix[j, j] += y_series

        y_shunt_half = (
            1j * b_total / 2.0
        )

        matrix[i, i] += y_shunt_half
        matrix[j, j] += y_shunt_half

    # ============================================================
    # SHUNT STAMPING
    # ============================================================

    def _stamp_shunts(
        self,
        matrix: lil_matrix,
        shunts: Any,
    ) -> None:
        """Stamp all in-service shunt elements."""

        for shunt in shunts:
            if not self._is_in_service(shunt):
                continue

            self._stamp_shunt(
                matrix=matrix,
                shunt=shunt,
            )

    def _stamp_shunt(
        self,
        matrix: lil_matrix,
        shunt: Any,
    ) -> None:
        """
        Stamp shunt admittance onto its connected Bus.

        Shunt contract:

            g_pu
            b_pu
            terminal
        """

        bus = self._resolve_shunt_bus(shunt)
        index = self._bus_index(bus)

        conductance = self._finite_float(
            getattr(
                shunt,
                "g_pu",
                0.0,
            ),
            shunt,
            "Shunt",
            "g_pu",
        )

        susceptance = self._finite_float(
            getattr(
                shunt,
                "b_pu",
                0.0,
            ),
            shunt,
            "Shunt",
            "b_pu",
        )

        matrix[index, index] += complex(
            conductance,
            susceptance,
        )

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def _finite_float(
        value: Any,
        element: Any,
        label: str,
        parameter: str,
    ) -> float:
        """Convert and validate a finite floating-point value."""

        try:
            result = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{label} "
                f"'{getattr(element, 'id', element)}' "
                f"has invalid '{parameter}'."
            ) from exc

        if not np.isfinite(result):
            raise ValueError(
                f"{label} "
                f"'{getattr(element, 'id', element)}' "
                f"has non-finite '{parameter}'."
            )

        return result

    @staticmethod
    def _finite_complex(
        value: Any,
        element: Any,
        label: str,
        parameter: str,
    ) -> complex:
        """Convert and validate a finite complex value."""

        try:
            result = complex(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{label} "
                f"'{getattr(element, 'id', element)}' "
                f"has invalid '{parameter}'."
            ) from exc

        if (
            not np.isfinite(result.real)
            or not np.isfinite(result.imag)
        ):
            raise ValueError(
                f"{label} "
                f"'{getattr(element, 'id', element)}' "
                f"has non-finite '{parameter}'."
            )

        return result
