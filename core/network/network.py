# core/network/network.py

"""
GridForge Network Core

Responsibilities:
- Own all grid elements
- Maintain system consistency
- Build Y-bus
- Run power flow

This is the central orchestration layer.
"""

from core.network.ybus import YBusBuilder
from core.solver.nr import NewtonRaphsonSolver


class Network:
    def __init__(self, per_unit_system):
        self.per_unit = per_unit_system

        # Element containers
        self.buses = []
        self.lines = []
        self.transformers = []
        self.shunts = []

        # Internal state
        self._bus_map = {}
        self._Ybus = None
        self._bus_index = None

    # ------------------------------------------------------------------
    # ELEMENT REGISTRATION
    # ------------------------------------------------------------------

    def add_bus(self, bus):
        if bus.id in self._bus_map:
            raise ValueError(f"Duplicate bus ID: {bus.id}")

        self.buses.append(bus)
        self._bus_map[bus.id] = bus

    def add_line(self, line):
        self._validate_bus(line.from_bus)
        self._validate_bus(line.to_bus)
        self.lines.append(line)

    def add_transformer(self, trafo):
        self._validate_bus(trafo.from_bus)
        self._validate_bus(trafo.to_bus)
        self.transformers.append(trafo)

    def add_shunt(self, shunt):
        self._validate_bus(shunt.bus)
        self.shunts.append(shunt)

    def _validate_bus(self, bus):
        if bus.id not in self._bus_map:
            raise ValueError(f"Bus {bus.id} not registered in network")

    # ------------------------------------------------------------------
    # BUILD PHASE
    # ------------------------------------------------------------------

    def build(self):
        """
        Builds system matrices (Y-bus)
        """
        if len(self.buses) == 0:
            raise RuntimeError("Network has no buses")

        ybus_builder = YBusBuilder(self)
        self._Ybus, self._bus_index = ybus_builder.build()

        return self._Ybus

    # ------------------------------------------------------------------
    # ACCESSORS
    # ------------------------------------------------------------------

    @property
    def Ybus(self):
        if self._Ybus is None:
            raise RuntimeError("Ybus not built. Call build() first.")
        return self._Ybus

    @property
    def bus_index(self):
        if self._bus_index is None:
            raise RuntimeError("Bus index not initialized")
        return self._bus_index

    # ------------------------------------------------------------------
    # SOLVER ENTRYPOINT
    # ------------------------------------------------------------------

    def solve_power_flow(self, tol=1e-6, max_iter=20):
        """
        Runs Newton-Raphson power flow
        """

        if self._Ybus is None:
            self.build()

        solver = NewtonRaphsonSolver(self)
        return solver.solve(tol=tol, max_iter=max_iter)

    # ------------------------------------------------------------------
    # DEBUG / VALIDATION
    # ------------------------------------------------------------------

    def validate(self):
        """
        Basic structural validation
        """
        if len(self.buses) == 0:
            raise ValueError("No buses defined")

        if not any(b.is_slack for b in self.buses):
            raise ValueError("No slack bus defined")

        if sum(b.is_slack for b in self.buses) > 1:
            raise ValueError("Multiple slack buses detected")

        return True
