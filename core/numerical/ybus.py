# File: core/numerical/ybus.py
# GridForge V2
# Author: Subhendu Mishra

"""
Numerical Y-bus construction.

## Ownership

Network owns:
- canonical electrical models
- registry/membership
- topology
- terminal relationships
- authoritative BusIndex
- topology revision

Numerical owns:
- derived Y-bus representation
- numerical matrix construction

Solver owns:
- numerical solution procedures

YBusBuilder is a read-only consumer of Network.

It requires Network.index to already be valid and corresponding
to the current Network bus membership. It never rebuilds,
ensures, invalidates, or otherwise mutates the BusIndex.

## Electrical conventions

Line:
Z = R + jX
Y = 1 / Z
Ysh,total = jB
Ysh,end = jB / 2

Transformer:
a = tap * exp(j * shift)

```
Yii += Y / |a|²
Yij -= Y / conj(a)
Yji -= Y / a
Yjj += Y
```

Transformer b_pu, when supplied, is treated as total shunt
susceptance and divided equally between both terminals.

Shunt:
Ysh = G + jB

YBus is a derived numerical artifact and is not stored on Network.
"""

from **future** import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix

from core.network.endpoint import resolve_terminal_bus

@dataclass(frozen=True)
class YBus:
"""Immutable numerical Y-bus representation."""

```
matrix: csr_matrix
bus_ids: tuple[str, ...]
topology_revision: Optional[int] = None

def __post_init__(self) -> None:
    if not isinstance(self.matrix, csr_matrix):
        raise TypeError(
            "YBus.matrix must be a scipy.sparse.csr_matrix."
        )

    if self.matrix.ndim != 2:
        raise ValueError("YBus matrix must be two-dimensional.")

    rows, columns = self.matrix.shape

    if rows != columns:
        raise ValueError("YBus matrix must be square.")

    if rows != len(self.bus_ids):
        raise ValueError(
            "YBus matrix dimension must match bus_ids length."
        )

    if self.matrix.dtype.kind != "c":
        raise TypeError(
            "YBus matrix must use a complex dtype."
        )

    if len(set(self.bus_ids)) != len(self.bus_ids):
        raise ValueError("YBus bus_ids must be unique.")

@property
def shape(self) -> tuple[int, int]:
    return self.matrix.shape

@property
def size(self) -> int:
    return self.matrix.size

@property
def ndim(self) -> int:
    return self.matrix.ndim

@property
def nnz(self) -> int:
    return self.matrix.nnz

@property
def data(self) -> np.ndarray:
    return self.matrix.data

def index_of(self, bus_id: str) -> int:
    try:
        return self.bus_ids.index(bus_id)
    except ValueError as exc:
        raise KeyError(
            f"Bus '{bus_id}' is not present in this YBus."
        ) from exc

def __getitem__(self, key: Any) -> Any:
    return self.matrix[key]

def tocsr(self) -> csr_matrix:
    return self.matrix

def toarray(self) -> np.ndarray:
    return self.matrix.toarray()

def todense(self) -> np.ndarray:
    return self.matrix.toarray()

def copy(self) -> "YBus":
    return YBus(
        matrix=self.matrix.copy(),
        bus_ids=self.bus_ids,
        topology_revision=self.topology_revision,
    )

def validate(self) -> bool:
    self.__post_init__()
    return True

def __repr__(self) -> str:
    return (
        "YBus("
        f"buses={len(self.bus_ids)}, "
        f"nnz={self.nnz}, "
        f"topology_revision={self.topology_revision}"
        ")"
    )
```

class YBusBuilder:
"""
Construct YBus from an authoritative Network.

```
The Network owns the canonical BusIndex. This builder requires
that index to already be valid and never mutates it.
"""

def __init__(self, network: Any) -> None:
    if network is None:
        raise ValueError("YBusBuilder requires a Network.")
    self.network = network

def build(self) -> YBus:
    """Build a YBus from the current authoritative Network."""

    buses = tuple(self.network.buses)

    if not buses:
        raise ValueError(
            "Cannot build Y-bus for a Network with no buses."
        )

    self._require_valid_network_index(buses)

    matrix = lil_matrix(
        (len(buses), len(buses)),
        dtype=np.complex128,
    )

    for line in self.network.lines:
        if self._is_in_service(line):
            self._stamp_line(matrix, line)

    for transformer in self.network.transformers:
        if self._is_in_service(transformer):
            self._stamp_transformer(matrix, transformer)

    for shunt in self.network.shunts:
        if self._is_in_service(shunt):
            self._stamp_shunt(matrix, shunt)

    result = YBus(
        matrix=matrix.tocsr(),
        bus_ids=tuple(str(bus.id) for bus in buses),
        topology_revision=self.network.topology_revision,
    )

    result.validate()
    return result

