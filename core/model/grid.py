```python
"""
core/model/grid.py

GridForge Grid Model

Defines the central electrical-network container.

Responsibilities
----------------
- Registry for electrical components.
- Stable component ordering for numerical analysis.
- Component lookup.
- Bus indexing.
- Structural/reference validation.
- Aggregation of connected power injections.

The Grid model does NOT:
- Build Ybus.
- Run power-flow calculations.
- Run short-circuit calculations.
- Solve numerical systems.
- Perform protection calculations.
- Perform dynamic simulation.

Numerical analysis belongs in the solver/analysis layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Dict, List, Iterable

from .bus import Bus, BusType
from .load import Load
from .generator import Generator
from .branch import Branch


class Grid:
    """
    Central container for a GridForge electrical network.

    Component registries use dictionaries keyed by stable object IDs.

    Numerical code should use the ordered list properties:

        bus_list
        load_list
        generator_list
        branch_list

    rather than depending on the internal dictionary representation.
    """

    def __init__(self, name: str = ""):

        self.name = name

        # =========================================================
        # COMPONENT REGISTRIES
        # =========================================================

        self.buses: Dict[str, Bus] = {}

        self.loads: Dict[str, Load] = {}

        self.generators: Dict[str, Generator] = {}

        self.branches: Dict[str, Branch] = {}

        # =========================================================
        # DERIVED / ANALYSIS STATE
        # =========================================================
        #
        # These are deliberately initialized as None.
        #
        # Grid does not construct Ybus itself.
        # A dedicated network/Ybus builder may populate these later.
        #
        # Keeping the attributes available provides a clean interface
        # for numerical engines without embedding numerical logic here.
        # =========================================================

        self.Ybus = None

        self.bus_index: Dict[str, int] = {}

    # =============================================================
    # ADD COMPONENTS
    # =============================================================

    def add_bus(self, bus: Bus) -> None:
        """
        Add a Bus to the grid.
        """

        if not isinstance(bus, Bus):
            raise TypeError(
                "add_bus() requires a Bus object"
            )

        self._add(
            self.buses,
            bus
        )

        # Bus ordering has changed.
        self._invalidate_bus_index()

    def add_load(self, load: Load) -> None:
        """
        Add a Load to the grid.
        """

        if not isinstance(load, Load):
            raise TypeError(
                "add_load() requires a Load object"
            )

        self._add(
            self.loads,
            load
        )

    def add_generator(self, generator: Generator) -> None:
        """
        Add a Generator to the grid.
        """

        if not isinstance(generator, Generator):
            raise TypeError(
                "add_generator() requires a Generator object"
            )

        self._add(
            self.generators,
            generator
        )

    def add_branch(self, branch: Branch) -> None:
        """
        Add a Branch to the grid.
        """

        if not isinstance(branch, Branch):
            raise TypeError(
                "add_branch() requires a Branch object"
            )

        self._add(
            self.branches,
            branch
        )

    @staticmethod
    def _add(
        container: Dict,
        obj
    ) -> None:
        """
        Add an object to a registry.

        Object IDs must be unique within the registry.
        """

        if obj.id in container:
            raise ValueError(
                f"Duplicate ID detected: {obj.id}"
            )

        container[obj.id] = obj

    # =============================================================
    # LOOKUP
    # =============================================================

    def get_bus(self, id: str) -> Bus:
        """
        Return a Bus by ID.
        """

        try:
            return self.buses[id]

        except KeyError as exc:

            raise KeyError(
                f"Bus '{id}' does not exist"
            ) from exc

    def get_load(self, id: str) -> Load:
        """
        Return a Load by ID.
        """

        try:
            return self.loads[id]

        except KeyError as exc:

            raise KeyError(
                f"Load '{id}' does not exist"
            ) from exc

    def get_generator(self, id: str) -> Generator:
        """
        Return a Generator by ID.
        """

        try:
            return self.generators[id]

        except KeyError as exc:

            raise KeyError(
                f"Generator '{id}' does not exist"
            ) from exc

    def get_branch(self, id: str) -> Branch:
        """
        Return a Branch by ID.
        """

        try:
            return self.branches[id]

        except KeyError as exc:

            raise KeyError(
                f"Branch '{id}' does not exist"
            ) from exc

    # =============================================================
    # ORDERED COMPONENT VIEWS
    # =============================================================

    @property
    def bus_list(self) -> List[Bus]:
        """
        Return buses in stable registry order.

        The returned list represents the bus ordering used when
        constructing bus-indexed numerical matrices such as Ybus.
        """

        return list(
            self.buses.values()
        )

    @property
    def load_list(self) -> List[Load]:
        """
        Return loads in registry order.
        """

        return list(
            self.loads.values()
        )

    @property
    def generator_list(self) -> List[Generator]:
        """
        Return generators in registry order.
        """

        return list(
            self.generators.values()
        )

    @property
    def branch_list(self) -> List[Branch]:
        """
        Return branches in registry order.
        """

        return list(
            self.branches.values()
        )

    # =============================================================
    # INJECTION COLLECTION
    # =============================================================

    @property
    def injection_list(self) -> List:
        """
        Return all objects implementing the Injection interface.

        Loads and generators are both injections.

        The ordering is:

            generators
            followed by loads

        This ordering is deterministic but should not be interpreted
        as a bus ordering.
        """

        return [
            *self.generator_list,
            *self.load_list
        ]

    def injections(self) -> List:
        """
        Backward-compatible method returning all injections.
        """

        return self.injection_list

    # =============================================================
    # BUS INDEXING
    # =============================================================

    def build_bus_index(self) -> Dict[str, int]:
        """
        Build and store the bus-ID → numerical-index mapping.

        The mapping corresponds exactly to ``bus_list`` ordering.

        Returns
        -------
        dict
            Example:

                {
                    "BUS1": 0,
                    "BUS2": 1,
                    "BUS3": 2
                }
        """

        self.bus_index = {
            bus.id: index
            for index, bus in enumerate(
                self.bus_list
            )
        }

        return self.bus_index.copy()

    def get_bus_index(self, bus_id: str) -> int:
        """
        Return the numerical index of a bus.

        The index is generated lazily if necessary.
        """

        if (
            not self.bus_index
            or set(self.bus_index.keys())
            != set(self.buses.keys())
        ):
            self.build_bus_index()

        try:
            return self.bus_index[bus_id]

        except KeyError as exc:

            raise KeyError(
                f"Bus '{bus_id}' does not exist in bus index"
            ) from exc

    def _invalidate_bus_index(self) -> None:
        """
        Invalidate the cached bus index.

        Called whenever the bus registry changes.
        """

        self.bus_index = {}

    # =============================================================
    # YBUS INTERFACE
    # =============================================================

    def set_ybus(self, Ybus) -> None:
        """
        Attach a calculated Ybus matrix to the grid.

        Ybus construction itself belongs to a dedicated numerical
        or network-building component.

        Parameters
        ----------
        Ybus:
            Complex bus admittance matrix whose ordering must match
            ``bus_list``.
        """

        if Ybus is None:
            raise ValueError(
                "Ybus cannot be None"
            )

        expected_shape = (
            len(self.buses),
            len(self.buses)
        )

        if not hasattr(Ybus, "shape"):
            raise ValueError(
                "Ybus must provide a matrix shape"
            )

        if Ybus.shape != expected_shape:
            raise ValueError(
                "Ybus dimension does not match grid bus count: "
                f"expected {expected_shape}, "
                f"received {Ybus.shape}"
            )

        self.Ybus = Ybus

    # =============================================================
    # STRUCTURAL VALIDATION
    # =============================================================

    def validate(self) -> bool:
        """
        Perform structural and reference-integrity validation.

        This method does not perform numerical convergence checks.
        """

        # ---------------------------------------------------------
        # At least one bus
        # ---------------------------------------------------------

        if not self.buses:

            raise ValueError(
                "Grid must contain at least one bus."
            )

        # ---------------------------------------------------------
        # Exactly one slack bus
        # ---------------------------------------------------------

        slack_buses = [
            bus
            for bus in self.bus_list
            if bus.type == BusType.SLACK
        ]

        if len(slack_buses) != 1:

            raise ValueError(
                "Grid must have exactly one SLACK bus."
            )

        # ---------------------------------------------------------
        # Reference integrity: loads
        # ---------------------------------------------------------

        for load in self.load_list:

            if load.bus.id not in self.buses:

                raise ValueError(
                    f"Load '{load.id}' "
                    f"connected to unknown bus "
                    f"'{load.bus.id}'."
                )

        # ---------------------------------------------------------
        # Reference integrity: generators
        # ---------------------------------------------------------

        for generator in self.generator_list:

            if generator.bus.id not in self.buses:

                raise ValueError(
                    f"Generator '{generator.id}' "
                    f"connected to unknown bus "
                    f"'{generator.bus.id}'."
                )

        # ---------------------------------------------------------
        # Reference integrity: branches
        # ---------------------------------------------------------

        for branch in self.branch_list:

            fb, tb = branch.buses()

            if fb.id not in self.buses:

                raise ValueError(
                    f"Branch '{branch.id}' "
                    f"connected to unknown from-bus "
                    f"'{fb.id}'."
                )

            if tb.id not in self.buses:

                raise ValueError(
                    f"Branch '{branch.id}' "
                    f"connected to unknown to-bus "
                    f"'{tb.id}'."
                )

        # ---------------------------------------------------------
        # Refresh bus indexing after validation.
        # ---------------------------------------------------------

        self.build_bus_index()

        return True

    # =============================================================
    # COUNTS
    # =============================================================

    @property
    def bus_count(self) -> int:
        return len(self.buses)

    @property
    def load_count(self) -> int:
        return len(self.loads)

    @property
    def generator_count(self) -> int:
        return len(self.generators)

    @property
    def branch_count(self) -> int:
        return len(self.branches)

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(self) -> dict:
        """
        Return structured grid information.
        """

        slack_count = sum(
            bus.type == BusType.SLACK
            for bus in self.bus_list
        )

        pv_count = sum(
            bus.type == BusType.PV
            for bus in self.bus_list
        )

        pq_count = sum(
            bus.type == BusType.PQ
            for bus in self.bus_list
        )

        return {
            "name": self.name,
            "buses": self.bus_count,
            "loads": self.load_count,
            "generators": self.generator_count,
            "branches": self.branch_count,
            "slack_buses": slack_count,
            "pv_buses": pv_count,
            "pq_buses": pq_count,
            "ybus_available": self.Ybus is not None,
            "bus_index_available": bool(self.bus_index),
        }

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<Grid name='{self.name}', "
            f"buses={self.bus_count}, "
            f"loads={self.load_count}, "
            f"generators={self.generator_count}, "
            f"branches={self.branch_count}>"
        )
```
