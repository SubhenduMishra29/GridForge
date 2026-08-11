```python
"""
GridForge Contingency Analysis
==============================

File:
    core/analysis/contingency.py

Purpose:
    Public analysis-level facade for contingency studies.

Scope:
    - N-1 contingency analysis
    - Extensible architecture for N-k / batch studies
    - Non-destructive outage simulation
    - Power-flow based post-contingency assessment
    - Violation-driven results

Architecture
------------

    Network
        |
        v
    ContingencyAnalysis
        |
        +---- isolated contingency Network
        |          |
        |          v
        |    PowerFlowAnalysis
        |          |
        |          v
        |    core/solver/power_flow/
        |
        v
    ContingencyResult

Responsibilities
----------------
This module is responsible for:

    - validating contingency-study inputs
    - identifying valid outage candidates
    - creating isolated contingency cases
    - delegating each case to PowerFlowAnalysis
    - collecting case results
    - detecting post-contingency violations
    - aggregating study-level results

This module does NOT:

    - modify the authoritative study Network
    - calculate Y-bus directly
    - calculate power mismatches
    - assemble Jacobians
    - perform Newton-Raphson iterations
    - implement numerical power-flow mathematics
    - implement short-circuit calculations
    - implement dynamic/stability calculations

Numerical responsibilities remain in:

    core/solver/

Topology and Y-bus responsibilities remain in:

    core/network/

Canonical GridForge terminology:
    "Contingency Analysis"
    "Power Flow"
    "Line"
    "Transformer"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import copy

from core.analysis.power_flow import PowerFlowAnalysis


# =====================================================================
# RESULT TYPES
# =====================================================================


@dataclass
class ContingencyViolation:
    """
    Single post-contingency engineering violation.

    Attributes
    ----------
    category:
        Violation category, e.g. ``"voltage"`` or ``"thermal"``.

    element_id:
        ID of the affected element, where applicable.

    value:
        Calculated value.

    limit:
        Applicable engineering limit.

    severity:
        Optional severity indicator.
    """

    category: str
    element_id: Any
    value: Optional[float] = None
    limit: Optional[float] = None
    severity: Optional[float] = None


@dataclass
class ContingencyCaseResult:
    """
    Result for one contingency case.
    """

    case_id: str
    outages: Tuple[Any, ...]

    success: bool = False
    converged: bool = False

    power_flow_result: Any = None

    violations: List[ContingencyViolation] = field(
        default_factory=list
    )

    error: Optional[str] = None


@dataclass
class ContingencyResult:
    """
    Complete contingency-study result.
    """

    cases: List[ContingencyCaseResult] = field(
        default_factory=list
    )

    success: bool = False
    converged: bool = False

    critical_cases: List[str] = field(
        default_factory=list
    )

    critical_violations: List[ContingencyViolation] = field(
        default_factory=list
    )

    @property
    def failed_cases(self) -> List[ContingencyCaseResult]:
        """
        Return cases for which the power-flow study failed.
        """

        return [
            case
            for case in self.cases
            if not case.success
        ]

    @property
    def violated_cases(self) -> List[ContingencyCaseResult]:
        """
        Return successfully solved cases containing violations.
        """

        return [
            case
            for case in self.cases
            if case.success and case.violations
        ]


# =====================================================================
# CONTINGENCY ANALYSIS
# =====================================================================


class ContingencyAnalysis:
    """
    Public facade for N-1 / N-k contingency studies.

    Parameters
    ----------
    network:
        Authoritative GridForge Network.

    Notes
    -----
    The supplied Network is never modified by the contingency study.

    Each contingency is executed on a deep-copied Network instance.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(self, network: Any) -> None:

        self.network = network

        self._validate_network()

        self._prepared_cases: List[Tuple[Any, ...]] = []

        self._result: Optional[ContingencyResult] = None

    # =================================================================
    # PUBLIC API
    # =================================================================

    def run(
        self,
        elements: Optional[Sequence[Any]] = None,
        *,
        contingency_type: str = "N-1",
        element_types: Optional[Sequence[str]] = None,
        power_flow_options: Optional[Any] = None,
        voltage_min: float = 0.95,
        voltage_max: float = 1.05,
        thermal_limit: float = 100.0,
    ) -> ContingencyResult:
        """
        Execute a contingency study.

        Parameters
        ----------
        elements:
            Optional sequence of element IDs.

            If omitted, all in-service lines and transformers are
            considered for N-1 analysis.

        contingency_type:
            ``"N-1"`` or ``"N-k"``.

        element_types:
            Optional filter:

                ``"line"``
                ``"transformer"``

        power_flow_options:
            Optional SolverOptions instance passed to
            PowerFlowAnalysis.

        voltage_min:
            Minimum acceptable bus voltage magnitude in pu.

        voltage_max:
            Maximum acceptable bus voltage magnitude in pu.

        thermal_limit:
            Default thermal loading limit in percent.

        Returns
        -------
        ContingencyResult
            Complete contingency-study result.
        """

        cases = self.prepare(
            elements=elements,
            contingency_type=contingency_type,
            element_types=element_types,
        )

        raw_cases = []

        for outages in cases:

            raw_cases.append(
                self._run_case(
                    outages=outages,
                    power_flow_options=power_flow_options,
                    voltage_min=voltage_min,
                    voltage_max=voltage_max,
                    thermal_limit=thermal_limit,
                )
            )

        result = self.post_process(raw_cases)

        self._result = result

        return result

    # =================================================================
    # PREPARATION
    # =================================================================

    def prepare(
        self,
        *,
        elements: Optional[Sequence[Any]] = None,
        contingency_type: str = "N-1",
        element_types: Optional[Sequence[str]] = None,
    ) -> List[Tuple[Any, ...]]:
        """
        Prepare contingency cases.

        N-1 produces one outage per selected element.

        N-k produces combinations of k selected elements.

        The actual network is never modified during preparation.
        """

        normalized_type = contingency_type.upper().replace(
            " ",
            "",
        )

        if normalized_type == "N-1":
            k = 1

        elif normalized_type.startswith("N-"):

            try:
                k = int(normalized_type[2:])

            except ValueError as exc:
                raise ValueError(
                    f"Invalid contingency type: "
                    f"{contingency_type!r}."
                ) from exc

            if k < 1:
                raise ValueError(
                    "Contingency order must be at least 1."
                )

        else:
            raise ValueError(
                "Unsupported contingency type. "
                "Use 'N-1' or 'N-k'."
            )

        candidates = self._get_candidates(
            elements=elements,
            element_types=element_types,
        )

        if len(candidates) < k:
            raise ValueError(
                f"N-{k} contingency analysis requires at least "
                f"{k} candidate elements; "
                f"only {len(candidates)} are available."
            )

        cases = list(
            combinations(candidates, k)
        )

        self._prepared_cases = cases

        return cases

    # =================================================================
    # CASE EXECUTION
    # =================================================================

    def _run_case(
        self,
        *,
        outages: Tuple[Any, ...],
        power_flow_options: Optional[Any],
        voltage_min: float,
        voltage_max: float,
        thermal_limit: float,
    ) -> ContingencyCaseResult:
        """
        Execute one isolated contingency case.
        """

        case_id = self._make_case_id(outages)

        case_result = ContingencyCaseResult(
            case_id=case_id,
            outages=outages,
        )

        try:

            outage_network = self._create_outage_case(
                outages
            )

            power_flow = PowerFlowAnalysis(
                outage_network,
                options=power_flow_options,
            )

            power_flow_result = power_flow.solve()

            case_result.power_flow_result = (
                power_flow_result
            )

            case_result.success = True

            case_result.converged = (
                self._result_converged(
                    power_flow_result
                )
            )

            case_result.violations = (
                self._detect_violations(
                    outage_network,
                    power_flow_result,
                    voltage_min=voltage_min,
                    voltage_max=voltage_max,
                    thermal_limit=thermal_limit,
                )
            )

        except Exception as exc:

            case_result.success = False
            case_result.converged = False
            case_result.error = str(exc)

        return case_result

    # =================================================================
    # NON-DESTRUCTIVE OUTAGE CREATION
    # =================================================================

    def _create_outage_case(
        self,
        outages: Tuple[Any, ...],
    ) -> Any:
        """
        Create an isolated Network for a contingency case.

        The authoritative Network is never modified.

        The copied Network uses its own Network.set_element_status()
        method so that topology/Y-bus invalidation follows the
        canonical Network lifecycle.
        """

        outage_network = copy.deepcopy(
            self.network
        )

        for element_id in outages:

            element = self._find_element(
                outage_network,
                element_id,
            )

            if element is None:
                raise KeyError(
                    f"Contingency element "
                    f"{element_id!r} was not found "
                    "in the copied Network."
                )

            outage_network.set_element_status(
                element,
                False,
            )

        return outage_network

    # =================================================================
    # CANDIDATE DISCOVERY
    # =================================================================

    def _get_candidates(
        self,
        *,
        elements: Optional[Sequence[Any]],
        element_types: Optional[Sequence[str]],
    ) -> List[Any]:
        """
        Return valid contingency candidate IDs.

        By default, all in-service lines and transformers are
        candidates.

        Generators, loads, buses and shunts are intentionally not
        treated as branch contingencies in v1.0.
        """

        normalized_types = None

        if element_types is not None:

            normalized_types = {
                str(item).lower()
                for item in element_types
            }

            valid_types = {
                "line",
                "transformer",
            }

            invalid = normalized_types - valid_types

            if invalid:
                raise ValueError(
                    "Unsupported contingency element type(s): "
                    f"{sorted(invalid)}"
                )

        available: Dict[Any, str] = {}

        if (
            normalized_types is None
            or "line" in normalized_types
        ):

            for line in self.network.lines:

                if getattr(
                    line,
                    "in_service",
                    True,
                ):
                    available[line.id] = "line"

        if (
            normalized_types is None
            or "transformer" in normalized_types
        ):

            for transformer in self.network.transformers:

                if getattr(
                    transformer,
                    "in_service",
                    True,
                ):
                    available[transformer.id] = (
                        "transformer"
                    )

        if elements is None:
            return list(available.keys())

        requested = list(elements)

        if len(requested) != len(set(requested)):
            raise ValueError(
                "Duplicate contingency element IDs "
                "are not permitted."
            )

        missing = [
            element_id
            for element_id in requested
            if element_id not in available
        ]

        if missing:
            raise KeyError(
                "Unknown or out-of-service contingency "
                f"element(s): {missing}"
            )

        return requested

    # =================================================================
    # ELEMENT LOOKUP
    # =================================================================

    @staticmethod
    def _find_element(
        network: Any,
        element_id: Any,
    ) -> Optional[Any]:
        """
        Locate a line or transformer by ID.
        """

        for line in network.lines:

            if line.id == element_id:
                return line

        for transformer in network.transformers:

            if transformer.id == element_id:
                return transformer

        return None

    # =================================================================
    # POST-PROCESSING
    # =================================================================

    def post_process(
        self,
        cases: Iterable[ContingencyCaseResult],
    ) -> ContingencyResult:
        """
        Aggregate individual contingency cases.
        """

        result = ContingencyResult(
            cases=list(cases)
        )

        result.success = all(
            case.success
            for case in result.cases
        )

        result.converged = all(
            case.success and case.converged
            for case in result.cases
        )

        for case in result.cases:

            if case.violations:

                result.critical_cases.append(
                    case.case_id
                )

                result.critical_violations.extend(
                    case.violations
                )

        return result

    # =================================================================
    # VIOLATION DETECTION
    # =================================================================

    def _detect_violations(
        self,
        network: Any,
        power_flow_result: Any,
        *,
        voltage_min: float,
        voltage_max: float,
        thermal_limit: float,
    ) -> List[ContingencyViolation]:
        """
        Detect post-contingency engineering violations.

        This method intentionally consumes the result of the
        numerical power-flow solver. It does not perform any
        power-flow mathematics.
        """

        violations: List[
            ContingencyViolation
        ] = []

        # -------------------------------------------------------------
        # VOLTAGE VIOLATIONS
        # -------------------------------------------------------------

        voltage = self._extract_result_value(
            power_flow_result,
            "bus_voltage",
        )

        if voltage is not None:

            violations.extend(
                self._detect_voltage_violations(
                    network,
                    voltage,
                    voltage_min,
                    voltage_max,
                )
            )

        # -------------------------------------------------------------
        # THERMAL / LINE LOADING VIOLATIONS
        # -------------------------------------------------------------

        loading = self._extract_result_value(
            power_flow_result,
            "line_loading",
        )

        if loading is not None:

            violations.extend(
                self._detect_loading_violations(
                    network,
                    loading,
                    thermal_limit,
                )
            )

        return violations

    # =================================================================
    # VOLTAGE VIOLATIONS
    # =================================================================

    @staticmethod
    def _detect_voltage_violations(
        network: Any,
        voltage: Any,
        voltage_min: float,
        voltage_max: float,
    ) -> List[ContingencyViolation]:
        """
        Detect bus voltage magnitude violations.
        """

        violations: List[
            ContingencyViolation
        ] = []

        try:
            values = list(voltage)

        except TypeError:
            return violations

        buses = network.buses

        for index, value in enumerate(values):

            if index >= len(buses):
                break

            bus = buses[index]

            try:
                numeric_value = float(value)

            except (TypeError, ValueError):
                continue

            if numeric_value < voltage_min:

                violations.append(
                    ContingencyViolation(
                        category="voltage_low",
                        element_id=bus.id,
                        value=numeric_value,
                        limit=voltage_min,
                    )
                )

            elif numeric_value > voltage_max:

                violations.append(
                    ContingencyViolation(
                        category="voltage_high",
                        element_id=bus.id,
                        value=numeric_value,
                        limit=voltage_max,
                    )
                )

        return violations

    # =================================================================
    # THERMAL VIOLATIONS
    # =================================================================

    @staticmethod
    def _detect_loading_violations(
        network: Any,
        loading: Any,
        thermal_limit: float,
    ) -> List[ContingencyViolation]:
        """
        Detect line loading violations.

        The default v1.0 threshold is 100 percent unless a more
        detailed result/limit is supplied by the solver/model layer.
        """

        violations: List[
            ContingencyViolation
        ] = []

        try:
            values = list(loading)

        except TypeError:
            return violations

        lines = network.lines

        for index, value in enumerate(values):

            if index >= len(lines):
                break

            line = lines[index]

            try:
                numeric_value = float(value)

            except (TypeError, ValueError):
                continue

            limit = getattr(
                line,
                "loading_limit",
                thermal_limit,
            )

            if numeric_value > limit:

                violations.append(
                    ContingencyViolation(
                        category="thermal",
                        element_id=line.id,
                        value=numeric_value,
                        limit=float(limit),
                    )
                )

        return violations

    # =================================================================
    # RESULT HELPERS
    # =================================================================

    @staticmethod
    def _extract_result_value(
        result: Any,
        name: str,
    ) -> Any:
        """
        Extract a result field from either an object-style or
        dictionary-style solver result.

        This compatibility boundary allows the analysis layer to
        consume the current solver result without dictifying the
        numerical solver interface.
        """

        if result is None:
            return None

        if isinstance(result, dict):
            return result.get(name)

        return getattr(
            result,
            name,
            None,
        )

    @classmethod
    def _result_converged(
        cls,
        result: Any,
    ) -> bool:
        """
        Determine whether the numerical power-flow result converged.
        """

        value = cls._extract_result_value(
            result,
            "converged",
        )

        if value is None:
            # If the numerical result does not expose a convergence
            # flag, successful completion is not automatically
            # interpreted as convergence.
            return False

        return bool(value)

    # =================================================================
    # CASE IDENTIFICATION
    # =================================================================

    @staticmethod
    def _make_case_id(
        outages: Tuple[Any, ...],
    ) -> str:
        """
        Create deterministic contingency case identifier.
        """

        return "N-{}:{}".format(
            len(outages),
            "+".join(
                str(item)
                for item in outages
            ),
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_network(self) -> None:
        """
        Validate the minimum Network interface required for
        contingency analysis.

        Engineering validation remains outside Network.
        """

        if self.network is None:
            raise ValueError(
                "Contingency Analysis requires "
                "a valid Network."
            )

        required = (
            "buses",
            "lines",
            "transformers",
            "rebuild_bus_index",
            "set_element_status",
        )

        for attribute in required:

            if not hasattr(
                self.network,
                attribute,
            ):
                raise ValueError(
                    "Network is missing required "
                    f"attribute or method '{attribute}'."
                )

        if not self.network.buses:
            raise ValueError(
                "Contingency Analysis requires "
                "at least one bus."
            )

    # =================================================================
    # RESULT ACCESS
    # =================================================================

    @property
    def result(self) -> Optional[ContingencyResult]:
        """
        Return the latest contingency-study result.
        """

        return self._result


__all__ = [
    "ContingencyAnalysis",
    "ContingencyResult",
    "ContingencyCaseResult",
    "ContingencyViolation",
]
```
