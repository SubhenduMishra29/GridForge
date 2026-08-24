# ============================================================
# File: core/network/registry.py
# GridForge V2 — Network Registry
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Network Registry
=============================

Canonical membership registry for an assembled Network.

The registry owns membership of canonical model objects:

    Bus
    Line
    Transformer
    Generator
    Load
    Shunt

Responsibilities
----------------
The registry is responsible only for:

    * validating minimal object structure;
    * registering canonical model objects;
    * preventing duplicate IDs within an element family;
    * removing registered objects by canonical identity;
    * exposing the registered collections.

The registry does NOT own:

    * electrical topology;
    * terminal connectivity;
    * bus indexing;
    * Y-bus construction;
    * network-derived state;
    * engineering validation;
    * study calculations;
    * command execution;
    * transactions;
    * SLD/UI state.

Architecture
------------

    core.model
        |
        | canonical model objects
        v
    NetworkRegistry
        |
        | membership
        v
    Network
        |
        +--> TopologyManager
        +--> BusIndex
        +--> YBusBuilder
        +--> NetworkState

Canonical Object Identity
--------------------------
The registry stores references to canonical model objects.

Registration uniqueness is determined by:

    element.id

Removal is intentionally identity-based:

    registered_element is element

An unrelated object having the same ID must never be removed from
the Network accidentally.

Bus Removal
-----------
Bus removal is a membership operation, but a bus cannot be removed
while another registered network element still references it.

The registry therefore performs the minimal structural reference
check required to preserve membership integrity.

Authoritative connection representation is terminal-based:

    Line:
        from_terminal
        to_terminal

    Transformer:
        from_terminal
        to_terminal

    Shunt:
        terminal

Generator and Load retain their canonical bus association:

    generator.bus
    load.bus

Terminal-to-bus resolution is delegated to the canonical endpoint
resolver rather than duplicated here.

The registry does not disconnect elements. It only determines whether
removal would leave an invalid registered-network reference.

Network is responsible for invalidating derived state after registry
membership changes.

GridForge V2 Boundary
---------------------
This registry is intentionally small.

If a requirement concerns:

    topology
    electrical compatibility
    terminal connection
    Y-bus
    bus indexing
    engineering validation
    command semantics

it belongs elsewhere.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any, List

from .endpoint import resolve_terminal_bus


