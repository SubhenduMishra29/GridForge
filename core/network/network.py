# ============================================================
# File: core/network/network.py
# GridForge V2 — Canonical Network Façade
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Canonical Network Façade
=======================================

Network is the public façade for the canonical electrical
network model.

Responsibilities
----------------

    * expose canonical network equipment;
    * delegate equipment membership to NetworkRegistry;
    * provide canonical equipment lookup;
    * coordinate network-level topology/cache invalidation;
    * expose network-level services.

Network does NOT:

    * own duplicate equipment collections;
    * resolve UI/SLD objects;
    * know about Qt;
    * render anything;
    * create application commands;
    * manage command history;
    * perform Application-layer endpoint resolution.

Canonical ownership
-------------------

    Network
        |
        +-- NetworkRegistry
        |      |
        |      +-- Bus
        |      +-- Grid
        |      +-- Generator
        |      +-- Load
        |      +-- Shunt
        |      +-- Line
        |      +-- Transformer
        |      +-- Branch
        |      +-- Cable
        |      +-- Switch
        |      +-- Disconnector
        |      +-- Fuse
        |
        +-- Topology
        +-- YBus
        +-- Services

Lookup boundary
---------------

Application code must use:

    network.get_by_id(element_type, object_id)

and must not access registry collections directly.

Terminal-centric topology
--------------------------

Network membership and topology are separate concerns.

Electrical equipment owns its authoritative Terminal objects.

For one-terminal equipment:

    Equipment
        |
        +-- Terminal
              |
              +-- endpoint

For two-terminal equipment:

    Equipment
        |
        +-- Terminal A
        |      |
        |      +-- endpoint
        |
        +-- Terminal B
               |
               +-- endpoint

Network does not introduce parallel bus-id topology state.

Endpoint resolution remains an Application-layer concern.

Y-bus / numerical indexing
---------------------------

This façade does not define:

    * Y-bus formulation;
    * numerical bus indexing;
    * matrix stamping;
    * solver ordering;
    * numerical index reconciliation.

