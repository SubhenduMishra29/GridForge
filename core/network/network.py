# ============================================================
# File: core/network/network.py
# GridForge V2 — Network Aggregate
# Author: Subhendu Mishra
# ============================================================

"""
Authoritative electrical Network aggregate.

Network owns the coordination boundary between:

    NetworkRegistry
        Canonical equipment membership.

    TopologyManager
        Derived terminal-centric electrical connectivity.

    NetworkState
        Network topology revision/lifecycle.

    BusIndex
        Canonical bus.id -> numerical matrix index.

Network does not own numerical artifacts such as YBus.
Numerical consumers read an explicitly prepared BusIndex and
construct their own derived numerical artifacts.

Network is intentionally a thin façade. Equipment behavior,
topology algorithms, indexing implementation, numerical
calculation, studies, solvers, commands, and UI state belong
to their respective layers.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from .indexing import BusIndex
from .registry import NetworkRegistry
from .state import NetworkState
from .topology import TopologyManager


class Network:
    """
    Authoritative electrical network aggregate.

    The Network coordinates canonical membership and the
    lifecycle of Network-derived structural representations.
    """

    def __init__(
        self,
        *,
        registry: Optional[NetworkRegistry] = None,
        topology: Optional[TopologyManager] = None,
        state: Optional[NetworkState] = None,
        index: Optional[BusIndex] = None,
    ) -> None:
        self.registry = registry or NetworkRegistry()
        self.state = state or NetworkState()
        self.index = index or BusIndex()

        if topology is None:
            self.topology = TopologyManager(self)
        else:
            self.topology = topology

            if getattr(self.topology, "network", self) is not self:
                raise ValueError(
                    "TopologyManager belongs to a different Network."
                )

    # ========================================================
    # CANONICAL COLLECTIONS
    # ========================================================

    @property
    def buses(self) -> tuple[Any, ...]:
        return self.registry.buses

    @property
    def grids(self) -> tuple[Any, ...]:
        return self.registry.grids

    @property
    def generators(self) -> tuple[Any, ...]:
        return self.registry.generators

    @property
    def loads(self) -> tuple[Any, ...]:
        return self.registry.loads

    @property
    def shunts(self) -> tuple[Any, ...]:
        return self.registry.shunts

    @property
    def lines(self) -> tuple[Any, ...]:
        return self.registry.lines

    @property
    def transformers(self) -> tuple[Any, ...]:
        return self.registry.transformers

    @property
    def branches(self) -> tuple[Any, ...]:
        return self.registry.branches

    @property
    def cables(self) -> tuple[Any, ...]:
        return self.registry.cables

    @property
    def switches(self) -> tuple[Any, ...]:
        return self.registry.switches

    @property
    def disconnectors(self) -> tuple[Any, ...]:
        return self.registry.disconnectors

    @property
    def fuses(self) -> tuple[Any, ...]:
        return self.registry.fuses

    # ========================================================
    # LOOKUP
    # ========================================================

    def get_by_id(
        self,
        element_type: str,
        object_id: str,
    ) -> Any:
        """
        Return the canonical registered model instance.

        The registry remains the authoritative lookup owner.
        """

        return self.registry.get_by_id(
            element_type,
            object_id,
        )

    # ========================================================
    # STRUCTURAL LIFECYCLE
    # ========================================================

    def _invalidate_topology(
        self,
        *,
        invalidate_index: bool = False,
    ) -> None:
        """
        Invalidate Network-derived structural representations.

        NetworkState owns the topology revision.

        TopologyManager owns the validity of its graph.

        BusIndex is invalidated only when bus membership/order
        changes.
        """

        self.state.invalidate_topology()
        self.topology.invalidate()

        if invalidate_index:
            self.index.invalidate()

    # ========================================================
    # BUS
    # ========================================================

    def add_bus(self, bus: Any) -> None:
        self.registry.add_bus(bus)
        self._invalidate_topology(
            invalidate_index=True
        )

    def remove_bus(self, bus: Any) -> None:
        self.registry.remove_bus(bus)
        self._invalidate_topology(
            invalidate_index=True
        )

    # ========================================================
    # GRID
    # ========================================================

    def add_grid(self, grid: Any) -> None:
        self.registry.add_grid(grid)

    def remove_grid(self, grid: Any) -> None:
        self.registry.remove_grid(grid)

    # ========================================================
    # GENERATOR
    # ========================================================

    def add_generator(self, generator: Any) -> None:
        self.registry.add_generator(generator)

    def remove_generator(self, generator: Any) -> None:
        self.registry.remove_generator(generator)

    # ========================================================
    # LOAD
    # ========================================================

    def add_load(self, load: Any) -> None:
        self.registry.add_load(load)

    def remove_load(self, load: Any) -> None:
        self.registry.remove_load(load)

    # ========================================================
    # SHUNT
    # ========================================================

    def add_shunt(self, shunt: Any) -> None:
        self.registry.add_shunt(shunt)

    def remove_shunt(self, shunt: Any) -> None:
        self.registry.remove_shunt(shunt)

    # ========================================================
    # LINE
    # ========================================================

    def add_line(self, line: Any) -> None:
        self.registry.add_line(line)
        self._invalidate_topology()

    def remove_line(self, line: Any) -> None:
        self.registry.remove_line(line)
        self._invalidate_topology()

    # ========================================================
    # TRANSFORMER
    # ========================================================

    def add_transformer(self, transformer: Any) -> None:
        self.registry.add_transformer(transformer)
        self._invalidate_topology()

    def remove_transformer(self, transformer: Any) -> None:
        self.registry.remove_transformer(transformer)
        self._invalidate_topology()

    # ========================================================
    # BRANCH
    # ========================================================

    def add_branch(self, branch: Any) -> None:
        self.registry.add_branch(branch)
        self._invalidate_topology()

    def remove_branch(self, branch: Any) -> None:
        self.registry.remove_branch(branch)
        self._invalidate_topology()

    # ========================================================
    # CABLE
    # ========================================================

    def add_cable(self, cable: Any) -> None:
        self.registry.add_cable(cable)
        self._invalidate_topology()

    def remove_cable(self, cable: Any) -> None:
        self.registry.remove_cable(cable)
        self._invalidate_topology()

    # ========================================================
    # SWITCH
    # ========================================================

    def add_switch(self, switch: Any) -> None:
        self.registry.add_switch(switch)
        self._invalidate_topology()

    def remove_switch(self, switch: Any) -> None:
        self.registry.remove_switch(switch)
        self._invalidate_topology()

    # ========================================================
    # DISCONNECTOR
    # ========================================================

    def add_disconnector(
        self,
        disconnector: Any,
    ) -> None:
        self.registry.add_disconnector(disconnector)
        self._invalidate_topology()

    def remove_disconnector(
        self,
        disconnector: Any,
    ) -> None:
        self.registry.remove_disconnector(disconnector)
        self._invalidate_topology()

    # ========================================================
    # FUSE
    # ========================================================

    def add_fuse(self, fuse: Any) -> None:
        self.registry.add_fuse(fuse)
        self._invalidate_topology()

    def remove_fuse(self, fuse: Any) -> None:
        self.registry.remove_fuse(fuse)
        self._invalidate_topology()

    # ========================================================
    # EXPLICIT PREPARATION
    # ========================================================

    def rebuild_topology(self) -> dict[Any, set[Any]]:
        """
        Explicitly rebuild the derived topology graph.
        """

        graph = self.topology.build()
        self.state.topology_rebuilt()
        return graph

    def rebuild_index(self) -> None:
        """
        Explicitly rebuild the canonical BusIndex.

        Numerical code must consume the prepared index rather
        than implicitly rebuilding it.
        """

        self.index.rebuild(self.buses)

    def prepare(self) -> None:
        """
        Prepare Network-derived structural representations.

        No numerical matrix is constructed here.
        """

        self.rebuild_topology()
        self.rebuild_index()

    # ========================================================
    # STATE QUERIES
    # ========================================================

    @property
    def topology_revision(self) -> int:
        return self.state.topology_revision

    @property
    def topology_valid(self) -> bool:
        return self.state.topology_valid

    @property
    def index_valid(self) -> bool:
        return self.index.valid

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "Network("
            f"buses={len(self.buses)}, "
            f"lines={len(self.lines)}, "
            f"transformers={len(self.transformers)}, "
            f"topology_revision="
            f"{self.topology_revision}, "
            f"topology_valid="
            f"{self.topology_valid}, "
            f"index_valid="
            f"{self.index_valid}"
            ")"
        )


__all__ = [
    "Network",
]
