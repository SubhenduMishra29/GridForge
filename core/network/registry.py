# ============================================================
# File: core/network/registry.py
# GridForge V2 — Canonical Network Equipment Registry
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Canonical Network Equipment Registry
====================================================

NetworkRegistry owns canonical equipment membership for a
Network.

Responsibilities
----------------

    * register equipment;
    * remove equipment;
    * provide canonical equipment lookup by ID;
    * expose immutable/read-only collection views.

The registry does NOT:

    * resolve electrical endpoints;
    * connect terminals;
    * perform topology validation;
    * calculate electrical quantities;
    * construct equipment;
    * own SLD state;
    * know about UI or canvas state.

Network remains the public façade.

The Application layer must access equipment through Network,
not through this registry directly.

Supported equipment families
----------------------------

    bus
    line
    transformer
    generator
    load
    shunt
    grid
"""

from __future__ import annotations

from typing import Any


class NetworkRegistry:
    """
    Canonical membership registry for Network equipment.
    """

    def __init__(self) -> None:
        self._buses: list[Any] = []
        self._lines: list[Any] = []
        self._transformers: list[Any] = []
        self._generators: list[Any] = []
        self._loads: list[Any] = []
        self._shunts: list[Any] = []
        self._grids: list[Any] = []

    # ========================================================
    # READ-ONLY COLLECTIONS
    # ========================================================

    @property
    def buses(self) -> tuple[Any, ...]:
        return tuple(self._buses)

    @property
    def lines(self) -> tuple[Any, ...]:
        return tuple(self._lines)

    @property
    def transformers(self) -> tuple[Any, ...]:
        return tuple(self._transformers)

    @property
    def generators(self) -> tuple[Any, ...]:
        return tuple(self._generators)

    @property
    def loads(self) -> tuple[Any, ...]:
        return tuple(self._loads)

    @property
    def shunts(self) -> tuple[Any, ...]:
        return tuple(self._shunts)

    @property
    def grids(self) -> tuple[Any, ...]:
        return tuple(self._grids)

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    @staticmethod
    def _validate_id(
        object_id: str,
    ) -> str:
        if not isinstance(object_id, str):
            raise TypeError(
                "object_id must be a string."
            )

        object_id = object_id.strip()

        if not object_id:
            raise ValueError(
                "object_id must not be empty."
            )

        return object_id

    @staticmethod
    def _validate_element_type(
        element_type: str,
    ) -> str:
        if not isinstance(
            element_type,
            str,
        ):
            raise TypeError(
                "element_type must be a string."
            )

        element_type = element_type.strip().lower()

        if not element_type:
            raise ValueError(
                "element_type must not be empty."
            )

        return element_type

    @staticmethod
    def _contains_identity(
        collection: list[Any],
        element: Any,
    ) -> bool:
        return any(
            existing is element
            for existing in collection
        )

    @staticmethod
    def _find_identity(
        collection: list[Any],
        object_id: str,
    ) -> Any | None:
        for element in collection:
            if getattr(
                element,
                "id",
                None,
            ) == object_id:
                return element

        return None

    # ========================================================
    # CANONICAL LOOKUP
    # ========================================================

    def get_by_id(
        self,
        element_type: str,
        object_id: str,
    ) -> Any:
        """
        Return the canonical registered equipment object.

        Lookup is identity-preserving and does not mutate the
        network.
        """

        element_type = self._validate_element_type(
            element_type
        )

        object_id = self._validate_id(
            object_id
        )

        collections = {
            "bus": self._buses,
            "line": self._lines,
            "transformer": self._transformers,
            "generator": self._generators,
            "load": self._loads,
            "shunt": self._shunts,
            "grid": self._grids,
        }

        collection = collections.get(
            element_type
        )

        if collection is None:
            raise KeyError(
                "Unsupported equipment type: "
                f"{element_type!r}"
            )

        element = self._find_identity(
            collection,
            object_id,
        )

        if element is None:
            raise KeyError(
                f"No {element_type!r} with ID "
                f"{object_id!r} is registered."
            )

        return element

    # ========================================================
    # BUS
    # ========================================================

    def add_bus(
        self,
        bus: Any,
    ) -> None:
        if bus is None:
            raise ValueError(
                "bus must not be None."
            )

        if self._contains_identity(
            self._buses,
            bus,
        ):
            raise ValueError(
                "Bus is already registered."
            )

        object_id = getattr(
            bus,
            "id",
            None,
        )

        if object_id is not None:
            if self._find_identity(
                self._buses,
                object_id,
            ) is not None:
                raise ValueError(
                    f"Bus ID {object_id!r} is already "
                    "registered."
                )

        self._buses.append(bus)

    def remove_bus(
        self,
        bus: Any,
    ) -> None:
        self._remove_identity(
            self._buses,
            bus,
            "Bus",
        )

    # ========================================================
    # LINE
    # ========================================================

    def add_line(
        self,
        line: Any,
    ) -> None:
        if line is None:
            raise ValueError(
                "line must not be None."
            )

        if self._contains_identity(
            self._lines,
            line,
        ):
            raise ValueError(
                "Line is already registered."
            )

        object_id = getattr(
            line,
            "id",
            None,
        )

        if object_id is not None:
            if self._find_identity(
                self._lines,
                object_id,
            ) is not None:
                raise ValueError(
                    f"Line ID {object_id!r} is already "
                    "registered."
                )

        self._lines.append(line)

    def remove_line(
        self,
        line: Any,
    ) -> None:
        self._remove_identity(
            self._lines,
            line,
            "Line",
        )

    # ========================================================
    # TRANSFORMER
    # ========================================================

    def add_transformer(
        self,
        transformer: Any,
    ) -> None:
        if transformer is None:
            raise ValueError(
                "transformer must not be None."
            )

        if self._contains_identity(
            self._transformers,
            transformer,
        ):
            raise ValueError(
                "Transformer is already registered."
            )

        object_id = getattr(
            transformer,
            "id",
            None,
        )

        if object_id is not None:
            if self._find_identity(
                self._transformers,
                object_id,
            ) is not None:
                raise ValueError(
                    f"Transformer ID {object_id!r} is already "
                    "registered."
                )

        self._transformers.append(
            transformer
        )

    def remove_transformer(
        self,
        transformer: Any,
    ) -> None:
        self._remove_identity(
            self._transformers,
            transformer,
            "Transformer",
        )

    # ========================================================
    # GENERATOR
    # ========================================================

    def add_generator(
        self,
        generator: Any,
    ) -> None:
        if generator is None:
            raise ValueError(
                "generator must not be None."
            )

        if self._contains_identity(
            self._generators,
            generator,
        ):
            raise ValueError(
                "Generator is already registered."
            )

        object_id = getattr(
            generator,
            "id",
            None,
        )

        if object_id is not None:
            if self._find_identity(
                self._generators,
                object_id,
            ) is not None:
                raise ValueError(
                    f"Generator ID {object_id!r} is already "
                    "registered."
                )

        self._generators.append(
            generator
        )

    def remove_generator(
        self,
        generator: Any,
    ) -> None:
        self._remove_identity(
            self._generators,
            generator,
            "Generator",
        )

    # ========================================================
    # LOAD
    # ========================================================

    def add_load(
        self,
        load: Any,
    ) -> None:
        if load is None:
            raise ValueError(
                "load must not be None."
            )

        if self._contains_identity(
            self._loads,
            load,
        ):
            raise ValueError(
                "Load is already registered."
            )

        object_id = getattr(
            load,
            "id",
            None,
        )

        if object_id is not None:
            if self._find_identity(
                self._loads,
                object_id,
            ) is not None:
                raise ValueError(
                    f"Load ID {object_id!r} is already "
                    "registered."
                )

        self._loads.append(load)

    def remove_load(
        self,
        load: Any,
    ) -> None:
        self._remove_identity(
            self._loads,
            load,
            "Load",
        )

    # ========================================================
    # SHUNT
    # ========================================================

    def add_shunt(
        self,
        shunt: Any,
    ) -> None:
        if shunt is None:
            raise ValueError(
                "shunt must not be None."
            )

        if self._contains_identity(
            self._shunts,
            shunt,
        ):
            raise ValueError(
                "Shunt is already registered."
            )

        object_id = getattr(
            shunt,
            "id",
            None,
        )

        if object_id is not None:
            if self._find_identity(
                self._shunts,
                object_id,
            ) is not None:
                raise ValueError(
                    f"Shunt ID {object_id!r} is already "
                    "registered."
                )

        self._shunts.append(shunt)

    def remove_shunt(
        self,
        shunt: Any,
    ) -> None:
        self._remove_identity(
            self._shunts,
            shunt,
            "Shunt",
        )

    # ========================================================
    # GRID
    # ========================================================

    def add_grid(
        self,
        grid: Any,
    ) -> None:
        if grid is None:
            raise ValueError(
                "grid must not be None."
            )

        if self._contains_identity(
            self._grids,
            grid,
        ):
            raise ValueError(
                "Grid is already registered."
            )

        object_id = getattr(
            grid,
            "id",
            None,
        )

        if object_id is not None:
            if self._find_identity(
                self._grids,
                object_id,
            ) is not None:
                raise ValueError(
                    f"Grid ID {object_id!r} is already "
                    "registered."
                )

        self._grids.append(grid)

    def remove_grid(
        self,
        grid: Any,
    ) -> None:
        self._remove_identity(
            self._grids,
            grid,
            "Grid",
        )

    # ========================================================
    # IDENTITY REMOVAL
    # ========================================================

    @staticmethod
    def _remove_identity(
        collection: list[Any],
        element: Any,
        label: str,
    ) -> None:
        """
        Remove exactly the registered object instance.

        Equality is intentionally not used.

        Registry membership is identity-based.
        """

        for index, existing in enumerate(
            collection
        ):
            if existing is element:
                collection.pop(index)
                return

        raise KeyError(
            f"{label} is not registered."
        )


__all__ = [
    "NetworkRegistry",
]
