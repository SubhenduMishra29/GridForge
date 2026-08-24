# ============================================================
# File: core/network/registry.py
# GridForge V2 — Network Registry
# Author: Subhendu Mishra
# ============================================================

"""
Canonical Network element membership.

Registry owns:

    Bus
    Line
    Transformer
    Generator
    Load
    Shunt

membership.

It does not own topology, Y-bus, indexing, study state, or
engineering validation.
"""

from __future__ import annotations

from typing import Any, List


class NetworkRegistry:

    def __init__(self) -> None:

        self.buses: List[Any] = []
        self.lines: List[Any] = []
        self.transformers: List[Any] = []
        self.generators: List[Any] = []
        self.loads: List[Any] = []
        self.shunts: List[Any] = []

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def require_element(
        element: Any,
        element_type: str,
    ) -> None:

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

        for existing in collection:

            if existing.id == element.id:
                raise ValueError(
                    f"Duplicate {element_type} ID: {element.id}"
                )

        collection.append(element)

    # ============================================================
    # ADD
    # ============================================================

    def add_bus(self, bus: Any) -> None:

        self.require_element(
            bus,
            "bus",
        )

        for existing in self.buses:

            if existing.id == bus.id:
                raise ValueError(
                    f"Duplicate bus ID: {bus.id}"
                )

        self.buses.append(bus)

    # ------------------------------------------------------------

    def add_line(self, line: Any) -> None:

        self.require_element(
            line,
            "line",
        )

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
    # REMOVE
    # ============================================================

    @staticmethod
    def remove_identity(
        collection: List[Any],
        element: Any,
        element_type: str,
    ) -> None:

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
