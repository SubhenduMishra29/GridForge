"""
GridForge - Analysis Results Layer

Defines standardized result containers for all analyses.

DESIGN GOALS:
- Strict structure (no loose dicts)
- UI-friendly (direct binding possible)
- Extensible (future studies: SC, OPF, stability)
- Comparable (for contingency / scenario analysis)
"""

from typing import Dict, Any, List, Optional
import numpy as np


# ----------------------------------------------------------------------
# BASE RESULT
# ----------------------------------------------------------------------

class BaseResult:
    """
    Base class for all analysis results.
    """

    def __init__(self):
        self.converged: bool = False
        self.success: bool = False

        self.iterations: int = 0
        self.execution_time: Optional[float] = None

        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict:
        return {
            "converged": self.converged,
            "success": self.success,
            "iterations": self.iterations,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }


# ----------------------------------------------------------------------
# LOAD FLOW RESULT
# ----------------------------------------------------------------------

class LoadFlowResult(BaseResult):
    """
    Standard Load Flow output.
    """

    def __init__(self):
        super().__init__()

        # -----------------------------
        # BUS RESULTS
        # -----------------------------
        self.bus_voltage: Optional[np.ndarray] = None   # pu
        self.bus_angle: Optional[np.ndarray] = None     # radians

        self.bus_p: Optional[np.ndarray] = None         # MW injection
        self.bus_q: Optional[np.ndarray] = None         # MVAR injection

        # -----------------------------
        # BRANCH RESULTS
        # -----------------------------
        self.line_p_from: Optional[np.ndarray] = None
        self.line_q_from: Optional[np.ndarray] = None

        self.line_p_to: Optional[np.ndarray] = None
        self.line_q_to: Optional[np.ndarray] = None

        self.line_loading: Optional[np.ndarray] = None  # %

        # -----------------------------
        # SYSTEM RESULTS
        # -----------------------------
        self.total_generation: Optional[float] = None
        self.total_load: Optional[float] = None
        self.total_losses: Optional[float] = None

    # ------------------------------------------------------------------
    # DERIVED METRICS
    # ------------------------------------------------------------------

    def compute_losses(self):
        if self.line_p_from is None or self.line_p_to is None:
            return None

        return np.sum(self.line_p_from + self.line_p_to)

    def voltage_min(self):
        return np.min(self.bus_voltage) if self.bus_voltage is not None else None

    def voltage_max(self):
        return np.max(self.bus_voltage) if self.bus_voltage is not None else None

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict:
        base = super().to_dict()

        base.update({
            "bus_voltage": self._safe_array(self.bus_voltage),
            "bus_angle": self._safe_array(self.bus_angle),
            "bus_p": self._safe_array(self.bus_p),
            "bus_q": self._safe_array(self.bus_q),

            "line_p_from": self._safe_array(self.line_p_from),
            "line_q_from": self._safe_array(self.line_q_from),
            "line_p_to": self._safe_array(self.line_p_to),
            "line_q_to": self._safe_array(self.line_q_to),
            "line_loading": self._safe_array(self.line_loading),

            "total_generation": self.total_generation,
            "total_load": self.total_load,
            "total_losses": self.total_losses
        })

        return base

    def _safe_array(self, arr):
        return arr.tolist() if arr is not None else None


# ----------------------------------------------------------------------
# CONTINGENCY RESULT (N-1 / N-2)
# ----------------------------------------------------------------------

class ContingencyCaseResult:
    """
    Result of a single contingency scenario.
    """

    def __init__(self, outage_id: str):
        self.outage_id = outage_id
        self.success: bool = False

        self.violations: Dict[str, Any] = {}
        self.load_flow_result: Optional[LoadFlowResult] = None


class ContingencyResult(BaseResult):
    """
    Aggregated contingency results.
    """

    def __init__(self):
        super().__init__()

        self.cases: List[ContingencyCaseResult] = []

        self.critical_violations: List[Dict] = []

    # ------------------------------------------------------------------
    # ADD CASE
    # ------------------------------------------------------------------

    def add_case(self, case: ContingencyCaseResult):
        self.cases.append(case)

    # ------------------------------------------------------------------
    # ANALYSIS HELPERS
    # ------------------------------------------------------------------

    def get_failed_cases(self):
        return [c for c in self.cases if not c.success]

    def get_violations(self):
        violations = []
        for c in self.cases:
            if c.violations:
                violations.append({
                    "outage": c.outage_id,
                    "violations": c.violations
                })
        return violations

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------

    def to_dict(self):
        base = super().to_dict()

        base.update({
            "cases": [
                {
                    "outage_id": c.outage_id,
                    "success": c.success,
                    "violations": c.violations,
                    "load_flow": c.load_flow_result.to_dict() if c.load_flow_result else None
                }
                for c in self.cases
            ],
            "critical_violations": self.critical_violations
        })

        return base


# ----------------------------------------------------------------------
# FUTURE PLACEHOLDERS (DO NOT REMOVE)
# ----------------------------------------------------------------------

class ShortCircuitResult(BaseResult):
    pass


class OPFResult(BaseResult):
    pass
