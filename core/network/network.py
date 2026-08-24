# ============================================================
# File: core/network/network.py
# GridForge V2 — Network Layer
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Assembled Electrical Network
============================================

The Network is the public façade of the assembled electrical
network layer.

Architecture
------------

    core.model
        canonical electrical model objects
                |
                v
    Network
        |-- NetworkRegistry
        |-- BusIndex
        |-- TopologyManager
        |-- YBusBuilder
        |-- NetworkState
        |-- PerUnitSystem
                |
                v
    core.analysis
    core.solver
    core.validation

The Network owns the assembled-network boundary.

It does NOT own:

    - electrical model definitions
    - GUI state
    - SLD representation
    - topology algorithms
    - Y-bus mathematics
    - numerical solvers
    - engineering validation rules
    - command orchestration

Those responsibilities belong to their respective layers.

Network responsibilities
------------------------

The Network:

    1. owns the network-level services;
    2. exposes registered canonical model objects;
    3. provides the configured per-unit service;
    4. coordinates bus indexing;
    5. coordinates topology construction;
    6. coordinates Y-bus construction;
    7. maintains derived network state;
    8. maintains lightweight study state;
    9. provides network-level façade operations.

The Network is therefore deliberately small.

Application / Command Layer
---------------------------

Commands create and mutate canonical model objects.

Typical flow:

    Command
        |
        v
    Application transaction
        |
        +--> create model object
        +--> validate
        +--> connect
        +--> register with Network
        |
        v
    Network

The Network is consumed by analysis, validation, and solver
layers after assembly.

Model ownership
---------------

Canonical electrical entities remain owned by ``core.model``.

Network stores references to those objects through
``NetworkRegistry``.

Network does not duplicate model classes.

Derived state
-------------

Topology and Y-bus are derived representations.

They are invalidated when network membership or relevant
element state changes.

The corresponding builders/managers are responsible for
reconstruction.

GridForge V2
------------

This module is part of the frozen Network Layer decomposition.

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


# ============================================================
# NETWORK
# ============================================================

