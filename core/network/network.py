```python
"""
GridForge Network
=================

Central assembled-network container for GridForge.

Responsibilities
----------------
- Maintain collections of canonical electrical model objects.
- Maintain the system MVA base.
- Maintain deterministic bus indexing.
- Coordinate topology management.
- Coordinate Y-bus construction.
- Maintain network-derived state and study state.
- Provide lightweight network-level utilities.

Does NOT
--------
- Implement numerical power-flow algorithms.
- Implement Newton-Raphson/Jacobian calculations.
- Implement short-circuit mathematics.
- Implement protection algorithms.
- Implement transient/dynamic numerical integration.
- Implement engineering validation rules.
- Define electrical equipment models.

Architecture
------------

    core/model/
        Canonical electrical entities
              |
              v
    core/network/
        Assembled network
        topology
        per-unit system
        Y-bus representation
              |
              v
    core/analysis/
        Engineering study orchestration
              |
              v
    core/solver/
        Numerical algorithms

Important
---------
core/model is the single source of truth for electrical entities.

core/network does not define duplicate Bus, Generator, Load,
Line, Transformer, or other equipment classes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .per_unit import PerUnitSystem
from .topology import TopologyManager
from .ybus import YBusBuilder


class Network:
    """
    Assembled GridForge electrical network.

    The Network object contains references to canonical objects
    defined under ``core.model`` and provides network-level
    services such as topology and Y-bus construction.

    Parameters
    ----------
    base_mva:
        System-wide apparent-power base in MVA.

    Notes
    -----
    Network is intentionally independent of specific numerical
    solver implementations.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self, base_mva: float = 100.0) -> None:

        if base_mva <= 0.0:
            raise ValueError(
                "Network base MVA must be positive."
            )

        self.base_mva = float(base_mva)

        # -----------------------------------------------------
        # SYSTEM SERVICES
        # -----------------------------------------------------

        self.per_unit = PerUnitSystem(
            base_mva=self.base_mva
        )

        # -----------------------------------------------------
        # CANONICAL MODEL COLLECTIONS
        #
        # Objects stored here must originate from core.model.
        # Network does not redefine those electrical models.
        # -----------------------------------------------------

        self.buses: List[Any] = []
        self.lines: List[Any] = []
        self.transformers: List[Any] = []
        self.generators: List[Any] = []
        self.loads: List[Any] = []
        self.shunts: List[Any] = []

        # -----------------------------------------------------
        # DERIVED BUS INDEX
        #
        # bus.id -> numerical matrix index
        # -----------------------------------------------------

        self.bus_index: Dict[Any, int] = {}

        # -----------------------------------------------------
        # DERIVED NETWORK REPRESENTATIONS
        # -----------------------------------------------------

        self.Ybus = None

        # -----------------------------------------------------
        # NETWORK SERVICES
        # -----------------------------------------------------

        self.topology = TopologyManager(self)
        self.ybus_builder = YBusBuilder(self)

        # -----------------------------------------------------
        # NETWORK STATE
        # -----------------------------------------------------

        self.active_fault: Optional[Dict[str, Any]] = None

        # Network revision counters are preferable to relying
        # exclusively on loosely coordinated dirty flags.
        self._topology_revision = 0
        self._ybus_revision = -1

        # Backward-compatible dirty flags.
        self._topology_dirty = True
        self._ybus_dirty = True

    # =========================================================
    # ELEMENT MANAGEMENT
    # =========================================================

    def add_bus(self, bus: Any) -> None:
        """
        Add a canonical Bus model to the network.

        Bus IDs must be unique.
        """

        if bus is None:
            raise ValueError(
                "Cannot add None as a bus."
            )

        if not hasattr(bus, "id"):
            raise TypeError(
                "Bus object must provide an 'id' attribute."
            )

        if bus.id in self.bus_index:
            raise ValueError(
                f"Duplicate bus ID: {bus.id}"
            )

        for existing in self.buses:
            if existing.id == bus.id:
                raise ValueError(
                    f"Duplicate bus ID: {bus.id}"
                )

        self.buses.append(bus)
        self._invalidate_topology()

    # ---------------------------------------------------------

    def add_line(self, line: Any) -> None:
        """
        Add a canonical Line model to the network.
        """

        self._require_element(line, "line")

        self.lines.append(line)
        self._invalidate_topology()

    # ---------------------------------------------------------

    def add_transformer(self, transformer: Any) -> None:
        """
        Add a canonical Transformer model to the network.
        """

        self._require_element(
            transformer,
            "transformer"
        )

        self.transformers.append(transformer)
        self._invalidate_topology()

    # ---------------------------------------------------------

    def add_generator(self, generator: Any) -> None:
        """
        Add a canonical Generator model to the network.
        """

        self._require_element(
            generator,
            "generator"
        )

        self.generators.append(generator)

    # ---------------------------------------------------------

    def add_load(self, load: Any) -> None:
        """
        Add a canonical Load model to the network.
        """

        self._require_element(load, "load")

        self.loads.append(load)

    # ---------------------------------------------------------

    def add_shunt(self, shunt: Any) -> None:
        """
        Add a canonical Shunt model to the network.
        """

        self._require_element(shunt, "shunt")

        self.shunts.append(shunt)
        self._invalidate_ybus()

    # ---------------------------------------------------------

    @staticmethod
    def _require_element(
        element: Any,
        element_type: str
    ) -> None:
        """
        Perform minimal structural validation.

        Detailed engineering validation belongs to
        core/validation/.
        """

        if element is None:
            raise ValueError(
                f"Cannot add None as a {element_type}."
            )

    # =========================================================
    # INVALIDATION
    # =========================================================

    def _invalidate_topology(self) -> None:
        """
        Mark topology and all topology-dependent representations
        as invalid.
        """

        self._topology_revision += 1

        self._topology_dirty = True
        self._ybus_dirty = True

        self._ybus_revision = -1

        if hasattr(self.topology, "_dirty"):
            self.topology._dirty = True

    # ---------------------------------------------------------

    def _invalidate_ybus(self) -> None:
        """
        Mark Y-bus as invalid without necessarily changing
        network topology.
        """

        self._ybus_dirty = True
        self._ybus_revision = -1

    # =========================================================
    # BUS INDEXING
    # =========================================================

    def rebuild_bus_index(self) -> Dict[Any, int]:
        """
        Rebuild the deterministic bus-ID to matrix-index mapping.

        Returns
        -------
        dict
            Mapping ``bus.id -> numerical index``.
        """

        index: Dict[Any, int] = {}

        for position, bus in enumerate(self.buses):

            if not hasattr(bus, "id"):
                raise TypeError(
                    "Every bus must provide an 'id' attribute."
                )

            if bus.id in index:
                raise ValueError(
                    f"Duplicate bus ID: {bus.id}"
                )

            index[bus.id] = position

        self.bus_index = index

        return self.bus_index

    # =========================================================
    # TOPOLOGY
    # =========================================================

    def rebuild_topology(self):
        """
        Rebuild and return the network topology graph.
        """

        graph = self.topology.build()

        self._topology_dirty = False

        return graph

    # ---------------------------------------------------------

    def find_islands(self):
        """
        Return the electrical network islands.

        Island detection itself is implemented by
        TopologyManager.
        """

        return self.topology.find_islands()

    # ---------------------------------------------------------

    def is_connected(
        self,
        bus_a: Any,
        bus_b: Any
    ) -> bool:
        """
        Determine whether two buses are electrically connected.
        """

        return self.topology.is_connected(
            bus_a,
            bus_b
        )

    # =========================================================
    # Y-BUS
    # =========================================================

    def build_ybus(self):
        """
        Build and return the network Y-bus.

        Y-bus mathematics is implemented exclusively by
        YBusBuilder.

        Returns
        -------
        scipy.sparse.csr_matrix
            Network admittance matrix.
        """

        self.rebuild_bus_index()

        ybus = self.ybus_builder.build()

        self.Ybus = ybus

        self._ybus_dirty = False
        self._ybus_revision = self._topology_revision

        return self.Ybus

    # ---------------------------------------------------------

    def get_ybus(self):
        """
        Return the current Y-bus.

        Rebuilds it automatically when invalid.
        """

        if (
            self.Ybus is None
            or self._ybus_dirty
            or self._ybus_revision != self._topology_revision
        ):
            return self.build_ybus()

        return self.Ybus

    # =========================================================
    # NETWORK RECONFIGURATION
    # =========================================================

    def reconfigure(self):
        """
        Rebuild topology and Y-bus after network changes.

        Returns
        -------
        scipy.sparse.csr_matrix
            Updated Y-bus.
        """

        self._invalidate_topology()

        self.rebuild_topology()

        return self.build_ybus()

    # =========================================================
    # ELEMENT STATUS
    # =========================================================

    def set_element_status(
        self,
        element: Any,
        in_service: bool
    ) -> None:
        """
        Change the service state of a topology-affecting element.

        This method does not perform engineering validation.
        """

        if element is None:
            raise ValueError(
                "Element cannot be None."
            )

        if not hasattr(element, "in_service"):
            raise AttributeError(
                "Element does not provide an 'in_service' state."
            )

        element.in_service = bool(in_service)

        self._invalidate_topology()

    # =========================================================
    # FAULT STATE
    # =========================================================

    def apply_fault(
        self,
        bus_id: Any,
        fault_type: str,
        Zf: complex = 0.0
    ) -> None:
        """
        Store an active fault condition.

        This method only stores network state.

        Fault-current calculations belong to the analysis/solver
        layers.
        """

        if not self.bus_index:
            self.rebuild_bus_index()

        if bus_id not in self.bus_index:
            raise KeyError(
                f"Unknown fault bus: {bus_id}"
            )

        if isinstance(Zf, (int, float)) and Zf < 0:
            raise ValueError(
                "Fault impedance cannot be negative."
            )

        if not isinstance(fault_type, str):
            raise TypeError(
                "fault_type must be a string."
            )

        self.active_fault = {
            "bus_id": bus_id,
            "type": fault_type,
            "Zf": Zf,
        }

    # ---------------------------------------------------------

    def clear_fault(self) -> None:
        """
        Clear the currently stored fault condition.
        """

        self.active_fault = None

    # =========================================================
    # VALIDATION HOOK
    # =========================================================

    def validate(self):
        """
        Delegate structural/engineering validation to the
        validation layer when available.

        Network itself does not implement engineering validation.

        Returns
        -------
        Validation result
        """

        from core.validation import validate_network

        return validate_network(self)

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(self) -> Dict[str, Any]:
        """
        Return a concise network-state summary.
        """

        return {
            "base_mva": self.base_mva,
            "buses": len(self.buses),
            "lines": len(self.lines),
            "transformers": len(self.transformers),
            "generators": len(self.generators),
            "loads": len(self.loads),
            "shunts": len(self.shunts),
            "ybus_built": self.Ybus is not None,
            "ybus_dirty": self._ybus_dirty,
            "topology_dirty": self._topology_dirty,
            "topology_revision": self._topology_revision,
            "ybus_revision": self._ybus_revision,
            "active_fault": self.active_fault is not None,
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self) -> str:
        return (
            f"Network("
            f"base_mva={self.base_mva}, "
            f"buses={len(self.buses)}, "
            f"lines={len(self.lines)}, "
            f"transformers={len(self.transformers)}, "
            f"generators={len(self.generators)}, "
            f"loads={len(self.loads)}, "
            f"shunts={len(self.shunts)}"
            f")"
        )
```
