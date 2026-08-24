# ============================================================
# File: core/network/registry.py
# GridForge V2 — Network Layer
# ============================================================
"""
Canonical Network Element Registry
==================================

Owns membership of canonical electrical model objects in an
assembled GridForge Network.

Responsibilities
----------------
- Maintain canonical references to registered model objects.
- Enforce unique IDs within each element collection.
- Perform structural registration checks.
- Enforce strict Bus removal semantics.
- Remove elements by canonical object identity.

Does NOT
--------
- Build topology.
- Build Y-bus.
- Perform engineering validation.
- Perform electrical calculations.
- Mutate SLD/UI state.
- Execute commands.
- Own canonical model definitions.

The registry is an internal Network service. Network remains the
architectural owner of assembled-network membership and controls
derived-state invalidation after registry mutation.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any, Iterable


class NetworkRegistry:
    """
    Canonical assembled-network membership registry.

    The registry stores references to objects defined by
    ``core.model``. It never creates replacement model objects.
    """

    _COLLECTION_NAMES = (
        "buses",
        "lines",
        "transformers",
        "generators",
        "loads",
        "shunts",
    )

    def __init__(self) -> None:
        self.buses: list[Any] = []
        self.lines: list[Any] = []
        self.transformers: list[Any] = []
        self.generators: list[Any] = []
        self.loads: list[Any] = []
        self.shunts: list[Any] = []

    # ============================================================
    # STRUCTURAL HELPERS
    # ============================================================

    @staticmethod
    def require_element(
        element: Any,
        element_type: str,
    ) -> None:
        """
        Perform minimal structural registration validation.

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

    # ------------------------------------------------------------

    @staticmethod
    def append_unique(
        collection: list[Any],
        element: Any,
        element_type: str,
    ) -> None:
        """
        Append an element while preventing duplicate IDs.
        """

        element_id = element.id

        for existing in collection:
            if existing.id == element_id:
                raise ValueError(
                    f"Duplicate {element_type} ID: {element_id}"
                )

        collection.append(element)

    # ============================================================
    # REGISTRATION
    # ============================================================

    def add_bus(self, bus: Any) -> None:
        self.require_element(bus, "bus")

        self.append_unique(
            self.buses,
            bus,
            "bus",
        )

    # ------------------------------------------------------------

    def add_line(self, line: Any) -> None:
        self.require_element(line, "line")

        self.append_unique(
            self.lines,
            line,
            "line",
        )

    # ------------------------------------------------------------

    def add_transformer(
        self,
        transformer: Any,
    ) -> None:
        self.require_element(
            transformer,
            "transformer",
        )

        self.append_unique(
            self.transformers,
            transformer,
            "transformer",
        )

    # ------------------------------------------------------------

    def add_generator(
        self,
        generator: Any,
    ) -> None:
        self.require_element(
            generator,
            "generator",
        )

        self.append_unique(
            self.generators,
            generator,
            "generator",
        )

    # ------------------------------------------------------------

    def add_load(
        self,
        load: Any,
    ) -> None:
        self.require_element(
            load,
            "load",
        )

        self.append_unique(
            self.loads,
            load,
            "load",
        )

    # ------------------------------------------------------------

    def add_shunt(
        self,
        shunt: Any,
    ) -> None:
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
    # BUS REFERENCE RESOLUTION
    # ============================================================

    @staticmethod
    def _terminal_endpoint(
        element: Any,
        terminal_name: str,
    ) -> Any:
        """
        Resolve a terminal endpoint.

        Terminal.endpoint remains the authoritative physical
        connection representation.
        """

        terminal = getattr(
            element,
            terminal_name,
            None,
        )

        return getattr(
            terminal,
            "endpoint",
            None,
        )

    # ------------------------------------------------------------

    def _bus_reference(
        self,
        bus: Any,
    ) -> str | None:
        """
        Return a description of the first registered element that
        references ``bus``.

        Returns
        -------
        str | None
            Human-readable reference description, or ``None`` when
            no registered element references the bus.
        """

        # --------------------------------------------------------
        # LINES
        # --------------------------------------------------------

        for line in self.lines:

            from_endpoint = self._terminal_endpoint(
                line,
                "from_terminal",
            )

            to_endpoint = self._terminal_endpoint(
                line,
                "to_terminal",
            )

            if (
                from_endpoint is bus
                or to_endpoint is bus
            ):
                return (
                    f"Line '{getattr(line, 'id', line)}'"
                )

        # --------------------------------------------------------
        # TRANSFORMERS
        # --------------------------------------------------------

        for transformer in self.transformers:

            from_endpoint = self._terminal_endpoint(
                transformer,
                "from_terminal",
            )

            to_endpoint = self._terminal_endpoint(
                transformer,
                "to_terminal",
            )

            if (
                from_endpoint is bus
                or to_endpoint is bus
            ):
                return (
                    f"Transformer "
                    f"'{getattr(transformer, 'id', transformer)}'"
                )

        # --------------------------------------------------------
        # GENERATORS
        # --------------------------------------------------------

        for generator in self.generators:

            if getattr(generator, "bus", None) is bus:
                return (
                    f"Generator "
                    f"'{getattr(generator, 'id', generator)}'"
                )

        # --------------------------------------------------------
        # LOADS
        # --------------------------------------------------------

        for load in self.loads:

            if getattr(load, "bus", None) is bus:
                return (
                    f"Load "
                    f"'{getattr(load, 'id', load)}'"
                )

        # --------------------------------------------------------
        # SHUNTS
        # --------------------------------------------------------

        for shunt in self.shunts:

            endpoint = self._terminal_endpoint(
                shunt,
                "terminal",
            )

            if endpoint is bus:
                return (
                    f"Shunt "
                    f"'{getattr(shunt, 'id', shunt)}'"
                )

        return None

    # ============================================================
    # REMOVAL
    # ============================================================

    def remove_bus(
        self,
        bus: Any,
    ) -> None:
        """
        Remove a registered Bus.

        Bus removal is deliberately strict. A Bus cannot be
        removed while another registered network element references
        it.
        """

        if bus is None:
            raise ValueError(
                "Bus cannot be None."
            )

        if bus not in self.buses:
            raise ValueError(
                f"Bus '{getattr(bus, 'id', bus)}' "
                "is not registered on this Network."
            )

        reference = self._bus_reference(bus)

        if reference is not None:
            raise ValueError(
                f"Bus '{bus.id}' cannot be removed because "
                f"{reference} references it."
            )

        self.buses.remove(bus)

    # ------------------------------------------------------------

    @staticmethod
    def _remove_identity(
        collection: list[Any],
        element: Any,
        element_type: str,
    ) -> None:
        """
        Remove the exact canonical object instance.

        Object identity is intentional. Matching only by ID could
        remove an unrelated object carrying the same identifier.
        """

        if element is None:
            raise ValueError(
                f"{element_type.capitalize()} cannot be None."
            )

        for index, registered in enumerate(collection):

            if registered is element:
                del collection[index]
                return

        raise ValueError(
            f"{element_type.capitalize()} "
            f"'{getattr(element, 'id', element)}' "
            "is not registered on this Network."
        )

    # ------------------------------------------------------------

    def remove_line(
        self,
        line: Any,
    ) -> None:
        self._remove_identity(
            self.lines,
            line,
            "line",
        )

    # ------------------------------------------------------------

    def remove_transformer(
        self,
        transformer: Any,
    ) -> None:
        self._remove_identity(
            self.transformers,
            transformer,
            "transformer",
        )

    # ------------------------------------------------------------

    def remove_generator(
        self,
        generator: Any,
    ) -> None:
        self._remove_identity(
            self.generators,
            generator,
            "generator",
        )

    # ------------------------------------------------------------

    def remove_load(
        self,
        load: Any,
    ) -> None:
        self._remove_identity(
            self.loads,
            load,
            "load",
        )

    # ------------------------------------------------------------

    def remove_shunt(
        self,
        shunt: Any,
    ) -> None:
        self._remove_identity(
            self.shunts,
            shunt,
            "shunt",
        )

    # ============================================================
    # ITERATION / DIAGNOSTICS
    # ============================================================

    def all_elements(self) -> Iterable[Any]:
        """
        Iterate over all registered canonical model objects.
        """

        for collection_name in self._COLLECTION_NAMES:
            yield from getattr(
                self,
                collection_name,
            )

    # ------------------------------------------------------------

    def counts(self) -> dict[str, int]:
        """
        Return element counts.
        """

        return {
            name: len(getattr(self, name))
            for name in self._COLLECTION_NAMES
        }
