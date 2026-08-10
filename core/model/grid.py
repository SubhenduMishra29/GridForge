```python
"""
GridForge Grid Model
====================

File:
    core/model/grid.py

Defines the central electrical-network container.

Responsibilities
----------------
- Registry for electrical components.
- Stable component ordering for numerical analysis.
- Component lookup.
- Bus indexing.
- Structural/reference validation.
- Aggregation of connected power injections.
- Registration of passive network elements.

Supported components
--------------------
- Bus
- Load
- Generator
- Branch
- Line
- Transformer
- Shunt

The Grid model does NOT:
- Build Ybus.
- Run power-flow calculations.
- Solve numerical systems.
- Perform short-circuit calculations.
- Perform protection calculations.
- Perform dynamic simulation.

Numerical analysis belongs in the solver/network/analysis layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Dict, List

from .bus import Bus, BusType
from .load import Load
from .generator import Generator
from .branch import Branch
from .line import Line
from .transformer import Transformer
from .shunt import Shunt


class Grid:
    """
    Central container for a GridForge electrical network.

    Component registries use dictionaries keyed by stable object IDs.

    Numerical code should use the ordered list properties:

        bus_list
        load_list
        generator_list
        branch_list
        line_list
        transformer_list
        shunt_list

    rather than depending on the internal dictionary
    representation.
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

        self.lines: Dict[str, Line] = {}

        self.transformers: Dict[str, Transformer] = {}

        self.shunts: Dict[str, Shunt] = {}

        # =========================================================
        # DERIVED / ANALYSIS STATE
        # =========================================================

        # Grid does not construct Ybus.
        #
        # A dedicated network/Ybus builder may populate this
        # attribute after construction.

        self.Ybus = None

        # Stable bus ID -> numerical index mapping.

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

    def add_generator(
        self,
        generator: Generator
    ) -> None:
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
        Add a generic Branch to the grid.

        Branch subclasses such as Line and Transformer can also
        be represented in the common branch registry.
        """

        if not isinstance(branch, Branch):
            raise TypeError(
                "add_branch() requires a Branch object"
            )

        self._add(
            self.branches,
            branch
        )

    def add_line(self, line: Line) -> None:
        """
        Add a transmission Line.

        The line is registered both in the specialized line
        registry and in the common branch registry.
        """

        if not isinstance(line, Line):
            raise TypeError(
                "add_line() requires a Line object"
            )

        self._add(
            self.lines,
            line
        )

        self._add(
            self.branches,
            line
        )

    def add_transformer(
        self,
        transformer: Transformer
    ) -> None:
        """
        Add a Transformer.

        Transformer is expected to participate in the common
        two-terminal network-element interface.
        """

        if not isinstance(transformer, Transformer):
            raise TypeError(
                "add_transformer() requires a Transformer object"
            )

        self._add(
            self.transformers,
            transformer
        )

        # Transformer is added to the common branch registry only
        # when it implements the Branch interface.
        #
        # This keeps Grid tolerant of the current Transformer model
        # while allowing the model to evolve toward Branch
        # inheritance.

        if isinstance(transformer, Branch):

            self._add(
                self.branches,
                transformer
            )

    def add_shunt(self, shunt: Shunt) -> None:
        """
        Add a passive Shunt element.
        """

        if not isinstance(shunt, Shunt):
            raise TypeError(
                "add_shunt() requires a Shunt object"
            )

        self._add(
            self.shunts,
            shunt
        )

    @staticmethod
    def _add(
        container: Dict,
        obj
    ) -> None:
        """
        Add an object to a component registry.

        IDs must be unique within the target registry.
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

    def get_generator(
        self,
        id: str
    ) -> Generator:
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
        Return a common Branch by ID.
        """

        try:
            return self.branches[id]

        except KeyError as exc:

            raise KeyError(
                f"Branch '{id}' does not exist"
            ) from exc

    def get_line(self, id: str) -> Line:
        """
        Return a Line by ID.
        """

        try:
            return self.lines[id]

        except KeyError as exc:

            raise KeyError(
                f"Line '{id}' does not exist"
            ) from exc

    def get_transformer(
        self,
        id: str
    ) -> Transformer:
        """
        Return a Transformer by ID.
        """

        try:
            return self.transformers[id]

        except KeyError as exc:

            raise KeyError(
                f"Transformer '{id}' does not exist"
            ) from exc

    def get_shunt(self, id: str) -> Shunt:
        """
        Return a Shunt by ID.
        """

        try:
            return self.shunts[id]

        except KeyError as exc:

            raise KeyError(
                f"Shunt '{id}' does not exist"
            ) from exc

    # =============================================================
    # ORDERED COMPONENT VIEWS
    # =============================================================

    @property
    def bus_list(self) -> List[Bus]:
        """
        Return buses in stable registry order.
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
        Return all common branch elements.

        This is the preferred collection for Ybus and other
        network-topology algorithms.
        """

        return list(
            self.branches.values()
        )

    @property
    def line_list(self) -> List[Line]:
        """
        Return transmission lines in registry order.
        """

        return list(
            self.lines.values()
        )

    @property
    def transformer_list(self) -> List[Transformer]:
        """
        Return transformers in registry order.
        """

        return list(
            self.transformers.values()
        )

    @property
    def shunt_list(self) -> List[Shunt]:
        """
        Return shunts in registry order.
        """

        return list(
            self.shunts.values()
        )

    # =============================================================
    # INJECTION COLLECTION
    # =============================================================

    @property
    def injection_list(self) -> List:
        """
        Return all objects implementing the Injection interface.

        Ordering:

            Generators
            Loads

        This ordering is deterministic but must not be interpreted
        as bus ordering.
        """

        return [
            *self.generator_list,
            *self.load_list
        ]

    def injections(self) -> List:
        """
        Backward-compatible access to all injections.
        """

        return self.injection_list

    # =============================================================
    # BUS INDEXING
    # =============================================================

    def build_bus_index(self) -> Dict[str, int]:
        """
        Build and store the bus-ID -> numerical-index mapping.

        The mapping corresponds exactly to ``bus_list`` ordering.
        """

        self.bus_index = {
            bus.id: index
            for index, bus in enumerate(
                self.bus_list
            )
        }

        return self.bus_index.copy()

    def get_bus_index(
        self,
        bus_id: str
    ) -> int:
        """
        Return the numerical index of a bus.

        The index is generated lazily when required.
        """

        if (
            not self.bus_index
            or len(self.bus_index) != len(self.buses)
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
        """

        self.bus_index = {}

    # =============================================================
    # YBUS INTERFACE
    # =============================================================

    def set_ybus(self, Ybus) -> None:
        """
        Attach a calculated Ybus matrix to the grid.

        Ybus construction belongs to the network layer.
        """

        if Ybus is None:
            raise ValueError(
                "Ybus cannot be None"
            )

        expected_shape = (
            len(self.buses),
            len(self.buses)
        )

        if not hasattr(
            Ybus,
            "shape"
        ):
            raise ValueError(
                "Ybus must provide a matrix shape"
            )

        if Ybus.shape != expected_shape:

            raise ValueError(
                "Ybus dimension does not match grid "
                "bus count: "
                f"expected {expected_shape}, "
                f"received {Ybus.shape}"
            )

        self.Ybus = Ybus

    def clear_ybus(self) -> None:
        """
        Remove the currently attached Ybus matrix.
        """

        self.Ybus = None

    # =============================================================
    # STRUCTURAL VALIDATION
    # =============================================================

    def validate(self) -> bool:
        """
        Perform structural and reference-integrity validation.

        This method does not perform numerical calculations.
        """

        # ---------------------------------------------------------
        # Bus existence
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
            if bus.type is BusType.SLACK
        ]

        if len(slack_buses) != 1:

            raise ValueError(
                "Grid must have exactly one SLACK bus."
            )

        # ---------------------------------------------------------
        # Load references
        # ---------------------------------------------------------

        for load in self.load_list:

            if load.bus.id not in self.buses:

                raise ValueError(
                    f"Load '{load.id}' connected to "
                    f"unknown bus '{load.bus.id}'."
                )

        # ---------------------------------------------------------
        # Generator references
        # ---------------------------------------------------------

        for generator in self.generator_list:

            if generator.bus.id not in self.buses:

                raise ValueError(
                    f"Generator '{generator.id}' connected "
                    f"to unknown bus '{generator.bus.id}'."
                )

        # ---------------------------------------------------------
        # Branch references
        # ---------------------------------------------------------

        for branch in self.branch_list:

            try:
                from_bus, to_bus = branch.buses()

            except AttributeError as exc:

                raise ValueError(
                    f"Branch '{branch.id}' does not provide "
                    f"the required buses() interface."
                ) from exc

            if from_bus.id not in self.buses:

                raise ValueError(
                    f"Branch '{branch.id}' connected to "
                    f"unknown from-bus '{from_bus.id}'."
                )

            if to_bus.id not in self.buses:

                raise ValueError(
                    f"Branch '{branch.id}' connected to "
                    f"unknown to-bus '{to_bus.id}'."
                )

        # ---------------------------------------------------------
        # Shunt references
        # ---------------------------------------------------------

        for shunt in self.shunt_list:

            if shunt.bus.id not in self.buses:

                raise ValueError(
                    f"Shunt '{shunt.id}' connected to "
                    f"unknown bus '{shunt.bus.id}'."
                )

        # ---------------------------------------------------------
        # Refresh bus indexing.
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

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def transformer_count(self) -> int:
        return len(self.transformers)

    @property
    def shunt_count(self) -> int:
        return len(self.shunts)

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(self) -> dict:
        """
        Return structured grid information.
        """

        slack_count = sum(
            bus.type is BusType.SLACK
            for bus in self.bus_list
        )

        pv_count = sum(
            bus.type is BusType.PV
            for bus in self.bus_list
        )

        pq_count = sum(
            bus.type is BusType.PQ
            for bus in self.bus_list
        )

        return {
            "name": self.name,

            "buses": self.bus_count,

            "loads": self.load_count,

            "generators": self.generator_count,

            "branches": self.branch_count,

            "lines": self.line_count,

            "transformers": self.transformer_count,

            "shunts": self.shunt_count,

            "slack_buses": slack_count,

            "pv_buses": pv_count,

            "pq_buses": pq_count,

            "ybus_available": (
                self.Ybus is not None
            ),

            "bus_index_available": bool(
                self.bus_index
            ),
        }

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<Grid "
            f"name='{self.name}', "
            f"buses={self.bus_count}, "
            f"loads={self.load_count}, "
            f"generators={self.generator_count}, "
            f"branches={self.branch_count}, "
            f"lines={self.line_count}, "
            f"transformers={self.transformer_count}, "
            f"shunts={self.shunt_count}>"
        )
```
