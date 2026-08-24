# ============================================================
# File: core/network/network.py
# GridForge V2 — Network Layer
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 assembled electrical Network.

Network is the façade joining:

    canonical model objects
    registry
    bus indexing
    topology
    Y-bus
    derived state

Network does not implement numerical engineering algorithms.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.base.per_unit import PerUnitSystem

from .endpoint import resolve_terminal_bus
from .indexing import BusIndex
from .registry import NetworkRegistry
from .state import NetworkState
from .topology import TopologyManager
from .ybus import YBusBuilder


class Network:

    def __init__(
        self,
        base_mva: float = 100.0,
    ) -> None:

        base_mva = float(base_mva)

        if base_mva <= 0.0:
            raise ValueError(
                "Network base MVA must be positive."
            )

        self.base_mva = base_mva

        self.per_unit = PerUnitSystem(
            base_mva=self.base_mva,
        )

        # ---------------------------------------------------------
        # NETWORK OWNED SERVICES
        # ---------------------------------------------------------

        self.registry = NetworkRegistry()
        self.index = BusIndex()
        self.state = NetworkState()

        self.topology = TopologyManager(self)
        self.ybus_builder = YBusBuilder(self)

        # ---------------------------------------------------------
        # DERIVED STATE
        # ---------------------------------------------------------

        self.Ybus = None

        # ---------------------------------------------------------
        # STUDY STATE
        # ---------------------------------------------------------

        self.active_fault: Optional[Dict[str, Any]] = None

    # ============================================================
    # COMPATIBILITY COLLECTION PROPERTIES
    # ============================================================

    @property
    def buses(self):
        return self.registry.buses

    @property
    def lines(self):
        return self.registry.lines

    @property
    def transformers(self):
        return self.registry.transformers

    @property
    def generators(self):
        return self.registry.generators

    @property
    def loads(self):
        return self.registry.loads

    @property
    def shunts(self):
        return self.registry.shunts

    @property
    def bus_index(self):
        """
        Compatibility access to the canonical BusIndex mapping.
        """

        return self.index.mapping

    # ============================================================
    # INVALIDATION
    # ============================================================

    def _invalidate_topology(self) -> None:

        self.state.invalidate_topology()
        self.index.invalidate()

    # ------------------------------------------------------------

    def _invalidate_ybus(self) -> None:

        self.state.invalidate_ybus()

    # ============================================================
    # REGISTRATION
    # ============================================================

    def add_bus(self, bus: Any) -> None:

        self.registry.add_bus(bus)
        self._invalidate_topology()

    # ------------------------------------------------------------

    def add_line(self, line: Any) -> None:

        self.registry.add_line(line)
        self._invalidate_topology()

    # ------------------------------------------------------------

    def add_transformer(
        self,
        transformer: Any,
    ) -> None:

        self.registry.add_transformer(transformer)
        self._invalidate_topology()

    # ------------------------------------------------------------

    def add_generator(
        self,
        generator: Any,
    ) -> None:

        self.registry.add_generator(generator)

    # ------------------------------------------------------------

    def add_load(
        self,
        load: Any,
    ) -> None:

        self.registry.add_load(load)

    # ------------------------------------------------------------

    def add_shunt(
        self,
        shunt: Any,
    ) -> None:

        self.registry.add_shunt(shunt)
        self._invalidate_ybus()

    # ============================================================
    # INDEXING
    # ============================================================

    def rebuild_bus_index(self):

        return self.index.rebuild(
            self.buses,
        )

    # ============================================================
    # TOPOLOGY
    # ============================================================

    def rebuild_topology(self):

        graph = self.topology.build()

        self.state.topology_rebuilt()

        return graph

    # ------------------------------------------------------------

    def find_islands(self):

        return self.topology.find_islands()

    # ------------------------------------------------------------

    def is_connected(
        self,
        bus_a: Any,
        bus_b: Any,
    ) -> bool:

        return self.topology.is_connected(
            bus_a,
            bus_b,
        )

    # ============================================================
    # Y-BUS
    # ============================================================

    def build_ybus(self):

        self.index.ensure(self.buses)

        self.Ybus = self.ybus_builder.build()

        self.state.ybus_rebuilt()

        return self.Ybus

    # ------------------------------------------------------------

    def get_ybus(self):

        if (
            self.Ybus is None
            or not self.state.ybus_valid
        ):
            return self.build_ybus()

        return self.Ybus

    # ============================================================
    # INJECTIONS
    # ============================================================

    def sync_injections(self) -> None:

        if not self.buses:
            raise ValueError(
                "Network contains no buses."
            )

        bus_set = set(self.buses)

        p = {bus: 0.0 for bus in self.buses}
        q = {bus: 0.0 for bus in self.buses}

        q_min = {bus: 0.0 for bus in self.buses}
        q_max = {bus: 0.0 for bus in self.buses}

        has_generator = {
            bus: False
            for bus in self.buses
        }

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

        for generator in self.generators:

            bus = generator.bus

            if bus not in bus_set:
                raise ValueError(
                    f"Generator '{generator.id}' is connected "
                    "to a bus that is not registered on this network."
                )

            dp, dq = generator.get_power()

            p[bus] += dp
            q[bus] += dq

            if bus.is_pv() or bus.is_slack():

                q_min[bus] += generator.q_min
                q_max[bus] += generator.q_max

                has_generator[bus] = True

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
    # STATUS
    # ============================================================

    def set_element_status(
        self,
        element: Any,
        in_service: bool,
    ) -> None:

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

    # ============================================================
    # RECONFIGURATION
    # ============================================================

    def reconfigure(self):

        self._invalidate_topology()

        self.rebuild_topology()

        return self.build_ybus()

    # ============================================================
    # FAULT STATE
    # ============================================================

    def apply_fault(
        self,
        bus_id: Any,
        fault_type: str,
        Zf: complex = 0.0,
    ) -> None:

        self.index.ensure(self.buses)

        if bus_id not in self.index:

            raise KeyError(
                f"Unknown fault bus: {bus_id}"
            )

        if not isinstance(fault_type, str):
            raise TypeError(
                "fault_type must be a string."
            )

        fault_type = fault_type.strip()

        if not fault_type:
            raise ValueError(
                "fault_type cannot be empty."
            )

        try:
            Zf = complex(Zf)

        except (TypeError, ValueError) as exc:

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

        self.active_fault = None

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate(self):

        from core.validation import validate_network

        return validate_network(self)

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(self) -> Dict[str, Any]:

        return {
            "base_mva": self.base_mva,
            "buses": len(self.buses),
            "lines": len(self.lines),
            "transformers": len(self.transformers),
            "generators": len(self.generators),
            "loads": len(self.loads),
            "shunts": len(self.shunts),
            "ybus_built": self.Ybus is not None,
            "ybus_dirty": self.state.ybus_dirty,
            "topology_dirty": self.state.topology_dirty,
            "topology_revision": (
                self.state.topology_revision
            ),
            "ybus_revision": (
                self.state.ybus_revision
            ),
            "bus_index_valid": self.index.valid,
            "active_fault": (
                self.active_fault is not None
            ),
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

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

    # ============================================================
    # BUS REMOVAL
    # ============================================================

    def remove_bus(
        self,
        bus: Any,
    ) -> None:

        if bus is None:
            raise ValueError(
                "Bus cannot be None."
            )

        if bus not in self.buses:
            raise ValueError(
                f"Bus '{getattr(bus, 'id', bus)}' "
                "is not registered on this Network."
            )

        # ---------------------------------------------------------
        # LINES
        # ---------------------------------------------------------

        for line in self.lines:

            if (
                resolve_terminal_bus(
                    getattr(line, "from_terminal", None)
                ) is bus
                or
                resolve_terminal_bus(
                    getattr(line, "to_terminal", None)
                ) is bus
            ):

                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Line '{line.id}' references it."
                )

        # ---------------------------------------------------------
        # TRANSFORMERS
        # ---------------------------------------------------------

        for transformer in self.transformers:

            if (
                resolve_terminal_bus(
                    getattr(
                        transformer,
                        "from_terminal",
                        None,
                    )
                ) is bus
                or
                resolve_terminal_bus(
                    getattr(
                        transformer,
                        "to_terminal",
                        None,
                    )
                ) is bus
            ):

                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Transformer '{transformer.id}' references it."
                )

        # ---------------------------------------------------------
        # GENERATORS
        # ---------------------------------------------------------

        for generator in self.generators:

            if getattr(generator, "bus", None) is bus:

                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Generator '{generator.id}' references it."
                )

        # ---------------------------------------------------------
        # LOADS
        # ---------------------------------------------------------

        for load in self.loads:

            if getattr(load, "bus", None) is bus:

                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Load '{load.id}' references it."
                )

        # ---------------------------------------------------------
        # SHUNTS
        # ---------------------------------------------------------

        for shunt in self.shunts:

            terminal = getattr(
                shunt,
                "terminal",
                None,
            )

            if resolve_terminal_bus(terminal) is bus:

                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Shunt '{shunt.id}' references it."
                )

        self.buses.remove(bus)

        self._invalidate_topology()

    # ============================================================
    # ELEMENT REMOVAL
    # ============================================================

    def remove_line(self, line: Any) -> None:

        self.registry.remove_identity(
            self.lines,
            line,
            "line",
        )

        self._invalidate_topology()

    # ------------------------------------------------------------

    def remove_transformer(
        self,
        transformer: Any,
    ) -> None:

        self.registry.remove_identity(
            self.transformers,
            transformer,
            "transformer",
        )

        self._invalidate_topology()