class Network:
    """
    Assembled GridForge electrical network.

    Network is a façade over the specialized network services.

    It contains references to canonical ``core.model`` objects;
    it does not define or duplicate those model classes.

    Parameters
    ----------
    base_mva:
        Global system MVA base.

    Notes
    -----
    Network does not perform engineering calculations.

    In particular, it does not implement:

        - load-flow algorithms;
        - short-circuit calculations;
        - Jacobian calculations;
        - protection calculations;
        - transient simulation;
        - numerical optimization.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        base_mva: float = 100.0,
    ) -> None:
        """
        Create an empty assembled network.
        """

        try:
            base_mva = float(base_mva)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "Network base MVA must be a real number."
            ) from exc

        if base_mva <= 0.0:
            raise ValueError(
                "Network base MVA must be positive."
            )

        self.base_mva = base_mva

        # ----------------------------------------------------
        # BASE SERVICE
        # ----------------------------------------------------

        self.per_unit = PerUnitSystem(
            base_mva=self.base_mva,
        )

        # ----------------------------------------------------
        # NETWORK SERVICES
        # ----------------------------------------------------

        self.registry = NetworkRegistry()
        self.index = BusIndex()
        self.state = NetworkState()

        self.topology = TopologyManager(self)
        self.ybus_builder = YBusBuilder(self)

        # ----------------------------------------------------
        # DERIVED Y-BUS
        #
        # Ybus is intentionally stored here as network-level
        # derived state. Construction belongs to YBusBuilder.
        # ----------------------------------------------------

        self.Ybus = None

        # ----------------------------------------------------
        # LIGHTWEIGHT STUDY STATE
        # ----------------------------------------------------

        self.active_fault: Optional[Dict[str, Any]] = None

    # ========================================================
    # CANONICAL COLLECTION ACCESS
    # ========================================================

    @property
    def buses(self):
        """
        Registered canonical Bus objects.
        """

        return self.registry.buses

    # --------------------------------------------------------

    @property
    def lines(self):
        """
        Registered canonical Line objects.
        """

        return self.registry.lines

    # --------------------------------------------------------

    @property
    def transformers(self):
        """
        Registered canonical Transformer objects.
        """

        return self.registry.transformers

    # --------------------------------------------------------

    @property
    def generators(self):
        """
        Registered canonical Generator objects.
        """

        return self.registry.generators

    # --------------------------------------------------------

    @property
    def loads(self):
        """
        Registered canonical Load objects.
        """

        return self.registry.loads

    # --------------------------------------------------------

    @property
    def shunts(self):
        """
        Registered canonical Shunt objects.
        """

        return self.registry.shunts

    # --------------------------------------------------------

    @property
    def bus_index(self):
        """
        Compatibility view of the canonical bus-index mapping.

        The index itself is owned by ``BusIndex``.
        """

        return self.index.mapping

    # ========================================================
    # INVALIDATION
    # ========================================================

    def _invalidate_topology(self) -> None:
        """
        Invalidate topology-dependent derived state.

        A topology change also invalidates the bus index and
        Y-bus because both depend on assembled network structure.
        """

        self.state.invalidate_topology()
        self.index.invalidate()

    # --------------------------------------------------------

    def _invalidate_ybus(self) -> None:
        """
        Invalidate Y-bus without changing topology structure.
        """

        self.state.invalidate_ybus()

    # ========================================================
    # ELEMENT REGISTRATION
    # ========================================================

    def add_bus(
        self,
        bus: Any,
    ) -> None:
        """
        Register a canonical Bus with the network.

        Registration semantics are delegated to NetworkRegistry.
        """

        self.registry.add_bus(bus)
        self._invalidate_topology()

    # --------------------------------------------------------

    def add_line(
        self,
        line: Any,
    ) -> None:
        """
        Register a canonical Line.

        Line membership affects topology and Y-bus.
        """

        self.registry.add_line(line)
        self._invalidate_topology()

    # --------------------------------------------------------

    def add_transformer(
        self,
        transformer: Any,
    ) -> None:
        """
        Register a canonical Transformer.

        Transformer membership affects topology and Y-bus.
        """

        self.registry.add_transformer(transformer)
        self._invalidate_topology()

    # --------------------------------------------------------

    def add_generator(
        self,
        generator: Any,
    ) -> None:
        """
        Register a canonical Generator.

        Generator registration does not itself alter topology or
        primitive network admittance.
        """

        self.registry.add_generator(generator)

    # --------------------------------------------------------

    def add_load(
        self,
        load: Any,
    ) -> None:
        """
        Register a canonical Load.

        Load registration does not itself alter topology or
        primitive network admittance.
        """

        self.registry.add_load(load)

    # --------------------------------------------------------

    def add_shunt(
        self,
        shunt: Any,
    ) -> None:
        """
        Register a canonical Shunt.

        A shunt affects network admittance and therefore
        invalidates Y-bus.
        """

        self.registry.add_shunt(shunt)
        self._invalidate_ybus()

    # ========================================================
    # ELEMENT REMOVAL
    # ========================================================

    def remove_bus(
        self,
        bus: Any,
    ) -> None:
        """
        Remove a Bus from network membership.

        Removal policy and reference checks are delegated to
        NetworkRegistry.

        The registry must reject removal when the Bus remains
        referenced by registered network elements.

        Network itself only coordinates invalidation after the
        membership operation succeeds.
        """

        self.registry.remove_bus(bus)
        self._invalidate_topology()

    # --------------------------------------------------------

    def remove_line(
        self,
        line: Any,
    ) -> None:
        """
        Remove a Line from network membership.
        """

        self.registry.remove_identity(
            self.lines,
            line,
            "line",
        )

        self._invalidate_topology()

    # --------------------------------------------------------

    def remove_transformer(
        self,
        transformer: Any,
    ) -> None:
        """
        Remove a Transformer from network membership.
        """

        self.registry.remove_identity(
            self.transformers,
            transformer,
            "transformer",
        )

        self._invalidate_topology()

    # --------------------------------------------------------

    def remove_generator(
        self,
        generator: Any,
    ) -> None:
        """
        Remove a Generator from network membership.
        """

        self.registry.remove_identity(
            self.generators,
            generator,
            "generator",
        )

    # --------------------------------------------------------

    def remove_load(
        self,
        load: Any,
    ) -> None:
        """
        Remove a Load from network membership.
        """

        self.registry.remove_identity(
            self.loads,
            load,
            "load",
        )

    # --------------------------------------------------------

    def remove_shunt(
        self,
        shunt: Any,
    ) -> None:
        """
        Remove a Shunt from network membership.

        Shunt removal invalidates Y-bus because the shunt may
        contribute directly to network admittance.
        """

        self.registry.remove_identity(
            self.shunts,
            shunt,
            "shunt",
        )

        self._invalidate_ybus()

    # ========================================================
    # BUS INDEXING
    # ========================================================

    def rebuild_bus_index(self):
        """
        Rebuild the deterministic bus-ID to matrix-index mapping.

        Actual indexing is implemented by ``BusIndex``.
        """

        return self.index.rebuild(
            self.buses,
        )

    # --------------------------------------------------------

    def ensure_bus_index(self):
        """
        Ensure the bus index is valid and return it.
        """

        self.index.ensure(
            self.buses,
        )

        return self.index.mapping

    # ========================================================
    # TOPOLOGY
    # ========================================================

    def rebuild_topology(self):
        """
        Build the current electrical topology.

        Topology algorithms belong exclusively to
        ``TopologyManager``.
        """

        graph = self.topology.build()

        self.state.topology_rebuilt()

        return graph

    # --------------------------------------------------------

    def find_islands(self):
        """
        Return the electrical islands detected by the topology
        service.
        """

        return self.topology.find_islands()

    # --------------------------------------------------------

    def is_connected(
        self,
        bus_a: Any,
        bus_b: Any,
    ) -> bool:
        """
        Determine whether two buses are electrically connected.

        Connectivity analysis belongs to ``TopologyManager``.
        """

        return self.topology.is_connected(
            bus_a,
            bus_b,
        )

    # ========================================================
    # Y-BUS
    # ========================================================

    def build_ybus(self):
        """
        Build the network Y-bus.

        The Network coordinates construction; all Y-bus
        mathematics belongs to ``YBusBuilder``.

        Returns
        -------
        scipy.sparse matrix
            Constructed network admittance matrix.
        """

        self.index.ensure(
            self.buses,
        )

        self.Ybus = self.ybus_builder.build()

        self.state.ybus_rebuilt()

        return self.Ybus

    # --------------------------------------------------------

    def get_ybus(self):
        """
        Return a valid Y-bus.

        If the current Y-bus is absent or invalid, it is rebuilt.
        """

        if (
            self.Ybus is None
            or not self.state.ybus_valid
        ):
            return self.build_ybus()

        return self.Ybus

    # ========================================================
    # INJECTION AGGREGATION
    # ========================================================

    def sync_injections(self) -> None:
        """
        Synchronize Generator and Load injections into Bus
        study-state quantities.

        This operation is intentionally limited to aggregation.

        It does not:

            - solve power flow;
            - change generator output;
            - perform PV/PQ switching;
            - calculate a Jacobian;
            - construct Y-bus.
        """

        if not self.buses:
            raise ValueError(
                "Network contains no buses."
            )

        bus_set = set(self.buses)

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

        # ----------------------------------------------------
        # LOADS
        # ----------------------------------------------------

        for load in self.loads:

            bus = getattr(
                load,
                "bus",
                None,
            )

            if bus not in bus_set:
                raise ValueError(
                    f"Load '{getattr(load, 'id', load)}' "
                    "is connected to a bus that is not "
                    "registered on this network."
                )

            dp, dq = load.get_power()

            p[bus] += dp
            q[bus] += dq

        # ----------------------------------------------------
        # GENERATORS
        # ----------------------------------------------------

        for generator in self.generators:

            bus = getattr(
                generator,
                "bus",
                None,
            )

            if bus not in bus_set:
                raise ValueError(
                    f"Generator "
                    f"'{getattr(generator, 'id', generator)}' "
                    "is connected to a bus that is not "
                    "registered on this network."
                )

            dp, dq = generator.get_power()

            p[bus] += dp
            q[bus] += dq

            if bus.is_pv() or bus.is_slack():

                q_min[bus] += generator.q_min
                q_max[bus] += generator.q_max

                has_generator[bus] = True

        # ----------------------------------------------------
        # APPLY BUS STUDY STATE
        # ----------------------------------------------------

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

    # ========================================================
    # ELEMENT SERVICE STATUS
    # ========================================================

    def set_element_status(
        self,
        element: Any,
        in_service: bool,
    ) -> None:
        """
        Change the service state of a registered network element.

        The Network does not perform engineering validation.

        Changing service state invalidates topology because an
        out-of-service topology element must no longer be treated
        as active by topology/Y-bus construction.
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
            in_service
        )

        self._invalidate_topology()

    # ========================================================
    # RECONFIGURATION
    # ========================================================

    def reconfigure(self):
        """
        Rebuild all topology-dependent derived state.

        Returns
        -------
        scipy.sparse matrix
            Rebuilt Y-bus.
        """

        self._invalidate_topology()

        self.rebuild_topology()

        return self.build_ybus()

    # ========================================================
    # FAULT STUDY STATE
    # ========================================================

    def apply_fault(
        self,
        bus_id: Any,
        fault_type: str,
        Zf: complex = 0.0,
    ) -> None:
        """
        Store lightweight fault-study state.

        Fault-current calculations belong to the analysis/solver
        layers.
        """

        self.index.ensure(
            self.buses,
        )

        if bus_id not in self.index:
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
            Zf = complex(Zf)

        except (TypeError, ValueError) as exc:

            raise TypeError(
                "Fault impedance must be a real or "
                "complex value."
            ) from exc

        self.active_fault = {
            "bus_id": bus_id,
            "type": fault_type,
            "Zf": Zf,
        }

    # --------------------------------------------------------

    def clear_fault(self) -> None:
        """
        Clear the currently stored fault-study state.
        """

        self.active_fault = None

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(self):
        """
        Delegate engineering validation to the validation layer.

        Network does not implement engineering validation rules.
        """

        from core.validation import validate_network

        return validate_network(
            self,
        )

    # ========================================================
    # SUMMARY
    # ========================================================

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

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            "Network("
            f"base_mva={self.base_mva}, "
            f"buses={len(self.buses)}, "
            f"lines={len(self.lines)}, "
            f"transformers={len(self.transformers)}, "
            f"generators={len(self.generators)}, "
            f"loads={len(self.loads)}, "
            f"shunts={len(self.shunts)}"
            ")"
        )
