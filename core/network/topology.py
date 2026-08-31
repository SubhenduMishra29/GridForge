# ============================================================
# File: core/network/topology.py
# GridForge V2 — Network Topology
# Author: Subhendu Mishra
# ============================================================
"""
GridForge V2 — Network Topology

Responsibility
--------------
Derive electrical bus connectivity from the authoritative Network
equipment and frozen Terminal contracts.

Topology is derived state. It is never authoritative equipment state.

This module:
    - resolves equipment terminals to canonical Buses;
    - determines whether registered equipment currently conducts;
    - builds the undirected electrical connectivity graph;
    - tracks conductive equipment between bus pairs;
    - provides read-only connectivity and island queries.

This module does NOT:
    - mutate model objects;
    - own equipment state;
    - own Terminal endpoint state;
    - modify Network membership;
    - assign numerical bus indices;
    - build Y-bus matrices;
    - solve electrical equations;
    - perform engineering analysis;
    - depend on Application or UI.

Architecture
------------
    core/model
        |
        v
    core/network/endpoint.py
        |
        v
    TopologyManager
        |
        +--> derived connectivity
        +--> electrical islands
        +--> branch relationships

The authoritative endpoint remains Terminal.endpoint.
The authoritative equipment operating state remains in the model.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Set, Tuple

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
    Derive and query electrical Network topology.

    The manager does not own authoritative electrical state. It builds
    a derived graph from the canonical objects currently registered
    with the Network.
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self, network: Any) -> None:
        """
        Create a topology manager for a Network aggregate.
        """

        if network is None:
            raise ValueError("network cannot be None.")

        self.network = network

        self._graph: Dict[Any, Set[Any]] = {}
        self._edges: Dict[Tuple[Any, Any], List[Any]] = {}

        self._dirty = True

    # ============================================================
    # INVALIDATION
    # ============================================================

    @property
    def dirty(self) -> bool:
        """Return True when the derived topology must be rebuilt."""

        return self._dirty

    def invalidate(self) -> None:
        """
        Mark the derived topology as stale.

        Network membership and model state are untouched.
        """

        self._dirty = True

    # ============================================================
    # BUILD
    # ============================================================

    def build(self) -> Dict[Any, Set[Any]]:
        """
        Rebuild the complete derived topology.

        Only presently conductive two-terminal elements with both
        terminals resolving to registered Buses become topology edges.

        Returns
        -------
        dict
            Mapping of canonical Bus objects to neighbouring Buses.
        """

        graph: Dict[Any, Set[Any]] = {
            bus: set()
            for bus in self.network.buses
        }

        edges: Dict[Tuple[Any, Any], List[Any]] = {}

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
                # A self-loop does not create a useful bus-to-bus
                # connectivity edge, but the equipment remains a
                # valid registered network element.
                continue

            graph.setdefault(bus_a, set()).add(bus_b)
            graph.setdefault(bus_b, set()).add(bus_a)

            key = self._edge_key(bus_a, bus_b)
            edges.setdefault(key, []).append(element)

        self._graph = graph
        self._edges = edges
        self._dirty = False

        return self._graph

    # ============================================================
    # TOPOLOGY ELEMENTS
    # ============================================================

    def _topology_elements(self) -> List[Any]:
        """
        Return registered two-terminal elements capable of creating
        electrical connectivity.

        Registry collections remain the source of membership.
        """

        elements: List[Any] = []

        collections = (
            "branches",
            "lines",
            "cables",
            "transformers",
            "breakers",
            "switches",
            "disconnectors",
            "fuses",
        )

        seen: Set[int] = set()

        for collection_name in collections:

            collection = getattr(
                self.network,
                collection_name,
                (),
            )

            for element in collection:

                identity = id(element)

                if identity in seen:
                    continue

                seen.add(identity)
                elements.append(element)

        return elements

    # ============================================================
    # CONDUCTION STATE
    # ============================================================

    @staticmethod
    def _is_conductive(element: Any) -> bool:
        """
        Return whether an element currently participates in topology.

        Existing model-state contracts are used directly.

        Priority:
            1. Model-provided ``conducts`` property.
            2. Breaker operational state.
            3. Switch operational state.
            4. Disconnector operational state.
            5. Fuse operational state.
            6. Generic ``in_service`` state.

        No state is modified here.
        """

        conducts = getattr(
            element,
            "conducts",
            None,
        )

        if conducts is not None:
            return bool(conducts)

        if isinstance(element, Breaker):
            return (
                bool(getattr(element, "in_service", True))
                and bool(getattr(element, "closed", False))
                and not bool(getattr(element, "failed", False))
            )

        if isinstance(
            element,
            (
                Switch,
                Disconnector,
            ),
        ):
            return (
                bool(getattr(element, "in_service", True))
                and bool(getattr(element, "closed", False))
            )

        if isinstance(element, Fuse):
            return (
                bool(getattr(element, "in_service", True))
                and not bool(getattr(element, "blown", False))
            )

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
                    True,
                )
            )

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

    def _resolve_bus(
        self,
        element: Any,
        terminal_name: str,
    ) -> Any | None:
        """
        Resolve one element Terminal to a canonical registered Bus.

        Invalid/unconnected endpoints do not create topology edges.
        """

        terminal = getattr(
            element,
            terminal_name,
            None,
        )

        if terminal is None:
            return None

        try:
            bus = resolve_terminal_bus(
                terminal,
            )
        except (TypeError, ValueError):
            return None

        if bus not in self.network.buses:
            raise ValueError(
                f"{type(element).__name__} "
                f"'{getattr(element, 'id', element)}' "
                f"terminal '{terminal_name}' resolves to Bus "
                f"'{getattr(bus, 'id', bus)}', which is not "
                "registered on this Network."
            )

        return bus

    # ============================================================
    # ENSURE
    # ============================================================

    def ensure_built(self) -> Dict[Any, Set[Any]]:
        """
        Return a valid derived topology graph.
        """

        if self._dirty:
            return self.build()

        return self._graph

    # ============================================================
    # CONNECTIVITY
    # ============================================================

    def is_connected(
        self,
        bus_a: Any,
        bus_b: Any,
    ) -> bool:
        """
        Return True when a conductive path exists between two Buses.
        """

        self._require_registered_bus(
            bus_a,
            "bus_a",
        )
        self._require_registered_bus(
            bus_b,
            "bus_b",
        )

        if bus_a is bus_b:
            return True

        graph = self.ensure_built()

        visited: Set[Any] = {bus_a}
        queue = deque([bus_a])

        while queue:

            current = queue.popleft()

            for neighbour in graph.get(
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

    # ============================================================
    # ISLANDS
    # ============================================================

    def find_islands(self) -> List[Set[Any]]:
        """
        Return all electrical connectivity islands.

        An isolated registered Bus is a valid one-Bus island.
        """

        graph = self.ensure_built()

        islands: List[Set[Any]] = []
        visited: Set[Any] = set()

        for bus in self.network.buses:

            if bus in visited:
                continue

            island: Set[Any] = set()
            queue = deque([bus])
            visited.add(bus)

            while queue:

                current = queue.popleft()
                island.add(current)

                for neighbour in graph.get(
                    current,
                    set(),
                ):

                    if neighbour in visited:
                        continue

                    visited.add(neighbour)
                    queue.append(neighbour)

            islands.append(island)

        return islands

    def island_count(self) -> int:
        """Return the number of electrical connectivity islands."""

        return len(self.find_islands())

    # ============================================================
    # CONNECTED COMPONENT
    # ============================================================

    def connected_component(
        self,
        bus: Any,
    ) -> Set[Any]:
        """
        Return the electrical island containing ``bus``.
        """

        self._require_registered_bus(
            bus,
            "bus",
        )

        graph = self.ensure_built()

        component: Set[Any] = {bus}
        queue = deque([bus])

        while queue:

            current = queue.popleft()

            for neighbour in graph.get(
                current,
                set(),
            ):

                if neighbour in component:
                    continue

                component.add(neighbour)
                queue.append(neighbour)

        return component

    # ============================================================
    # BRANCH QUERY
    # ============================================================

    def branches_between(
        self,
        bus_a: Any,
        bus_b: Any,
    ) -> List[Any]:
        """
        Return conductive topology elements connecting two Buses.

        A copy is returned so callers cannot mutate internal state.
        """

        self._require_registered_bus(
            bus_a,
            "bus_a",
        )
        self._require_registered_bus(
            bus_b,
            "bus_b",
        )

        self.ensure_built()

        key = self._edge_key(
            bus_a,
            bus_b,
        )

        return list(
            self._edges.get(
                key,
                [],
            )
        )

    # ============================================================
    # NEIGHBOURS
    # ============================================================

    def neighbours(
        self,
        bus: Any,
    ) -> Set[Any]:
        """
        Return the directly connected Buses.

        A copy is returned so internal topology cannot be mutated.
        """

        self._require_registered_bus(
            bus,
            "bus",
        )

        graph = self.ensure_built()

        return set(
            graph.get(
                bus,
                set(),
            )
        )

    # ============================================================
    # DEGREE
    # ============================================================

    def degree(
        self,
        bus: Any,
    ) -> int:
        """Return the topological degree of a Bus."""

        return len(self.neighbours(bus))

    # ============================================================
    # EDGE KEY
    # ============================================================

    @staticmethod
    def _edge_key(
        bus_a: Any,
        bus_b: Any,
    ) -> Tuple[Any, Any]:
        """
        Return a stable unordered edge key.

        Bus objects themselves may not be orderable, so their IDs are
        compared where possible with a string fallback.
        """

        id_a = getattr(bus_a, "id", bus_a)
        id_b = getattr(bus_b, "id", bus_b)

        try:

            if id_a <= id_b:
                return bus_a, bus_b

            return bus_b, bus_a

        except TypeError:

            if str(id_a) <= str(id_b):
                return bus_a, bus_b

            return bus_b, bus_a

    # ============================================================
    # BUS VALIDATION
    # ============================================================

    def _require_registered_bus(
        self,
        bus: Any,
        argument_name: str,
    ) -> None:
        """
        Ensure a supplied Bus belongs to this Network.
        """

        if bus is None:
            raise ValueError(
                f"{argument_name} cannot be None."
            )

        if bus not in self.network.buses:
            raise ValueError(
                f"{argument_name} "
                f"'{getattr(bus, 'id', bus)}' "
                "is not registered on this Network."
            )

    # ============================================================
    # CLEAR
    # ============================================================

    def clear(self) -> None:
        """
        Discard derived topology without changing Network membership.
        """

        self._graph = {}
        self._edges = {}
        self._dirty = True

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(self) -> Dict[str, Any]:
        """
        Return a concise derived-topology summary.
        """

        graph = self.ensure_built()

        edge_count = sum(
            len(neighbours)
            for neighbours in graph.values()
        ) // 2

        return {
            "buses": len(graph),
            "edges": edge_count,
            "islands": self.island_count(),
            "dirty": self._dirty,
        }


__all__ = [
    "TopologyManager",
]
