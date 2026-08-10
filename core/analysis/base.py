"""
GridForge - Analysis Base Layer

Defines the standard lifecycle and interface for all analysis modules.

STRICT RULES:
- Analysis does NOT modify the network
- Analysis does NOT perform numerical solving
- Analysis orchestrates: validate → prepare → solve → post-process
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class AnalysisError(Exception):
    """Base exception for all analysis-related failures."""
    pass


class ValidationError(AnalysisError):
    """Raised when network or inputs are invalid."""
    pass


class ConvergenceError(AnalysisError):
    """Raised when solver fails to converge."""
    pass


class BaseAnalysis(ABC):
    """
    Abstract base class for all analysis modules.

    Lifecycle:
        run() →
            validate() →
            prepare() →
            solve() →
            post_process() →
        return result

    Subclasses MUST implement:
        - validate
        - prepare
        - solve
        - post_process
    """

    def __init__(self, network: Any):
        """
        Parameters:
            network: Immutable network model (read-only usage only)
        """
        if network is None:
            raise ValueError("Network cannot be None")

        self.network = network

        # Execution state (for debugging / logging)
        self._is_validated = False
        self._case = None
        self._raw_result = None

    # ------------------------------------------------------------------
    # REQUIRED IMPLEMENTATION METHODS
    # ------------------------------------------------------------------

    @abstractmethod
    def validate(self) -> None:
        """
        Validate network and inputs.

        Must raise:
            ValidationError if invalid
        """
        pass

    @abstractmethod
    def prepare(self, **kwargs) -> Dict:
        """
        Prepare solver-ready case from network.

        Returns:
            dict → solver input structure
        """
        pass

    @abstractmethod
    def solve(self, case: Dict, **kwargs) -> Dict:
        """
        Call solver (NO numerical logic here).

        Returns:
            dict → raw solver output
        """
        pass

    @abstractmethod
    def post_process(self, raw: Dict):
        """
        Convert raw solver output into standardized results object.

        Returns:
            Analysis result object
        """
        pass

    # ------------------------------------------------------------------
    # PIPELINE EXECUTION
    # ------------------------------------------------------------------

    def run(self, **kwargs):
        """
        Execute full analysis pipeline.

        Steps:
            1. Validate
            2. Prepare case
            3. Solve
            4. Post-process

        Returns:
            Standardized result object
        """

        # Step 1: Validation
        self._run_validation()

        # Step 2: Prepare case
        case = self._run_preparation(**kwargs)

        # Step 3: Solve
        raw = self._run_solver(case, **kwargs)

        # Step 4: Post-process
        result = self._run_postprocessing(raw)

        return result

    # ------------------------------------------------------------------
    # INTERNAL EXECUTION WRAPPERS (CONTROL + SAFETY)
    # ------------------------------------------------------------------

    def _run_validation(self):
        try:
            self.validate()
            self._is_validated = True
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Validation failed: {str(e)}") from e

    def _run_preparation(self, **kwargs) -> Dict:
        if not self._is_validated:
            raise AnalysisError("Validation must run before preparation")

        try:
            case = self.prepare(**kwargs)
            self._case = case

            if not isinstance(case, dict):
                raise AnalysisError("Prepared case must be a dictionary")

            return case

        except Exception as e:
            raise AnalysisError(f"Preparation failed: {str(e)}") from e

    def _run_solver(self, case: Dict, **kwargs) -> Dict:
        try:
            raw = self.solve(case, **kwargs)
            self._raw_result = raw

            if not isinstance(raw, dict):
                raise AnalysisError("Solver output must be a dictionary")

            return raw

        except ConvergenceError:
            raise
        except Exception as e:
            raise AnalysisError(f"Solver execution failed: {str(e)}") from e

    def _run_postprocessing(self, raw: Dict):
        try:
            result = self.post_process(raw)

            if result is None:
                raise AnalysisError("Post-processing returned None")

            return result

        except Exception as e:
            raise AnalysisError(f"Post-processing failed: {str(e)}") from e

    # ------------------------------------------------------------------
    # OPTIONAL HOOKS (FOR FUTURE EXTENSIONS)
    # ------------------------------------------------------------------

    def pre_run_hook(self):
        """Hook before run() starts (logging, profiling, etc.)"""
        pass

    def post_run_hook(self, result):
        """Hook after run() completes"""
        pass
