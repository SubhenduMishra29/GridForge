# ============================================================
# File: core/network/topology.py
# GridForge V2 — Network Topology
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Network Topology Manager.

The TopologyManager owns only the assembled-network topology view.

Responsibilities
----------------
- Build the electrical connectivity graph.
- Resolve branch terminal endpoints to buses.
- Respect element in-service state.
- Determine electrical connectivity.
- Detect electrical islands.

Does NOT
--------
- Own canonical model objects.
- Register/remove network elements.
- Own bus indexing.
- Build Y-bus.
- Perform electrical calculations.
- Modify model objects.
- Perform engineering validation.
- Implement command/application workflows.

Ownership boundary
------------------

    Network
        |
        +-- NetworkRegistry
        |       canonical membership
        |
        +-- BusIndex
        |       bus.id -> matrix index
        |
        +-- NetworkState
        |       derived-state validity
        |
        +-- TopologyManager
        |       connectivity graph
        |
        +-- YBusBuilder
                admittance matrix

Terminal architecture
---------------------

For branch equipment, terminal endpoints are authoritative.

    Line
        from_terminal -> endpoint -> Bus
        to_terminal   -> endpoint -> Bus

    Transformer
        from_terminal -> endpoint -> Bus
        to_terminal   -> endpoint -> Bus

The shared endpoint resolver is therefore used instead of
duplicating terminal-resolution logic here.

GridForge V2
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .endpoint import resolve_terminal_bus


