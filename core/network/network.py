# ============================================================
# File: core/network/network.py
# GridForge V2 — Network Aggregate
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Network Aggregate
================================

The Network is the authoritative electrical-system aggregate.

Network owns:

    - canonical equipment membership through NetworkRegistry
    - terminal-centric topology through NetworkTopology
    - Network-derived lifecycle state through NetworkState
    - canonical BusIndex used by numerical consumers

Network does NOT own:

    - YBus or other numerical matrices
    - solver state
    - study state
    - numerical operating-point state
    - GUI state
    - command/history state

Numerical artifacts are derived from Network and carry the
Network topology revision from which they were created.

A Network mutation affecting structural topology must invalidate:

    1. NetworkState.topology_revision
    2. NetworkState.topology_dirty
    3. BusIndex

Network is intentionally a thin façade. Equipment-specific
electrical behavior belongs to the model layer; topology logic
belongs to NetworkTopology; membership belongs to NetworkRegistry;
and numerical construction belongs to Numerical.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from core.model import (
    Battery,
    Branch,
    Bus,
    Cable,
    Capacitor,
    CT,
    CVT,
    Disconnector,
    Generator,
    Grid,
    Injection,
    Line,
    Load,
    Motor,
    PT,
    Reactor,
    Relay,
    Shunt,
    Solar,
    Switch,
    SynchronousMachine,
    Transformer,
)

from .indexing import BusIndex
from .registry import NetworkRegistry
from .state import NetworkState
from .topology import NetworkTopology


