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

Architecture
------------

    core.model
        canonical physical models
              |
              v
        core.network
        ----------------
        Registry
        Topology
        Endpoint resolution
        BusIndex
              |
              v
        core.numerical
        ----------------
        YBusBuilder
              |
              v
             YBus
              |
              v
        Analysis / Solver

Ownership
---------

    Network
        owns canonical electrical objects, membership, topology,
        endpoint relationships, and deterministic bus identity/indexing.

    Numerical
        owns derived mathematical representations such as YBus.

    Solver
        consumes numerical representations and numerical state.

YBus is NOT authoritative electrical network state.

YBusBuilder is intentionally read-only with respect to the
canonical Network and model objects.

The builder does not:

- register network elements;
- remove network elements;
- modify buses;
- modify branches;
- modify topology;
- assign or redefine bus indices;
- perform power-flow calculations;
- perform short-circuit calculations;
- perform engineering validation;
- manage application commands;
- perform GUI operations.

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

For complex off-nominal tap:

    a = |tap| exp(j*shift)

The standard two-winding transformer contribution is:

    Yii += Y / |a|²
    Yij -= Y / conj(a)
    Yji -= Y / a
    Yjj += Y

Transformer shunt susceptance, when present, is treated as a
total shunt susceptance and split equally between the two sides.

Shunt:

    Ysh = G + jB

Network endpoint resolution remains a Network responsibility.

The numerical layer consumes the resolver; it does not duplicate
terminal-to-bus relationship management.

GridForge V2
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
    Numerical Y-bus representation.

    Parameters
    ----------
    matrix:
        Complex sparse CSR nodal-admittance matrix.

    bus_ids:
        Bus identifiers in exactly the matrix row/column order.

    revision:
        Optional Network revision associated with this derived
        representation.

    Notes
    -----
    YBus is a derived Numerical artifact.

    It does not own or mutate the canonical Network.
    """

    matrix: csr_matrix
    bus_ids: tuple[str, ...]
    revision: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate the numerical representation."""

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
    # BASIC NUMERICAL ACCESS
    # ========================================================

    @property
    def shape(self) -> tuple[int, int]:
        """Return the matrix shape."""

        return self.matrix.shape

    @property
    def size(self) -> int:
        """Return the total number of matrix elements."""

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
        Return the matrix index associated with a bus identifier.

        The mapping is derived from the canonical Network BusIndex
        when the YBus is constructed.
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
        """Delegate matrix indexing to the CSR representation."""

        return self.matrix[key]

    def tocsr(self) -> csr_matrix:
        """
        Return the underlying CSR matrix.

        A CSR matrix is already the canonical stored representation,
        so this operation returns the same matrix object.
        """

        return self.matrix

    def toarray(self) -> np.ndarray:
        """Return a dense NumPy representation."""

        return self.matrix.toarray()

    def todense(self) -> np.ndarray:
        """Return a dense NumPy representation."""

        return self.matrix.toarray()

    def copy(self) -> "YBus":
        """Return an independent copy of the numerical artifact."""

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

    The Network supplies:

    - canonical buses;
    - canonical branches and shunts;
    - terminal relationships;
    - deterministic BusIndex mapping.

    The builder supplies:

    - numerical admittance conversion;
    - matrix stamping;
    - derived YBus construction.

    The builder never stores the YBus on the Network.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        network: Any,
    ) -> None:

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

        The canonical Network remains unchanged.

        Returns
        -------
        YBus
            Derived complex sparse nodal-admittance representation.
        """

        buses = tuple(
            self.network.buses
        )

        if not buses:
            raise ValueError(
                "Cannot build Y-bus for a Network with no buses."
            )

        self._ensure_network_index(
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
    # NETWORK INDEX
    # ========================================================

    def _ensure_network_index(
        self,
        buses: tuple[Any, ...],
    ) -> None:
        """
        Ensure that the authoritative Network BusIndex contains
        every canonical bus.

        BusIndex remains owned by Network.

        This method does not create a second numerical index.
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

        ensure = getattr(
            index,
            "ensure",
            None,
        )

        if ensure is None:
            raise AttributeError(
                "Network BusIndex must provide ensure()."
            )

        ensure(
            buses
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
        Stamp a canonical Line using its explicit numerical model.

        The audited Line model provides:

            series_admittance
            total_shunt_susceptance
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

        y_series = complex(
            line.series_admittance
        )

        b_total = float(
            getattr(
                line,
                "total_shunt_susceptance",
                0.0,
            )
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
        Stamp a canonical Transformer.

        Transformer parameters are taken directly from the audited
        Transformer model:

            series_admittance
            shunt_admittance
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

        i = self._bus_index(
            from_bus,
        )

        j = self._bus_index(
            to_bus,
        )

        y_series = complex(
            transformer.series_admittance
        )

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

        # Transformer model b is total shunt susceptance.
        b_total = float(
            getattr(
                transformer,
                "b_pu",
                0.0,
            )
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

        The audited Shunt model stores:

            g_pu
            b_pu

        and therefore:

            Y = G + jB
        """

        bus = self._resolve_shunt_bus(
            shunt,
        )

        index = self._bus_index(
            bus,
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

        if not np.isfinite(
            conductance
        ):
            raise ValueError(
                f"Shunt "
                f"'{getattr(shunt, 'id', shunt)}' "
                "has invalid conductance."
            )

        if not np.isfinite(
            susceptance
        ):
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

        Terminal-to-bus interpretation remains delegated to the
        Network endpoint resolver.
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
        Resolve a canonical Shunt terminal to its Bus.
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
        Ensure that the resolved Bus belongs to this Network.
        """

        if bus is None:
            raise ValueError(
                f"{type(element).__name__} "
                f"'{getattr(element, 'id', element)}' "
                f"terminal '{terminal_name}' "
                "does not resolve to a Bus."
            )

        buses = tuple(
            self.network.buses
        )

        if bus not in buses:
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
        Obtain the authoritative Network BusIndex value.

        Numerical does not create a competing index mapping.
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

        get = getattr(
            index,
            "get",
            None,
        )

        if get is None:
            raise AttributeError(
                "Network BusIndex must provide get()."
            )

        try:
            value = int(
                get(bus.id)
            )

        except (KeyError, AttributeError, TypeError, ValueError) as exc:

            raise ValueError(
                f"Bus "
                f"'{getattr(bus, 'id', bus)}' "
                "does not have a valid matrix index."
            ) from exc

        if value < 0:
            raise ValueError(
                f"Bus "
                f"'{getattr(bus, 'id', bus)}' "
                "has a negative matrix index."
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
        Return whether an element participates in the numerical
        network representation.

        Models without an explicit operational-state attribute
        are treated as active.
        """

        return bool(
            getattr(
                element,
                "in_service",
                True,
            )
        )

    # ========================================================
    # RESULT VALIDATION
    # ========================================================

    @staticmethod
    def validate_matrix(
        Ybus: Any,
    ) -> None:
        """
        Validate a raw CSR Y-bus matrix.

        This performs structural numerical checks only.
        It does not perform engineering validation.
        """

        if Ybus is None:
            raise ValueError(
                "Y-bus cannot be None."
            )

        if not isinstance(
            Ybus,
            csr_matrix,
        ):
            raise TypeError(
                "Y-bus must be a scipy.sparse.csr_matrix."
            )

        if Ybus.ndim != 2:
            raise ValueError(
                "Y-bus must be two-dimensional."
            )

        rows, columns = Ybus.shape

        if rows != columns:
            raise ValueError(
                "Y-bus must be square."
            )

        if Ybus.dtype.kind != "c":
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
