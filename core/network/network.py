# ============================================================
# File: core/network/network.py
# GridForge V2 — Network Layer
# ============================================================
"""
GridForge Network Layer V2
==========================

Central assembled-network container for GridForge.

Architecture
------------

    core/model/
        Canonical electrical entities
              |
              v
    core/network/
        Assembled network
        topology
        per-unit service
        Y-bus representation
              |
              v
    core/analysis/
        Engineering study orchestration
              |
              v
    core/solver/
        Numerical algorithms


Responsibilities
----------------
The Network object:

- Maintains collections of canonical electrical model objects.
- Maintains the system MVA base.
- Provides the canonical PerUnitSystem service.
- Maintains deterministic bus indexing.
- Coordinates topology management.
- Coordinates Y-bus construction.
- Maintains network-derived state.
- Maintains lightweight network study state.
- Provides network-level utilities.
- Provides injection aggregation for bus study state.
- Provides canonical network-element registration/removal.


Does NOT
--------
The Network does not:

- Implement numerical power-flow algorithms.
- Implement Newton-Raphson calculations.
- Implement Jacobian calculations.
- Implement short-circuit mathematics.
- Implement protection algorithms.
- Implement transient/dynamic numerical integration.
- Define electrical equipment models.
- Duplicate model classes.
- Perform GUI operations.
- Implement engineering validation rules.


Model Ownership
---------------
``core.model`` is the single source of truth for electrical
entities.

The Network stores references to those canonical model objects.

It does not define duplicate Bus, Generator, Load, Line,
Transformer, Shunt, or other equipment classes.


Per-Unit Ownership
------------------
The canonical per-unit implementation belongs to:

    core.base.per_unit.PerUnitSystem

The Network exposes a configured instance through:

    network.per_unit

There is intentionally no active ``core.network.per_unit`` module.


Y-Bus Ownership
---------------
Y-bus construction is delegated to ``YBusBuilder``.

The Network stores the resulting matrix as derived network state:

    network.Ybus


Topology Ownership
------------------
Topology construction and connectivity analysis are delegated to
``TopologyManager``.


Injection State
---------------
Generator and Load electrical injections are aggregated into the
corresponding Bus study-state quantities by ``sync_injections()``.

The Network does not perform power-flow calculations or bus-type
switching.


Element Removal
---------------
Canonical element membership belongs to Network.

Removal therefore occurs through Network-level APIs rather than
through:

    * Application;
    * TopologyManager;
    * UI;
    * plugins.

Bus removal is deliberately strict.

A Bus cannot be removed while another registered network element
still references that Bus.

Line removal removes only Network membership. It does not delete
or disconnect either endpoint element.

The model layer uses Terminal objects as the authoritative physical
connection representation for branch and shunt equipment.

Therefore:

    Line
        from_terminal.endpoint
        to_terminal.endpoint

    Transformer
        from_terminal.endpoint
        to_terminal.endpoint

    Shunt
        terminal.endpoint

are used for canonical reference checks.

Compatibility properties such as ``from_bus``, ``to_bus`` and
``bus`` remain model-level derived interfaces and are not treated
as the authoritative storage representation.


GridForge V2 Status
-------------------
This module is part of the GridForge Network Layer V2 baseline.

Changes require evidence of a genuinely fundamental network-layer
requirement that cannot be satisfied by the model, base, topology,
Y-bus, analysis, or solver layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.base.per_unit import PerUnitSystem

from .topology import TopologyManager
from .ybus import YBusBuilder


# =====================================================================
# NETWORK
# =====================================================================

class Network:
    """
    Assembled GridForge electrical network.

    Parameters
    ----------
    base_mva : float, optional
        Global system apparent-power base in MVA.

    Notes
    -----
    Network contains references to canonical electrical objects
    defined under ``core.model``.

    Network-level services include:

    - per-unit conversion service
    - topology management
    - deterministic bus indexing
    - Y-bus construction
    - injection aggregation
    - lightweight fault state
    - canonical element registration/removal
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        base_mva: float = 100.0,
    ) -> None:
        """
        Initialize an empty assembled network.
        """

        base_mva = float(base_mva)

        if base_mva <= 0.0:
            raise ValueError(
                "Network base MVA must be positive."
            )

        self.base_mva = base_mva

        # -------------------------------------------------------------
        # BASE-LAYER PER-UNIT SERVICE
        # -------------------------------------------------------------

        self.per_unit = PerUnitSystem(
            base_mva=self.base_mva,
        )

        # -------------------------------------------------------------
        # CANONICAL MODEL COLLECTIONS
        #
        # These collections contain references to objects originating
        # from core.model.
        # -------------------------------------------------------------

        self.buses: List[Any] = []
        self.lines: List[Any] = []
        self.transformers: List[Any] = []
        self.generators: List[Any] = []
        self.loads: List[Any] = []
        self.shunts: List[Any] = []

        # -------------------------------------------------------------
        # DETERMINISTIC BUS INDEX
        #
        # bus.id -> numerical matrix index
        # -------------------------------------------------------------

        self.bus_index: Dict[Any, int] = {}

        # -------------------------------------------------------------
        # DERIVED NETWORK REPRESENTATION
        # -------------------------------------------------------------

        self.Ybus = None

        # -------------------------------------------------------------
        # NETWORK SERVICES
        # -------------------------------------------------------------

        self.topology = TopologyManager(self)
        self.ybus_builder = YBusBuilder(self)

        # -------------------------------------------------------------
        # LIGHTWEIGHT NETWORK STUDY STATE
        # -------------------------------------------------------------

        self.active_fault: Optional[Dict[str, Any]] = None

        # -------------------------------------------------------------
        # REVISION / DIRTY STATE
        #
        # A topology change invalidates both topology and Y-bus.
        #
        # A Y-bus-only change invalidates Y-bus without incrementing
        # the topology revision.
        # -------------------------------------------------------------

        self._topology_revision = 0
        self._ybus_revision = -1

        self._topology_dirty = True
        self._ybus_dirty = True

    # =================================================================
    # ELEMENT MANAGEMENT
    # =================================================================

    def add_bus(
        self,
        bus: Any,
    ) -> None:
        """
        Add a canonical Bus model to the network.

        Bus IDs must be unique within the network.
        """

        if bus is None:
            raise ValueError(
                "Cannot add None as a bus."
            )

        if not hasattr(bus, "id"):
            raise TypeError(
                "Bus object must provide an 'id' attribute."
            )

        for existing in self.buses:
            if existing.id == bus.id:
                raise ValueError(
                    f"Duplicate bus ID: {bus.id}"
                )

        self.buses.append(bus)

        self._invalidate_topology()

    # -----------------------------------------------------------------

    def add_line(
        self,
        line: Any,
    ) -> None:
        """
        Add a canonical Line model to the network.
        """

        self._require_element(
            line,
            "line",
        )

        self._append_unique(
            self.lines,
            line,
            "line",
        )

        self._invalidate_topology()

    # -----------------------------------------------------------------

    def add_transformer(
        self,
        transformer: Any,
    ) -> None:
        """
        Add a canonical Transformer model to the network.
        """

        self._require_element(
            transformer,
            "transformer",
        )

        self._append_unique(
            self.transformers,
            transformer,
            "transformer",
        )

        self._invalidate_topology()

    # -----------------------------------------------------------------

    def add_generator(
        self,
        generator: Any,
    ) -> None:
        """
        Add a canonical Generator model to the network.

        Generator electrical power does not directly modify Y-bus.

        Bus study-state quantities are synchronized through
        ``sync_injections()``.
        """

        self._require_element(
            generator,
            "generator",
        )

        self._append_unique(
            self.generators,
            generator,
            "generator",
        )

    # -----------------------------------------------------------------

    def add_load(
        self,
        load: Any,
    ) -> None:
        """
        Add a canonical Load model to the network.

        Load electrical demand does not directly modify Y-bus.

        Bus study-state quantities are synchronized through
        ``sync_injections()``.
        """

        self._require_element(
            load,
            "load",
        )

        self._append_unique(
            self.loads,
            load,
            "load",
        )

    # -----------------------------------------------------------------

    def add_shunt(
        self,
        shunt: Any,
    ) -> None:
        """
        Add a canonical Shunt model to the network.

        Shunt elements contribute to network admittance and therefore
        invalidate the current Y-bus representation.
        """

        self._require_element(
            shunt,
            "shunt",
        )

        self._append_unique(
            self.shunts,
            shunt,
            "shunt",
        )

        self._invalidate_ybus()

    # -----------------------------------------------------------------

    @staticmethod
    def _require_element(
        element: Any,
        element_type: str,
    ) -> None:
        """
        Perform minimal structural validation.

        Detailed engineering validation belongs to the validation
        layer.
        """

        if element is None:
            raise ValueError(
                f"Cannot add None as a {element_type}."
            )

        if not hasattr(element, "id"):
            raise TypeError(
                f"{element_type.capitalize()} object must provide "
                "an 'id' attribute."
            )

    # -----------------------------------------------------------------

    @staticmethod
    def _append_unique(
        collection: List[Any],
        element: Any,
        element_type: str,
    ) -> None:
        """
        Append an element while preventing duplicate IDs within the
        target network collection.
        """

        element_id = element.id

        for existing in collection:
            if existing.id == element_id:
                raise ValueError(
                    f"Duplicate {element_type} ID: {element_id}"
                )

        collection.append(element)

    # =================================================================
    # INVALIDATION
    # =================================================================

    def _invalidate_topology(self) -> None:
        """
        Invalidate topology and all topology-dependent derived state.
        """

        self._topology_revision += 1

        self._topology_dirty = True
        self._ybus_dirty = True
        self._ybus_revision = -1

        if hasattr(self.topology, "_dirty"):
            self.topology._dirty = True

    # -----------------------------------------------------------------

    def _invalidate_ybus(self) -> None:
        """
        Invalidate Y-bus without changing topology revision.
        """

        self._ybus_dirty = True
        self._ybus_revision = -1

    # =================================================================
    # BUS INDEXING
    # =================================================================

    def rebuild_bus_index(self) -> Dict[Any, int]:
        """
        Rebuild the deterministic bus-ID to matrix-index mapping.

        Returns
        -------
        dict
            Mapping:

                bus.id -> numerical matrix index
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

    # =================================================================
    # TOPOLOGY
    # =================================================================

    def rebuild_topology(self):
        """
        Rebuild and return the network topology graph.
        """

        graph = self.topology.build()

        self._topology_dirty = False

        return graph

    # -----------------------------------------------------------------

    def find_islands(self):
        """
        Return the electrical network islands.

        Island detection is implemented by TopologyManager.
        """

        return self.topology.find_islands()

    # -----------------------------------------------------------------

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

    # =================================================================
    # Y-BUS
    # =================================================================

    def build_ybus(self):
        """
        Build and return the network Y-bus.

        Y-bus mathematics is implemented exclusively by
        ``YBusBuilder``.

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

    # -----------------------------------------------------------------

    def get_ybus(self):
        """
        Return the current Y-bus.

        Rebuilds the matrix automatically when invalid.
        """

        if (
            self.Ybus is None
            or self._ybus_dirty
            or self._ybus_revision != self._topology_revision
        ):
            return self.build_ybus()

        return self.Ybus

    # =================================================================
    # INJECTION AGGREGATION
    # =================================================================

    def sync_injections(self) -> None:
        """
        Aggregate Generator and Load injections onto each Bus.

        For every registered bus this recomputes:

            P_spec
            Q_spec

        from all generators and loads connected to that bus.

        Generator reactive-power limits are aggregated for buses
        operating as PV or SLACK buses.

        Notes
        -----
        This method modifies Bus study-state quantities only.

        It does not:

        - Build Y-bus.
        - Solve power flow.
        - Change generator Q.
        - Change bus classification.
        - Perform PV-to-PQ switching.
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

        # -------------------------------------------------------------
        # LOADS
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # GENERATORS
        # -------------------------------------------------------------

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

            if bus.is_pv() or bus.is_slack():

                q_min[bus] += generator.q_min
                q_max[bus] += generator.q_max

                has_generator[bus] = True

        # -------------------------------------------------------------
        # APPLY AGGREGATED BUS STATE
        # -------------------------------------------------------------

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

    # =================================================================
    # NETWORK RECONFIGURATION
    # =================================================================

    def reconfigure(self):
        """
        Rebuild topology and Y-bus after network reconfiguration.

        Returns
        -------
        scipy.sparse.csr_matrix
            Updated Y-bus.
        """

        self._invalidate_topology()

        self.rebuild_topology()

        return self.build_ybus()

    # =================================================================
    # ELEMENT STATUS
    # =================================================================

    def set_element_status(
        self,
        element: Any,
        in_service: bool,
    ) -> None:
        """
        Change the service state of a topology-affecting element.

        Parameters
        ----------
        element : object
            Network model element.

        in_service : bool
            Desired service state.

        Notes
        -----
        The Network only changes the model's service-state attribute
        and invalidates derived topology/Y-bus state.

        Engineering validation remains outside Network.
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

    # =================================================================
    # FAULT STATE
    # =================================================================

    def apply_fault(
        self,
        bus_id: Any,
        fault_type: str,
        Zf: complex = 0.0,
    ) -> None:
        """
        Store an active fault condition.

        This method only stores network study state.

        Fault-current calculations belong to the appropriate
        analysis/solver layers.
        """

        if not self.bus_index:
            self.rebuild_bus_index()

        if bus_id not in self.bus_index:
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

    # -----------------------------------------------------------------

    def clear_fault(self) -> None:
        """
        Clear the currently stored fault condition.
        """

        self.active_fault = None

    # =================================================================
    # VALIDATION HOOK
    # =================================================================

    def validate(self):
        """
        Delegate engineering validation to the validation layer.

        Network itself does not implement engineering validation.

        Returns
        -------
        object
            Validation result returned by ``core.validation``.
        """

        from core.validation import validate_network

        return validate_network(self)

    # =================================================================
    # SUMMARY
    # =================================================================

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

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
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

    # =================================================================
    # NETWORK ELEMENT REMOVAL
    # =================================================================

    def remove_bus(
        self,
        bus: Any,
    ) -> None:
        """
        Remove a registered Bus from the Network.

        Parameters
        ----------
        bus : Bus
            Canonical Bus object registered on this Network.

        Raises
        ------
        ValueError
            If the bus is None, is not registered, or is still
            referenced by another registered network element.

        Notes
        -----
        Bus removal is deliberately strict.

        A Bus cannot be removed while another canonical element
        references it because doing so would leave dangling
        topology/model references.

        Connection references are checked using the authoritative
        Terminal architecture of the model layer:

            Line:
                from_terminal.endpoint
                to_terminal.endpoint

            Transformer:
                from_terminal.endpoint
                to_terminal.endpoint

            Generator:
                bus

            Load:
                bus

            Shunt:
                terminal.endpoint

        The Network owns:

            * canonical collection membership;
            * registration indexes;
            * topology invalidation;
            * Y-bus invalidation.

        Therefore removal is implemented here rather than in:

            * Application;
            * TopologyManager;
            * UI;
            * plugins.

        Engineering/domain validation remains outside Network.
        """

        if bus is None:
            raise ValueError(
                "Bus cannot be None."
            )

        # -------------------------------------------------------------
        # REGISTRATION CHECK
        # -------------------------------------------------------------

        if bus not in self.buses:
            raise ValueError(
                f"Bus '{getattr(bus, 'id', bus)}' "
                "is not registered on this Network."
            )

        # -------------------------------------------------------------
        # REFERENCE CHECK — LINES
        #
        # Terminal endpoints are authoritative.
        # -------------------------------------------------------------

        for line in self.lines:

            from_terminal = getattr(
                line,
                "from_terminal",
                None,
            )

            to_terminal = getattr(
                line,
                "to_terminal",
                None,
            )

            from_endpoint = getattr(
                from_terminal,
                "endpoint",
                None,
            )

            to_endpoint = getattr(
                to_terminal,
                "endpoint",
                None,
            )

            if (
                from_endpoint is bus
                or to_endpoint is bus
            ):
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Line '{line.id}' references it."
                )

        # -------------------------------------------------------------
        # REFERENCE CHECK — TRANSFORMERS
        #
        # Terminal endpoints are authoritative.
        # -------------------------------------------------------------

        for transformer in self.transformers:

            from_terminal = getattr(
                transformer,
                "from_terminal",
                None,
            )

            to_terminal = getattr(
                transformer,
                "to_terminal",
                None,
            )

            from_endpoint = getattr(
                from_terminal,
                "endpoint",
                None,
            )

            to_endpoint = getattr(
                to_terminal,
                "endpoint",
                None,
            )

            if (
                from_endpoint is bus
                or to_endpoint is bus
            ):
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Transformer '{transformer.id}' references it."
                )

        # -------------------------------------------------------------
        # REFERENCE CHECK — GENERATORS
        # -------------------------------------------------------------

        for generator in self.generators:

            if getattr(generator, "bus", None) is bus:
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Generator '{generator.id}' references it."
                )

        # -------------------------------------------------------------
        # REFERENCE CHECK — LOADS
        # -------------------------------------------------------------

        for load in self.loads:

            if getattr(load, "bus", None) is bus:
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Load '{load.id}' references it."
                )

        # -------------------------------------------------------------
        # REFERENCE CHECK — SHUNTS
        #
        # Shunt is a single-terminal element.
        # -------------------------------------------------------------

        for shunt in self.shunts:

            terminal = getattr(
                shunt,
                "terminal",
                None,
            )

            endpoint = getattr(
                terminal,
                "endpoint",
                None,
            )

            if endpoint is bus:
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Shunt '{shunt.id}' references it."
                )

        # -------------------------------------------------------------
        # REMOVE FROM CANONICAL COLLECTION
        # -------------------------------------------------------------

        self.buses.remove(bus)

        # -------------------------------------------------------------
        # UPDATE BUS INDEX
        #
        # The existing deterministic index may now contain stale
        # positions for buses after the removed bus. Therefore the
        # entire index is rebuilt rather than merely deleting one key.
        # -------------------------------------------------------------

        self.rebuild_bus_index()

        # -------------------------------------------------------------
        # INVALIDATE DERIVED NETWORK STATE
        #
        # Bus membership is topology-affecting and therefore both
        # topology and Y-bus must be invalidated.
        # -------------------------------------------------------------

        self._invalidate_topology()

    # -----------------------------------------------------------------

    def remove_line(
        self,
        line: Any,
    ) -> None:
        """
        Remove a registered Line from the Network.

        Parameters
        ----------
        line : Line
            Canonical Line object registered on this Network.

        Raises
        ------
        ValueError
            If ``line`` is None or the exact canonical Line object
            is not registered on this Network.

        Notes
        -----
        Line removal changes Network membership only.

        It does NOT:

            * disconnect ``from_terminal``;
            * disconnect ``to_terminal``;
            * delete either endpoint element;
            * modify either endpoint Bus;
            * directly manipulate TopologyManager;
            * directly manipulate YBusBuilder;
            * rebuild topology immediately;
            * rebuild Y-bus immediately.

        The Line's terminal relationships remain part of the Line
        model object.

        Network owns only the assembled-network membership of the
        Line.

        Removing a Line is therefore an edge-removal operation:

            Element A
                |
              Terminal
                |
               Line
                |
              Terminal
                |
            Element B

        becomes:

            Element A          Element B

        without deleting either Element A or Element B.

        Derived topology and Y-bus representations are invalidated
        through the existing Network invalidation boundary and will
        be rebuilt lazily when requested.

        Canonical Object Identity
        --------------------------
        The Network stores references to canonical Core model
        objects.

        Consequently the removal operation searches for the exact
        object instance using identity:

            registered_line is line

        rather than relying on equality or matching only ``line.id``.

        This prevents an unrelated object with the same identifier
        from being removed accidentally.
        """

        if line is None:
            raise ValueError(
                "Line cannot be None."
            )

        # -------------------------------------------------------------
        # FIND THE CANONICAL REGISTERED OBJECT
        #
        # Identity is intentional.
        # -------------------------------------------------------------

        for index, registered_line in enumerate(self.lines):

            if registered_line is line:

                # -----------------------------------------------------
                # REMOVE ONLY NETWORK MEMBERSHIP
                # -----------------------------------------------------

                del self.lines[index]

                # -----------------------------------------------------
                # INVALIDATE DERIVED NETWORK STATE
                #
                # Line membership is topology-affecting.
                # Therefore both topology and Y-bus become dirty.
                # -----------------------------------------------------

                self._invalidate_topology()

                return

        # -------------------------------------------------------------
        # CANONICAL REGISTRATION FAILURE
        # -------------------------------------------------------------

        raise ValueError(
            f"Line '{getattr(line, 'id', line)}' "
            "is not registered on this Network."
        )
