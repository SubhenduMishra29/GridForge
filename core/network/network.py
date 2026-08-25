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
        |      +-- Line
        |      +-- Transformer
        |      +-- Generator
        |      +-- Load
        |      +-- Shunt
        |
        +-- Topology
        +-- YBus
        +-- Services

Lookup boundary
---------------

Application code must use:

    network.get_by_id(element_type, object_id)

and must not access registry collections directly.

The Network façade delegates lookup to NetworkRegistry.

Terminal resolution remains an Application-layer concern.
"""

from __future__ import annotations

from typing import Any

from .registry import NetworkRegistry
from .topology import NetworkTopology
from .ybus import YBus


class Network:
    """
    Canonical electrical network façade.

    The Network owns the canonical network-level infrastructure
    while NetworkRegistry owns equipment membership.
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
        return self.registry.buses

    @property
    def lines(self) -> tuple[Any, ...]:
        return self.registry.lines

    @property
    def transformers(self) -> tuple[Any, ...]:
        return self.registry.transformers

    @property
    def generators(self) -> tuple[Any, ...]:
        return self.registry.generators

    @property
    def loads(self) -> tuple[Any, ...]:
        return self.registry.loads

    @property
    def shunts(self) -> tuple[Any, ...]:
        return self.registry.shunts

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
            Canonical equipment family:

                bus
                line
                transformer
                generator
                load
                shunt

        object_id:
            Canonical equipment identifier.

        Returns
        -------
        Any
            The exact registered equipment instance.

        Notes
        -----
        Lookup is delegated to NetworkRegistry.

        This method does not:

            * create equipment;
            * clone equipment;
            * mutate equipment;
            * connect terminals;
            * resolve endpoints;
            * modify topology.
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
        """
        Register a Bus in the canonical network.
        """

        self.registry.add_bus(bus)
        self._invalidate_topology()

    def remove_bus(
        self,
        bus: Any,
    ) -> None:
        """
        Remove a Bus from the canonical network.
        """

        self.registry.remove_bus(bus)
        self._invalidate_topology()

    # ========================================================
    # LINE
    # ========================================================

    def add_line(
        self,
        line: Any,
    ) -> None:
        """
        Register a Line in the canonical network.
        """

        self.registry.add_line(line)
        self._invalidate_topology()

    def remove_line(
        self,
        line: Any,
    ) -> None:
        """
        Remove a Line from the canonical network.
        """

        self.registry.remove_line(line)
        self._invalidate_topology()

    # ========================================================
    # TRANSFORMER
    # ========================================================

    def add_transformer(
        self,
        transformer: Any,
    ) -> None:
        """
        Register a Transformer in the canonical network.
        """

        self.registry.add_transformer(transformer)
        self._invalidate_topology()

    def remove_transformer(
        self,
        transformer: Any,
    ) -> None:
        """
        Remove a Transformer from the canonical network.
        """

        self.registry.remove_transformer(
            transformer
        )
        self._invalidate_topology()

    # ========================================================
    # GENERATOR
    # ========================================================

    def add_generator(
        self,
        generator: Any,
    ) -> None:
        """
        Register a Generator in the canonical network.
        """

        self.registry.add_generator(generator)

    def remove_generator(
        self,
        generator: Any,
    ) -> None:
        """
        Remove a Generator from the canonical network.
        """

        self.registry.remove_generator(
            generator
        )

    # ========================================================
    # LOAD
    # ========================================================

    def add_load(
        self,
        load: Any,
    ) -> None:
        """
        Register a Load in the canonical network.
        """

        self.registry.add_load(load)

    def remove_load(
        self,
        load: Any,
    ) -> None:
        """
        Remove a Load from the canonical network.
        """

        self.registry.remove_load(load)

    # ========================================================
    # SHUNT
    # ========================================================

    def add_shunt(
        self,
        shunt: Any,
    ) -> None:
        """
        Register a Shunt in the canonical network.
        """

        self.registry.add_shunt(shunt)
        self._invalidate_ybus()

    def remove_shunt(
        self,
        shunt: Any,
    ) -> None:
        """
        Remove a Shunt from the canonical network.
        """

        self.registry.remove_shunt(shunt)
        self._invalidate_ybus()

    # ========================================================
    # CACHE / ANALYSIS INVALIDATION
    # ========================================================

    def _invalidate_topology(self) -> None:
        """
        Invalidate network topology-dependent state.
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
        Invalidate Y-bus dependent state.

        The YBus implementation owns the actual cache semantics.
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
