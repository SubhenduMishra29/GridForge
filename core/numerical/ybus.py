# ============================================================
# File: core/numerical/ybus.py
# GridForge V2 — Numerical Y-Bus Representation
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Numerical Y-Bus Representation
==============================================

The Numerical layer owns the mathematical Y-bus representation
derived from the authoritative electrical Network.

Ownership
---------

Network owns:
    - canonical electrical models
    - registry/membership
    - topology
    - terminal relationships
    - authoritative BusIndex

Numerical owns:
    - derived Y-bus representation
    - numerical matrix construction

Solver owns:
    - numerical solution procedures

YBusBuilder is a read-only consumer of the Network.

It MUST NOT:
    - rebuild the Network BusIndex
    - mutate Network topology
    - register/remove equipment
    - modify canonical model objects
    - perform power-flow calculations
    - perform short-circuit calculations
    - perform engineering validation
    - perform GUI/application operations

Before YBusBuilder.build() is called, Network.index MUST already
be valid and correspond to the current Network bus membership.

Electrical conventions
----------------------

Line:

    Z = R + jX
    Y = 1 / Z
    Ysh,total = jB
    Ysh,end = jB / 2

Transformer:

    Z = R + jX
    Y = 1 / Z

    a = tap * exp(j * shift)

    Yii += Y / |a|²
    Yij -= Y / conj(a)
    Yji -= Y / a
    Yjj += Y

Transformer shunt susceptance, when explicitly supplied by the
model, is treated as total susceptance and divided equally between
the two terminals.

Shunt:

    Ysh = G + jB

The resulting YBus is a derived numerical artifact. It is not
stored as authoritative state on Network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix

from core.network.endpoint import resolve_terminal_bus


# ============================================================
# Y-BUS REPRESENTATION
# ============================================================


