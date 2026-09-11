"""Contingency analysis over isolated Network cases and prepared Power Flow results."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from math import isfinite
from typing import Any, Iterable, List, Optional, Sequence, Tuple
import copy

from core.analysis.power_flow import PowerFlowAnalysis
from core.analysis.line_flow import LineFlowCalculator
from core.analysis.transformer_flow import TransformerFlowCalculator
from core.network.endpoint import resolve_terminal_bus
from core.solver.power_flow.preparation import PowerFlowPreparation, PreparedPowerFlow
from core.solver.power_flow.study_configuration import PowerFlowStudyConfiguration


@dataclass
class ContingencyViolation:
    category: str
    element_id: Any
    value: Optional[float] = None
    limit: Optional[float] = None
    severity: Optional[float] = None


@dataclass
class ContingencyCaseResult:
    case_id: str
    outages: Tuple[Any, ...]
    success: bool = False
    converged: bool = False
    power_flow_result: Any = None
    violations: List[ContingencyViolation] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ContingencyResult:
    cases: List[ContingencyCaseResult] = field(default_factory=list)
    success: bool = False
    converged: bool = False
    critical_cases: List[str] = field(default_factory=list)
    critical_violations: List[ContingencyViolation] = field(default_factory=list)

    @property
    def failed_cases(self) -> List[ContingencyCaseResult]:
        return [case for case in self.cases if not case.success]

    @property
    def violated_cases(self) -> List[ContingencyCaseResult]:
        return [case for case in self.cases if case.success and case.violations]


class ContingencyAnalysis:
    """Public N-1/N-k contingency facade using the canonical Power Flow boundary."""

    def __init__(self, network: Any, power_flow_configuration: Optional[PowerFlowStudyConfiguration] = None) -> None:
        self.network = network
        self.power_flow_configuration = power_flow_configuration
        self._validate_network()
        if power_flow_configuration is not None and not isinstance(power_flow_configuration, PowerFlowStudyConfiguration):
            raise TypeError("power_flow_configuration must be PowerFlowStudyConfiguration.")
        self._prepared_cases: List[Tuple[Any, ...]] = []
        self._result: Optional[ContingencyResult] = None

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
        self._validate_limits(voltage_min=voltage_min, voltage_max=voltage_max, thermal_limit=thermal_limit)
        if self.power_flow_configuration is None:
            raise ValueError("ContingencyAnalysis requires a PowerFlowStudyConfiguration to execute power-flow based contingency cases.")
        cases = self.prepare(elements=elements, contingency_type=contingency_type, element_types=element_types)
        result = self.post_process([
            self._run_case(
                outages=outages,
                power_flow_options=power_flow_options,
                voltage_min=voltage_min,
                voltage_max=voltage_max,
                thermal_limit=thermal_limit,
            )
            for outages in cases
        ])
        self._result = result
        return result

    def prepare(
        self,
        *,
        elements: Optional[Sequence[Any]] = None,
        contingency_type: str = "N-1",
        element_types: Optional[Sequence[str]] = None,
    ) -> List[Tuple[Any, ...]]:
        k = self._parse_contingency_order(contingency_type)
        candidates = self._get_candidates(elements=elements, element_types=element_types)
        if len(candidates) < k:
            raise ValueError(f"N-{k} contingency analysis requires at least {k} candidate elements; only {len(candidates)} are available.")
        self._prepared_cases = list(combinations(candidates, k))
        return self._prepared_cases

    def _run_case(
        self,
        *,
        outages: Tuple[Any, ...],
        power_flow_options: Optional[Any],
        voltage_min: float,
        voltage_max: float,
        thermal_limit: float,
    ) -> ContingencyCaseResult:
        case_result = ContingencyCaseResult(case_id=self._make_case_id(outages), outages=outages)
        try:
            case_network = self._create_outage_case(outages)
            prepared = PowerFlowPreparation(case_network, self.power_flow_configuration).prepare()
            power_flow = PowerFlowAnalysis(prepared.input, prepared.ybus, options=power_flow_options, prepared=prepared)
            power_flow_result = power_flow.solve()
            case_result.power_flow_result = power_flow_result
            case_result.success = bool(power_flow_result.success)
            case_result.converged = bool(power_flow_result.success)
            if not case_result.success:
                case_result.error = str(power_flow_result.message)
                return case_result
            case_result.violations = self._detect_violations(
                case_network,
                prepared,
                power_flow_result,
                voltage_min=voltage_min,
                voltage_max=voltage_max,
                thermal_limit=thermal_limit,
            )
        except Exception as exc:
            case_result.error = f"{type(exc).__name__}: {exc}"
        return case_result

    def _create_outage_case(self, outages: Tuple[Any, ...]) -> Any:
        case_network = copy.deepcopy(self.network)
        for element_id in outages:
            element = self._find_element(case_network, element_id)
            if element is None:
                raise KeyError(f"Contingency element {element_id!r} was not found in the isolated case Network.")
            if self._is_bus(element):
                self._set_in_service(element, False)
                self._disable_connected_equipment(case_network, element)
            else:
                self._set_in_service(element, False)
        return case_network

    @staticmethod
    def _is_bus(element: Any) -> bool:
        return type(element).__name__.lower() == "bus"

    @staticmethod
    def _set_in_service(element: Any, in_service: bool) -> None:
        if not hasattr(element, "in_service"):
            raise TypeError(f"Contingency element {element!r} has no in_service state.")
        try:
            element.in_service = bool(in_service)
        except AttributeError:
            setter = getattr(element, "set_in_service", None)
            if setter is None:
                raise
            setter(bool(in_service))

    @classmethod
    def _disable_connected_equipment(cls, network: Any, bus: Any) -> None:
        for collection_name in ("lines", "transformers", "generators", "loads", "shunts", "cables"):
            for element in getattr(network, collection_name, ()):
                if cls._element_connected_to_bus(element, bus):
                    cls._set_in_service(element, False)

    @staticmethod
    def _element_connected_to_bus(element: Any, bus: Any) -> bool:
        terminals = getattr(element, "terminals", None)
        if terminals is None:
            terminal = getattr(element, "terminal", None)
            terminals = (terminal,) if terminal is not None else ()
        for terminal in terminals:
            if terminal is None:
                continue
            try:
                resolved_bus = resolve_terminal_bus(terminal)
            except (TypeError, ValueError):
                continue
            if resolved_bus is bus:
                return True
            if getattr(resolved_bus, "id", None) == getattr(bus, "id", None):
                return True
        return False

    def _get_candidates(self, *, elements: Optional[Sequence[Any]], element_types: Optional[Sequence[str]]) -> List[Any]:
        normalized_types = self._normalize_element_types(element_types)
        available: List[Any] = []
        for element_type, collection in (
            ("bus", self.network.buses),
            ("line", self.network.lines),
            ("transformer", self.network.transformers),
            ("generator", self.network.generators),
            ("load", self.network.loads),
            ("shunt", self.network.shunts),
        ):
            if normalized_types is not None and element_type not in normalized_types:
                continue
            available.extend(element.id for element in collection if getattr(element, "in_service", True))
        if elements is None:
            return available
        requested = list(elements)
        if len(requested) != len(set(requested)):
            raise ValueError("Duplicate contingency element IDs are not permitted.")
        missing = [element_id for element_id in requested if element_id not in available]
        if missing:
            raise KeyError(f"Unknown or out-of-service contingency element(s): {missing}")
        return requested

    @staticmethod
    def _normalize_element_types(element_types: Optional[Sequence[str]]) -> Optional[set[str]]:
        if element_types is None:
            return None
        normalized = {str(item).strip().lower() for item in element_types}
        valid = {"bus", "line", "transformer", "generator", "load", "shunt"}
        invalid = normalized - valid
        if invalid:
            raise ValueError(f"Unsupported contingency element type(s): {sorted(invalid)}")
        if not normalized:
            raise ValueError("element_types cannot be empty.")
        return normalized

    @staticmethod
    def _parse_contingency_order(contingency_type: str) -> int:
        normalized = str(contingency_type).strip().upper().replace(" ", "")
        if not normalized.startswith("N-"):
            raise ValueError("Unsupported contingency type. Use 'N-1' or 'N-k', for example 'N-2'.")
        try:
            k = int(normalized[2:])
        except ValueError as exc:
            raise ValueError(f"Invalid contingency type: {contingency_type!r}.") from exc
        if k < 1:
            raise ValueError("Contingency order must be at least 1.")
        return k

    @staticmethod
    def _find_element(network: Any, element_id: Any) -> Optional[Any]:
        for collection_name in ("buses", "lines", "transformers", "generators", "loads", "shunts", "cables"):
            for element in getattr(network, collection_name, ()):
                if element.id == element_id:
                    return element
        return None

    def post_process(self, cases: Iterable[ContingencyCaseResult]) -> ContingencyResult:
        result = ContingencyResult(cases=list(cases))
        if not result.cases:
            return result
        result.success = all(case.success for case in result.cases)
        result.converged = all(case.success and case.converged for case in result.cases)
        for case in result.cases:
            if case.violations:
                result.critical_cases.append(case.case_id)
                result.critical_violations.extend(case.violations)
        return result

    def _detect_violations(
        self,
        network: Any,
        prepared: PreparedPowerFlow,
        power_flow_result: Any,
        *,
        voltage_min: float,
        voltage_max: float,
        thermal_limit: float,
    ) -> List[ContingencyViolation]:
        violations: List[ContingencyViolation] = []
        voltage = tuple(power_flow_result.voltage_magnitudes)
        if len(voltage) != len(prepared.bus_ids):
            raise ValueError("PowerFlowResult voltage vector does not match prepared bus identity ordering.")
        violations.extend(self._detect_voltage_violations(prepared.bus_ids, voltage, voltage_min, voltage_max))

        line_results = LineFlowCalculator.from_prepared(prepared, network=network).calculate_all(
            tuple(vm * complex(__import__("math").cos(va), __import__("math").sin(va)) for vm, va in zip(power_flow_result.voltage_magnitudes, power_flow_result.voltage_angles))
        )
        for line_id, flow in line_results.items():
            line = next((item for item in network.lines if str(item.id) == str(line_id)), None)
            if line is None or getattr(line, "rate_mva", None) is None:
                continue
            limit = float(line.rate_mva)
            if not isfinite(limit) or limit <= 0.0:
                continue
            value = max(flow.s_from_magnitude, flow.s_to_magnitude) * prepared.base_mva / limit * 100.0
            if value > thermal_limit:
                violations.append(ContingencyViolation("thermal", line.id, value, thermal_limit, value - thermal_limit))

        transformer_results = TransformerFlowCalculator.from_prepared(prepared, network=network).calculate(
            power_flow_result.voltage_magnitudes,
            power_flow_result.voltage_angles,
        )
        for transformer_id, flow in transformer_results.items():
            transformer = next((item for item in network.transformers if str(item.id) == str(transformer_id)), None)
            if transformer is None or getattr(transformer, "rate_mva", None) is None:
                continue
            limit = float(transformer.rate_mva)
            if not isfinite(limit) or limit <= 0.0:
                continue
            value = max(flow.s_from_pu, flow.s_to_pu) * prepared.base_mva / limit * 100.0
            if value > thermal_limit:
                violations.append(ContingencyViolation("transformer_thermal", transformer.id, value, thermal_limit, value - thermal_limit))
        return violations

    @staticmethod
    def _detect_voltage_violations(bus_ids: Sequence[str], voltage: Sequence[Any], voltage_min: float, voltage_max: float) -> List[ContingencyViolation]:
        violations: List[ContingencyViolation] = []
        for bus_id, value in zip(bus_ids, voltage):
            numeric = float(value)
            if not isfinite(numeric):
                continue
            if numeric < voltage_min:
                violations.append(ContingencyViolation("voltage_low", bus_id, numeric, voltage_min, voltage_min - numeric))
            elif numeric > voltage_max:
                violations.append(ContingencyViolation("voltage_high", bus_id, numeric, voltage_max, numeric - voltage_max))
        return violations

    @classmethod
    def _extract_result_value(cls, result: Any, name: str) -> Any:
        if result is None:
            return None
        if isinstance(result, dict):
            return result.get(name)
        return getattr(result, name, None)

    @classmethod
    def _result_converged(cls, result: Any) -> bool:
        success = cls._extract_result_value(result, "success")
        if success is not None:
            return bool(success)
        legacy = cls._extract_result_value(result, "converged")
        return bool(legacy) if legacy is not None else False

    @staticmethod
    def _make_case_id(outages: Tuple[Any, ...]) -> str:
        return "N-{}:{}".format(len(outages), "+".join(str(item) for item in outages))

    @staticmethod
    def _validate_limits(*, voltage_min: float, voltage_max: float, thermal_limit: float) -> None:
        try:
            v_min, v_max, thermal = float(voltage_min), float(voltage_max), float(thermal_limit)
        except (TypeError, ValueError) as exc:
            raise ValueError("Voltage and thermal limits must be numeric.") from exc
        if not all(isfinite(value) for value in (v_min, v_max, thermal)):
            raise ValueError("Voltage and thermal limits must be finite.")
        if v_min < 0.0:
            raise ValueError("voltage_min cannot be negative.")
        if v_max <= v_min:
            raise ValueError("voltage_max must be greater than voltage_min.")
        if thermal < 0.0:
            raise ValueError("thermal_limit cannot be negative.")

    def _validate_network(self) -> None:
        if self.network is None:
            raise ValueError("Contingency Analysis requires a valid Network.")
        for attribute in ("buses", "lines", "transformers", "generators", "loads", "shunts"):
            if not hasattr(self.network, attribute):
                raise ValueError(f"Network is missing required attribute or method '{attribute}'.")
        if len(self.network.buses) == 0:
            raise ValueError("Contingency Analysis requires at least one bus.")

    @property
    def result(self) -> Optional[ContingencyResult]:
        return self._result


__all__ = ["ContingencyAnalysis", "ContingencyResult", "ContingencyCaseResult", "ContingencyViolation"]
