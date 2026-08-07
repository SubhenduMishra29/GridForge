# core/network/network.py

from core.network.ybus import YBusBuilder
from core.simulation.load_flow import LoadFlowSolver


class Network:
    """
    GridForge Core Network Engine

    Manages:
    - Buses
    - Lines
    - Transformers
    - Shunts

    Provides:
    - Y-bus formation
    - Load flow execution
    """

    def __init__(self, base_mva=100.0):
        self.base_mva = base_mva

        self.buses = []
        self.lines = []
        self.transformers = []
        self.shunts = []

        self.bus_lookup = {}

    # ---------------------------------------------------------
    # ADD ELEMENTS
    # ---------------------------------------------------------
    def add_bus(self, bus):
        if bus.id in self.bus_lookup:
            raise ValueError(f"Bus {bus.id} already exists")

        self.buses.append(bus)
        self.bus_lookup[bus.id] = bus

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

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------
    def _validate_bus(self, bus_id):
        if bus_id not in self.bus_lookup:
            raise ValueError(f"Bus {bus_id} not found in network")

    # ---------------------------------------------------------
    # BUILD YBUS
    # ---------------------------------------------------------
    def build_ybus(self):
        builder = YBusBuilder(self.buses)

        Y = builder.build(
            lines=self.lines,
            transformers=self.transformers,
            shunts=self.shunts,
        )

        return Y

    # ---------------------------------------------------------
    # LOAD FLOW
    # ---------------------------------------------------------
    def run_load_flow(self, tol=1e-6, max_iter=20):
        # Reset buses to specified values
        for bus in self.buses:
            bus.reset()

        Ybus = self.build_ybus()

        solver = LoadFlowSolver(
            self.buses,
            Ybus,
            tolerance=tol,
            max_iter=max_iter
        )

        V, theta = solver.solve()

        # Update bus states
        for i, bus in enumerate(self.buses):
            bus.V = V[i]
            bus.theta = theta[i]

        return self.get_results()

    # ---------------------------------------------------------
    # NEW: LINE FLOW + LOSS CALCULATION
    # ---------------------------------------------------------
    def get_line_flows(self):
        """
        Uses Line.calculate_flow() to compute:
        - Power flows
        - Losses
        """
        Ybus = self.build_ybus()

        flows = []

        for line in self.lines:
            f = line.calculate_flow(self.buses, Ybus)

            flows.append({
                "from": line.from_bus,
                "to": line.to_bus,
                **f
            })

        return flows

    # ---------------------------------------------------------
    # RESULTS
    # ---------------------------------------------------------
    def get_results(self):
        bus_results = []

        for bus in self.buses:
            bus_results.append({
                "bus_id": bus.id,
                "V": bus.V,
                "theta": bus.theta,
                "P": bus.P,
                "Q": bus.Q,
            })

        # 🔥 Include line flows here
        line_results = self.get_line_flows()

        return {
            "buses": bus_results,
            "lines": line_results
        }

    # ---------------------------------------------------------
    # DEBUG
    # ---------------------------------------------------------
    def summary(self):
        return {
            "buses": len(self.buses),
            "lines": len(self.lines),
            "transformers": len(self.transformers),
            "shunts": len(self.shunts),
        }
