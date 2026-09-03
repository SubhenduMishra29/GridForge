"""
GridForge - Contingency Analysis
================================

File:
    core/analysis/contingency.py

Purpose:
    Public analysis-level facade for contingency studies.

Scope:
    - N-1 contingency analysis
    - N-k contingency architecture
    - Non-destructive outage simulation
    - Power-flow based post-contingency assessment
    - Voltage and thermal violation detection
    - Study-level result aggregation

Architecture
------------

    Authoritative Network
            |
            v
    ContingencyAnalysis
            |
            +---- isolated case Network
            |          |
            |          v
            |    PowerFlowStudyConfiguration
            |          |
            |          v
            |    PowerFlowPreparation
            |          |
            |          v
            |    PowerFlowAnalysis
            |          |
            |          v
            |    core/solver/power_flow/
            |
            v
    ContingencyResult

IMPORTANT STATE-ISOLATION CONTRACT
----------------------------------

The Network supplied to ContingencyAnalysis is authoritative.

A contingency study MUST NOT modify it.

Every contingency case therefore operates on a completely
isolated deep copy of the authoritative Network.

Outage status is applied only to the copied case Network.

PowerFlowPreparation and PowerFlowAnalysis operate only on the
isolated case Network and its prepared numerical contracts.

The authoritative Network is never passed to:

    - set_element_status()
    - PowerFlowAnalysis
    - contingency-case numerical execution

Numerical mathematics remains outside this module.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from math import isfinite
from typing import Any, Iterable, List, Optional, Sequence, Tuple
import copy

from core.analysis.power_flow import PowerFlowAnalysis
from core.solver.power_flow.preparation import PowerFlowPreparation
from core.solver.power_flow.study_configuration import PowerFlowStudyConfiguration


# =====================================================================
# RESULT TYPES
# =====================================================================


@dataclass
class ContingencyViolation:
    """
    Single post-contingency engineering violation.

    Parameters
    ----------
    category:
        Violation category.

    element_id:
        ID of the affected bus or network element.

    value:
        Calculated engineering value.

    limit:
        Applicable engineering limit.

    severity:
        Positive violation magnitude.
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
        """Return cases for which execution failed."""

        return [
            case
            for case in self.cases
            if not case.success
        ]

    @property
    def violated_cases(self) -> List[ContingencyCaseResult]:
        """Return successfully executed cases containing violations."""

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

    power_flow_configuration:
        Optional reusable study-level power-flow configuration. A
        configuration is required when ``run()`` executes power flow.
        The same instance is reused for every isolated contingency case.

    Notes
    -----
    The supplied Network is never modified by this analysis.

    Every contingency case receives its own isolated deep-copied
    Network before outage state is applied.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        network: Any,
        power_flow_configuration: Optional[PowerFlowStudyConfiguration] = None,
    ) -> None:
        self.network = network
        self.power_flow_configuration = power_flow_configuration

        self._validate_network()

        if power_flow_configuration is not None and not isinstance(
            power_flow_configuration,
            PowerFlowStudyConfiguration,
        ):
            raise TypeError(
                "power_flow_configuration must be PowerFlowStudyConfiguration."
            )

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
            Optional sequence of line/transformer IDs.

            If omitted, all in-service lines and transformers
            are considered.

        contingency_type:
            "N-1" or "N-k".

        element_types:
            Optional element-type filter.

            Supported:
                "line"
                "transformer"

        power_flow_options:
            SolverOptions passed to PowerFlowAnalysis.

        voltage_min:
            Minimum acceptable bus voltage in pu.

        voltage_max:
            Maximum acceptable bus voltage in pu.

        thermal_limit:
            Default thermal loading limit in percent.

        Returns
        -------
        ContingencyResult
            Complete contingency-study result.

        State Safety
        ------------
        The authoritative Network is never modified.
        """

        self._validate_limits(
            voltage_min=voltage_min,
            voltage_max=voltage_max,
            thermal_limit=thermal_limit,
        )

        if self.power_flow_configuration is None:
            raise ValueError(
                "ContingencyAnalysis requires a PowerFlowStudyConfiguration "
                "to execute power-flow based contingency cases."
            )

        cases = self.prepare(
            elements=elements,
            contingency_type=contingency_type,
            element_types=element_types,
        )

        case_results: List[ContingencyCaseResult] = []

        for outages in cases:
            case_results.append(
                self._run_case(
                    outages=outages,
                    power_flow_options=power_flow_options,
                    voltage_min=voltage_min,
                    voltage_max=voltage_max,
                    thermal_limit=thermal_limit,
                )
            )

        result = self.post_process(case_results)

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

        N-1:
            One outage per selected element.

        N-k:
            All k-element combinations of selected elements.

        The authoritative Network is never modified.
        """

        k = self._parse_contingency_order(
            contingency_type
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

        The authoritative Network is never used for case mutation.
        """

        case_result = ContingencyCaseResult(
            case_id=self._make_case_id(outages),
            outages=outages,
        )

        try:
            # ---------------------------------------------------------
            # CRITICAL ARCHITECTURAL BOUNDARY
            # ---------------------------------------------------------
            #
            # _create_outage_case() MUST return an independent copy.
            # Everything below operates exclusively on that copy.
            # ---------------------------------------------------------

            case_network = self._create_outage_case(
                outages
            )

            prepared = PowerFlowPreparation(
                case_network,
                self.power_flow_configuration,
            ).prepare()

            power_flow = PowerFlowAnalysis(
                prepared.input,
                prepared.ybus,
                options=power_flow_options,
            )

            power_flow_result = power_flow.solve()

            case_result.power_flow_result = (
                power_flow_result
            )

            case_result.converged = (
                self._result_converged(
                    power_flow_result
                )
            )

            case_result.success = True

            case_result.violations = (
                self._detect_violations(
                    case_network,
                    power_flow_result,
                    voltage_min=voltage_min,
                    voltage_max=voltage_max,
                    thermal_limit=thermal_limit,
                )
            )

        except Exception as exc:
            case_result.success = False
            case_result.converged = False
            case_result.error = (
                f"{type(exc).__name__}: {exc}"
            )

        return case_result

    # =================================================================
    # NON-DESTRUCTIVE OUTAGE CREATION
    # =================================================================

    def _create_outage_case(
        self,
        outages: Tuple[Any, ...],
    ) -> Any:
        """
        Create a completely isolated Network for one contingency.

        IMPORTANT
        ---------
        The authoritative Network is deep-copied BEFORE any outage
        state is changed.

        No mutation is ever performed on self.network.
        """

        case_network = copy.deepcopy(
            self.network
        )

        for element_id in outages:
            element = self._find_element(
                case_network,
                element_id,
            )

            if element is None:
                raise KeyError(
                    f"Contingency element "
                    f"{element_id!r} was not found "
                    "in the isolated case Network."
                )

            # ---------------------------------------------------------
            # Mutation occurs ONLY on the copied Network.
            # ---------------------------------------------------------

            case_network.set_element_status(
                element,
                False,
            )

        return case_network

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

        v1.0 supports:

            - Line
            - Transformer

        Only currently in-service elements are candidates.
        """

        normalized_types = self._normalize_element_types(
            element_types
        )

        available: List[Any] = []

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
                    available.append(line.id)

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
                    available.append(transformer.id)

        # -------------------------------------------------------------
        # No explicit selection:
        # use every valid in-service candidate.
        # -------------------------------------------------------------

        if elements is None:
            return available

        requested = list(elements)

        try:
            unique_requested = set(requested)
        except TypeError as exc:
            raise ValueError(
                "Contingency element IDs must be hashable."
            ) from exc

        if len(requested) != len(unique_requested):
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
    # ELEMENT-TYPE NORMALIZATION
    # =================================================================

    @staticmethod
    def _normalize_element_types(
        element_types: Optional[Sequence[str]],
    ) -> Optional[set[str]]:
        """
        Normalize and validate contingency element types.
        """

        if element_types is None:
            return None

        normalized = {
            str(item).strip().lower()
            for item in element_types
        }

        valid_types = {
            "line",
            "transformer",
        }

        invalid = normalized - valid_types

        if invalid:
            raise ValueError(
                "Unsupported contingency element type(s): "
                f"{sorted(invalid)}"
            )

        if not normalized:
            raise ValueError(
                "element_types cannot be empty."
            )

        return normalized

    # =================================================================
    # CONTINGENCY ORDER
    # =================================================================

    @staticmethod
    def _parse_contingency_order(
        contingency_type: str,
    ) -> int:
        """
        Parse:

            N-1
            N-2
            N-3
            ...

        """

        normalized = (
            str(contingency_type)
            .strip()
            .upper()
            .replace(" ", "")
        )

        if not normalized.startswith("N-"):
            raise ValueError(
                "Unsupported contingency type. "
                "Use 'N-1' or 'N-k', for example 'N-2'."
            )

        try:
            k = int(normalized[2:])
        except ValueError as exc:
            raise ValueError(
                f"Invalid contingency type: "
                f"{contingency_type!r}."
            ) from exc

        if k < 1:
            raise ValueError(
                "Contingency order must be at least 1."
            )

        return k

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

        if not result.cases:
            return result

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

        No power-flow numerical calculations are performed here.
        """

        violations: List[ContingencyViolation] = []

        # -------------------------------------------------------------
        # BUS VOLTAGE
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
        # LINE LOADING
        # -------------------------------------------------------------

        line_loading = self._extract_result_value(
            power_flow_result,
            "line_loading",
        )

        if line_loading is not None:
            violations.extend(
                self._detect_loading_violations(
                    network,
                    line_loading,
                    thermal_limit,
                )
            )

        # -------------------------------------------------------------
        # TRANSFORMER LOADING
        # -------------------------------------------------------------

        transformer_loading = (
            self._extract_result_value(
                power_flow_result,
                "transformer_loading",
            )
        )

        if transformer_loading is not None:
            violations.extend(
                self._detect_transformer_loading_violations(
                    network,
                    transformer_loading,
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
        Detect bus-voltage magnitude violations.

        Voltage values are expected in per-unit and in the same
        stable bus ordering used by the Power Flow result.
        """

        violations: List[ContingencyViolation] = []

        try:
            values = list(voltage)
        except TypeError:
            return violations

        buses = list(network.buses)

        for index, value in enumerate(values):

            if index >= len(buses):
                break

            bus = buses[index]

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue

            if not isfinite(numeric_value):
                continue

            if numeric_value < voltage_min:
                violations.append(
                    ContingencyViolation(
                        category="voltage_low",
                        element_id=bus.id,
                        value=numeric_value,
                        limit=voltage_min,
                        severity=(
                            voltage_min - numeric_value
                        ),
                    )
                )

            elif numeric_value > voltage_max:
                violations.append(
                    ContingencyViolation(
                        category="voltage_high",
                        element_id=bus.id,
                        value=numeric_value,
                        limit=voltage_max,
                        severity=(
                            numeric_value - voltage_max
                        ),
                    )
                )

        return violations

    # =================================================================
    # LINE THERMAL VIOLATIONS
    # =================================================================

    @staticmethod
    def _detect_loading_violations(
        network: Any,
        loading: Any,
        thermal_limit: float,
    ) -> List[ContingencyViolation]:
        """
        Detect line-loading violations.

        Loading is expected in percent.
        """

        violations: List[ContingencyViolation] = []

        try:
            values = list(loading)
        except TypeError:
            return violations

        lines = list(network.lines)

        for index, value in enumerate(values):

            if index >= len(lines):
                break

            line = lines[index]

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue

            if not isfinite(numeric_value):
                continue

            limit = getattr(
                line,
                "loading_limit",
                thermal_limit,
            )

            try:
                limit = float(limit)
            except (TypeError, ValueError):
                limit = thermal_limit

            if not isfinite(limit):
                limit = thermal_limit

            if numeric_value > limit:
                violations.append(
                    ContingencyViolation(
                        category="thermal",
                        element_id=line.id,
                        value=numeric_value,
                        limit=limit,
                        severity=(
                            numeric_value - limit
                        ),
                    )
                )

        return violations

    # =================================================================
    # TRANSFORMER THERMAL VIOLATIONS
    # =================================================================

    @staticmethod
    def _detect_transformer_loading_violations(
        network: Any,
        loading: Any,
        thermal_limit: float,
    ) -> List[ContingencyViolation]:
        """
        Detect transformer-loading violations.

        Transformer electrical calculations are not performed here.
        """

        violations: List[ContingencyViolation] = []

        try:
            values = list(loading)
        except TypeError:
            return violations

        transformers = list(
            network.transformers
        )

        for index, value in enumerate(values):

            if index >= len(transformers):
                break

            transformer = transformers[index]

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue

            if not isfinite(numeric_value):
                continue

            limit = getattr(
                transformer,
                "loading_limit",
                thermal_limit,
            )

            try:
                limit = float(limit)
            except (TypeError, ValueError):
                limit = thermal_limit

            if not isfinite(limit):
                limit = thermal_limit

            if numeric_value > limit:
                violations.append(
                    ContingencyViolation(
                        category="transformer_thermal",
                        element_id=transformer.id,
                        value=numeric_value,
                        limit=limit,
                        severity=(
                            numeric_value - limit
                        ),
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
        Extract a result field from either:

            - dictionary-style result
            - object-style result

        This is the compatibility boundary between the Analysis
        Layer and solver result representations.
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
        Determine whether the power-flow result converged.
        """

        value = cls._extract_result_value(
            result,
            "converged",
        )

        if value is None:
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
    # LIMIT VALIDATION
    # =================================================================

    @staticmethod
    def _validate_limits(
        *,
        voltage_min: float,
        voltage_max: float,
        thermal_limit: float,
    ) -> None:
        """
        Validate engineering limits.
        """

        try:
            v_min = float(voltage_min)
            v_max = float(voltage_max)
            thermal = float(thermal_limit)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Voltage and thermal limits must be numeric."
            ) from exc

        if not (
            isfinite(v_min)
            and isfinite(v_max)
            and isfinite(thermal)
        ):
            raise ValueError(
                "Voltage and thermal limits must be finite."
            )

        if v_min < 0.0:
            raise ValueError(
                "voltage_min cannot be negative."
            )

        if v_max <= v_min:
            raise ValueError(
                "voltage_max must be greater than "
                "voltage_min."
            )

        if thermal < 0.0:
            raise ValueError(
                "thermal_limit cannot be negative."
            )

    # =================================================================
    # NETWORK VALIDATION
    # =================================================================

    def _validate_network(self) -> None:
        """
        Validate the minimum public Network interface required
        by contingency analysis.
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
            "set_element_status",
        )

        for attribute in required:
            if not hasattr(
                self.network,
                attribute,
            ):
                raise ValueError(
                    "Network is missing required "
                    f"attribute or method "
                    f"'{attribute}'."
                )

        if len(self.network.buses) == 0:
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


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ContingencyAnalysis",
    "ContingencyResult",
    "ContingencyCaseResult",
    "ContingencyViolation",
]
