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
        Derived terminal-centric connectivity.

    NetworkState
        Network topology revision/lifecycle.

    BusIndex
        Canonical bus.id -> numerical matrix index.

Network does not own YBus or any other numerical artifact.
"""

from __future__ import annotations

from typing import Any, Optional

from .indexing import BusIndex
from .registry import NetworkRegistry
from .state import NetworkState
from .topology import TopologyManager


class Network:
    """
    Authoritative electrical network aggregate.

    This is intentionally a thin façade. Domain behavior remains
    in model components, membership in NetworkRegistry, topology
    construction in TopologyManager, indexing in BusIndex, and
    numerical artifacts in the Numerical layer.
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
            if getattr(topology, "network", self) is not self:
                raise ValueError(
                    "TopologyManager belongs to a different Network."
                )
            self.topology = topology

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
        """Return the canonical registered model instance."""

        return self.registry.get_by_id(
            element_type,
            object_id,
        )

    # ========================================================
    # TOPOLOGY LIFECYCLE
    # ========================================================

    def _invalidate_topology(
        self,
        *,
        invalidate_index: bool = False,
    ) -> None:
        """
        Invalidate Network-derived topology.

        BusIndex is invalidated only when bus membership changes.
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
    # NON-TOPOLOGY EQUIPMENT
    # ========================================================

    def add_grid(self, grid: Any) -> None:
        self.registry.add_grid(grid)

    def remove_grid(self, grid: Any) -> None:
        self.registry.remove_grid(grid)

    def add_generator(self, generator: Any) -> None:
        self.registry.add_generator(generator)

    def remove_generator(self, generator: Any) -> None:
        self.registry.remove_generator(generator)

    def add_load(self, load: Any) -> None:
        self.registry.add_load(load)

    def remove_load(self, load: Any) -> None:
        self.registry.remove_load(load)

    def add_shunt(self, shunt: Any) -> None:
        self.registry.add_shunt(shunt)

    def remove_shunt(self, shunt: Any) -> None:
        self.registry.remove_shunt(shunt)

    def add_branch(self, branch: Any) -> None:
        self.registry.add_branch(branch)

    def remove_branch(self, branch: Any) -> None:
        self.registry.remove_branch(branch)

    def add_cable(self, cable: Any) -> None:
        self.registry.add_cable(cable)

    def remove_cable(self, cable: Any) -> None:
        self.registry.remove_cable(cable)

    def add_switch(self, switch: Any) -> None:
        self.registry.add_switch(switch)

    def remove_switch(self, switch: Any) -> None:
        self.registry.remove_switch(switch)

    def add_disconnector(self, disconnector: Any) -> None:
        self.registry.add_disconnector(disconnector)

    def remove_disconnector(self, disconnector: Any) -> None:
        self.registry.remove_disconnector(disconnector)

    def add_fuse(self, fuse: Any) -> None:
        self.registry.add_fuse(fuse)

    def remove_fuse(self, fuse: Any) -> None:
        self.registry.remove_fuse(fuse)

    # ========================================================
    # TOPOLOGY-AFFECTING EQUIPMENT
    # ========================================================

    def add_line(self, line: Any) -> None:
        self.registry.add_line(line)
        self._invalidate_topology()

    def remove_line(self, line: Any) -> None:
        self.registry.remove_line(line)
        self._invalidate_topology()

    def add_transformer(self, transformer: Any) -> None:
        self.registry.add_transformer(transformer)
        self._invalidate_topology()

    def remove_transformer(self, transformer: Any) -> None:
        self.registry.remove_transformer(transformer)
        self._invalidate_topology()

    # ========================================================
    # EXPLICIT PREPARATION
    # ========================================================

    def rebuild_topology(self) -> dict[Any, set[Any]]:
        """
        Build the derived topology graph and synchronize state.
        """

        graph = self.topology.build()
        self.state.topology_rebuilt()
        return graph

    def rebuild_index(self) -> None:
        """
        Explicitly rebuild the canonical BusIndex.

        Numerical consumers must consume the prepared index and
        must not rebuild it implicitly.
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
    # STATE
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
            f"topology_revision={self.topology_revision}, "
            f"topology_valid={self.topology_valid}, "
            f"index_valid={self.index_valid}"
            ")"
        )


__all__ = [
    "Network",
]