def _require_valid_network_index(
    self,
    buses: tuple[Any, ...],
) -> None:
    """
    Require a valid, already-prepared authoritative BusIndex.

    No rebuild/ensure/invalidate operation is permitted here.
    """

    index = getattr(self.network, "index", None)

    if index is None:
        raise AttributeError(
            "Network must provide an authoritative BusIndex."
        )

    if getattr(index, "valid", False) is not True:
        raise RuntimeError(
            "Network BusIndex is invalid or not prepared. "
            "Rebuild the Network BusIndex before constructing YBus."
        )

    expected_ids = {
        getattr(bus, "id", None)
        for bus in buses
    }

    if None in expected_ids:
        raise ValueError(
            "Every Network Bus must provide an id."
        )

    mapping = index.mapping

    if set(mapping) != expected_ids:
        raise RuntimeError(
            "Network BusIndex does not correspond to the current "
            "Network bus membership."
        )

    expected_positions = set(range(len(buses)))

    if set(mapping.values()) != expected_positions:
        raise RuntimeError(
            "Network BusIndex does not provide a complete "
            "deterministic bus ordering."
        )

def _stamp_line(
    self,
    matrix: lil_matrix,
    line: Any,
) -> None:
    from_bus = self._resolve_branch_bus(
        line,
        "from_terminal",
    )
    to_bus = self._resolve_branch_bus(
        line,
        "to_terminal",
    )

    i = self._bus_index(from_bus)
    j = self._bus_index(to_bus)

    try:
        y_series = complex(line.series_admittance)
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

    y_shunt_half = 1j * b_total / 2.0

    matrix[i, i] += y_series + y_shunt_half
    matrix[j, j] += y_series + y_shunt_half
    matrix[i, j] -= y_series
    matrix[j, i] -= y_series

def _stamp_transformer(
    self,
    matrix: lil_matrix,
    transformer: Any,
) -> None:
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

    try:
        tap = float(transformer.tap)
        shift = float(transformer.shift)
    except (
        AttributeError,
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"Transformer "
            f"'{getattr(transformer, 'id', transformer)}' "
            "does not provide valid tap/shift values."
        ) from exc

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

    complex_tap = tap * np.exp(1j * shift)

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

    y_shunt_half = 1j * b_total / 2.0

    matrix[i, i] += y_shunt_half
    matrix[j, j] += y_shunt_half

def _stamp_shunt(
    self,
    matrix: lil_matrix,
    shunt: Any,
) -> None:
    bus = self._resolve_shunt_bus(shunt)
    index = self._bus_index(bus)

    conductance = float(
        getattr(shunt, "g_pu", 0.0)
    )
    susceptance = float(
        getattr(shunt, "b_pu", 0.0)
    )

    if not np.isfinite(conductance):
        raise ValueError(
            f"Shunt '{getattr(shunt, 'id', shunt)}' "
            "has invalid conductance."
        )

    if not np.isfinite(susceptance):
        raise ValueError(
            f"Shunt '{getattr(shunt, 'id', shunt)}' "
            "has invalid susceptance."
        )

    matrix[index, index] += complex(
        conductance,
        susceptance,
    )

def _resolve_branch_bus(
    self,
    element: Any,
    terminal_name: str,
) -> Any:
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

    bus = resolve_terminal_bus(terminal)

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

    bus = resolve_terminal_bus(terminal)

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
    if bus is None:
        raise ValueError(
            f"{type(element).__name__} "
            f"'{getattr(element, 'id', element)}' "
            f"terminal '{terminal_name}' "
            "does not resolve to a Bus."
        )

    if not any(
        registered_bus is bus
        for registered_bus in self.network.buses
    ):
        raise ValueError(
            f"{type(element).__name__} "
            f"'{getattr(element, 'id', element)}' "
            f"terminal '{terminal_name}' resolves to "
            f"Bus '{getattr(bus, 'id', bus)}', "
            "which is not registered on this Network."
        )

def _bus_index(self, bus: Any) -> int:
    index = getattr(self.network, "index", None)

    if index is None:
        raise AttributeError(
            "Network must provide an authoritative BusIndex."
        )

    if getattr(index, "valid", False) is not True:
        raise RuntimeError(
            "Network BusIndex is invalid or not prepared."
        )

    bus_id = getattr(bus, "id", None)

    if bus_id is None:
        raise ValueError("Bus must provide an id.")

    try:
        value = index.get(bus_id)
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

    if value < 0 or value >= len(self.network.buses):
        raise ValueError(
            f"Bus '{bus_id}' has invalid matrix index {value}."
        )

    return value

@staticmethod
def _is_in_service(element: Any) -> bool:
    return bool(
        getattr(
            element,
            "in_service",
            True,
        )
    )

@staticmethod
def validate_matrix(ybus: Any) -> None:
    if ybus is None:
        raise ValueError("Y-bus cannot be None.")

    if not isinstance(ybus, csr_matrix):
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

def __repr__(self) -> str:
    return (
        "YBusBuilder("
        f"buses={len(self.network.buses)}, "
        f"lines={len(self.network.lines)}, "
        f"transformers={len(self.network.transformers)}, "
        f"shunts={len(self.network.shunts)}"
        ")"
    )
```

**all** = [
"YBus",
"YBusBuilder",
]
