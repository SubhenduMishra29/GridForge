# ============================================================
# File: core/numerical/ybus.py
# GridForge V2 — Numerical Y-Bus
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Numerical Y-bus construction.

Location
--------
    core/numerical/ybus.py

Architecture
------------

    Model
      ↓
    Network
      ↓
    Numerical
      ├── authoritative BusIndex consumption
      └── derived Y-bus construction
      ↓
    Solver

Ownership
---------

Network owns:

    - canonical electrical models;
    - equipment membership;
    - terminal relationships;
    - topology;
    - authoritative BusIndex;
    - topology revision.

Numerical owns:

    - derived Y-bus representation;
    - numerical matrix construction.

Solver owns:

    - numerical solution procedures.

YBusBuilder is a read-only consumer of Network.

The builder requires Network.index to already be valid. It never
rebuilds, ensures, invalidates, or otherwise mutates Network state.

Electrical stamping
-------------------

Two-terminal branches:

    Z = R + jX
    Y = 1 / Z

    Yii += Y + jB/2
    Yjj += Y + jB/2
    Yij -= Y
    Yji -= Y

Transformer:

    a = tap * exp(j * shift)

    Yii += Y / |a|² + jB/2
    Yij -= Y / conj(a)
    Yji -= Y / a
    Yjj += Y + jB/2

Shunt:

    Ysh = G + jB

    Yii += Ysh

YBus is a derived numerical artifact. It is never stored on or
mutated into Network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix

from core.network.endpoint import resolve_terminal_bus


@dataclass(frozen=True)
class YBus:
    """Immutable numerical Y-bus representation."""

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
        """Return matrix shape."""
        return self.matrix.shape

    @property
    def nnz(self) -> int:
        """Return number of stored non-zero entries."""
        return self.matrix.nnz

    def index_of(self, bus_id: str) -> int:
        """Return the matrix index for a bus identifier."""
        try:
            return self.bus_ids.index(bus_id)
        except ValueError as exc:
            raise KeyError(
                f"Bus '{bus_id}' is not present in this YBus."
            ) from exc

    def __getitem__(self, key: Any) -> Any:
        return self.matrix[key]

    def tocsr(self) -> csr_matrix:
        """Return the sparse CSR matrix."""
        return self.matrix

    def toarray(self) -> np.ndarray:
        """Return a dense array representation."""
        return self.matrix.toarray()

    def copy(self) -> "YBus":
        """Return an independent YBus copy."""
        return YBus(
            matrix=self.matrix.copy(),
            bus_ids=self.bus_ids,
            topology_revision=self.topology_revision,
        )


class YBusBuilder:
    """
    Construct a YBus from an authoritative Network.

    The Network owns the BusIndex and electrical connectivity.
    This builder consumes that state read-only.
    """

    def __init__(self, network: Any) -> None:
        if network is None:
            raise ValueError(
                "YBusBuilder requires a Network."
            )

        self._network = network

    def build(self) -> YBus:
        """
        Build YBus from the current authoritative Network.

        Network state is never mutated.
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
            matrix,
            getattr(self._network, "lines", ()),
            "Line",
        )

        self._stamp_branches(
            matrix,
            getattr(self._network, "cables", ()),
            "Cable",
        )

        self._stamp_transformers(
            matrix,
            getattr(self._network, "transformers", ()),
        )

        self._stamp_shunts(
            matrix,
            getattr(self._network, "shunts", ()),
        )

        return YBus(
            matrix=matrix.tocsr(),
            bus_ids=tuple(str(bus.id) for bus in buses),
            topology_revision=getattr(
                self._network,
                "topology_revision",
                None,
            ),
        )

    # ============================================================
    # NETWORK CONTRACT
    # ============================================================

    def _require_valid_index(
        self,
        buses: tuple[Any, ...],
    ) -> None:
        """
        Require a prepared authoritative Network BusIndex.

        This method performs validation only.
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
                "Network BusIndex does not correspond to "
                "current Network bus membership."
            )

        expected_positions = set(range(len(buses)))

        if set(mapping.values()) != expected_positions:
            raise RuntimeError(
                "Network BusIndex does not provide a complete "
                "matrix ordering."
            )

    def _bus_index(
        self,
        bus: Any,
    ) -> int:
        """Resolve the authoritative numerical index of a bus."""

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
                f"Bus '{bus_id}' is not present in Network BusIndex."
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

        Endpoint interpretation remains delegated to the Network
        endpoint contract.
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
        """Resolve a shunt connection to its authoritative Bus."""

        for terminal_name in (
            "terminal",
            "bus_terminal",
        ):
            terminal = getattr(
                shunt,
                terminal_name,
                None,
            )

            if terminal is None:
                continue

            try:
                bus = resolve_terminal_bus(terminal)
            except Exception:
                continue

            if bus is not None:
                return bus

        raise ValueError(
            f"Shunt '{getattr(shunt, 'id', shunt)}' "
            "does not resolve to a Bus."
        )

    # ============================================================
    # STANDARD BRANCH STAMPING
    # ============================================================

    def _stamp_branches(
        self,
        matrix: lil_matrix,
        branches: Any,
        label: str,
    ) -> None:
        """Stamp in-service standard two-terminal branches."""

        for branch in branches:
            if not self._is_in_service(branch):
                continue

            self._stamp_branch(
                matrix,
                branch,
                label,
            )

    def _stamp_branch(
        self,
        matrix: lil_matrix,
        branch: Any,
        label: str,
    ) -> None:
        """
        Stamp a standard pi-equivalent branch.

        The Branch contract supplies:

            series_admittance
            b
            from_terminal
            to_terminal
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

        y_shunt_half = 1j * b_total / 2.0

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
                matrix,
                transformer,
            )

    def _stamp_transformer(
        self,
        matrix: lil_matrix,
        transformer: Any,
    ) -> None:
        """
        Stamp an off-nominal transformer.

        Branch supplies:

            series_admittance
            b

        Transformer supplies:

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
                f"Transformer '{getattr(transformer, 'id', transformer)}' "
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
                matrix,
                shunt,
            )

    def _stamp_shunt(
        self,
        matrix: lil_matrix,
        shunt: Any,
    ) -> None:
        """Stamp a shunt admittance onto its connected bus."""

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
                f"{label} '{getattr(element, 'id', element)}' "
                f"has invalid '{parameter}'."
            ) from exc

        if not np.isfinite(result):
            raise ValueError(
                f"{label} '{getattr(element, 'id', element)}' "
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
                f"{label} '{getattr(element, 'id', element)}' "
                f"has invalid '{parameter}'."
            ) from exc

        if (
            not np.isfinite(result.real)
            or not np.isfinite(result.imag)
        ):
            raise ValueError(
                f"{label} '{getattr(element, 'id', element)}' "
                f"has non-finite '{parameter}'."
            )

        return result