Those remain separate functionality-audit concerns.
"""


from __future__ import annotations

from typing import Any

from .registry import NetworkRegistry
from .topology import NetworkTopology
from .ybus import YBus


class Network:
    """
    Canonical electrical network façade.

    Network owns the canonical network-level infrastructure
    while NetworkRegistry owns equipment membership.

    Network does not duplicate registry state.
    """

    def __init__(
        self,
        *,
        registry: NetworkRegistry | None = None,
        topology: NetworkTopology | None = None,
        ybus: YBus | None = None,
    ) -> None:
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

        self.ybus = (
            ybus
            if ybus is not None
            else YBus()
        )

    # ========================================================
    # CANONICAL COLLECTIONS
    # ========================================================

    @property
    def buses(self) -> tuple[Any, ...]:
        """Return all canonical Bus objects."""

        return self.registry.buses

    @property
    def grids(self) -> tuple[Any, ...]:
        """Return all canonical Grid objects."""

        return self.registry.grids

    @property
    def generators(self) -> tuple[Any, ...]:
        """Return all canonical Generator objects."""

        return self.registry.generators

    @property
    def loads(self) -> tuple[Any, ...]:
        """Return all canonical Load objects."""

        return self.registry.loads

    @property
    def shunts(self) -> tuple[Any, ...]:
        """Return all canonical Shunt objects."""

        return self.registry.shunts

    @property
    def lines(self) -> tuple[Any, ...]:
        """Return all canonical Line objects."""

        return self.registry.lines

    @property
    def transformers(self) -> tuple[Any, ...]:
        """Return all canonical Transformer objects."""

        return self.registry.transformers

    @property
    def branches(self) -> tuple[Any, ...]:
        """Return all canonical Branch objects."""

        return self.registry.branches

    @property
    def cables(self) -> tuple[Any, ...]:
        """Return all canonical Cable objects."""

        return self.registry.cables

    @property
    def switches(self) -> tuple[Any, ...]:
        """Return all canonical Switch objects."""

        return self.registry.switches

    @property
    def disconnectors(self) -> tuple[Any, ...]:
        """Return all canonical Disconnector objects."""

        return self.registry.disconnectors

    @property
    def fuses(self) -> tuple[Any, ...]:
        """Return all canonical Fuse objects."""

        return self.registry.fuses

    # ========================================================
    # CANONICAL EQUIPMENT LOOKUP
    # ========================================================

    def get_by_id(
        self,
        element_type: str,
        object_id: str,
    ) -> Any:
        """
        Return the canonical registered equipment object.

        Parameters
        ----------
        element_type:
            Canonical equipment family.

        object_id:
            Canonical equipment identifier.

        Returns
        -------
        Any
            Exact registered Core model instance.

        Notes
        -----
        Lookup is delegated to NetworkRegistry.

        This method does not:

            * create equipment;
            * clone equipment;
            * mutate equipment;
            * connect terminals;
            * resolve endpoints;
            * modify topology;
            * perform numerical indexing.
        """

        return self.registry.get_by_id(
            element_type,
            object_id,
        )

    # ========================================================
    # BUS
    # ========================================================

    def add_bus(
        self,
        bus: Any,
    ) -> None:
        """Register a Bus in the canonical network."""

        self.registry.add_bus(bus)
        self._invalidate_topology()

    def remove_bus(
        self,
        bus: Any,
    ) -> None:
        """Remove a Bus from the canonical network."""

        self.registry.remove_bus(bus)
        self._invalidate_topology()

    # ========================================================
    # GRID
    # ========================================================

    def add_grid(
        self,
        grid: Any,
    ) -> None:
        """
        Register a Grid in the canonical network.

        Grid is a first-class electrical network element.

        Grid is NOT a Network container.
        """

        self.registry.add_grid(grid)
        self._invalidate_topology()

    def remove_grid(
        self,
        grid: Any,
    ) -> None:
        """Remove a Grid from the canonical network."""

        self.registry.remove_grid(grid)
        self._invalidate_topology()

    # ========================================================
    # GENERATOR
    # ========================================================

    def add_generator(
        self,
        generator: Any,
    ) -> None:
        """Register a Generator in the canonical network."""

        self.registry.add_generator(generator)
        self._invalidate_topology()

    def remove_generator(
        self,
        generator: Any,
    ) -> None:
        """Remove a Generator from the canonical network."""

        self.registry.remove_generator(generator)
        self._invalidate_topology()

    # ========================================================
    # LOAD
    # ========================================================

    def add_load(
        self,
        load: Any,
    ) -> None:
        """Register a Load in the canonical network."""

        self.registry.add_load(load)
        self._invalidate_topology()

    def remove_load(
        self,
        load: Any,
    ) -> None:
        """Remove a Load from the canonical network."""

        self.registry.remove_load(load)
        self._invalidate_topology()

    # ========================================================
    # SHUNT
    # ========================================================

    def add_shunt(
        self,
        shunt: Any,
    ) -> None:
        """
        Register a Shunt in the canonical network.

        Shunt owns its electrical admittance.

        Network does not perform Y-bus stamping.
        """

        self.registry.add_shunt(shunt)
        self._invalidate_topology()
        self._invalidate_ybus()

    def remove_shunt(
        self,
        shunt: Any,
    ) -> None:
        """Remove a Shunt from the canonical network."""

        self.registry.remove_shunt(shunt)
        self._invalidate_topology()
        self._invalidate_ybus()

    # ========================================================
    # LINE
    # ========================================================

    def add_line(
        self,
        line: Any,
    ) -> None:
        """Register a Line in the canonical network."""

        self.registry.add_line(line)
        self._invalidate_topology()

    def remove_line(
        self,
        line: Any,
    ) -> None:
        """Remove a Line from the canonical network."""

        self.registry.remove_line(line)
        self._invalidate_topology()

    # ========================================================
    # TRANSFORMER
    # ========================================================

    def add_transformer(
        self,
        transformer: Any,
    ) -> None:
        """Register a Transformer in the canonical network."""

        self.registry.add_transformer(transformer)
        self._invalidate_topology()

    def remove_transformer(
        self,
        transformer: Any,
    ) -> None:
        """Remove a Transformer from the canonical network."""

        self.registry.remove_transformer(transformer)
        self._invalidate_topology()

    # ========================================================
    # BRANCH
    # ========================================================

    def add_branch(
        self,
        branch: Any,
    ) -> None:
        """
        Register a Branch in the canonical network.

        Branch topology is represented exclusively through
        its authoritative terminals.
        """

        self.registry.add_branch(branch)
        self._invalidate_topology()

    def remove_branch(
        self,
        branch: Any,
    ) -> None:
        """
        Remove a Branch from the canonical network.
        """

        self.registry.remove_branch(branch)
        self._invalidate_topology()

    # ========================================================
    # CABLE
    # ========================================================

    def add_cable(
        self,
        cable: Any,
    ) -> None:
        """
        Register a Cable in the canonical network.

        Cable remains a branch-family model and therefore
        remains terminal-centric.
        """

        self.registry.add_cable(cable)
        self._invalidate_topology()

    def remove_cable(
        self,
        cable: Any,
    ) -> None:
        """Remove a Cable from the canonical network."""

        self.registry.remove_cable(cable)
        self._invalidate_topology()

    # ========================================================
    # SWITCH
    # ========================================================

    def add_switch(
        self,
        switch: Any,
    ) -> None:
        """
        Register a Switch in the canonical network.

        Switching state belongs to the Switch model.

        Topological endpoints remain represented by terminals.
        """

        self.registry.add_switch(switch)
        self._invalidate_topology()
        self._invalidate_ybus()

    def remove_switch(
        self,
        switch: Any,
    ) -> None:
        """Remove a Switch from the canonical network."""

        self.registry.remove_switch(switch)
        self._invalidate_topology()
        self._invalidate_ybus()

    # ========================================================
    # DISCONNECTOR
    # ========================================================

    def add_disconnector(
        self,
        disconnector: Any,
    ) -> None:
        """
        Register a Disconnector in the canonical network.

        Disconnector operating state remains model-owned.
        """

        self.registry.add_disconnector(disconnector)
        self._invalidate_topology()
        self._invalidate_ybus()

    def remove_disconnector(
        self,
        disconnector: Any,
    ) -> None:
        """Remove a Disconnector from the canonical network."""

        self.registry.remove_disconnector(disconnector)
        self._invalidate_topology()
        self._invalidate_ybus()

    # ========================================================
    # FUSE
    # ========================================================

    def add_fuse(
        self,
        fuse: Any,
    ) -> None:
        """
        Register a Fuse in the canonical network.

        Fuse state remains model-owned.
        """

        self.registry.add_fuse(fuse)
        self._invalidate_topology()
        self._invalidate_ybus()

    def remove_fuse(
        self,
        fuse: Any,
    ) -> None:
        """Remove a Fuse from the canonical network."""

        self.registry.remove_fuse(fuse)
        self._invalidate_topology()
        self._invalidate_ybus()

    # ========================================================
    # NETWORK MODEL INVENTORY
    # ========================================================

    @property
    def model_types(self) -> tuple[str, ...]:
        """
        Return the canonical supported model families.

        This is descriptive only. Registry remains the authority
        for membership.
        """

        return (
            "bus",
            "grid",
            "generator",
            "load",
            "shunt",
            "line",
            "transformer",
            "branch",
            "cable",
            "switch",
            "disconnector",
            "fuse",
        )

    # ========================================================
    # CACHE / ANALYSIS INVALIDATION
    # ========================================================

    def _invalidate_topology(self) -> None:
        """
        Invalidate topology-dependent state.

        Network does not rebuild topology here.
        """

        invalidate = getattr(
            self.topology,
            "invalidate",
            None,
        )

        if callable(invalidate):
            invalidate()

        self._invalidate_ybus()

    def _invalidate_ybus(self) -> None:
        """
        Invalidate Y-bus-dependent cached state.

        This does NOT perform:

            * bus indexing;
            * Y-bus construction;
            * numerical stamping;
            * solver ordering.

        Those remain outside this architectural reconciliation.
        """

        invalidate = getattr(
            self.ybus,
            "invalidate",
            None,
        )

        if callable(invalidate):
            invalidate()


__all__ = [
    "Network",
]
