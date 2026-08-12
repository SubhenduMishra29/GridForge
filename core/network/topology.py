"""
GridForge Network Topology Manager
==================================

GridForge Network Layer V2

Builds and manages the electrical connectivity graph of an
assembled GridForge Network.

Responsibilities
----------------
- Build the network connectivity graph.
- Represent buses as graph nodes.
- Represent topology-forming electrical elements as graph edges.
- Respect element service state.
- Detect electrical islands.
- Determine bus-to-bus connectivity.
- Support temporary element-outage studies.
- Provide lightweight topology diagnostics.

The TopologyManager operates on canonical electrical model objects
from ``core.model``.

Architecture
------------

    core/model/
        Canonical electrical entities
              |
              v
    core/network/
        Network
        TopologyManager
              |
              v
    core/analysis/
        Study orchestration

The topology layer does NOT:

- Define electrical equipment models.
- Calculate electrical impedance.
- Build Y-bus.
- Solve power flow.
- Calculate short-circuit currents.
- Perform protection calculations.
- Perform dynamic simulation.
- Modify GUI state.
- Own the canonical electrical objects.

Topology Semantics
------------------
A graph edge represents an electrically conductive/topology-forming
connection between two buses.

Currently supported direct bus-to-bus topology elements include:

- Line
- Transformer

Switching elements such as breakers and disconnectors are evaluated
through their ``in_service`` state when they expose bus endpoints.

The topology manager deliberately does not calculate electrical
admittance. Electrical parameters remain the responsibility of the
model and Y-bus layers.

Network Object Ownership
------------------------
The Network owns the assembled collections.

The TopologyManager only references the Network:

    TopologyManager
          |
          v
       Network
          |
          +-- buses
          +-- lines
          +-- transformers
          +-- ...

No electrical object is copied into the topology graph.

Graph Representation
--------------------
NetworkX ``MultiGraph`` is used because multiple electrical elements
may connect the same pair of buses.

Each graph edge contains:

    element
        Reference to the canonical model object.

    type
        Topology element classification.

For example:

    Bus A ---- Line 1 ---- Bus B
    Bus A ---- Transformer 1 ---- Bus B

Both connections can coexist.

GridForge V2 Status
-------------------
This module is part of the Network Layer V2 baseline.

Changes require evidence of a genuinely fundamental topology
requirement that cannot be satisfied by the existing model,
network, or analysis layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

import networkx as nx


# =====================================================================
# TOPOLOGY MANAGER
# =====================================================================

class TopologyManager:
    """
    Manage the assembled electrical topology of a GridForge Network.

    Parameters
    ----------
    network :
        GridForge ``Network`` instance.

    Notes
    -----
    The manager stores only graph connectivity. It does not duplicate
    electrical model state.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(self, network) -> None:
        self.network = network

        # MultiGraph is required because more than one electrical
        # element may connect the same pair of buses.
        self.graph = nx.MultiGraph()

        self._dirty = True

    # =================================================================
    # GRAPH BUILD
    # =================================================================

    def build(self):
        """
        Build and return the current electrical topology graph.

        Returns
        -------
        networkx.MultiGraph
            Current electrical connectivity graph.

        Notes
        -----
        The graph contains buses as nodes and topology-forming
        electrical elements as edges.

        Elements that are out of service are excluded.
        """

        if not self._dirty:
            return self.graph

        self.graph.clear()

        # -------------------------------------------------------------
        # BUSES
        # -------------------------------------------------------------

        for bus in self.network.buses:
            self.graph.add_node(bus.id)

        # -------------------------------------------------------------
        # DIRECT BUS-TO-BUS ELEMENTS
        # -------------------------------------------------------------

        self._add_elements(
            getattr(self.network, "lines", []),
            "line",
        )

        self._add_elements(
            getattr(self.network, "transformers", []),
            "transformer",
        )

        # -------------------------------------------------------------
        # BRANCH COLLECTION
        #
        # ``Branch`` is included only when the assembled Network
        # explicitly provides such a collection.
        #
        # This keeps TopologyManager compatible with the canonical
        # model architecture without requiring Network to maintain
        # duplicate collections.
        # -------------------------------------------------------------

        self._add_elements(
            getattr(self.network, "branches", []),
            "branch",
        )

        # -------------------------------------------------------------
        # SWITCHING ELEMENTS
        #
        # Breakers/disconnectors may be represented as topology
        # elements when the Network exposes their collections.
        # Their own in_service state determines whether the
        # connection participates in the graph.
        # -------------------------------------------------------------

        self._add_elements(
            getattr(self.network, "breakers", []),
            "breaker",
        )

        self._add_elements(
            getattr(self.network, "disconnectors", []),
            "disconnector",
        )

        self._dirty = False

        return self.graph

    # =================================================================
    # ELEMENT GRAPH INSERTION
    # =================================================================

    def _add_elements(
        self,
        elements,
        element_type: str,
    ) -> None:
        """
        Add supported bus-to-bus elements to the topology graph.

        Parameters
        ----------
        elements :
            Iterable of canonical model elements.

        element_type : str
            Graph classification stored on each edge.

        Notes
        -----
        Elements without a usable pair of bus endpoints are ignored
        here rather than having topology invent a connection that the
        model does not define.
        """

        for element in elements:

            if not getattr(element, "in_service", True):
                continue

            endpoints = self._get_bus_endpoints(element)

            if endpoints is None:
                continue

            from_bus, to_bus = endpoints

            if from_bus is None or to_bus is None:
                continue

            if not hasattr(from_bus, "id"):
                raise TypeError(
                    f"{element_type} from_bus must provide an 'id' "
                    "attribute."
                )

            if not hasattr(to_bus, "id"):
                raise TypeError(
                    f"{element_type} to_bus must provide an 'id' "
                    "attribute."
                )

            u = from_bus.id
            v = to_bus.id

            # Self-connections do not create meaningful network
            # connectivity.
            if u == v:
                continue

            self.graph.add_edge(
                u,
                v,
                element=element,
                type=element_type,
            )

    # =================================================================
    # ENDPOINT DISCOVERY
    # =================================================================

    @staticmethod
    def _get_bus_endpoints(element):
        """
        Return the two bus endpoints of a topology-forming element.

        Returns
        -------
        tuple or None
            ``(from_bus, to_bus)`` when both endpoints are available.

        Notes
        -----
        The preferred canonical representation is:

            element.from_bus
            element.to_bus

        A terminal-based representation is also supported when an
        element exposes two terminals containing bus references.

        The topology layer does not create or infer new terminals.
        """

        if (
            hasattr(element, "from_bus")
            and hasattr(element, "to_bus")
        ):
            return (
                element.from_bus,
                element.to_bus,
            )

        # -------------------------------------------------------------
        # Optional terminal-based fallback.
        #
        # This supports future/generalized topology elements without
        # forcing the topology manager to depend on a concrete
        # Terminal implementation.
        # -------------------------------------------------------------

        terminals = getattr(element, "terminals", None)

        if terminals is not None:

            try:
                terminals = list(terminals)
            except TypeError:
                terminals = None

            if terminals is not None and len(terminals) >= 2:

                bus_a = getattr(
                    terminals[0],
                    "bus",
                    None,
                )

                bus_b = getattr(
                    terminals[1],
                    "bus",
                    None,
                )

                if bus_a is not None and bus_b is not None:
                    return bus_a, bus_b

        return None

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    def is_connected(
        self,
        bus_a: Any,
        bus_b: Any,
    ) -> bool:
        """
        Determine whether two buses are electrically connected.

        Parameters
        ----------
        bus_a :
            Bus object or bus ID.

        bus_b :
            Bus object or bus ID.

        Returns
        -------
        bool
            True when a path exists between the two buses.
        """

        self.build()

        a = bus_a.id if hasattr(bus_a, "id") else bus_a
        b = bus_b.id if hasattr(bus_b, "id") else bus_b

        if a not in self.graph:
            return False

        if b not in self.graph:
            return False

        return nx.has_path(
            self.graph,
            a,
            b,
        )

    # =================================================================
    # ISLAND DETECTION
    # =================================================================

    def find_islands(self) -> list[list[Any]]:
        """
        Return the electrical islands of the current topology.

        Returns
        -------
        list[list]
            Each list contains the bus IDs belonging to one
            electrically connected island.

        Notes
        -----
        Isolated buses are valid islands containing one bus.
        """

        self.build()

        return [
            list(component)
            for component in nx.connected_components(
                self.graph
            )
        ]

    # =================================================================
    # ISLANDING CHECK
    # =================================================================

    def has_islanding(self) -> bool:
        """
        Return True when the network contains more than one island.
        """

        return len(self.find_islands()) > 1

    # =================================================================
    # ELEMENT STATUS
    # =================================================================

    def open_element(
        self,
        element: Any,
    ) -> None:
        """
        Open an electrical topology element.

        The canonical model object remains owned by the Network.
        Only its service state is changed.
        """

        self._require_service_state(element)

        element.in_service = False
        self._dirty = True

    def close_element(
        self,
        element: Any,
    ) -> None:
        """
        Close an electrical topology element.
        """

        self._require_service_state(element)

        element.in_service = True
        self._dirty = True

    @staticmethod
    def _require_service_state(
        element: Any,
    ) -> None:
        """
        Validate that an element exposes service state.
        """

        if element is None:
            raise ValueError(
                "Topology element cannot be None."
            )

        if not hasattr(element, "in_service"):
            raise AttributeError(
                "Topology element does not provide "
                "'in_service' state."
            )

    # =================================================================
    # CONTINGENCY SUPPORT
    # =================================================================

    def simulate_outage(
        self,
        element: Any,
    ) -> dict[str, Any]:
        """
        Temporarily remove an element and report topology impact.

        Parameters
        ----------
        element :
            Canonical topology-forming element.

        Returns
        -------
        dict
            Contains:

                element
                    Element name or representation.

                islanded
                    True when the outage creates multiple islands.

                islands
                    Bus IDs grouped by resulting island.

        Notes
        -----
        The original service state is restored before this method
        returns.

        This is a topology-only operation. It does not alter Y-bus,
        solve power flow, or perform a complete contingency study.
        """

        self._require_service_state(element)

        original = element.in_service

        try:
            element.in_service = False
            self._dirty = True

            islands = self.find_islands()

            return {
                "element": getattr(
                    element,
                    "name",
                    str(element),
                ),
                "islanded": len(islands) > 1,
                "islands": islands,
            }

        finally:
            element.in_service = original
            self._dirty = True
            self.build()

    # =================================================================
    # GRAPH ACCESS
    # =================================================================

    def get_graph(self):
        """
        Return the current topology graph.
        """

        return self.build()

    # =================================================================
    # SUMMARY
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return a concise topology summary.
        """

        self.build()

        return {
            "buses": self.graph.number_of_nodes(),
            "connections": self.graph.number_of_edges(),
            "islands": len(
                list(
                    nx.connected_components(
                        self.graph
                    )
                )
            ),
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        self.build()

        return (
            f"<TopologyManager "
            f"buses={self.graph.number_of_nodes()}, "
            f"connections={self.graph.number_of_edges()}, "
            f"islands={len(list(nx.connected_components(self.graph)))}>"
        )
