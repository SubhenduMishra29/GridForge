"""
GridForge Network Topology Manager
==================================

GridForge Network Layer V2

Maintains the electrical connectivity graph of an assembled
GridForge Network.

Responsibilities
----------------
- Build the network connectivity graph.
- Represent buses as graph nodes.
- Represent topology-forming branches as graph edges.
- Respect element in-service state.
- Determine electrical connectivity.
- Detect electrical islands.
- Support element open/close operations.
- Support non-persistent outage simulation.
- Provide topology diagnostics.

Does NOT
--------
- Define electrical equipment models.
- Perform power-flow calculations.
- Build Y-bus numerical stamps.
- Perform short-circuit calculations.
- Perform protection calculations.
- Perform dynamic simulation.
- Perform engineering validation.
- Own canonical electrical objects.

Architecture
------------
    core/model/
        Canonical electrical entities
                |
                v
    core/network/
        Network
        TopologyManager
        PerUnitSystem
        YBusBuilder
                |
                v
    core/analysis/
        Study orchestration
                |
                v
    core/solver/
        Numerical algorithms

Topology Principle
------------------
The topology manager operates on canonical objects already owned by
the Network.

It does not create replacement Bus, Line, Transformer, Breaker, or
other electrical model objects.

Graph representation
--------------------
A NetworkX MultiGraph is used because multiple physical electrical
connections may exist between the same pair of buses.

Nodes:
    bus.id

Edges:
    physical topology-forming network elements

Each edge stores:

    element
        Reference to the canonical model object.

    type
        Logical element type.

Current V2 topology-forming branch classes are:

    - Line
    - Transformer

Switching-device topology can be extended when the Network exposes
those canonical switching elements to the topology layer.

Service State
-------------
Elements with:

    in_service == False

are excluded from the active topology graph.

Changing an element's service state invalidates both:

    - topology
    - topology-dependent network representations such as Y-bus

The Network remains the owner of network-level invalidation.

GridForge V2 Status
-------------------
This module is part of the GridForge Network Layer V2 audit/freeze
baseline.

Changes require evidence of a fundamental topology requirement that
cannot be satisfied by the existing model, network, or analysis
architecture.

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
    Manage electrical connectivity for an assembled GridForge Network.

    Parameters
    ----------
    network :
        Owning GridForge Network instance.

    Notes
    -----
    The manager maintains a derived graph.

    The graph is never the source of truth for electrical equipment.
    Canonical model objects remain owned by the Network/model layers.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(self, network: Any) -> None:
        """
        Initialize the topology manager.
        """

        if network is None:
            raise ValueError(
                "TopologyManager requires a Network instance."
            )

        self.network = network

        # -------------------------------------------------------------
        # MultiGraph is intentional.
        #
        # Parallel lines/transformers between the same buses are
        # electrically valid and must remain independently represented.
        # -------------------------------------------------------------

        self.graph = nx.MultiGraph()

        self._dirty = True

    # =================================================================
    # INTERNAL INVALIDATION
    # =================================================================

    def _invalidate(self) -> None:
        """
        Invalidate the derived topology graph and notify the Network.

        Network-level invalidation is attempted through the owning
        Network's private invalidation hook.

        This keeps topology-changing operations synchronized with
        Y-bus and other topology-dependent network state.
        """

        self._dirty = True

        invalidate = getattr(
            self.network,
            "_invalidate_topology",
            None,
        )

        if callable(invalidate):
            invalidate()

    # =================================================================
    # GRAPH BUILD
    # =================================================================

    def build(self) -> nx.MultiGraph:
        """
        Build and return the current electrical topology graph.

        Returns
        -------
        networkx.MultiGraph
            Derived electrical connectivity graph.

        Notes
        -----
        Only in-service topology-forming elements are included.

        The method is idempotent while topology remains unchanged.
        """

        if not self._dirty:
            return self.graph

        self.graph.clear()

        # -------------------------------------------------------------
        # BUS NODES
        # -------------------------------------------------------------

        for bus in self.network.buses:

            if not hasattr(bus, "id"):
                raise TypeError(
                    "Every network bus must provide an 'id' attribute."
                )

            self.graph.add_node(
                bus.id,
                element=bus,
                type="bus",
            )

        # -------------------------------------------------------------
        # LINES
        # -------------------------------------------------------------

        for line in getattr(
            self.network,
            "lines",
            [],
        ):

            self._add_branch_edge(
                line,
                "line",
            )

        # -------------------------------------------------------------
        # TRANSFORMERS
        # -------------------------------------------------------------

        for transformer in getattr(
            self.network,
            "transformers",
            [],
        ):

            self._add_branch_edge(
                transformer,
                "transformer",
            )

        self._dirty = False

        return self.graph

    # =================================================================
    # BRANCH GRAPH SUPPORT
    # =================================================================

    def _add_branch_edge(
        self,
        element: Any,
        element_type: str,
    ) -> None:
        """
        Add a topology-forming branch to the graph.

        Parameters
        ----------
        element :
            Canonical branch-like model object.

        element_type : str
            Logical topology element type.

        Notes
        -----
        Elements that are out of service are ignored.

        A branch whose endpoints are identical is ignored because it
        does not provide inter-bus connectivity.

        Missing endpoints are treated as structural errors because
        topology cannot be constructed safely without them.
        """

        if not getattr(
            element,
            "in_service",
            True,
        ):
            return

        from_bus = getattr(
            element,
            "from_bus",
            None,
        )

        to_bus = getattr(
            element,
            "to_bus",
            None,
        )

        if from_bus is None or to_bus is None:
            raise AttributeError(
                f"{element_type.capitalize()} topology element "
                "must provide from_bus and to_bus."
            )

        if not hasattr(from_bus, "id"):
            raise AttributeError(
                f"{element_type.capitalize()} from_bus must "
                "provide an 'id' attribute."
            )

        if not hasattr(to_bus, "id"):
            raise AttributeError(
                f"{element_type.capitalize()} to_bus must "
                "provide an 'id' attribute."
            )

        u = from_bus.id
        v = to_bus.id

        # -------------------------------------------------------------
        # Ignore self-connections.
        # -------------------------------------------------------------

        if u == v:
            return

        # -------------------------------------------------------------
        # Ensure endpoints actually exist in the network graph.
        # -------------------------------------------------------------

        if u not in self.graph:
            raise ValueError(
                f"{element_type.capitalize()} '{getattr(element, 'id', element)}' "
                f"references unregistered from_bus '{u}'."
            )

        if v not in self.graph:
            raise ValueError(
                f"{element_type.capitalize()} '{getattr(element, 'id', element)}' "
                f"references unregistered to_bus '{v}'."
            )

        self.graph.add_edge(
            u,
            v,
            element=element,
            type=element_type,
        )

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

        Raises
        ------
        KeyError
            If either bus is not present in the topology graph.
        """

        self.build()

        a = (
            bus_a.id
            if hasattr(bus_a, "id")
            else bus_a
        )

        b = (
            bus_b.id
            if hasattr(bus_b, "id")
            else bus_b
        )

        if a not in self.graph:
            raise KeyError(
                f"Unknown topology bus: {a}"
            )

        if b not in self.graph:
            raise KeyError(
                f"Unknown topology bus: {b}"
            )

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
        Return the electrical islands in the current topology.

        Returns
        -------
        list[list]
            Each inner list contains bus IDs belonging to one
            connected electrical island.

        Notes
        -----
        Isolated buses are valid islands consisting of one bus.
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

        return len(
            self.find_islands()
        ) > 1

    # =================================================================
    # ELEMENT STATUS
    # =================================================================

    def open_element(
        self,
        element: Any,
    ) -> None:
        """
        Open a topology-forming element.

        Parameters
        ----------
        element :
            Canonical network element.

        Notes
        -----
        This changes the element's service state and invalidates
        topology-dependent network state.
        """

        if element is None:
            raise ValueError(
                "Element cannot be None."
            )

        if not hasattr(
            element,
            "in_service",
        ):
            raise AttributeError(
                "Element does not provide an "
                "'in_service' state."
            )

        element.in_service = False

        self._invalidate()

    # -----------------------------------------------------------------

    def close_element(
        self,
        element: Any,
    ) -> None:
        """
        Close a topology-forming element.

        Parameters
        ----------
        element :
            Canonical network element.

        Notes
        -----
        This changes the element's service state and invalidates
        topology-dependent network state.
        """

        if element is None:
            raise ValueError(
                "Element cannot be None."
            )

        if not hasattr(
            element,
            "in_service",
        ):
            raise AttributeError(
                "Element does not provide an "
                "'in_service' state."
            )

        element.in_service = True

        self._invalidate()

    # =================================================================
    # CONTINGENCY SUPPORT
    # =================================================================

    def simulate_outage(
        self,
        element: Any,
    ) -> dict[str, Any]:
        """
        Simulate a temporary element outage.

        Parameters
        ----------
        element :
            Canonical network element.

        Returns
        -------
        dict
            Outage diagnostic information containing:

                element
                islanded
                islands

        Notes
        -----
        The original element service state is always restored.

        This method does not permanently modify network topology.

        Numerical contingency studies should normally use the
        appropriate analysis layer rather than relying on this
        convenience method for complete study execution.
        """

        if element is None:
            raise ValueError(
                "Element cannot be None."
            )

        if not hasattr(
            element,
            "in_service",
        ):
            raise AttributeError(
                "Element does not provide an "
                "'in_service' state."
            )

        original_state = bool(
            element.in_service
        )

        try:
            element.in_service = False

            self._invalidate()

            islands = self.find_islands()

            return {
                "element": getattr(
                    element,
                    "name",
                    getattr(
                        element,
                        "id",
                        str(element),
                    ),
                ),
                "islanded": len(islands) > 1,
                "islands": islands,
            }

        finally:
            element.in_service = original_state

            self._invalidate()

            # Rebuild immediately so the manager does not retain a
            # temporary outage graph after the method returns.
            self.build()

    # =================================================================
    # GRAPH ACCESS
    # =================================================================

    def get_graph(self) -> nx.MultiGraph:
        """
        Return the current derived topology graph.

        The graph is rebuilt automatically when topology is dirty.
        """

        return self.build()

    # =================================================================
    # SUMMARY
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return concise topology diagnostics.
        """

        self.build()

        return {
            "buses": self.graph.number_of_nodes(),
            "connections": self.graph.number_of_edges(),
            "islands": nx.number_connected_components(
                self.graph
            ),
            "dirty": self._dirty,
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
            f"islands={nx.number_connected_components(self.graph)}, "
            f"dirty={self._dirty}>"
        )
