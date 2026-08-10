"""
GridForge - Contingency Analysis (N-1 / N-k)

Design Principles:
- NON-destructive (network is never modified directly)
- Reuses LoadFlowAnalysis
- Scalable to N-2 / batch / probabilistic
- Violation-driven output
"""

from typing import List, Dict, Any
import copy

from core.analysis.base import BaseAnalysis, ValidationError
from core.analysis.results import (
    ContingencyResult,
    ContingencyCaseResult,
)
from core.analysis.load_flow import LoadFlowAnalysis


class ContingencyAnalysis(BaseAnalysis):
    """
    N-1 / N-k Contingency Analysis Engine
    """

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def validate(self) -> None:
        net = self.network

        if not hasattr(net, "buses") or len(net.buses) == 0:
            raise ValidationError("Network has no buses")

        if not hasattr(net, "branches") or len(net.branches) == 0:
            raise ValidationError("Network has no branches")

    # ------------------------------------------------------------------
    # PREPARATION
    # ------------------------------------------------------------------

    def prepare(self, **kwargs) -> Dict:
        """
        Prepare contingency list.

        Options:
            elements: list of elements to outage
            type: 'line', 'transformer', etc.
        """

        elements = kwargs.get("elements", None)

        if elements is None:
            # Default: all branches (N-1)
            elements = [b.id for b in self.network.branches]

        case = {
            "elements": elements,
            "options": kwargs
        }

        return case

    # ------------------------------------------------------------------
    # SOLVER LOOP (ORCHESTRATOR)
    # ------------------------------------------------------------------

    def solve(self, case: Dict, **kwargs) -> Dict:
        """
        Run load flow for each contingency.
        """

        elements = case["elements"]

        results = []

        for elem_id in elements:
            outage_case = self._create_outage_case(elem_id)

            lf = LoadFlowAnalysis(outage_case)

            try:
                lf_result = lf.run(**case["options"])

                case_result = {
                    "id": elem_id,
                    "success": True,
                    "lf_result": lf_result
                }

            except Exception as e:
                case_result = {
                    "id": elem_id,
                    "success": False,
                    "error": str(e),
                    "lf_result": None
                }

            results.append(case_result)

        return {"cases": results}

    # ------------------------------------------------------------------
    # POST-PROCESSING
    # ------------------------------------------------------------------

    def post_process(self, raw: Dict) -> ContingencyResult:
        result = ContingencyResult()

        for case_raw in raw["cases"]:
            case = ContingencyCaseResult(case_raw["id"])

            case.success = case_raw["success"]
            case.load_flow_result = case_raw.get("lf_result")

            if case.success:
                case.violations = self._detect_violations(case.load_flow_result)
            else:
                case.violations = {"error": case_raw.get("error")}

            result.add_case(case)

        # Aggregate critical violations
        result.critical_violations = result.get_violations()

        result.success = True
        result.converged = all(c.success for c in result.cases)

        return result

    # ------------------------------------------------------------------
    # OUTAGE MODELING (NON-DESTRUCTIVE)
    # ------------------------------------------------------------------

    def _create_outage_case(self, elem_id):
        """
        Create a modified network copy with one element outaged.

        IMPORTANT:
        - Uses deep copy → safe but can be optimized later
        """

        net_copy = copy.deepcopy(self.network)

        for branch in net_copy.branches:
            if branch.id == elem_id:
                branch.in_service = False
                break

        return net_copy

    # ------------------------------------------------------------------
    # VIOLATION DETECTION
    # ------------------------------------------------------------------

    def _detect_violations(self, lf_result) -> Dict[str, Any]:
        """
        Detect engineering violations.

        Current:
            - Voltage limits
            - Line loading

        Future:
            - Thermal time curves
            - Stability margins
        """

        violations = {}

        # -----------------------------
        # VOLTAGE VIOLATIONS
        # -----------------------------
        v = lf_result.bus_voltage

        if v is not None:
            v_min = 0.95
            v_max = 1.05

            low = (v < v_min).nonzero()[0]
            high = (v > v_max).nonzero()[0]

            if len(low) > 0 or len(high) > 0:
                violations["voltage"] = {
                    "low_buses": low.tolist(),
                    "high_buses": high.tolist()
                }

        # -----------------------------
        # LINE LOADING
        # -----------------------------
        loading = lf_result.line_loading

        if loading is not None:
            overloaded = (loading > 100.0).nonzero()[0]

            if len(overloaded) > 0:
                violations["thermal"] = {
                    "overloaded_lines": overloaded.tolist()
                }

        return violations
