# core/network/network.py

import numpy as np

# Analysis modules
from core.analysis.load_flow import LoadFlowSolver
from core.analysis.line_flow import LineFlowCalculator
from core.analysis.transformer_flow import TransformerFlowCalculator
from core.analysis.contingency import ContingencyAnalyzer
from core.analysis.short_circuit import ShortCircuitAnalyzer
from core.analysis.unbalanced_fault import UnbalancedFaultAnalyzer


class Network:
    def __init__(self):
        # Core containers
        self.buses = []
        self.lines = []
        self.transformers = []
        self.generators = []

        # Internal structures
        self.bus_index = {}
        self.Ybus = None

    # ------------------------------------------------------------------
    # ADD ELEMENTS
    # ------------------------------------------------------------------

    def add_bus(self, bus):
        self.buses.append(bus)

    def add_line(self, line):
        self.lines.append(line)

    def add_transformer(self, trafo):
        self.transformers.append(trafo)

    def add_generator(self, gen):
        self.generators.append(gen)

    # ------------------------------------------------------------------
    # INDEXING
    # ------------------------------------------------------------------

    def _build_bus_index(self):
        self.bus_index = {
            bus.id: idx for idx, bus in enumerate(self.buses)
        }

    # ------------------------------------------------------------------
    # YBUS BUILD
    # ------------------------------------------------------------------

    def build_ybus(self):
        self._build_bus_index()

        n = len(self.buses)
        Y = np.zeros((n, n), dtype=complex)

        # -------------------------
        # LINES (π model)
        # -------------------------
        for line in self.lines:
            i = self.bus_index[line.from_bus.id]
            j = self.bus_index[line.to_bus.id]

            z = complex(line.r_pu, line.x_pu)
            y = 1 / z

            b = 1j * line.b_pu / 2

            Y[i, i] += y + b
            Y[j, j] += y + b
            Y[i, j] -= y
            Y[j, i] -= y

        # -------------------------
        # TRANSFORMERS (tap + shift)
        # -------------------------
        for trafo in self.transformers:
            i = self.bus_index[trafo.from_bus.id]
            j = self.bus_index[trafo.to_bus.id]

            z = complex(trafo.r_pu, trafo.x_pu)
            y = 1 / z

            tap = getattr(trafo, "tap_ratio", 1.0)
            shift = np.deg2rad(getattr(trafo, "phase_shift_deg", 0.0))
            a = tap * np.exp(1j * shift)

            Y[i, i] += y / (a * np.conj(a))
            Y[j, j] += y
            Y[i, j] -= y / np.conj(a)
            Y[j, i] -= y / a

        self.Ybus = Y
        return Y

    # ------------------------------------------------------------------
    # LOAD FLOW
    # ------------------------------------------------------------------

    def run_load_flow(self):
        solver = LoadFlowSolver(self)
        return solver.solve()

    # ------------------------------------------------------------------
    # FLOWS
    # ------------------------------------------------------------------

    def compute_line_flows(self, lf_result):
        calc = LineFlowCalculator(self)
        return calc.compute(lf_result["Vm"], lf_result["Va"])

    def compute_transformer_flows(self, lf_result):
        calc = TransformerFlowCalculator(self)
        return calc.compute(lf_result["Vm"], lf_result["Va"])

    # ------------------------------------------------------------------
    # CONTINGENCY ANALYSIS
    # ------------------------------------------------------------------

    def run_contingency(self):
        analyzer = ContingencyAnalyzer(self, LoadFlowSolver)
        return analyzer.run_n_minus_1()

    # ------------------------------------------------------------------
    # SHORT CIRCUIT (BALANCED)
    # ------------------------------------------------------------------

    def run_short_circuit(self):
        sc = ShortCircuitAnalyzer(self)
        return sc.run_three_phase_faults()

    # ------------------------------------------------------------------
    # UNBALANCED FAULTS (SEQUENCE NETWORKS)
    # ------------------------------------------------------------------

    def run_unbalanced_faults(self, fault_type="SLG", Zf=0.0, lf_result=None):
        analyzer = UnbalancedFaultAnalyzer(self)
        return analyzer.run(fault_type=fault_type, Zf=Zf, lf_result=lf_result)

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def validate(self):
        assert len(self.buses) > 0, "No buses in network"
        assert self.Ybus is not None, "Ybus not built"

    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------

    def summary(self):
        return {
            "buses": len(self.buses),
            "lines": len(self.lines),
            "transformers": len(self.transformers),
            "generators": len(self.generators)
        }
