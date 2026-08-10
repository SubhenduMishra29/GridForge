# ============================================================
# File: core/model/graph.py
# GridForge Network Graph (Topology Manager)
# ============================================================

from typing import Dict, List

from core.models.bus import Bus
from core.models.line import Line


class Graph:
    """
    Central topology container for the power network.

    Responsibilities:
    -----------------
    - Store buses and lines
    - Maintain connectivity
    - Bind UI + Solver layers together
    - Provide safe access APIs

    Design Principles:
    ------------------
    - Buses indexed by ID (fast lookup)
    - Lines stored as list (ordered iteration)
    - Dual compatibility (UI + Solver)
    """

    def __init__(self):
        # -------------------------
        # Core storage
        # -------------------------

        self.buses: Dict[str, Bus] = {}
        self.lines: List[Line] = []

    # =====================================================
    # BUS MANAGEMENT
    # =====================================================

    def add_bus(self, bus: Bus):
        """
        Add a bus to the network.
        """

        if bus.id in self.buses:
            raise ValueError(f"Bus '{bus.id}' already exists")

        self.buses[bus.id] = bus

    def remove_bus(self, bus_id: str):
        """
        Remove a bus and all connected lines.
        """

        if bus_id not in self.buses:
            return

        # Remove connected lines
        self.lines = [
            line for line in self.lines
            if line.from_bus != bus_id and line.to_bus != bus_id
        ]

        del self.buses[bus_id]

    def get_bus(self, bus_id: str) -> Bus:
        return self.buses.get(bus_id)

    def all_buses(self) -> List[Bus]:
        return list(self.buses.values())

    # =====================================================
    # LINE MANAGEMENT
    # =====================================================

    def add_line(
        self,
        from_bus_id: str,
        to_bus_id: str,
        r: float,
        x: float,
        b: float = 0.0,
        name: str = None,
    ) -> Line:
        """
        Create and register a new line.

        This method:
        - Validates bus existence
        - Creates line
        - Binds UI references
        - Stores in graph
        """

        if from_bus_id not in self.buses:
            raise ValueError(f"Bus '{from_bus_id}' not found")

        if to_bus_id not in self.buses:
            raise ValueError(f"Bus '{to_bus_id}' not found")

        # Prevent duplicate connections (optional strictness)
        for line in self.lines:
            if (
                line.from_bus == from_bus_id
                and line.to_bus == to_bus_id
            ) or (
                line.from_bus == to_bus_id
                and line.to_bus == from_bus_id
            ):
                raise ValueError("Line already exists between these buses")

        # Create line
        line = Line(
            from_bus=from_bus_id,
            to_bus=to_bus_id,
            r_pu=r,
            x_pu=x,
            b_pu=b,
            name=name,
        )

        # 🔥 CRITICAL: Bind UI references
        line.bind_buses(
            self.buses[from_bus_id],
            self.buses[to_bus_id],
        )

        self.lines.append(line)

        return line

    def remove_line(self, line: Line):
        """
        Remove a line from the network.
        """

        if line in self.lines:
            self.lines.remove(line)

    def all_lines(self) -> List[Line]:
        return self.lines

    # =====================================================
    # TOPOLOGY HELPERS
    # =====================================================

    def get_connected_lines(self, bus_id: str) -> List[Line]:
        """
        Return all lines connected to a bus.
        """

        return [
            line for line in self.lines
            if line.from_bus == bus_id or line.to_bus == bus_id
        ]

    def get_neighbors(self, bus_id: str) -> List[Bus]:
        """
        Return neighboring buses.
        """

        neighbors = []

        for line in self.get_connected_lines(bus_id):
            if line.from_bus == bus_id:
                neighbors.append(self.buses[line.to_bus])
            else:
                neighbors.append(self.buses[line.from_bus])

        return neighbors

    # =====================================================
    # SOLVER SUPPORT
    # =====================================================

    def get_bus_index_map(self) -> Dict[str, int]:
        """
        Map bus IDs to solver indices.
        """

        return {
            bus_id: idx
            for idx, bus_id in enumerate(self.buses.keys())
        }

    def build_ybus(self):
        """
        Construct Y-bus admittance matrix.

        Returns:
            numpy.ndarray
        """

        import numpy as np

        n = len(self.buses)
        ybus = np.zeros((n, n), dtype=complex)

        bus_index = self.get_bus_index_map()

        for line in self.lines:

            if not line.in_service:
                continue

            i = bus_index[line.from_bus]
            j = bus_index[line.to_bus]

            y = line.y_pu

            # Off-diagonal
            ybus[i, j] -= y
            ybus[j, i] -= y

            # Diagonal
            ybus[i, i] += y + complex(0, line.b_pu / 2)
            ybus[j, j] += y + complex(0, line.b_pu / 2)

        return ybus

    # =====================================================
    # DEBUG / INFO
    # =====================================================

    def __repr__(self):
        return (
            f"Graph(Buses={len(self.buses)}, "
            f"Lines={len(self.lines)})"
        )