class TopologyManager:
    """
    Build and query the electrical topology of a Network.

    The manager does not own the network elements. It creates a
    derived connectivity graph from the canonical elements currently
    registered on the Network.
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self, network: Any) -> None:
        if network is None:
            raise ValueError(
                "TopologyManager requires a Network."
            )

        self.network = network

        # --------------------------------------------------------
        # DERIVED GRAPH
        #
        # bus -> set of electrically connected buses
        # --------------------------------------------------------

        self._graph: Dict[Any, Set[Any]] = {}

        # --------------------------------------------------------
        # DERIVED BRANCH MAP
        #
        # (bus_a, bus_b) -> registered branch elements
        #
        # This is supplementary information and is not the
        # authoritative network membership.
        # --------------------------------------------------------

        self._edges: Dict[
            Tuple[Any, Any],
            List[Any],
        ] = {}

        self._dirty = True

    # ============================================================
    # PROPERTIES
    # ============================================================

    @property
    def graph(self) -> Dict[Any, Set[Any]]:
        """
        Return the currently built topology graph.

        The returned graph is the manager's derived representation.
        Call ``build()`` when the topology is dirty.
        """

        return self._graph

    # ------------------------------------------------------------

    @property
    def edges(self) -> Dict[Tuple[Any, Any], List[Any]]:
        """
        Return the derived branch-edge mapping.
        """

        return self._edges

    # ------------------------------------------------------------

    @property
    def dirty(self) -> bool:
        """
        Whether the topology graph requires rebuilding.
        """

        return self._dirty

    # ============================================================
    # INVALIDATION
    # ============================================================

    def invalidate(self) -> None:
        """
        Mark the topology graph as stale.

        TopologyManager owns the validity of its own derived graph.

        NetworkState separately tracks Network-level derived-state
        validity.
        """

        self._dirty = True

    # ============================================================
    # BUILD
    # ============================================================

    def build(
        self,
    ) -> Dict[Any, Set[Any]]:
        """
        Build the electrical connectivity graph.

        Returns
        -------
        dict
            Mapping:

                Bus -> set(Bus)

        Notes
        -----
        Only in-service topology-affecting branch elements are
        included.

        Currently supported branch families are:

            - Line
            - Transformer

        Shunts, generators, and loads do not create bus-to-bus
        connectivity edges.
        """

        graph: Dict[Any, Set[Any]] = {
            bus: set()
            for bus in self.network.buses
        }

        edges: Dict[
            Tuple[Any, Any],
            List[Any],
        ] = {}

        # --------------------------------------------------------
        # LINES
        # --------------------------------------------------------

        for line in self.network.lines:

            if not self._is_in_service(line):
                continue

            from_bus = self._resolve_branch_terminal(
                line,
                "from_terminal",
            )

            to_bus = self._resolve_branch_terminal(
                line,
                "to_terminal",
            )

            self._validate_registered_bus(
                from_bus,
                line,
                "from_terminal",
            )

            self._validate_registered_bus(
                to_bus,
                line,
                "to_terminal",
            )

            self._add_edge(
                graph,
                edges,
                from_bus,
                to_bus,
                line,
            )

        # --------------------------------------------------------
        # TRANSFORMERS
        # --------------------------------------------------------

        for transformer in self.network.transformers:

            if not self._is_in_service(transformer):
                continue

            from_bus = self._resolve_branch_terminal(
                transformer,
                "from_terminal",
            )

            to_bus = self._resolve_branch_terminal(
                transformer,
                "to_terminal",
            )

            self._validate_registered_bus(
                from_bus,
                transformer,
                "from_terminal",
            )

            self._validate_registered_bus(
                to_bus,
                transformer,
                "to_terminal",
            )

            self._add_edge(
                graph,
                edges,
                from_bus,
                to_bus,
                transformer,
            )

        self._graph = graph
        self._edges = edges
        self._dirty = False

        return self._graph

    # ============================================================
    # BRANCH RESOLUTION
    # ============================================================

    def _resolve_branch_terminal(
        self,
        element: Any,
        terminal_name: str,
    ) -> Any:
        """
        Resolve one branch terminal to its Bus.

        Terminal resolution is delegated to the canonical endpoint
        resolver.

        Raises
        ------
        ValueError
            If the terminal is absent or cannot resolve to a Bus.
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

        bus = resolve_terminal_bus(terminal)

        if bus is None:
            raise ValueError(
                f"{type(element).__name__} "
                f"'{getattr(element, 'id', element)}' "
                f"terminal '{terminal_name}' does not resolve "
                "to a Bus."
            )

        return bus

    # ============================================================
    # EDGE CONSTRUCTION
    # ============================================================

    @staticmethod
    def _add_edge(
        graph: Dict[Any, Set[Any]],
        edges: Dict[Tuple[Any, Any], List[Any]],
        bus_a: Any,
        bus_b: Any,
        element: Any,
    ) -> None:
        """
        Add an undirected electrical branch edge.

        Topology is treated as an undirected connectivity graph.

        A branch connecting a bus to itself is retained as an
        element edge but does not create a second graph node.
        """

        graph.setdefault(bus_a, set())
        graph.setdefault(bus_b, set())

        graph[bus_a].add(bus_b)
        graph[bus_b].add(bus_a)

        key = TopologyManager._edge_key(
            bus_a,
            bus_b,
        )

        edges.setdefault(
            key,
            [],
        ).append(element)

    # ------------------------------------------------------------

    @staticmethod
    def _edge_key(
        bus_a: Any,
        bus_b: Any,
    ) -> Tuple[Any, Any]:
        """
        Produce a deterministic undirected edge key.

        Bus IDs are used only for deterministic ordering of the
        derived edge dictionary. Bus object identity remains the
        graph node identity.
        """

        id_a = getattr(bus_a, "id", None)
        id_b = getattr(bus_b, "id", None)

        try:
            if id_a <= id_b:
                return bus_a, bus_b
            return bus_b, bus_a

        except TypeError:
            # Mixed/non-orderable ID types are legal at the topology
            # layer. Fall back to stable string representations.
            if str(id_a) <= str(id_b):
                return bus_a, bus_b

            return bus_b, bus_a

    # ============================================================
    # BUS VALIDATION
    # ============================================================

    def _validate_registered_bus(
        self,
        bus: Any,
        element: Any,
        terminal_name: str,
    ) -> None:
        """
        Ensure a resolved endpoint belongs to this Network.

        This is a structural topology check, not engineering
        validation.
        """

        if bus not in self.network.buses:
            raise ValueError(
                f"{type(element).__name__} "
                f"'{getattr(element, 'id', element)}' "
                f"terminal '{terminal_name}' resolves to Bus "
                f"'{getattr(bus, 'id', bus)}', which is not "
                "registered on this Network."
            )

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @staticmethod
    def _is_in_service(
        element: Any,
    ) -> bool:
        """
        Return whether an element participates in topology.

        Missing ``in_service`` is treated as active for compatibility
        with model objects that do not expose an explicit service
        state.

        This method does not modify the element.
        """

        return bool(
            getattr(
                element,
                "in_service",
                True,
            )
        )

    # ============================================================
    # ENSURE
    # ============================================================

    def ensure_built(
        self,
    ) -> Dict[Any, Set[Any]]:
        """
        Return a valid topology graph, rebuilding when necessary.
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
        Determine whether two buses belong to the same electrical
        connectivity component.

        Parameters
        ----------
        bus_a, bus_b
            Canonical Bus objects registered on the Network.

        Returns
        -------
        bool
            True when a path exists between the two buses.

        Notes
        -----
        Connectivity is topological only. It does not determine
        electrical operating conditions, power flow, voltage, or
        stability.
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

        visited: Set[Any] = set()
        queue = deque([bus_a])

        visited.add(bus_a)

        while queue:

            current = queue.popleft()

            for neighbour in graph.get(
                current,
                set(),
            ):

                if neighbour is bus_b:
                    return True

                if neighbour not in visited:

                    visited.add(neighbour)
                    queue.append(neighbour)

        return False

    # ============================================================
    # ISLAND DETECTION
    # ============================================================

    def find_islands(
        self,
    ) -> List[Set[Any]]:
        """
        Return the electrical connectivity islands.

        Each island is represented as a set of canonical Bus objects.

        Isolated buses are valid one-bus islands.
        """

        graph = self.ensure_built()

        islands: List[Set[Any]] = []
        visited: Set[Any] = set()

        # --------------------------------------------------------
        # Preserve Network bus ordering when discovering islands.
        # --------------------------------------------------------

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

                    if neighbour not in visited:

                        visited.add(neighbour)
                        queue.append(neighbour)

            islands.append(island)

        return islands

    # ============================================================
    # ISLAND COUNT
    # ============================================================

    def island_count(self) -> int:
        """
        Return the number of electrical islands.
        """

        return len(
            self.find_islands()
        )

    # ============================================================
    # CONNECTED COMPONENT
    # ============================================================

    def connected_component(
        self,
        bus: Any,
    ) -> Set[Any]:
        """
        Return the complete electrical island containing ``bus``.
        """

        self._require_registered_bus(
            bus,
            "bus",
        )

        graph = self.ensure_built()

        component: Set[Any] = set()
        queue = deque([bus])

        component.add(bus)

        while queue:

            current = queue.popleft()

            for neighbour in graph.get(
                current,
                set(),
            ):

                if neighbour not in component:

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
        Return registered in-service branch elements connecting
        ``bus_a`` and ``bus_b``.

        The returned list is a copy and does not expose internal
        topology state for mutation.
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
        Return the buses directly connected to ``bus``.
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
        """
        Return the topological degree of a bus.
        """

        return len(
            self.neighbours(bus)
        )

    # ============================================================
    # REGISTERED BUS CHECK
    # ============================================================

    def _require_registered_bus(
        self,
        bus: Any,
        argument_name: str,
    ) -> None:
        """
        Ensure a supplied Bus belongs to the Network.
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

    def clear(
        self,
    ) -> None:
        """
        Discard the derived topology graph.

        Network membership is untouched.
        """

        self._graph = {}
        self._edges = {}
        self._dirty = True

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(self) -> Dict[str, Any]:
        """
        Return a concise topology summary.
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

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"TopologyManager("
            f"buses={len(self._graph)}, "
            f"edges={sum(len(v) for v in self._graph.values()) // 2}, "
            f"dirty={self._dirty}"
            f")"
        )