class Network:
    """
    Authoritative electrical network aggregate.

    The class provides a stable façade over the Network
    infrastructure without implementing equipment-specific
    electrical logic.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        *,
        registry: Optional[NetworkRegistry] = None,
        topology: Optional[NetworkTopology] = None,
        state: Optional[NetworkState] = None,
        index: Optional[BusIndex] = None,
    ) -> None:
        """
        Initialize an authoritative Network aggregate.

        Parameters
        ----------
        registry:
            Optional existing NetworkRegistry.

        topology:
            Optional existing NetworkTopology.

        state:
            Optional existing NetworkState.

        index:
            Optional existing BusIndex.

        No numerical YBus object is accepted or stored.
        """

        self.registry = (
            registry
            if registry is not None
            else NetworkRegistry()
        )

        self.topology = (
            topology
            if topology is not None
            else NetworkTopology()
        )

        self.state = (
            state
            if state is not None
            else NetworkState()
        )

        self.index = (
            index
            if index is not None
            else BusIndex()
        )

    # ========================================================
    # REGISTRY FAÇADES
    # ========================================================

    @property
    def buses(self) -> tuple[Bus, ...]:
        """Return registered buses."""

        return tuple(self.registry.buses)

    @property
    def grids(self) -> tuple[Grid, ...]:
        """Return registered grids."""

        return tuple(self.registry.grids)

    @property
    def generators(self) -> tuple[Generator, ...]:
        """Return registered generators."""

        return tuple(self.registry.generators)

    @property
    def loads(self) -> tuple[Load, ...]:
        """Return registered loads."""

        return tuple(self.registry.loads)

    @property
    def shunts(self) -> tuple[Shunt, ...]:
        """Return registered shunts."""

        return tuple(self.registry.shunts)

    @property
    def lines(self) -> tuple[Line, ...]:
        """Return registered lines."""

        return tuple(self.registry.lines)

    @property
    def transformers(self) -> tuple[Transformer, ...]:
        """Return registered transformers."""

        return tuple(self.registry.transformers)

    @property
    def branches(self) -> tuple[Branch, ...]:
        """Return registered branches."""

        return tuple(self.registry.branches)

    @property
    def cables(self) -> tuple[Cable, ...]:
        """Return registered cables."""

        return tuple(self.registry.cables)

    @property
    def switches(self) -> tuple[Switch, ...]:
        """Return registered switches."""

        return tuple(self.registry.switches)

    @property
    def disconnectors(self) -> tuple[Disconnector, ...]:
        """Return registered disconnectors."""

        return tuple(self.registry.disconnectors)

    @property
    def fuses(self) -> tuple[Any, ...]:
        """Return registered fuses when supported by the registry."""

        return tuple(
            getattr(
                self.registry,
                "fuses",
                (),
            )
        )

    @property
    def reactors(self) -> tuple[Reactor, ...]:
        """Return registered reactors."""

        return tuple(
            getattr(
                self.registry,
                "reactors",
                (),
            )
        )

    @property
    def capacitors(self) -> tuple[Capacitor, ...]:
        """Return registered capacitors."""

        return tuple(
            getattr(
                self.registry,
                "capacitors",
                (),
            )
        )

    @property
    def motors(self) -> tuple[Motor, ...]:
        """Return registered motors."""

        return tuple(
            getattr(
                self.registry,
                "motors",
                (),
            )
        )

    @property
    def batteries(self) -> tuple[Battery, ...]:
        """Return registered batteries."""

        return tuple(
            getattr(
                self.registry,
                "batteries",
                (),
            )
        )

    @property
    def solar(self) -> tuple[Solar, ...]:
        """Return registered solar models."""

        return tuple(
            getattr(
                self.registry,
                "solar",
                (),
            )
        )

    @property
    def injections(self) -> tuple[Injection, ...]:
        """Return registered injections."""

        return tuple(
            getattr(
                self.registry,
                "injections",
                (),
            )
        )

    @property
    def relays(self) -> tuple[Relay, ...]:
        """Return registered relays."""

        return tuple(
            getattr(
                self.registry,
                "relays",
                (),
            )
        )

    @property
    def synchronous_machines(
        self,
    ) -> tuple[SynchronousMachine, ...]:
        """Return registered synchronous machines."""

        return tuple(
            getattr(
                self.registry,
                "synchronous_machines",
                (),
            )
        )

    @property
    def cts(self) -> tuple[CT, ...]:
        """Return registered CT models."""

        return tuple(
            getattr(
                self.registry,
                "cts",
                (),
            )
        )

    @property
    def pts(self) -> tuple[PT, ...]:
        """Return registered PT models."""

        return tuple(
            getattr(
                self.registry,
                "pts",
                (),
            )
        )

    @property
    def cvts(self) -> tuple[CVT, ...]:
        """Return registered CVT models."""

        return tuple(
            getattr(
                self.registry,
                "cvts",
                (),
            )
        )

    # ========================================================
    # LOOKUP
    # ========================================================

    def get_by_id(
        self,
        model_id: str,
    ) -> Any:
        """
        Return a registered model by identifier.
        """

        return self.registry.get_by_id(
            model_id
        )

    # ========================================================
    # ADD
    # ========================================================

    def add_bus(self, bus: Bus) -> None:
        """Register a Bus and invalidate structural state."""

        self.registry.add_bus(bus)
        self._invalidate_structure()

    def add_grid(self, grid: Grid) -> None:
        """Register a Grid."""

        self.registry.add_grid(grid)
        self._invalidate_structure()

    def add_generator(
        self,
        generator: Generator,
    ) -> None:
        """Register a Generator."""

        self.registry.add_generator(generator)
        self._invalidate_structure()

    def add_load(
        self,
        load: Load,
    ) -> None:
        """Register a Load."""

        self.registry.add_load(load)
        self._invalidate_structure()

    def add_shunt(
        self,
        shunt: Shunt,
    ) -> None:
        """Register a Shunt."""

        self.registry.add_shunt(shunt)
        self._invalidate_structure()

    def add_line(
        self,
        line: Line,
    ) -> None:
        """Register a Line."""

        self.registry.add_line(line)
        self._invalidate_structure()

    def add_transformer(
        self,
        transformer: Transformer,
    ) -> None:
        """Register a Transformer."""

        self.registry.add_transformer(transformer)
        self._invalidate_structure()

    def add_branch(
        self,
        branch: Branch,
    ) -> None:
        """Register a Branch."""

        self.registry.add_branch(branch)
        self._invalidate_structure()

    def add_cable(
        self,
        cable: Cable,
    ) -> None:
        """Register a Cable."""

        self.registry.add_cable(cable)
        self._invalidate_structure()

    def add_switch(
        self,
        switch: Switch,
    ) -> None:
        """Register a Switch."""

        self.registry.add_switch(switch)
        self._invalidate_structure()

    def add_disconnector(
        self,
        disconnector: Disconnector,
    ) -> None:
        """Register a Disconnector."""

        self.registry.add_disconnector(disconnector)
        self._invalidate_structure()

    def add_fuse(
        self,
        fuse: Any,
    ) -> None:
        """Register a Fuse when supported by the registry."""

        self.registry.add_fuse(fuse)
        self._invalidate_structure()

    def add_reactor(
        self,
        reactor: Reactor,
    ) -> None:
        """Register a Reactor."""

        self.registry.add_reactor(reactor)
        self._invalidate_structure()

    def add_capacitor(
        self,
        capacitor: Capacitor,
    ) -> None:
        """Register a Capacitor."""

        self.registry.add_capacitor(capacitor)
        self._invalidate_structure()

    def add_motor(
        self,
        motor: Motor,
    ) -> None:
        """Register a Motor."""

        self.registry.add_motor(motor)
        self._invalidate_structure()

    def add_battery(
        self,
        battery: Battery,
    ) -> None:
        """Register a Battery."""

        self.registry.add_battery(battery)
        self._invalidate_structure()

    def add_solar(
        self,
        solar: Solar,
    ) -> None:
        """Register a Solar model."""

        self.registry.add_solar(solar)
        self._invalidate_structure()

    def add_injection(
        self,
        injection: Injection,
    ) -> None:
        """Register an Injection."""

        self.registry.add_injection(injection)
        self._invalidate_structure()

    def add_relay(
        self,
        relay: Relay,
    ) -> None:
        """Register a Relay."""

        self.registry.add_relay(relay)
        self._invalidate_structure()

    def add_synchronous_machine(
        self,
        machine: SynchronousMachine,
    ) -> None:
        """Register a SynchronousMachine."""

        self.registry.add_synchronous_machine(machine)
        self._invalidate_structure()

    def add_ct(
        self,
        ct: CT,
    ) -> None:
        """Register a CT."""

        self.registry.add_ct(ct)
        self._invalidate_structure()

    def add_pt(
        self,
        pt: PT,
    ) -> None:
        """Register a PT."""

        self.registry.add_pt(pt)
        self._invalidate_structure()

    def add_cvt(
        self,
        cvt: CVT,
    ) -> None:
        """Register a CVT."""

        self.registry.add_cvt(cvt)
        self._invalidate_structure()

    # ========================================================
    # REMOVE
    # ========================================================

    def remove_by_id(
        self,
        model_id: str,
    ) -> Any:
        """
        Remove a registered model by identifier.

        Returns the removed model.
        """

        removed = self.registry.remove_by_id(
            model_id
        )

        self._invalidate_structure()

        return removed

    # ========================================================
    # STRUCTURAL INVALIDATION
    # ========================================================

    def _invalidate_structure(self) -> None:
        """
        Invalidate Network-derived structural state.

        NetworkState owns the topology revision.

        BusIndex owns the bus-to-matrix-index lifecycle.

        Neither responsibility is duplicated here.
        """

        self.state.invalidate_topology()
        self.index.invalidate()

    # ========================================================
    # INDEX PREPARATION
    # ========================================================

    def rebuild_index(self) -> None:
        """
        Explicitly prepare the authoritative BusIndex.

        This is a Network preparation operation and is therefore
        allowed to mutate BusIndex.

        Numerical consumers must never call this implicitly.
        """

        self.index.rebuild(
            self.buses
        )

    # ========================================================
    # TOPOLOGY SYNCHRONIZATION
    # ========================================================

    def rebuild_topology(self) -> None:
        """
        Rebuild the Network topology representation.

        NetworkTopology owns the topology implementation.
        """

        rebuild = getattr(
            self.topology,
            "rebuild",
            None,
        )

        if rebuild is None:
            raise AttributeError(
                "NetworkTopology must provide rebuild()."
            )

        rebuild(
            self
        )

        self.state.topology_rebuilt()

    # ========================================================
    # PREPARATION
    # ========================================================

    def prepare(self) -> None:
        """
        Explicitly prepare Network-derived structures.

        Preparation:

            1. rebuilds Network topology
            2. rebuilds BusIndex

        No numerical YBus is constructed here.
        """

        self.rebuild_topology()
        self.rebuild_index()

    # ========================================================
    # BASIC STATE
    # ========================================================

    @property
    def topology_revision(self) -> int:
        """Return the authoritative Network topology revision."""

        return self.state.topology_revision

    @property
    def topology_valid(self) -> bool:
        """Return whether derived topology is synchronized."""

        return self.state.topology_valid

    @property
    def index_valid(self) -> bool:
        """Return whether the authoritative BusIndex is valid."""

        return self.index.valid

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """Return a concise developer-facing representation."""

        return (
            "Network("
            f"buses={len(self.buses)}, "
            f"lines={len(self.lines)}, "
            f"transformers={len(self.transformers)}, "
            f"topology_revision="
            f"{self.state.topology_revision}, "
            f"topology_valid="
            f"{self.state.topology_valid}, "
            f"index_valid="
            f"{self.index.valid}"
            ")"
        )


__all__ = [
    "Network",
]
