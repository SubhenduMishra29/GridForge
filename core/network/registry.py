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
    * know about UI or canvas state;
    * construct Y-bus matrices;
    * assign numerical solver indices.

Network remains the public façade.

The Application layer must access equipment through Network,
not through this registry directly.

Supported equipment families
----------------------------

    bus
    grid
    generator
    load
    shunt
    line
    transformer
    branch
    cable
    switch
    disconnector
    fuse
"""

from __future__ import annotations

from typing import Any


class NetworkRegistry:
    """
    Canonical membership registry for Network equipment.

    Registry membership is identity-preserving.

    The registry stores the canonical Core model instances and
    never creates replacement objects during lookup.
    """

    def __init__(self) -> None:
        self._buses: list[Any] = []
        self._grids: list[Any] = []
        self._generators: list[Any] = []
        self._loads: list[Any] = []
        self._shunts: list[Any] = []
        self._lines: list[Any] = []
        self._transformers: list[Any] = []
        self._branches: list[Any] = []
        self._cables: list[Any] = []
        self._switches: list[Any] = []
        self._disconnectors: list[Any] = []
        self._fuses: list[Any] = []

    # ========================================================
    # READ-ONLY COLLECTIONS
    # ========================================================

    @property
    def buses(self) -> tuple[Any, ...]:
        return tuple(self._buses)

    @property
    def grids(self) -> tuple[Any, ...]:
        return tuple(self._grids)

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
    def lines(self) -> tuple[Any, ...]:
        return tuple(self._lines)

    @property
    def transformers(self) -> tuple[Any, ...]:
        return tuple(self._transformers)

    @property
    def branches(self) -> tuple[Any, ...]:
        return tuple(self._branches)

    @property
    def cables(self) -> tuple[Any, ...]:
        return tuple(self._cables)

    @property
    def switches(self) -> tuple[Any, ...]:
        return tuple(self._switches)

    @property
    def disconnectors(self) -> tuple[Any, ...]:
        return tuple(self._disconnectors)

    @property
    def fuses(self) -> tuple[Any, ...]:
        return tuple(self._fuses)

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    @staticmethod
    def _validate_id(
        object_id: str,
    ) -> str:
        """
        Validate and normalize an equipment identifier.
        """

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
        """
        Validate and normalize an equipment family name.
        """

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
        """
        Return True when the exact object instance is registered.
        """

        return any(
            existing is element
            for existing in collection
        )

    @staticmethod
    def _find_identity(
        collection: list[Any],
        object_id: str,
    ) -> Any | None:
        """
        Find the canonical object having the supplied ID.

        The returned object is the actual registered instance.
        """

        for element in collection:
            if getattr(
                element,
                "id",
                None,
            ) == object_id:
                return element

        return None

    @staticmethod
    def _register(
        collection: list[Any],
        element: Any,
        label: str,
    ) -> None:
        """
        Register one canonical equipment instance.

        Both object identity and object ID are protected.
        """

        if element is None:
            raise ValueError(
                f"{label} must not be None."
            )

        if NetworkRegistry._contains_identity(
            collection,
            element,
        ):
            raise ValueError(
                f"{label} is already registered."
            )

        object_id = getattr(
            element,
            "id",
            None,
        )

        if object_id is not None:
            if NetworkRegistry._find_identity(
                collection,
                object_id,
            ) is not None:
                raise ValueError(
                    f"{label} ID {object_id!r} is already "
                    "registered."
                )

        collection.append(element)

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

        Parameters
        ----------
        element_type:
            Canonical equipment family name.

        object_id:
            Canonical equipment identifier.

        Returns
        -------
        Any
            The actual registered Core model instance.

        Raises
        ------
        KeyError
            If the equipment family is unsupported or the
            requested object is not registered.
        """

        element_type = self._validate_element_type(
            element_type
        )

        object_id = self._validate_id(
            object_id
        )

        collections = {
            "bus": self._buses,
            "grid": self._grids,
            "generator": self._generators,
            "load": self._loads,
            "shunt": self._shunts,
            "line": self._lines,
            "transformer": self._transformers,
            "branch": self._branches,
            "cable": self._cables,
            "switch": self._switches,
            "disconnector": self._disconnectors,
            "fuse": self._fuses,
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
        self._register(
            self._buses,
            bus,
            "Bus",
        )

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
    # GRID
    # ========================================================

    def add_grid(
        self,
        grid: Any,
    ) -> None:
        self._register(
            self._grids,
            grid,
            "Grid",
        )

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
    # GENERATOR
    # ========================================================

    def add_generator(
        self,
        generator: Any,
    ) -> None:
        self._register(
            self._generators,
            generator,
            "Generator",
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
        self._register(
            self._loads,
            load,
            "Load",
        )

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
        self._register(
            self._shunts,
            shunt,
            "Shunt",
        )

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
    # LINE
    # ========================================================

    def add_line(
        self,
        line: Any,
    ) -> None:
        self._register(
            self._lines,
            line,
            "Line",
        )

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
        self._register(
            self._transformers,
            transformer,
            "Transformer",
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
    # BRANCH
    # ========================================================

    def add_branch(
        self,
        branch: Any,
    ) -> None:
        self._register(
            self._branches,
            branch,
            "Branch",
        )

    def remove_branch(
        self,
        branch: Any,
    ) -> None:
        self._remove_identity(
            self._branches,
            branch,
            "Branch",
        )

    # ========================================================
    # CABLE
    # ========================================================

    def add_cable(
        self,
        cable: Any,
    ) -> None:
        self._register(
            self._cables,
            cable,
            "Cable",
        )

    def remove_cable(
        self,
        cable: Any,
    ) -> None:
        self._remove_identity(
            self._cables,
            cable,
            "Cable",
        )

    # ========================================================
    # SWITCH
    # ========================================================

    def add_switch(
        self,
        switch: Any,
    ) -> None:
        self._register(
            self._switches,
            switch,
            "Switch",
        )

    def remove_switch(
        self,
        switch: Any,
    ) -> None:
        self._remove_identity(
            self._switches,
            switch,
            "Switch",
        )

    # ========================================================
    # DISCONNECTOR
    # ========================================================

    def add_disconnector(
        self,
        disconnector: Any,
    ) -> None:
        self._register(
            self._disconnectors,
            disconnector,
            "Disconnector",
        )

    def remove_disconnector(
        self,
        disconnector: Any,
    ) -> None:
        self._remove_identity(
            self._disconnectors,
            disconnector,
            "Disconnector",
        )

    # ========================================================
    # FUSE
    # ========================================================

    def add_fuse(
        self,
        fuse: Any,
    ) -> None:
        self._register(
            self._fuses,
            fuse,
            "Fuse",
        )

    def remove_fuse(
        self,
        fuse: Any,
    ) -> None:
        self._remove_identity(
            self._fuses,
            fuse,
            "Fuse",
        )


__all__ = [
    "NetworkRegistry",
]