class NetworkRegistry:
    """
    Canonical membership registry for a GridForge Network.

    The registry stores references to canonical objects originating
    from ``core.model``. It does not create or clone model objects.
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self) -> None:
        """
        Initialize an empty network registry.
        """

        self.buses: List[Any] = []
        self.lines: List[Any] = []
        self.transformers: List[Any] = []
        self.generators: List[Any] = []
        self.loads: List[Any] = []
        self.shunts: List[Any] = []

    # ============================================================
    # STRUCTURAL VALIDATION
    # ============================================================

    @staticmethod
    def require_element(
        element: Any,
        element_type: str,
    ) -> None:
        """
        Perform minimal structural validation.

        Engineering validation does not belong to the registry.

        Parameters
        ----------
        element:
            Canonical model object.

        element_type:
            Human-readable element family name.
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

    # ------------------------------------------------------------

    @staticmethod
    def append_unique(
        collection: List[Any],
        element: Any,
        element_type: str,
    ) -> None:
        """
        Append an element while enforcing ID uniqueness.

        Uniqueness is enforced only within the supplied element
        collection.

        Parameters
        ----------
        collection:
            Target registry collection.

        element:
            Canonical model object.

        element_type:
            Human-readable element family name.
        """

        element_id = element.id

        for existing in collection:

            if existing.id == element_id:
                raise ValueError(
                    f"Duplicate {element_type} ID: {element_id}"
                )

        collection.append(element)

    # ============================================================
    # ADD — BUS
    # ============================================================

    def add_bus(
        self,
        bus: Any,
    ) -> None:
        """
        Register a canonical Bus.

        Bus IDs must be unique within this Network.
        """

        self.require_element(
            bus,
            "bus",
        )

        self.append_unique(
            self.buses,
            bus,
            "bus",
        )

    # ============================================================
    # ADD — LINE
    # ============================================================

    def add_line(
        self,
        line: Any,
    ) -> None:
        """
        Register a canonical Line.
        """

        self.require_element(
            line,
            "line",
        )

        self.append_unique(
            self.lines,
            line,
            "line",
        )

    # ============================================================
    # ADD — TRANSFORMER
    # ============================================================

    def add_transformer(
        self,
        transformer: Any,
    ) -> None:
        """
        Register a canonical Transformer.
        """

        self.require_element(
            transformer,
            "transformer",
        )

        self.append_unique(
            self.transformers,
            transformer,
            "transformer",
        )

    # ============================================================
    # ADD — GENERATOR
    # ============================================================

    def add_generator(
        self,
        generator: Any,
    ) -> None:
        """
        Register a canonical Generator.
        """

        self.require_element(
            generator,
            "generator",
        )

        self.append_unique(
            self.generators,
            generator,
            "generator",
        )

    # ============================================================
    # ADD — LOAD
    # ============================================================

    def add_load(
        self,
        load: Any,
    ) -> None:
        """
        Register a canonical Load.
        """

        self.require_element(
            load,
            "load",
        )

        self.append_unique(
            self.loads,
            load,
            "load",
        )

    # ============================================================
    # ADD — SHUNT
    # ============================================================

    def add_shunt(
        self,
        shunt: Any,
    ) -> None:
        """
        Register a canonical Shunt.
        """

        self.require_element(
            shunt,
            "shunt",
        )

        self.append_unique(
            self.shunts,
            shunt,
            "shunt",
        )

    # ============================================================
    # REMOVE — BUS
    # ============================================================

    def remove_bus(
        self,
        bus: Any,
    ) -> None:
        """
        Remove a registered Bus.

        A Bus cannot be removed while any other registered network
        element references it.

        This method does not disconnect anything and does not mutate
        the referencing model objects.

        Network is responsible for invalidating topology, indexing,
        and derived Y-bus state after successful removal.
        """

        if bus is None:
            raise ValueError(
                "Bus cannot be None."
            )

        if not self._contains_identity(
            self.buses,
            bus,
        ):
            raise ValueError(
                f"Bus '{getattr(bus, 'id', bus)}' "
                "is not registered on this Network."
            )

        # --------------------------------------------------------
        # LINE REFERENCES
        # --------------------------------------------------------

        for line in self.lines:

            if (
                resolve_terminal_bus(
                    getattr(
                        line,
                        "from_terminal",
                        None,
                    )
                )
                is bus
                or
                resolve_terminal_bus(
                    getattr(
                        line,
                        "to_terminal",
                        None,
                    )
                )
                is bus
            ):
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Line '{line.id}' references it."
                )

        # --------------------------------------------------------
        # TRANSFORMER REFERENCES
        # --------------------------------------------------------

        for transformer in self.transformers:

            if (
                resolve_terminal_bus(
                    getattr(
                        transformer,
                        "from_terminal",
                        None,
                    )
                )
                is bus
                or
                resolve_terminal_bus(
                    getattr(
                        transformer,
                        "to_terminal",
                        None,
                    )
                )
                is bus
            ):
                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Transformer '{transformer.id}' references it."
                )

        # --------------------------------------------------------
        # GENERATOR REFERENCES
        # --------------------------------------------------------

        for generator in self.generators:

            if getattr(
                generator,
                "bus",
                None,
            ) is bus:

                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Generator '{generator.id}' references it."
                )

        # --------------------------------------------------------
        # LOAD REFERENCES
        # --------------------------------------------------------

        for load in self.loads:

            if getattr(
                load,
                "bus",
                None,
            ) is bus:

                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Load '{load.id}' references it."
                )

        # --------------------------------------------------------
        # SHUNT REFERENCES
        # --------------------------------------------------------

        for shunt in self.shunts:

            terminal = getattr(
                shunt,
                "terminal",
                None,
            )

            if resolve_terminal_bus(
                terminal,
            ) is bus:

                raise ValueError(
                    f"Bus '{bus.id}' cannot be removed because "
                    f"Shunt '{shunt.id}' references it."
                )

        # --------------------------------------------------------
        # REMOVE CANONICAL MEMBERSHIP
        # --------------------------------------------------------

        self._remove_identity(
            self.buses,
            bus,
            "bus",
        )

    # ============================================================
    # REMOVE — GENERIC IDENTITY
    # ============================================================

    @staticmethod
    def remove_identity(
        collection: List[Any],
        element: Any,
        element_type: str,
    ) -> None:
        """
        Remove an exact canonical object from a registry collection.

        Removal is based on object identity, not equality and not ID.
        """

        if element is None:
            raise ValueError(
                f"{element_type.capitalize()} cannot be None."
            )

        NetworkRegistry._remove_identity(
            collection,
            element,
            element_type,
        )

    # ------------------------------------------------------------

    @staticmethod
    def _remove_identity(
        collection: List[Any],
        element: Any,
        element_type: str,
    ) -> None:
        """
        Internal identity-based removal primitive.
        """

        for index, registered in enumerate(collection):

            if registered is element:

                del collection[index]
                return

        raise ValueError(
            f"{element_type.capitalize()} "
            f"'{getattr(element, 'id', element)}' "
            "is not registered on this Network."
        )

    # ============================================================
    # REMOVE — LINE
    # ============================================================

    def remove_line(
        self,
        line: Any,
    ) -> None:
        """
        Remove a canonical Line from registry membership.

        Endpoint relationships are not modified.
        """

        self.remove_identity(
            self.lines,
            line,
            "line",
        )

    # ============================================================
    # REMOVE — TRANSFORMER
    # ============================================================

    def remove_transformer(
        self,
        transformer: Any,
    ) -> None:
        """
        Remove a canonical Transformer from registry membership.

        Terminal relationships are not modified.
        """

        self.remove_identity(
            self.transformers,
            transformer,
            "transformer",
        )

    # ============================================================
    # REMOVE — GENERATOR
    # ============================================================

    def remove_generator(
        self,
        generator: Any,
    ) -> None:
        """
        Remove a canonical Generator from registry membership.

        The Generator model object itself is not mutated.
        """

        self.remove_identity(
            self.generators,
            generator,
            "generator",
        )

    # ============================================================
    # REMOVE — LOAD
    # ============================================================

    def remove_load(
        self,
        load: Any,
    ) -> None:
        """
        Remove a canonical Load from registry membership.

        The Load model object itself is not mutated.
        """

        self.remove_identity(
            self.loads,
            load,
            "load",
        )

    # ============================================================
    # REMOVE — SHUNT
    # ============================================================

    def remove_shunt(
        self,
        shunt: Any,
    ) -> None:
        """
        Remove a canonical Shunt from registry membership.

        The Shunt terminal relationship is not modified.
        """

        self.remove_identity(
            self.shunts,
            shunt,
            "shunt",
        )

    # ============================================================
    # INTERNAL MEMBERSHIP TEST
    # ============================================================

    @staticmethod
    def _contains_identity(
        collection: List[Any],
        element: Any,
    ) -> bool:
        """
        Return True when the exact object instance is registered.
        """

        return any(
            registered is element
            for registered in collection
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(self) -> dict[str, int]:
        """
        Return registry membership counts.
        """

        return {
            "buses": len(self.buses),
            "lines": len(self.lines),
            "transformers": len(self.transformers),
            "generators": len(self.generators),
            "loads": len(self.loads),
            "shunts": len(self.shunts),
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            "NetworkRegistry("
            f"buses={len(self.buses)}, "
            f"lines={len(self.lines)}, "
            f"transformers={len(self.transformers)}, "
            f"generators={len(self.generators)}, "
            f"loads={len(self.loads)}, "
            f"shunts={len(self.shunts)}"
            ")"
        )
