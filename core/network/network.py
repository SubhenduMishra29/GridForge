# ============================================================
# File: core/network/network.py
# GridForge V2 — Network Layer
# ============================================================
"""
GridForge V2 Network
====================

Assembled-network façade for the GridForge Core.

Architecture
------------

    core.model
        canonical electrical entities
              |
              v
    NetworkRegistry
        assembled membership
              |
              v
    Network
       /       \
      v         v
Topology     YBusBuilder
      |         |
      v         v
 connectivity  admittance
      \         /
       \       /
        derived state

Responsibilities
----------------
Network owns the assembled-network boundary and coordinates:

- canonical element registration;
- canonical element removal;
- system MVA base;
- PerUnitSystem configuration;
- deterministic bus indexing;
- topology service;
- Y-bus service;
- derived-state invalidation;
- network-level diagnostics.

Network does NOT implement:

- power-flow algorithms;
- Newton-Raphson;
- Jacobian calculations;
- short-circuit mathematics;
- protection algorithms;
- transient integration;
- topology algorithms;
- Y-bus mathematics;
- GUI operations;
- SLD operations;
- canonical model definitions.

Study/fault compatibility
-------------------------
``sync_injections()``, ``apply_fault()``, ``clear_fault()`` and
``set_element_status()`` are retained here temporarily because they
exist in the current Network public contract.

They are migration candidates for the Application/Study command
architecture and must not be expanded into additional Network
responsibilities.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.base.per_unit import PerUnitSystem

from .indexing import BusIndex
from .registry import NetworkRegistry
from .state import NetworkState
from .topology import TopologyManager
from .ybus import YBusBuilder


class Network:
    """
    Assembled GridForge electrical network.

    Network references canonical objects from ``core.model``.
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        base_mva: float = 100.0,
    ) -> None:
        """
        Initialize an empty assembled Network.
        """

        base_mva = float(base_mva)

        if base_mva <= 0.0:
            raise ValueError(
                "Network base MVA must be positive."
            )

        self.base_mva = base_mva

        # --------------------------------------------------------
        # BASE SERVICE
        # --------------------------------------------------------

        self.per_unit = PerUnitSystem(
            base_mva=self.base_mva,
        )

        # --------------------------------------------------------
        # INTERNAL NETWORK SERVICES
        # --------------------------------------------------------

        self.registry = NetworkRegistry()

        self.index = BusIndex(
            self,
        )

        self.state = NetworkState()

        # --------------------------------------------------------
        # DERIVED REPRESENTATION
        # --------------------------------------------------------

        self.Ybus = None

        # --------------------------------------------------------
        # TEMPORARY STUDY STATE
        # --------------------------------------------------------

        self.active_fault: Optional[
            Dict[str, Any]
        ] = None

        # --------------------------------------------------------
        # DERIVED NETWORK SERVICES
        # --------------------------------------------------------

        self.topology = TopologyManager(
            self,
        )

        self.ybus_builder = YBusBuilder(
            self,
        )

    # ============================================================
    # COMPATIBILITY COLLECTION PROPERTIES
    # ============================================================

    @property
    def buses(self) -> list[Any]:
        """
        Canonical registered buses.
        """

        return self.registry.buses

    # ------------------------------------------------------------

    @property
    def lines(self) -> list[Any]:
        """
        Canonical registered lines.
        """

        return self.registry.lines

    # ------------------------------------------------------------

    @property
    def transformers(self) -> list[Any]:
        """
        Canonical registered transformers.
        """

        return self.registry.transformers

    # ------------------------------------------------------------

    @property
    def generators(self) -> list[Any]:
        """
        Canonical registered generators.
        """

        return self.registry.generators

    # ------------------------------------------------------------

    @property
    def loads(self) -> list[Any]:
        """
        Canonical registered loads.
        """

        return self.registry.loads

    # ------------------------------------------------------------

    @property
    def shunts(self) -> list[Any]:
        """
        Canonical registered shunts.
        """

        return self.registry.shunts

    # ============================================================
    # COMPATIBILITY BUS INDEX
    # ============================================================

    @property
    def bus_index(self) -> dict[Any, int]:
        """
        Backward-compatible access to the deterministic Bus index.

        The implementation is owned by ``BusIndex``.
        """

        return self.index.mapping

    # ============================================================
    # COMPATIBILITY DERIVED-STATE PROPERTIES
    # ============================================================

    @property
    def _topology_revision(self) -> int:
        return self.state.topology_revision

    # ------------------------------------------------------------

    @property
    def _ybus_revision(self) -> int:
        return self.state.ybus_revision

    # ------------------------------------------------------------

    @property
    def _topology_dirty(self) -> bool:
        return self.state.topology_dirty

    # ------------------------------------------------------------

    @property
    def _ybus_dirty(self) -> bool:
        return self.state.ybus_dirty

    # ============================================================
    # ELEMENT MANAGEMENT
    # ============================================================

    def add_bus(
        self,
        bus: Any,
    ) -> None:
        """
        Register a canonical Bus and invalidate topology.
        """

        self.registry.add_bus(
            bus,
        )

        self._invalidate_topology()

    # ------------------------------------------------------------

    def add_line(
        self,
        line: Any,
    ) -> None:
        """
        Register a canonical Line and invalidate topology.
        """

        self.registry.add_line(
            line,
        )

        self._invalidate_topology()

    # ------------------------------------------------------------

    def add_transformer(
        self,
        transformer: Any,
    ) -> None:
        """
        Register a canonical Transformer and invalidate topology.
        """

        self.registry.add_transformer(
            transformer,
        )

        self._invalidate_topology()

    # ------------------------------------------------------------

    def add_generator(
        self,
        generator: Any,
    ) -> None:
        """
        Register a canonical Generator.

        Generator P/Q injection does not directly alter Y-bus.
        """

        self.registry.add_generator(
            generator,
        )

    # ------------------------------------------------------------

    def add_load(
        self,
        load: Any,
    ) -> None:
        """
        Register a canonical Load.

        Load P/Q demand does not directly alter Y-bus.
        """

        self.registry.add_load(
            load,
        )

    # ------------------------------------------------------------

    def add_shunt(
        self,
        shunt: Any,
    ) -> None:
        """
        Register a canonical Shunt and invalidate Y-bus.
        """

        self.registry.add_shunt(
            shunt,
        )

        self._invalidate_ybus()

    # ============================================================
    # ELEMENT REMOVAL
    # ============================================================

    def remove_bus(
        self,
        bus: Any,
    ) -> None:
        """
        Remove a canonical Bus.

        Removal is rejected if another registered network element
        references the Bus.
        """

        self.registry.remove_bus(
            bus,
        )

        self.index.rebuild()

        self._invalidate_topology()

    # ------------------------------------------------------------

    def remove_line(
        self,
        line: Any,
    ) -> None:
        """
        Remove Line membership only.

        Terminal relationships are not disconnected here.
        """

        self.registry.remove_line(
            line,
        )

        self._invalidate_topology()

    # ------------------------------------------------------------

    def remove_transformer(
        self,
        transformer: Any,
    ) -> None:
        """
        Remove Transformer membership only.

        Terminal relationships are not disconnected here.
        """

        self.registry.remove_transformer(
            transformer,
        )

        self._invalidate_topology()

    # ------------------------------------------------------------

    def remove_generator(
        self,
        generator: Any,
    ) -> None:
        """
        Remove Generator membership.
        """

        self.registry.remove_generator(
            generator,
        )

    # ------------------------------------------------------------

    def remove_load(
        self,
        load: Any,
    ) -> None:
        """
        Remove Load membership.
        """

        self.registry.remove_load(
            load,
        )

    # ------------------------------------------------------------

    def remove_shunt(
        self,
        shunt: Any,
    ) -> None:
        """
        Remove Shunt membership and invalidate Y-bus.
        """

        self.registry.remove_shunt(
            shunt,
        )

        self._invalidate_ybus()

    # ============================================================
    # INVALIDATION
    # ============================================================

    def _invalidate_topology(self) -> None:
        """
        Invalidate topology and all topology-dependent state.
        """

        self.state.invalidate_topology()

        # --------------------------------------------------------
        # Compatibility with the existing TopologyManager contract.
        #
        # We deliberately do not require a new TopologyManager API
        # during this refactor. If the existing implementation
        # exposes its local dirty flag, synchronize it.
        # --------------------------------------------------------

        if hasattr(
            self.topology,
            "_dirty",
        ):
            self.topology._dirty = True

    # ------------------------------------------------------------

    def _invalidate_ybus(self) -> None:
        """
        Invalidate Y-bus without changing topology revision.
        """

        self.state.invalidate_ybus()

    # ============================================================
    # BUS INDEXING
    # ============================================================

    def rebuild_bus_index(
        self,
    ) -> dict[Any, int]:
        """
        Rebuild the deterministic Bus ID -> matrix-index mapping.
        """

        return self.index.rebuild()

    # ============================================================
    # TOPOLOGY
    # ============================================================

    def rebuild_topology(self):
        """
        Rebuild and return the topology graph.

        Topology construction remains exclusively delegated to
        TopologyManager.
        """

        graph = self.topology.build()

        self.state.mark_topology_built()

        return graph

    # ------------------------------------------------------------

    def find_islands(self):
        """
        Return electrical network islands.
        """

        return self.topology.find_islands()

    # ------------------------------------------------------------

    def is_connected(
        self,
        bus_a: Any,
        bus_b: Any,
    ) -> bool:
        """
        Determine whether two buses are electrically connected.
        """

        return self.topology.is_connected(
            bus_a,
            bus_b,
        )

    # ============================================================
    # Y-BUS
    # ============================================================

    def build_ybus(self):
        """
        Build the current Network Y-bus.

        Bus indexing is rebuilt before invoking YBusBuilder.

        Y-bus mathematics remains exclusively owned by
        YBusBuilder.
        """

        self.rebuild_bus_index()

        ybus = self.ybus_builder.build()

        self.Ybus = ybus

        self.state.mark_ybus_built()

        return self.Ybus

    # ------------------------------------------------------------

    def get_ybus(self):
        """
        Return the current Y-bus.

        Rebuild automatically if the representation is stale.
        """

        if not self.state.ybus_is_current(
            self.Ybus,
        ):
            return self.build_ybus()

        return self.Ybus

    # ============================================================
    # INJECTION AGGREGATION
    # ============================================================

    def sync_injections(self) -> None:
        """
        Aggregate registered Generator and Load injections into
        Bus study-state quantities.

        This method is retained temporarily for compatibility with
        the existing Network contract.

        It is a migration candidate for the Study/Application
        preparation architecture.
        """

        if not self.buses:
            raise ValueError(
                "Network contains no buses."
            )

        bus_set = set(
            self.buses,
        )

        p = {
            bus: 0.0
            for bus in self.buses
        }

        q = {
            bus: 0.0
            for bus in self.buses
        }

        q_min = {
            bus: 0.0
            for bus in self.buses
        }

        q_max = {
            bus: 0.0
            for bus in self.buses
        }

        has_generator = {
            bus: False
            for bus in self.buses
        }

        # --------------------------------------------------------
        # LOADS
        # --------------------------------------------------------

        for load in self.loads:

            bus = load.bus

            if bus not in bus_set:
                raise ValueError(
                    f"Load '{load.id}' is connected to a bus "
                    "that is not registered on this network."
                )

            dp, dq = load.get_power()

            p[bus] += dp
            q[bus] += dq

        # --------------------------------------------------------
        # GENERATORS
        # --------------------------------------------------------

        for generator in self.generators:

            bus = generator.bus

            if bus not in bus_set:
                raise ValueError(
                    f"Generator '{generator.id}' is connected "
                    "to a bus that is not registered on this "
                    "network."
                )

            dp, dq = generator.get_power()

            p[bus] += dp
            q[bus] += dq

            if (
                bus.is_pv()
                or bus.is_slack()
            ):

                q_min[bus] += generator.q_min
                q_max[bus] += generator.q_max

                has_generator[bus] = True

        # --------------------------------------------------------
        # APPLY STUDY STATE
        # --------------------------------------------------------

        for bus in self.buses:

            bus.set_power(
                P_spec=p[bus],
                Q_spec=q[bus],
            )

            if has_generator[bus]:

                bus.set_q_limits(
                    q_min[bus],
                    q_max[bus],
                )

            else:

                bus.set_q_limits(
                    float("-inf"),
                    float("inf"),
                )

    # ============================================================
    # RECONFIGURATION
    # ============================================================

    def reconfigure(self):
        """
        Explicitly invalidate and rebuild topology and Y-bus.
        """

        self._invalidate_topology()

        self.rebuild_topology()

        return self.build_ybus()

    # ============================================================
    # ELEMENT STATUS
    # ============================================================

    def set_element_status(
        self,
        element: Any,
        in_service: bool,
    ) -> None:
        """
        Change the service state of a topology-affecting element.

        Retained temporarily for compatibility.

        The eventual engineering mutation path is expected to be:

            SetElementStatusCommand
                    ↓
            Application Handler
                    ↓
            canonical model mutation
                    ↓
            Network invalidation
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

        element.in_service = bool(
            in_service,
        )

        self._invalidate_topology()

    # ============================================================
    # FAULT STATE
    # ============================================================

    def apply_fault(
        self,
        bus_id: Any,
        fault_type: str,
        Zf: complex = 0.0,
    ) -> None:
        """
        Store an active fault condition.

        Fault calculations remain outside Network.
        """

        if not self.bus_index:
            self.rebuild_bus_index()

        if bus_id not in self.bus_index:
            raise KeyError(
                f"Unknown fault bus: {bus_id}"
            )

        if not isinstance(
            fault_type,
            str,
        ):
            raise TypeError(
                "fault_type must be a string."
            )

        fault_type = fault_type.strip()

        if not fault_type:
            raise ValueError(
                "fault_type cannot be empty."
            )

        try:
            Zf = complex(
                Zf,
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise TypeError(
                "Fault impedance must be a real or complex value."
            ) from exc

        self.active_fault = {
            "bus_id": bus_id,
            "type": fault_type,
            "Zf": Zf,
        }

    # ------------------------------------------------------------

    def clear_fault(self) -> None:
        """
        Clear the stored fault condition.
        """

        self.active_fault = None

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate(self):
        """
        Delegate engineering validation to the validation layer.
        """

        from core.validation import validate_network

        return validate_network(
            self,
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(
        self,
    ) -> Dict[str, Any]:
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
            "active_fault": (
                self.active_fault is not None
            ),
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return concise developer-facing representation.
        """

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