@dataclass(frozen=True)
class YBus:
    """
    Immutable Y-bus numerical representation.

    Parameters
    ----------
    matrix:
        Complex sparse CSR nodal-admittance matrix.

    bus_ids:
        Bus identifiers in matrix row/column order.

    revision:
        Optional Network revision associated with this derived
        numerical representation.
    """

    matrix: csr_matrix
    bus_ids: tuple[str, ...]
    revision: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate the structural numerical representation."""

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

    # ========================================================
    # BASIC ACCESS
    # ========================================================

    @property
    def shape(self) -> tuple[int, int]:
        """Return the matrix shape."""

        return self.matrix.shape

    @property
    def size(self) -> int:
        """Return the total matrix element count."""

        return self.matrix.size

    @property
    def ndim(self) -> int:
        """Return the matrix dimensionality."""

        return self.matrix.ndim

    @property
    def nnz(self) -> int:
        """Return the number of stored non-zero entries."""

        return self.matrix.nnz

    @property
    def data(self) -> np.ndarray:
        """Return the stored complex matrix data."""

        return self.matrix.data

    # ========================================================
    # BUS INDEXING
    # ========================================================

    def index_of(self, bus_id: str) -> int:
        """
        Return the numerical matrix index for a bus identifier.
        """

        try:
            return self.bus_ids.index(bus_id)

        except ValueError as exc:
            raise KeyError(
                f"Bus '{bus_id}' is not present in this YBus."
            ) from exc

    # ========================================================
    # MATRIX ACCESS
    # ========================================================

    def __getitem__(self, key: Any) -> Any:
        """Delegate indexing to the underlying CSR matrix."""

        return self.matrix[key]

    def tocsr(self) -> csr_matrix:
        """Return the underlying CSR matrix."""

        return self.matrix

    def toarray(self) -> np.ndarray:
        """Return a dense NumPy representation."""

        return self.matrix.toarray()

    def todense(self) -> np.ndarray:
        """Return a dense NumPy representation."""

        return self.matrix.toarray()

    def copy(self) -> "YBus":
        """Return an independent copy of the YBus artifact."""

        return YBus(
            matrix=self.matrix.copy(),
            bus_ids=self.bus_ids,
            revision=self.revision,
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(self) -> bool:
        """Validate the YBus representation."""

        self.__post_init__()

        return True

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """Return a concise developer-facing representation."""

        return (
            f"YBus("
            f"buses={len(self.bus_ids)}, "
            f"nnz={self.nnz}, "
            f"revision={self.revision}"
            f")"
        )


# ============================================================
# Y-BUS BUILDER
# ============================================================


class YBusBuilder:
    """
    Construct a Numerical YBus from an authoritative Network.

    BusIndex contract
    -----------------

    The Network owns the canonical BusIndex.

    YBusBuilder requires that index to already be valid.

    YBusBuilder NEVER calls:

        index.ensure()
        index.rebuild()
        index.invalidate()

    Consequently, constructing a YBus does not mutate Network
    numerical-index state.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self, network: Any) -> None:
        """
        Create a YBusBuilder for an authoritative Network.
        """

        if network is None:
            raise ValueError(
                "YBusBuilder requires a Network."
            )

        self.network = network

    # ========================================================
    # PUBLIC BUILD API
    # ========================================================

    def build(self) -> YBus:
        """
        Build and return a Numerical YBus.

        The Network BusIndex must already be valid.

        The canonical Network and its BusIndex are never modified.
        """

        buses = tuple(
            self.network.buses
        )

        if not buses:
            raise ValueError(
                "Cannot build Y-bus for a Network with no buses."
            )

        self._require_valid_network_index(
            buses
        )

        n = len(buses)

        matrix = lil_matrix(
            (n, n),
            dtype=np.complex128,
        )

        # ----------------------------------------------------
        # LINES
        # ----------------------------------------------------

        for line in self.network.lines:
            if not self._is_in_service(line):
                continue

            self._stamp_line(
                matrix,
                line,
            )

        # ----------------------------------------------------
        # TRANSFORMERS
        # ----------------------------------------------------

        for transformer in self.network.transformers:
            if not self._is_in_service(transformer):
                continue

            self._stamp_transformer(
                matrix,
                transformer,
            )

        # ----------------------------------------------------
        # SHUNTS
        # ----------------------------------------------------

        for shunt in self.network.shunts:
            if not self._is_in_service(shunt):
                continue

            self._stamp_shunt(
                matrix,
                shunt,
            )

        csr = matrix.tocsr()

        bus_ids = tuple(
            str(bus.id)
            for bus in buses
        )

        revision = getattr(
            self.network,
            "revision",
            None,
        )

        result = YBus(
            matrix=csr,
            bus_ids=bus_ids,
            revision=revision,
        )

        result.validate()

        return result

    # ========================================================
    # INDEX CONTRACT
    # ========================================================

    def _require_valid_network_index(
        self,
        buses: tuple[Any, ...],
    ) -> None:
        """
        Require an already-prepared authoritative Network BusIndex.

        This method is deliberately read-only.

        It does not call ensure(), rebuild(), or invalidate().
        """

        index = getattr(
            self.network,
            "index",
            None,
        )

        if index is None:
            raise AttributeError(
                "Network must provide an authoritative BusIndex."
            )

        valid = getattr(
            index,
            "valid",
            None,
        )

        if valid is not True:
            raise RuntimeError(
                "Network BusIndex is invalid or not prepared. "
                "Rebuild the Network BusIndex before constructing YBus."
            )

        for bus in buses:
            bus_id = getattr(
                bus,
                "id",
                None,
            )

            if bus_id is None:
                raise ValueError(
                    "Every Network Bus must provide an id."
                )

            try:
                value = index.get(
                    bus_id
                )

            except (
                KeyError,
                AttributeError,
                TypeError,
                ValueError,
            ) as exc:
                raise RuntimeError(
                    f"Network BusIndex does not contain "
                    f"Bus '{bus_id}'. "
                    "Rebuild the Network BusIndex before "
                    "constructing YBus."
                ) from exc

            if not isinstance(value, int):
                raise TypeError(
                    f"Network BusIndex returned a non-integer "
                    f"index for Bus '{bus_id}'."
                )

            if value < 0 or value >= len(buses):
                raise ValueError(
                    f"Network BusIndex returned invalid index "
                    f"{value} for Bus '{bus_id}'."
                )

    # ========================================================
    # LINE STAMPING
    # ========================================================

    def _stamp_line(
        self,
        matrix: lil_matrix,
        line: Any,
    ) -> None:
        """
        Stamp a canonical Line using its explicit electrical model.
        """

        from_bus = self._resolve_branch_bus(
            line,
            "from_terminal",
        )

        to_bus = self._resolve_branch_bus(
            line,
            "to_terminal",
        )

        i = self._bus_index(
            from_bus,
        )

        j = self._bus_index(
            to_bus,
        )

        try:
            y_series = complex(
                line.series_admittance
            )

        except (
            AttributeError,
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"Line '{getattr(line, 'id', line)}' "
                "does not provide a valid series_admittance."
            ) from exc

        b_total = float(
            getattr(
                line,
                "total_shunt_susceptance",
                0.0,
            )
        )

        if not np.isfinite(b_total):
            raise ValueError(
                f"Line '{getattr(line, 'id', line)}' "
                "has invalid total shunt susceptance."
            )

        y_shunt_half = (
            1j * b_total / 2.0
        )

        matrix[i, i] += (
            y_series
            + y_shunt_half
        )

        matrix[j, j] += (
            y_series
            + y_shunt_half
        )

        matrix[i, j] -= y_series
        matrix[j, i] -= y_series

    # ========================================================
    # TRANSFORMER STAMPING
    # ========================================================

    def _stamp_transformer(
        self,
        matrix: lil_matrix,
        transformer: Any,
    ) -> None:
        """
        Stamp a canonical two-winding Transformer.
        """

        from_bus = self._resolve_branch_bus(
            transformer,
            "from_terminal",
        )

        to_bus = self._resolve_branch_bus(
            transformer,
            "to_terminal",
        )

        i = self._bus_index(
            from_bus,
        )

        j = self._bus_index(
            to_bus,
        )

        try:
            y_series = complex(
                transformer.series_admittance
            )

        except (
            AttributeError,
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"Transformer "
                f"'{getattr(transformer, 'id', transformer)}' "
                "does not provide a valid series_admittance."
            ) from exc

        tap = float(
            transformer.tap
        )

        shift = float(
            transformer.shift
        )

        if not np.isfinite(tap) or tap <= 0.0:
            raise ValueError(
                f"Transformer "
                f"'{getattr(transformer, 'id', transformer)}' "
                "has an invalid tap ratio."
            )

        if not np.isfinite(shift):
            raise ValueError(
                f"Transformer "
                f"'{getattr(transformer, 'id', transformer)}' "
                "has an invalid phase shift."
            )

        complex_tap = (
            tap
            * np.exp(
                1j * shift
            )
        )

        matrix[i, i] += (
            y_series
            / abs(complex_tap) ** 2
        )

        matrix[i, j] -= (
            y_series
            / np.conj(complex_tap)
        )

        matrix[j, i] -= (
            y_series
            / complex_tap
        )

        matrix[j, j] += y_series

        # ----------------------------------------------------
        # Optional total transformer shunt susceptance.
        # ----------------------------------------------------

        b_total = float(
            getattr(
                transformer,
                "b_pu",
                0.0,
            )
        )

        if not np.isfinite(b_total):
            raise ValueError(
                f"Transformer "
                f"'{getattr(transformer, 'id', transformer)}' "
                "has invalid shunt susceptance."
            )

        y_shunt_half = (
            1j * b_total / 2.0
        )

        matrix[i, i] += y_shunt_half
        matrix[j, j] += y_shunt_half

    # ========================================================
    # SHUNT STAMPING
    # ========================================================

    def _stamp_shunt(
        self,
        matrix: lil_matrix,
        shunt: Any,
    ) -> None:
        """
        Stamp a canonical Shunt.

        The audited Shunt contract is:

            g_pu
            b_pu

        with:

            Y = G + jB
        """

        bus = self._resolve_shunt_bus(
            shunt
        )

        index = self._bus_index(
            bus
        )

        conductance = float(
            getattr(
                shunt,
                "g_pu",
                0.0,
            )
        )

        susceptance = float(
            getattr(
                shunt,
                "b_pu",
                0.0,
            )
        )

        if not np.isfinite(conductance):
            raise ValueError(
                f"Shunt "
                f"'{getattr(shunt, 'id', shunt)}' "
                "has invalid conductance."
            )

        if not np.isfinite(susceptance):
            raise ValueError(
                f"Shunt "
                f"'{getattr(shunt, 'id', shunt)}' "
                "has invalid susceptance."
            )

        matrix[index, index] += complex(
            conductance,
            susceptance,
        )

    # ========================================================
    # TERMINAL RESOLUTION
    # ========================================================

    def _resolve_branch_bus(
        self,
        element: Any,
        terminal_name: str,
    ) -> Any:
        """
        Resolve a branch terminal to its canonical Network Bus.

        Terminal interpretation remains a Network responsibility.
        """

        terminal = getattr(
            element,
            terminal_name,
            None,
        )

        if terminal is None:
            raise ValueError(
                f"{type(element).__name__} "
                f"'{getattr(element, 'id', element)}' "
                f"does not provide '{terminal_name}'."
            )

        bus = resolve_terminal_bus(
            terminal
        )

        self._require_registered_bus(
            element,
            terminal_name,
            bus,
        )

        return bus

    def _resolve_shunt_bus(
        self,
        shunt: Any,
    ) -> Any:
        """
        Resolve a Shunt terminal to its canonical Network Bus.
        """

        terminal = getattr(
            shunt,
            "terminal",
            None,
        )

        if terminal is None:
            raise ValueError(
                f"Shunt "
                f"'{getattr(shunt, 'id', shunt)}' "
                "does not provide a terminal."
            )

        bus = resolve_terminal_bus(
            terminal
        )

        self._require_registered_bus(
            shunt,
            "terminal",
            bus,
        )

        return bus

    def _require_registered_bus(
        self,
        element: Any,
        terminal_name: str,
        bus: Any,
    ) -> None:
        """
        Ensure the resolved Bus belongs to this Network.

        This is a consistency check only; it does not mutate Network.
        """

        if bus is None:
            raise ValueError(
                f"{type(element).__name__} "
                f"'{getattr(element, 'id', element)}' "
                f"terminal '{terminal_name}' "
                "does not resolve to a Bus."
            )

        network_buses = tuple(
            self.network.buses
        )

        if bus not in network_buses:
            raise ValueError(
                f"{type(element).__name__} "
                f"'{getattr(element, 'id', element)}' "
                f"terminal '{terminal_name}' resolves to "
                f"Bus '{getattr(bus, 'id', bus)}', "
                "which is not registered on this Network."
            )

    # ========================================================
    # BUS INDEX ACCESS
    # ========================================================

    def _bus_index(
        self,
        bus: Any,
    ) -> int:
        """
        Read an already-prepared Network BusIndex.

        No index mutation is permitted here.
        """

        index = getattr(
            self.network,
            "index",
            None,
        )

        if index is None:
            raise AttributeError(
                "Network must provide an authoritative BusIndex."
            )

        valid = getattr(
            index,
            "valid",
            None,
        )

        if valid is not True:
            raise RuntimeError(
                "Network BusIndex is invalid or not prepared."
            )

        bus_id = getattr(
            bus,
            "id",
            None,
        )

        if bus_id is None:
            raise ValueError(
                "Bus must provide an id."
            )

        try:
            value = index.get(
                bus_id
            )

        except (
            KeyError,
            AttributeError,
            TypeError,
            ValueError,
        ) as exc:
            raise KeyError(
                f"Bus '{bus_id}' is not present "
                "in the valid Network BusIndex."
            ) from exc

        if not isinstance(value, int):
            raise TypeError(
                f"Network BusIndex returned a non-integer "
                f"index for Bus '{bus_id}'."
            )

        if value < 0:
            raise ValueError(
                f"Bus '{bus_id}' has a negative matrix index."
            )

        return value

    # ========================================================
    # SERVICE STATE
    # ========================================================

    @staticmethod
    def _is_in_service(
        element: Any,
    ) -> bool:
        """
        Return whether an element participates in the numerical model.

        Models without an explicit in_service attribute are treated
        as active.
        """

        return bool(
            getattr(
                element,
                "in_service",
                True,
            )
        )

    # ========================================================
    # MATRIX VALIDATION
    # ========================================================

    @staticmethod
    def validate_matrix(
        ybus: Any,
    ) -> None:
        """
        Validate a raw Y-bus CSR matrix.

        This performs structural numerical checks only.
        """

        if ybus is None:
            raise ValueError(
                "Y-bus cannot be None."
            )

        if not isinstance(
            ybus,
            csr_matrix,
        ):
            raise TypeError(
                "Y-bus must be a scipy.sparse.csr_matrix."
            )

        if ybus.ndim != 2:
            raise ValueError(
                "Y-bus must be two-dimensional."
            )

        rows, columns = ybus.shape

        if rows != columns:
            raise ValueError(
                "Y-bus must be square."
            )

        if ybus.dtype.kind != "c":
            raise TypeError(
                "Y-bus must use a complex dtype."
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """Return a concise developer-facing representation."""

        return (
            f"YBusBuilder("
            f"buses={len(self.network.buses)}, "
            f"lines={len(self.network.lines)}, "
            f"transformers={len(self.network.transformers)}, "
            f"shunts={len(self.network.shunts)}"
            f")"
        )


__all__ = [
    "YBus",
    "YBusBuilder",
]
