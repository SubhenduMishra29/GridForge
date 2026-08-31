# ============================================================
# File: core/network/topology.py
# GridForge V2 — Derived Network Topology
# Author: Subhendu Mishra
# ============================================================
"""
GridForge V2 — Derived Network Topology.

TopologyManager derives bus-to-bus electrical connectivity from
canonical Network model objects.

Responsibilities
----------------
    - discover registered topology-capable equipment;
    - resolve authoritative Terminal endpoints;
    - interpret existing model conduction state;
    - build the derived Bus connectivity graph;
    - provide read-only connectivity queries.

Ownership
---------
    Model:
        equipment state and Terminal endpoint state.

    NetworkRegistry:
        canonical equipment membership.

    Network:
        aggregate and lifecycle coordination.

    NetworkState:
        topology revision and synchronization state.

    TopologyManager:
        derived topology graph.

    Numerical layer:
        numerical indices and Y-bus artifacts.

This module does not:
    - mutate model objects;
    - modify Terminal endpoints;
    - register equipment;
    - assign numerical indices;
    - construct Y-bus;
    - solve electrical equations;
    - depend on Application or UI.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from core.model.branch import Branch
from core.model.breaker import Breaker
from core.model.cable import Cable
from core.model.disconnector import Disconnector
from core.model.fuse import Fuse
from core.model.line import Line
from core.model.switch import Switch
from core.model.transformer import Transformer

from .endpoint import resolve_terminal_bus


class TopologyManager:
    """
    Build and query derived Network connectivity.

    TopologyManager owns only the derived graph and equipment-to-edge
    relationships. Topology lifecycle is owned by NetworkState.
    """

    _TOPOLOGY_COLLECTIONS = (
        "branches",
        "lines",
        "cables",
        "transformers",
        "breakers",
        "switches",
        "disconnectors",
        "fuses",
    )

    _TOPOLOGY_TYPES = (
        Branch,
        Line,
        Cable,
        Transformer,
        Breaker,
        Switch,
        Disconnector,
        Fuse,
    )

    def __init__(self, network: Any) -> None:
        if network is None:
            raise ValueError("network cannot be None.")

        self.network = network
        self._graph: dict[Any, set[Any]] = {}
        self._edges: dict[tuple[Any, Any], list[Any]] = {}

    # ========================================================
    # BUILD
    # ========================================================

    def build(self) -> dict[Any, set[Any]]:
        """
        Rebuild the derived connectivity graph.

        NetworkState synchronization is deliberately performed by
        Network.rebuild_topology(), not by this graph builder.
        """

        graph = {
            bus: set()
            for bus in self.network.buses
        }
        edges: dict[tuple[Any, Any], list[Any]] = {}

        for element in self._topology_elements():
            if not self._is_conductive(element):
                continue

            bus_a = self._resolve_bus(
                element,
                "from_terminal",
            )
            bus_b = self._resolve_bus(
                element,
                "to_terminal",
            )

            if bus_a is None or bus_b is None:
                continue

            if bus_a is bus_b:
                continue

            graph.setdefault(bus_a, set()).add(bus_b)
            graph.setdefault(bus_b, set()).add(bus_a)

            key = self._edge_key(bus_a, bus_b)
            edges.setdefault(key, []).append(element)

        self._graph = graph
        self._edges = edges

        return self._graph

    # ========================================================
    # INVALIDATION
    # ========================================================

    def invalidate(self) -> None:
        """
        Discard the cached derived graph.

        NetworkState remains the authoritative lifecycle state.
        """

        self._graph = {}
        self._edges = {}

    # ========================================================
    # TOPOLOGY ELEMENTS
    # ========================================================

    def _topology_elements(self) -> list[Any]:
        """
        Return unique registered topology-capable model objects.
        """

        elements: list[Any] = []
        seen: set[int] = set()

        for collection_name in self._TOPOLOGY_COLLECTIONS:
            collection = getattr(
                self.network,
                collection_name,
                (),
            )

            for element in collection:
                if not isinstance(
                    element,
                    self._TOPOLOGY_TYPES,
                ):
                    continue

                identity = id(element)

                if identity in seen:
                    continue

                seen.add(identity)
                elements.append(element)

        return elements

    # ========================================================
    # CONDUCTION
    # ========================================================

    @staticmethod
    def _is_conductive(element: Any) -> bool:
        """
        Return the existing model's present conduction state.

        Model-provided ``conducts`` is authoritative whenever the
        model exposes it.

        Generic branch elements use ``in_service`` because their
        normal conductive semantics are defined by service state.

        Unsupported objects are never silently accepted.
        """

        conducts = getattr(
            element,
            "conducts",
            None,
        )

        if conducts is not None:
            return bool(conducts)

        if isinstance(
            element,
            (
                Branch,
                Line,
                Cable,
                Transformer,
            ),
        ):
            return bool(
                getattr(
                    element,
                    "in_service",
                    False,
                )
            )

        if isinstance(element, Breaker):
            return (
                bool(
                    getattr(
                        element,
                        "in_service",
                        False,
                    )
                )
                and bool(
                    getattr(
                        element,
                        "closed",
                        False,
                    )
                )
                and not bool(
                    getattr(
                        element,
                        "failed",
                        False,
                    )
                )
            )

        if isinstance(
            element,
            (
                Switch,
                Disconnector,
            ),
        ):
            return (
                bool(
                    getattr(
                        element,
                        "in_service",
                        False,
                    )
                )
                and bool(
                    getattr(
                        element,
                        "closed",
                        False,
                    )
                )
            )

        if isinstance(element, Fuse):
            return (
                bool(
                    getattr(
                        element,
                        "in_service",
                        False,
                    )
                )
                and not bool(
                    getattr(
                        element,
                        "blown",
                        False,
                    )
                )
            )

        return False

    # ========================================================
    # ENDPOINTS
    # ========================================================

    def _resolve_bus(
        self,
        element: Any,
        terminal_name: str,
    ) -> Any | None:
        """
        Resolve an equipment Terminal to a registered Bus.
        """

        terminal = getattr(
            element,
            terminal_name,
            None,
        )

        if terminal is None:
            return None

        try:
            bus = resolve_terminal_bus(terminal)
        except (TypeError, ValueError):
            return None

        if bus not in self.network.buses:
            raise ValueError(
                f"{type(element).__name__} "
                f"'{getattr(element, 'id', element)}' "
                f"terminal '{terminal_name}' resolves to an "
                "unregistered Bus."
            )

        return bus

    # ========================================================
    # GRAPH ACCESS
    # ========================================================

    def _ensure_built(self) -> None:
        """
        Ensure the graph exists for the current Network state.

        NetworkState is authoritative for lifecycle. A dirty Network
        is rebuilt through the public Network lifecycle method.
        """

        if self.network.state.topology_dirty:
            self.network.rebuild_topology()

        elif not self._graph:
            self.build()

    @staticmethod
    def _edge_key(
        bus_a: Any,
        bus_b: Any,
    ) -> tuple[Any, Any]:
        """
        Create a deterministic unordered edge key.
        """

        id_a = getattr(bus_a, "id", None)
        id_b = getattr(bus_b, "id", None)

        if id_a is not None and id_b is not None:
            if str(id_a) <= str(id_b):
                return bus_a, bus_b
            return bus_b, bus_a

        if id(bus_a) <= id(bus_b):
            return bus_a, bus_b

        return bus_b, bus_a

    # ========================================================
    # CONNECTIVITY
    # ========================================================

    def neighbours(self, bus: Any) -> set[Any]:
        """
        Return directly connected Buses.
        """

        self._require_bus(bus)
        self._ensure_built()

        return set(
            self._graph.get(
                bus,
                set(),
            )
        )

    def degree(self, bus: Any) -> int:
        """Return the derived topological degree of a Bus."""

        return len(self.neighbours(bus))

    def is_connected(
        self,
        bus_a: Any,
        bus_b: Any,
    ) -> bool:
        """
        Return True if a conductive path exists between two Buses.
        """

        self._require_bus(bus_a)
        self._require_bus(bus_b)

        if bus_a is bus_b:
            return True

        self._ensure_built()

        visited = {bus_a}
        queue = deque([bus_a])

        while queue:
            current = queue.popleft()

            for neighbour in self._graph.get(
                current,
                set(),
            ):
                if neighbour is bus_b:
                    return True

                if neighbour in visited:
                    continue

                visited.add(neighbour)
                queue.append(neighbour)

        return False

    # ========================================================
    # ISLANDS
    # ========================================================

    def connected_component(
        self,
        bus: Any,
    ) -> set[Any]:
        """
        Return the electrical island containing ``bus``.
        """

        self._require_bus(bus)
        self._ensure_built()

        component = {bus}
        queue = deque([bus])

        while queue:
            current = queue.popleft()

            for neighbour in self._graph.get(
                current,
                set(),
            ):
                if neighbour in component:
                    continue

                component.add(neighbour)
                queue.append(neighbour)

        return component

    def find_islands(self) -> list[set[Any]]:
        """
        Return all derived electrical connectivity islands.
        """

        self._ensure_built()

        islands: list[set[Any]] = []
        visited: set[Any] = set()

        for bus in self.network.buses:
            if bus in visited:
                continue

            island = self.connected_component(bus)
            islands.append(island)
            visited.update(island)

        return islands

    def island_count(self) -> int:
        """Return the number of electrical connectivity islands."""

        return len(self.find_islands())

    # ========================================================
    # EDGE QUERIES
    # ========================================================

    def branches_between(
        self,
        bus_a: Any,
        bus_b: Any,
    ) -> list[Any]:
        """
        Return conductive registered elements between two Buses.
        """

        self._require_bus(bus_a)
        self._require_bus(bus_b)
        self._ensure_built()

        return list(
            self._edges.get(
                self._edge_key(
                    bus_a,
                    bus_b,
                ),
                [],
            )
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def _require_bus(self, bus: Any) -> None:
        """Require a canonical Bus registered on this Network."""

        if bus is None:
            raise ValueError("bus cannot be None.")

        if bus not in self.network.buses:
            raise ValueError(
                f"Bus '{getattr(bus, 'id', bus)}' "
                "is not registered on this Network."
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    def summary(self) -> dict[str, Any]:
        """Return a concise topology summary."""

        self._ensure_built()

        edge_count = sum(
            len(neighbours)
            for neighbours in self._graph.values()
        ) // 2

        return {
            "buses": len(self.network.buses),
            "edges": edge_count,
            "islands": self.island_count(),
            "topology_revision": (
                self.network.state.topology_revision
            ),
            "topology_valid": (
                self.network.state.topology_valid
            ),
        }


__all__ = [
    "TopologyManager",
]
