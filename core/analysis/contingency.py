# core/analysis/contingency.py

"""
GridForge Contingency Analysis (N-1)

Supports:
- Line outages
- Transformer outages
- Generator outages

Outputs:
- Convergence status
- Voltage violations
- Line overloads
"""

import copy
import numpy as np


class ContingencyAnalyzer:
    def __init__(self, network, solver_cls):
        """
        solver_cls: your LoadFlowSolver class
        """
        self.base_network = network
        self.solver_cls = solver_cls

    # ------------------------------------------------------------------
    # MAIN ENTRY
    # ------------------------------------------------------------------

    def run_n_minus_1(self):
        results = []

        contingencies = self._generate_contingencies()

        for c in contingencies:
            print(f"Running contingency: {c['type']} {c['id']}")

            net = self._apply_contingency(c)

            try:
                solver = self.solver_cls(net)
                lf_result = solver.solve()

                line_flows = net.compute_line_flows(lf_result)
                trafo_flows = net.compute_transformer_flows(lf_result)

                violations = self._check_violations(
                    net, lf_result, line_flows, trafo_flows
                )

                results.append({
                    "contingency": c,
                    "converged": True,
                    "violations": violations
                })

            except Exception as e:
                results.append({
                    "contingency": c,
                    "converged": False,
                    "error": str(e)
                })

        return results

    # ------------------------------------------------------------------
    # CONTINGENCY GENERATION
    # ------------------------------------------------------------------

    def _generate_contingencies(self):
        contingencies = []

        # Lines
        for line in self.base_network.lines:
            contingencies.append({
                "type": "line",
                "id": line.id
            })

        # Transformers
        for trafo in self.base_network.transformers:
            contingencies.append({
                "type": "transformer",
                "id": trafo.id
            })

        # Generators
        for gen in self.base_network.generators:
            contingencies.append({
                "type": "generator",
                "id": gen.id
            })

        return contingencies

    # ------------------------------------------------------------------
    # APPLY OUTAGE
    # ------------------------------------------------------------------

    def _apply_contingency(self, contingency):
        net = copy.deepcopy(self.base_network)

        if contingency["type"] == "line":
            net.lines = [
                l for l in net.lines if l.id != contingency["id"]
            ]

        elif contingency["type"] == "transformer":
            net.transformers = [
                t for t in net.transformers if t.id != contingency["id"]
            ]

        elif contingency["type"] == "generator":
            net.generators = [
                g for g in net.generators if g.id != contingency["id"]
            ]

        # Rebuild Ybus
        net.build_ybus()

        return net

    # ------------------------------------------------------------------
    # VIOLATION CHECKS
    # ------------------------------------------------------------------

    def _check_violations(self, net, lf_result, line_flows, trafo_flows):
        violations = {
            "voltage": [],
            "thermal": []
        }

        Vm = lf_result["Vm"]

        # -------------------------
        # Voltage limits
        # -------------------------
        for bus in net.buses:
            v = Vm[net.bus_index[bus.id]]

            if v < bus.v_min or v > bus.v_max:
                violations["voltage"].append({
                    "bus": bus.id,
                    "Vm": v
                })

        # -------------------------
        # Line overloads
        # -------------------------
        for lf, line in zip(line_flows, net.lines):
            S = np.sqrt(lf["P_from_to"]**2 + lf["Q_from_to"]**2)

            if hasattr(line, "rating") and S > line.rating:
                violations["thermal"].append({
                    "element": line.id,
                    "loading": S,
                    "limit": line.rating
                })

        # -------------------------
        # Transformer overloads
        # -------------------------
        for tf, trafo in zip(trafo_flows, net.transformers):
            S = np.sqrt(tf["P_from_to"]**2 + tf["Q_from_to"]**2)

            if hasattr(trafo, "rating") and S > trafo.rating:
                violations["thermal"].append({
                    "element": trafo.id,
                    "loading": S,
                    "limit": trafo.rating
                })

        return violations
