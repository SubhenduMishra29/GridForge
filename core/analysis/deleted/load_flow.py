"""
GridForge - Load Flow Analysis Wrapper

Acts as a bridge between:
    Network Model → Solver → Standardized Results

STRICT RULES:
- No numerical solving here
- No mutation of network
- Only orchestration + mapping
"""

from typing import Dict, Any
import numpy as np
import time

from core.analysis.base import BaseAnalysis, ValidationError, ConvergenceError
from core.analysis.results import LoadFlowResult

# Import solver (aligned with your frozen structure)
from core.solver.load_flow.newton_raphson import solve as nr_solve


class LoadFlowAnalysis(BaseAnalysis):
    """
    Load Flow Analysis using Newton-Raphson (default).

    Supported:
        - NR (current)
        - Future: Fast Decoupled, DC, etc.
    """

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def validate(self) -> None:
        net = self.network

        # Basic structure checks (adapt to your model)
        if not hasattr(net, "buses") or len(net.buses) == 0:
            raise ValidationError("Network has no buses")

        if not hasattr(net, "slack_bus"):
            raise ValidationError("Slack bus not defined")

        # Optional: connectivity check (placeholder)
        # TODO: move to utils.validation later

    # ------------------------------------------------------------------
    # PREPARATION
    # ------------------------------------------------------------------

    def prepare(self, **kwargs) -> Dict:
        """
        Prepare solver-ready case.

        NOTE:
        - Do NOT build Y-bus here (solver responsibility)
        - Only pass references / structured inputs
        """

        options = {
            "tolerance": kwargs.get("tolerance", 1e-6),
            "max_iter": kwargs.get("max_iter", 20),
            "verbose": kwargs.get("verbose", False)
        }

        case = {
            "network": self.network,
            "options": options
        }

        return case

    # ------------------------------------------------------------------
    # SOLVER CALL
    # ------------------------------------------------------------------

    def solve(self, case: Dict, **kwargs) -> Dict:
        """
        Call Newton-Raphson solver.
        """

        net = case["network"]
        opts = case["options"]

        start_time = time.time()

        raw = nr_solve(
            network=net,
            tolerance=opts["tolerance"],
            max_iter=opts["max_iter"],
            verbose=opts["verbose"]
        )

        elapsed = time.time() - start_time

        if not raw.get("converged", False):
            raise ConvergenceError("Load flow did not converge")

        raw["execution_time"] = elapsed

        return raw

    # ------------------------------------------------------------------
    # POST-PROCESSING
    # ------------------------------------------------------------------

    def post_process(self, raw: Dict) -> LoadFlowResult:
        """
        Convert solver output → standardized result
        """

        result = LoadFlowResult()

        # -----------------------------
        # STATUS
        # -----------------------------
        result.converged = raw.get("converged", False)
        result.success = result.converged
        result.iterations = raw.get("iterations", 0)
        result.execution_time = raw.get("execution_time")

        # -----------------------------
        # BUS DATA
        # -----------------------------
        result.bus_voltage = self._as_array(raw.get("V"))
        result.bus_angle = self._as_array(raw.get("theta"))

        result.bus_p = self._as_array(raw.get("P"))
        result.bus_q = self._as_array(raw.get("Q"))

        # -----------------------------
        # BRANCH DATA
        # -----------------------------
        result.line_p_from = self._as_array(raw.get("Pf"))
        result.line_q_from = self._as_array(raw.get("Qf"))

        result.line_p_to = self._as_array(raw.get("Pt"))
        result.line_q_to = self._as_array(raw.get("Qt"))

        result.line_loading = self._compute_loading(raw)

        # -----------------------------
        # SYSTEM METRICS
        # -----------------------------
        result.total_generation = raw.get("Pg_total")
        result.total_load = raw.get("Pl_total")

        result.total_losses = self._compute_losses(
            result.line_p_from,
            result.line_p_to
        )

        # -----------------------------
        # METADATA
        # -----------------------------
        result.metadata = {
            "solver": "Newton-Raphson",
            "tolerance": raw.get("tolerance"),
            "max_iter": raw.get("max_iter")
        }

        return result

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    def _as_array(self, data):
        if data is None:
            return None
        return np.asarray(data, dtype=float)

    def _compute_losses(self, pf, pt):
        if pf is None or pt is None:
            return None
        return float(np.sum(pf + pt))

    def _compute_loading(self, raw):
        """
        Compute line loading (%)

        Requires:
            - apparent power OR P/Q + rating
        """

        Sf = raw.get("Sf")  # apparent power magnitude
        rating = raw.get("rating")

        if Sf is None or rating is None:
            return None

        Sf = np.asarray(Sf)
        rating = np.asarray(rating)

        with np.errstate(divide='ignore', invalid='ignore'):
            loading = 100.0 * Sf / rating
            loading[np.isnan(loading)] = 0.0

        return loading
