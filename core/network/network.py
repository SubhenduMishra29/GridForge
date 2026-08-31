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

Architecture rule
-----------------
Network coordinates the domain infrastructure. It does not
implement equipment behavior, topology algorithms, or numerical
solvers.
"""

from __future__ import annotations

from typing import Any, Optional

from .indexing import BusIndex
from .registry import NetworkRegistry
from .state import NetworkState
from .topology import TopologyManager


class Network:
    """
    Authoritative electrical Network aggregate.

    Membership is delegated to NetworkRegistry.
    Derived topology is delegated to TopologyManager.
    Topology lifecycle is owned by NetworkState.
    Numerical bus indexing is delegated to BusIndex.
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
    def breakers(self) -> tuple[Any, ...]:
        return self.registry.breakers

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
        """

        return self.registry.get_by_id(
            element_type,
            object_id,
        )

    # ========================================================
    # DERIVED-STATE INVALIDATION
    # ========================================================

    def _invalidate_topology(
        self,
        *,
        invalidate_index: bool = False,
    ) -> None:
        """
        Invalidate Network-derived topology.

        BusIndex is invalidated only when Bus membership changes.

        Equipment membership changes invalidate topology but do not
        invalidate the numerical BusIndex because the set/order of
        Buses has not changed.
        """

        self.state.invalidate_topology()
        self.topology.invalidate()

        if invalidate_index:
            self.index.invalidate()

    # ========================================================
    # BUS MEMBERSHIP
    # ========================================================

    def add_bus(self, bus: Any) -> None:
        """
        Register a Bus and invalidate topology and BusIndex.
        """

        self.registry.add_bus(bus)
        self._invalidate_topology(
            invalidate_index=True,
        )

    def remove_bus(self, bus: Any) -> None:
        """
        Remove a Bus and invalidate topology and BusIndex.
        """

        self.registry.remove_bus(bus)
        self._invalidate_topology(
            invalidate_index=True,
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

    # ========================================================
    # TOPOLOGY EQUIPMENT
    # ========================================================

    def add_branch(self, branch: Any) -> None:
        """
        Register a Branch and invalidate derived topology.
        """

        self.registry.add_branch(branch)
        self._invalidate_topology()

    def remove_branch(self, branch: Any) -> None:
        """
        Remove a Branch and invalidate derived topology.
        """

        self.registry.remove_branch(branch)
        self._invalidate_topology()

    def add_line(self, line: Any) -> None:
        """
        Register a Line and invalidate derived topology.
        """

        self.registry.add_line(line)
        self._invalidate_topology()

    def remove_line(self, line: Any) -> None:
        """
        Remove a Line and invalidate derived topology.
        """

        self.registry.remove_line(line)
        self._invalidate_topology()

    def add_cable(self, cable: Any) -> None:
        """
        Register a Cable and invalidate derived topology.
        """

        self.registry.add_cable(cable)
        self._invalidate_topology()

    def remove_cable(self, cable: Any) -> None:
        """
        Remove a Cable and invalidate derived topology.
        """

        self.registry.remove_cable(cable)
        self._invalidate_topology()

    def add_transformer(self, transformer: Any) -> None:
        """
        Register a Transformer and invalidate derived topology.
        """

        self.registry.add_transformer(transformer)
        self._invalidate_topology()

    def remove_transformer(self, transformer: Any) -> None:
        """
        Remove a Transformer and invalidate derived topology.
        """

        self.registry.remove_transformer(transformer)
        self._invalidate_topology()

    def add_breaker(self, breaker: Any) -> None:
        """
        Register a Breaker and invalidate derived topology.
        """

        self.registry.add_breaker(breaker)
        self._invalidate_topology()

    def remove_breaker(self, breaker: Any) -> None:
        """
        Remove a Breaker and invalidate derived topology.
        """

        self.registry.remove_breaker(breaker)
        self._invalidate_topology()

    def add_switch(self, switch: Any) -> None:
        """
        Register a Switch and invalidate derived topology.
        """

        self.registry.add_switch(switch)
        self._invalidate_topology()

    def remove_switch(self, switch: Any) -> None:
        """
        Remove a Switch and invalidate derived topology.
        """

        self.registry.remove_switch(switch)
        self._invalidate_topology()

    def add_disconnector(
        self,
        disconnector: Any,
    ) -> None:
        """
        Register a Disconnector and invalidate derived topology.
        """

        self.registry.add_disconnector(disconnector)
        self._invalidate_topology()

    def remove_disconnector(
        self,
        disconnector: Any,
    ) -> None:
        """
        Remove a Disconnector and invalidate derived topology.
        """

        self.registry.remove_disconnector(disconnector)
        self._invalidate_topology()

    def add_fuse(self, fuse: Any) -> None:
        """
        Register a Fuse and invalidate derived topology.
        """

        self.registry.add_fuse(fuse)
        self._invalidate_topology()

    def remove_fuse(self, fuse: Any) -> None:
        """
        Remove a Fuse and invalidate derived topology.
        """

        self.registry.remove_fuse(fuse)
        self._invalidate_topology()

    # ========================================================
    # TOPOLOGY PREPARATION
    # ========================================================

    def rebuild_topology(self) -> dict[Any, set[Any]]:
        """
        Build the derived topology graph and synchronize state.
        """

        graph = self.topology.build()
        self.state.topology_rebuilt()

        return graph

    # ========================================================
    # NUMERICAL INDEX PREPARATION
    # ========================================================

    def rebuild_index(self) -> None:
        """
        Rebuild the canonical BusIndex.

        Numerical consumers receive the prepared index from Network.
        Network itself does not construct numerical matrices.
        """

        self.index.rebuild(self.buses)

    # ========================================================
    # EXPLICIT PREPARATION
    # ========================================================

    def prepare(self) -> None:
        """
        Prepare structural Network representations.

        This prepares topology and BusIndex only.

        No Y-bus or other numerical artifact is constructed here.
        """

        self.rebuild_topology()
        self.rebuild_index()

    # ========================================================
    # STATE ACCESS
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
