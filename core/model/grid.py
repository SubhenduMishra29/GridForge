"""
grid.py

Defines the Grid container.

This is the central registry for all network components.
"""

from typing import Dict, List

from .bus import Bus, BusType
from .load import Load
from .generator import Generator
from .branch import Branch


class Grid:
    """
    Power system network container.
    """

    def __init__(self, name: str = ""):
        self.name = name

        # Component storage
        self.buses: Dict[str, Bus] = {}
        self.loads: Dict[str, Load] = {}
        self.generators: Dict[str, Generator] = {}
        self.branches: Dict[str, Branch] = {}

    # -------------------------
    # Add methods
    # -------------------------

    def add_bus(self, bus: Bus):
        self._add(self.buses, bus)

    def add_load(self, load: Load):
        self._add(self.loads, load)

    def add_generator(self, gen: Generator):
        self._add(self.generators, gen)

    def add_branch(self, branch: Branch):
        self._add(self.branches, branch)

    def _add(self, container: Dict, obj):
        if obj.id in container:
            raise ValueError(f"Duplicate ID detected: {obj.id}")
        container[obj.id] = obj

    # -------------------------
    # Get methods
    # -------------------------

    def get_bus(self, id: str) -> Bus:
        return self.buses[id]

    # -------------------------
    # Iteration helpers
    # -------------------------

    @property
    def bus_list(self) -> List[Bus]:
        return list(self.buses.values())

    @property
    def load_list(self) -> List[Load]:
        return list(self.loads.values())

    @property
    def generator_list(self) -> List[Generator]:
        return list(self.generators.values())

    @property
    def branch_list(self) -> List[Branch]:
        return list(self.branches.values())

    # -------------------------
    # Derived collections
    # -------------------------

    def injections(self):
        """
        Returns all Injection objects.
        """
        return [*self.loads.values(), *self.generators.values()]

    # -------------------------
    # Utilities
    # -------------------------

    def build_bus_index(self):
        """
        Returns mapping: bus_id → index
        """
        return {bus.id: i for i, bus in enumerate(self.bus_list)}

    # -------------------------
    # Validation
    # -------------------------

    def validate(self):
        """
        Structural validation.
        """
        if not self.buses:
            raise ValueError("Grid must contain at least one bus.")

        # Slack bus check
        slack_buses = [b for b in self.buses.values() if b.type == BusType.SLACK]
        if len(slack_buses) != 1:
            raise ValueError("Grid must have exactly one SLACK bus.")

        # Connectivity existence
        if not self.branches:
            raise ValueError("Grid must contain at least one branch.")

        # Reference integrity
        for load in self.loads.values():
            if load.bus.id not in self.buses:
                raise ValueError(f"Load {load.id} connected to unknown bus.")

        for gen in self.generators.values():
            if gen.bus.id not in self.buses:
                raise ValueError(f"Generator {gen.id} connected to unknown bus.")

        for br in self.branches.values():
            fb, tb = br.buses()
            if fb.id not in self.buses or tb.id not in self.buses:
                raise ValueError(f"Branch {br.id} connected to unknown bus.")

    # -------------------------
    # Debug
    # -------------------------

    def summary(self):
        return (
            f"Grid '{self.name}': "
            f"{len(self.buses)} buses, "
            f"{len(self.loads)} loads, "
            f"{len(self.generators)} generators, "
            f"{len(self.branches)} branches"
        )

    def __repr__(self):
        return self.summary()
