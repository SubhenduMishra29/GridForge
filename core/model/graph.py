```python
"""
GridForge Network Graph
=======================

File:
    core/model/graph.py

Defines the topology manager for the GridForge electrical network.

Responsibilities
----------------
- Maintain bus topology.
- Maintain line connectivity.
- Provide topology queries.
- Provide stable bus/line iteration.
- Bind UI references to electrical model objects.
- Provide solver-independent topology information.

The Graph model does NOT:
- Build Ybus.
- Calculate power flow.
- Calculate branch flows.
- Perform fault calculations.
- Solve numerical systems.
- Perform protection calculations.

Those responsibilities belong to the appropriate network,
analysis, solver, protection, or simulation layers.

Architecture
------------
Grid
    ↓
Electrical model / component registry

Graph
    ↓
Topology and connectivity

Network / Solver
    ↓
Ybus and numerical analysis

GUI
    ↓
Visualization and interaction

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Dict, List

from .bus import Bus
from .line import Line


class Graph:
    """
    GridForge topology manager.

    The Graph maintains connectivity between buses and lines.

    It is intentionally separate from Grid so that topology
    operations can be used by the UI and network-management
    layers without embedding numerical calculations.

    Notes
    -----
    Bus IDs are the authoritative topology references.

    Actual Bus objects may additionally be attached to Line
    instances for UI/topology operations.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self):
        """
        Initialize an empty topology graph.
        """

        # -----------------------------------------------------
        # Bus registry
        # -----------------------------------------------------

        self.buses: Dict[str, Bus] = {}

        # -----------------------------------------------------
        # Ordered line registry
        # -----------------------------------------------------

        self.lines: List[Line] = []

    # =========================================================
    # BUS MANAGEMENT
    # =========================================================

    def add_bus(
        self,
        bus: Bus
    ) -> None:
        """
        Add an existing Bus to the graph.
        """

        if not isinstance(
            bus,
            Bus
        ):
            raise TypeError(
                "add_bus() requires a Bus object"
            )

        if bus.id in self.buses:

            raise ValueError(
                f"Bus '{bus.id}' already exists"
            )

        self.buses[bus.id] = bus

    def remove_bus(
        self,
        bus_id: str
    ) -> None:
        """
        Remove a bus and all connected lines.

        Parameters
        ----------
        bus_id:
            ID of the bus to remove.

        Notes
        -----
        Removing a bus also removes topology references to all
        connected lines.
        """

        if bus_id not in self.buses:
            return

        # -----------------------------------------------------
        # Remove connected lines
        # -----------------------------------------------------

        connected = [
            line
            for line in self.lines
            if (
                line.from_bus == bus_id
                or line.to_bus == bus_id
            )
        ]

        for line in connected:
            self.remove_line(line)

        # -----------------------------------------------------
        # Remove bus
        # -----------------------------------------------------

        del self.buses[bus_id]

    def get_bus(
        self,
        bus_id: str
    ) -> Bus | None:
        """
        Return a bus by ID.

        Returns None if the bus does not exist.
        """

        return self.buses.get(
            bus_id
        )

    def require_bus(
        self,
        bus_id: str
    ) -> Bus:
        """
        Return a bus by ID.

        Raises
        ------
        KeyError
            If the bus does not exist.
        """

        try:

            return self.buses[bus_id]

        except KeyError as exc:

            raise KeyError(
                f"Bus '{bus_id}' does not exist"
            ) from exc

    def all_buses(self) -> List[Bus]:
        """
        Return buses in stable insertion order.
        """

        return list(
            self.buses.values()
        )

    # =========================================================
    # LINE MANAGEMENT
    # =========================================================

    def add_line(
        self,
        from_bus_id: str,
        to_bus_id: str,
        r_pu: float,
        x_pu: float,
        b_pu: float = 0.0,
        name: str | None = None,
        rate_mva: float = 100.0,
    ) -> Line:
        """
        Create and register a transmission line.

        Parameters
        ----------
        from_bus_id:
            Sending-end bus ID.

        to_bus_id:
            Receiving-end bus ID.

        r_pu:
            Series resistance in per-unit.

        x_pu:
            Series reactance in per-unit.

        b_pu:
            Total shunt susceptance in per-unit.

        name:
            Optional line name.

        rate_mva:
            Thermal rating in MVA.

        Returns
        -------
        Line
            Newly created line.
        """

        # -----------------------------------------------------
        # Validate buses
        # -----------------------------------------------------

        if from_bus_id not in self.buses:

            raise ValueError(
                f"Bus '{from_bus_id}' not found"
            )

        if to_bus_id not in self.buses:

            raise ValueError(
                f"Bus '{to_bus_id}' not found"
            )

        if from_bus_id == to_bus_id:

            raise ValueError(
                "Line cannot connect a bus to itself"
            )

        # -----------------------------------------------------
        # Prevent duplicate topology
        # -----------------------------------------------------

        if self.has_connection(
            from_bus_id,
            to_bus_id
        ):

            raise ValueError(
                "A line already exists between "
                f"'{from_bus_id}' and '{to_bus_id}'"
            )

        # -----------------------------------------------------
        # Create electrical line
        # -----------------------------------------------------

        line = Line(
            from_bus=from_bus_id,
            to_bus=to_bus_id,
            r_pu=r_pu,
            x_pu=x_pu,
            b_pu=b_pu,
            name=name,
            rate_mva=rate_mva,
        )

        # -----------------------------------------------------
        # Bind actual Bus objects.
        #
        # This is useful for topology/UI geometry.
        # Solver identity remains the bus ID.
        # -----------------------------------------------------

        line.bind_buses(
            self.buses[from_bus_id],
            self.buses[to_bus_id]
        )

        self.lines.append(
            line
        )

        return line

    def add_existing_line(
        self,
        line: Line
    ) -> None:
        """
        Add an already-created Line object.

        Useful when loading a network model from a file.
        """

        if not isinstance(
            line,
            Line
        ):
            raise TypeError(
                "add_existing_line() requires a Line object"
            )

        if line.from_bus not in self.buses:

            raise ValueError(
                f"Bus '{line.from_bus}' not found"
            )

        if line.to_bus not in self.buses:

            raise ValueError(
                f"Bus '{line.to_bus}' not found"
            )

        if self.has_connection(
            line.from_bus,
            line.to_bus
        ):

            raise ValueError(
                "A line already exists between "
                f"'{line.from_bus}' and "
                f"'{line.to_bus}'"
            )

        line.bind_buses(
            self.buses[line.from_bus],
            self.buses[line.to_bus]
        )

        self.lines.append(
            line
        )

    def remove_line(
        self,
        line: Line
    ) -> None:
        """
        Remove a line from the topology.
        """

        if line in self.lines:

            self.lines.remove(
                line
            )

    def all_lines(self) -> List[Line]:
        """
        Return lines in stable insertion order.
        """

        return list(
            self.lines
        )

    # =========================================================
    # TOPOLOGY QUERIES
    # =========================================================

    def has_connection(
        self,
        from_bus_id: str,
        to_bus_id: str
    ) -> bool:
        """
        Check whether a line exists between two buses.

        Direction is ignored for topology purposes.
        """

        for line in self.lines:

            if (
                line.from_bus == from_bus_id
                and line.to_bus == to_bus_id
            ):

                return True

            if (
                line.from_bus == to_bus_id
                and line.to_bus == from_bus_id
            ):

                return True

        return False

    def get_connected_lines(
        self,
        bus_id: str
    ) -> List[Line]:
        """
        Return all lines connected to a bus.
        """

        if bus_id not in self.buses:

            raise KeyError(
                f"Bus '{bus_id}' does not exist"
            )

        return [
            line
            for line in self.lines
            if (
                line.from_bus == bus_id
                or line.to_bus == bus_id
            )
        ]

    def get_neighbors(
        self,
        bus_id: str
    ) -> List[Bus]:
        """
        Return buses directly connected to a bus.
        """

        if bus_id not in self.buses:

            raise KeyError(
                f"Bus '{bus_id}' does not exist"
            )

        neighbors: List[Bus] = []

        for line in self.get_connected_lines(
            bus_id
        ):

            if line.from_bus == bus_id:

                neighbor_id = line.to_bus

            else:

                neighbor_id = line.from_bus

            neighbor = self.buses.get(
                neighbor_id
            )

            if neighbor is not None:

                neighbors.append(
                    neighbor
                )

        return neighbors

    def degree(
        self,
        bus_id: str
    ) -> int:
        """
        Return the topological degree of a bus.
        """

        return len(
            self.get_connected_lines(
                bus_id
            )
        )

    # =========================================================
    # BUS INDEXING
    # =========================================================

    def get_bus_index_map(self) -> Dict[str, int]:
        """
        Return a stable bus-ID → numerical-index mapping.

        This method provides indexing information to numerical
        layers but does not perform numerical calculations.

        The ordering corresponds to ``all_buses()``.
        """

        return {
            bus.id: index
            for index, bus in enumerate(
                self.all_buses()
            )
        }

    # =========================================================
    # CONNECTIVITY
    # =========================================================

    def is_isolated(
        self,
        bus_id: str
    ) -> bool:
        """
        Return True when a bus has no connected lines.
        """

        return (
            self.degree(bus_id)
            == 0
        )

    def connected_component(
        self,
        bus_id: str
    ) -> List[Bus]:
        """
        Return the connected component containing a bus.

        Uses a simple breadth-first traversal.

        This is a topology operation only.
        """

        if bus_id not in self.buses:

            raise KeyError(
                f"Bus '{bus_id}' does not exist"
            )

        visited = set()

        queue = [
            bus_id
        ]

        while queue:

            current = queue.pop(
                0
            )

            if current in visited:
                continue

            visited.add(
                current
            )

            for neighbor in self.get_neighbors(
                current
            ):

                if neighbor.id not in visited:

                    queue.append(
                        neighbor.id
                    )

        return [
            self.buses[bus_id]
            for bus_id in self.buses
            if bus_id in visited
        ]

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate(self) -> bool:
        """
        Validate topology and connectivity references.

        Returns
        -------
        bool
            True when topology is structurally valid.
        """

        # -----------------------------------------------------
        # Validate buses
        # -----------------------------------------------------

        for bus_id, bus in self.buses.items():

            if bus.id != bus_id:

                raise ValueError(
                    f"Bus registry key '{bus_id}' "
                    f"does not match Bus ID '{bus.id}'"
                )

        # -----------------------------------------------------
        # Validate lines
        # -----------------------------------------------------

        for line in self.lines:

            if line.from_bus not in self.buses:

                raise ValueError(
                    f"Line '{line.name}' references "
                    f"unknown bus '{line.from_bus}'"
                )

            if line.to_bus not in self.buses:

                raise ValueError(
                    f"Line '{line.name}' references "
                    f"unknown bus '{line.to_bus}'"
                )

            if line.from_bus == line.to_bus:

                raise ValueError(
                    f"Line '{line.name}' connects "
                    "a bus to itself"
                )

            # -------------------------------------------------
            # Ensure UI references remain synchronized.
            # -------------------------------------------------

            if (
                line.from_bus_ref
                is not self.buses[line.from_bus]
            ):

                line.bind_buses(
                    self.buses[line.from_bus],
                    self.buses[line.to_bus]
                )

            elif (
                line.to_bus_ref
                is not self.buses[line.to_bus]
            ):

                line.bind_buses(
                    self.buses[line.from_bus],
                    self.buses[line.to_bus]
                )

        return True

    # =========================================================
    # COUNTS
    # =========================================================

    @property
    def bus_count(self) -> int:
        """
        Number of buses.
        """

        return len(
            self.buses
        )

    @property
    def line_count(self) -> int:
        """
        Number of lines.
        """

        return len(
            self.lines
        )

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(self) -> dict:
        """
        Return structured topology information.
        """

        return {
            "buses": self.bus_count,
            "lines": self.line_count,
            "connected": (
                self.bus_count > 0
                and self.line_count > 0
            ),
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<Graph "
            f"buses={self.bus_count}, "
            f"lines={self.line_count}>"
        )
```
