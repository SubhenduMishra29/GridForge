"""Application-executable, explicitly configured IDMT coordination studies.

The study consumes relay-input currents supplied for each protection
function. It never infers primary/backup relationships or CT conversions.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Any, Mapping

from core.protection.coordination.relay_coordination import (
    CoordinationResult,
    RelayCoordination,
)
from core.protection.relay_functions import iec_time


def _identity(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()


def _positive(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric, not boolean.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and positive.")
    return result


@dataclass(frozen=True, slots=True)
class CoordinationStudyPair:
    """Explicit primary/backup protection-function identity pair."""

    primary_element_id: str
    backup_element_id: str

    def __post_init__(self) -> None:
        primary = _identity(self.primary_element_id, "primary_element_id")
        backup = _identity(self.backup_element_id, "backup_element_id")
        if primary == backup:
            raise ValueError("Primary and backup protection elements must differ.")
        object.__setattr__(self, "primary_element_id", primary)
        object.__setattr__(self, "backup_element_id", backup)


@dataclass(frozen=True, slots=True)
class CoordinationRelayCurrent:
    """One explicit relay-input current value and engineering unit."""

    current: float
    current_unit: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "current", _positive(self.current, "current"))
        object.__setattr__(self, "current_unit", _identity(self.current_unit, "current_unit"))


@dataclass(frozen=True, slots=True)
class CoordinationFaultScenario:
    """Explicit relay-input currents for each protection function in a scenario."""

    scenario_id: str
    currents_by_element_id: Mapping[str, CoordinationRelayCurrent]
    fault_location_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_id", _identity(self.scenario_id, "scenario_id"))
        if not isinstance(self.currents_by_element_id, Mapping) or not self.currents_by_element_id:
            raise ValueError("currents_by_element_id must be a non-empty mapping.")
        currents: dict[str, CoordinationRelayCurrent] = {}
        for element_id, value in self.currents_by_element_id.items():
            identity = _identity(element_id, "currents_by_element_id key")
            if not isinstance(value, CoordinationRelayCurrent):
                raise TypeError("currents_by_element_id values must be CoordinationRelayCurrent.")
            if identity in currents:
                raise ValueError(f"Duplicate current record for protection function {identity!r}.")
            currents[identity] = value
        object.__setattr__(self, "currents_by_element_id", MappingProxyType(currents))
        if not isinstance(self.fault_location_id, str):
            raise TypeError("fault_location_id must be a string.")
        if self.fault_location_id:
            object.__setattr__(self, "fault_location_id", _identity(self.fault_location_id, "fault_location_id"))


@dataclass(frozen=True, slots=True)
class CoordinationStudyConfiguration:
    """Immutable Study Case configuration for explicit IDMT coordination."""

    pairs: tuple[CoordinationStudyPair, ...]
    scenarios: tuple[CoordinationFaultScenario, ...]
    required_cti_s: float
    display_name: str = "Protection Coordination Study"

    def __post_init__(self) -> None:
        pairs = tuple(self.pairs)
        scenarios = tuple(self.scenarios)
        if not pairs or not all(isinstance(item, CoordinationStudyPair) for item in pairs):
            raise ValueError("At least one explicit CoordinationStudyPair is required.")
        if not scenarios or not all(isinstance(item, CoordinationFaultScenario) for item in scenarios):
            raise ValueError("At least one explicit CoordinationFaultScenario is required.")
        pair_ids = [(item.primary_element_id, item.backup_element_id) for item in pairs]
        if len(set(pair_ids)) != len(pair_ids):
            raise ValueError("Duplicate primary/backup pairs are not allowed.")
        scenario_ids = [item.scenario_id for item in scenarios]
        if len(set(scenario_ids)) != len(scenario_ids):
            raise ValueError("Coordination scenario IDs must be unique.")
        required_elements = {
            identity
            for pair in pairs
            for identity in (pair.primary_element_id, pair.backup_element_id)
        }
        for scenario in scenarios:
            missing_currents = sorted(required_elements.difference(scenario.currents_by_element_id))
            if missing_currents:
                raise ValueError(
                    f"Scenario {scenario.scenario_id!r} lacks relay-input currents for: "
                    + ", ".join(missing_currents)
                )
        if isinstance(self.required_cti_s, bool):
            raise TypeError("required_cti_s must be numeric, not boolean.")
        cti = float(self.required_cti_s)
        if not math.isfinite(cti) or cti < 0.0:
            raise ValueError("required_cti_s must be finite and non-negative.")
        name = str(self.display_name).strip() or "Protection Coordination Study"
        object.__setattr__(self, "pairs", pairs)
        object.__setattr__(self, "scenarios", scenarios)
        object.__setattr__(self, "required_cti_s", cti)
        object.__setattr__(self, "display_name", name)


@dataclass(frozen=True, slots=True)
class CoordinationStudyPointResult:
    """One pair/scenario evaluation with explicit current and CTI provenance."""

    primary_element_id: str
    backup_element_id: str
    scenario_id: str
    fault_location_id: str
    primary_current: float
    backup_current: float
    primary_current_unit: str
    backup_current_unit: str
    primary_time_s: float
    backup_time_s: float
    margin_s: float
    required_cti_s: float
    status: str
    required_additional_backup_delay_s: float

    @classmethod
    def from_engine_result(
        cls,
        result: CoordinationResult,
        scenario: CoordinationFaultScenario,
        primary_input: CoordinationRelayCurrent,
        backup_input: CoordinationRelayCurrent,
    ) -> "CoordinationStudyPointResult":
        if not result.primary_operates:
            status = "NOT_APPLICABLE"
        elif not result.backup_operates:
            status = "BACKUP_DOES_NOT_OPERATE"
        elif not result.coordinated:
            status = "CTI_VIOLATION"
        else:
            status = "COORDINATED"
        return cls(
            primary_element_id=str(result.primary),
            backup_element_id=str(result.backup),
            scenario_id=scenario.scenario_id,
            fault_location_id=scenario.fault_location_id,
            primary_current=primary_input.current,
            backup_current=backup_input.current,
            primary_current_unit=primary_input.current_unit,
            backup_current_unit=backup_input.current_unit,
            primary_time_s=result.primary_time,
            backup_time_s=result.backup_time,
            margin_s=result.margin,
            required_cti_s=result.CTI,
            status=status,
            required_additional_backup_delay_s=result.required_additional_delay,
        )



@dataclass(frozen=True, slots=True)
class CoordinationStudyResult:
    """Immutable aggregate result published by the Application StudyService."""

    status: str
    required_cti_s: float
    points: tuple[CoordinationStudyPointResult, ...]
    pair_count: int
    scenario_count: int
    project_id: str
    activation_generation: int
    source_model_revision: int
    source_topology_revision: int

    def __post_init__(self) -> None:
        points = tuple(self.points)
        if not points or not all(isinstance(item, CoordinationStudyPointResult) for item in points):
            raise ValueError("CoordinationStudyResult requires evaluated points.")
        allowed = {"COORDINATED", "VIOLATION", "INDETERMINATE"}
        if self.status not in allowed:
            raise ValueError(f"Unsupported coordination study status: {self.status!r}.")
        object.__setattr__(self, "points", points)

    @classmethod
    def aggregate(
        cls,
        *,
        configuration: CoordinationStudyConfiguration,
        points: tuple[CoordinationStudyPointResult, ...],
        project_id: str,
        activation_generation: int,
        source_model_revision: int,
        source_topology_revision: int,
    ) -> "CoordinationStudyResult":
        statuses = {point.status for point in points}
        if statuses.intersection({"CTI_VIOLATION", "BACKUP_DOES_NOT_OPERATE"}):
            status = "VIOLATION"
        elif statuses == {"COORDINATED"}:
            status = "COORDINATED"
        else:
            status = "INDETERMINATE"
        return cls(
            status=status,
            required_cti_s=configuration.required_cti_s,
            points=points,
            pair_count=len(configuration.pairs),
            scenario_count=len(configuration.scenarios),
            project_id=project_id,
            activation_generation=activation_generation,
            source_model_revision=source_model_revision,
            source_topology_revision=source_topology_revision,
        )


class _ConfiguredIDMTFunction:
    """Operating-time adapter built from an immutable IDMT curve snapshot."""

    def __init__(self, curve: Any) -> None:
        self.element_id = curve.element_id
        self._pickup = curve.pickup
        self._curve = curve.curve
        self._tms = curve.TMS

    def operating_time(self, fault_current: float) -> float:
        return iec_time(
            current=fault_current,
            pickup=self._pickup,
            curve=self._curve,
            TMS=self._tms,
        )


def execute_coordination_study(
    configuration: CoordinationStudyConfiguration,
    curve_read_models: tuple[Any, ...],
    *,
    project_id: str,
    activation_generation: int,
    source_model_revision: int,
    source_topology_revision: int,
    cancellation_token: Any | None = None,
) -> CoordinationStudyResult:
    """Evaluate every configured pair at every explicit fault scenario."""
    if not isinstance(configuration, CoordinationStudyConfiguration):
        raise TypeError("configuration must be CoordinationStudyConfiguration.")
    curve_models = {item.element_id: item for item in tuple(curve_read_models)}
    required_ids = {
        identity
        for pair in configuration.pairs
        for identity in (pair.primary_element_id, pair.backup_element_id)
    }
    unavailable = sorted(
        element_id for element_id, item in curve_models.items()
        if not item.function_enabled or item.function_blocked
    )
    referenced_unavailable = sorted(required_id for required_id in required_ids if required_id in unavailable)
    if referenced_unavailable:
        raise ValueError(
            "Coordination cannot use disabled or blocked protection functions: "
            + ", ".join(referenced_unavailable)
        )
    curves = {
        element_id: _ConfiguredIDMTFunction(item)
        for element_id, item in curve_models.items()
    }
    missing = sorted(required_ids.difference(curves))
    if missing:
        raise ValueError(
            "Coordination configuration references missing or unsupported "
            f"ANSI 51/51N curve elements: {', '.join(missing)}."
        )
    engine = RelayCoordination(CTI=configuration.required_cti_s)
    points: list[CoordinationStudyPointResult] = []
    for pair in configuration.pairs:
        primary = curves[pair.primary_element_id]
        backup = curves[pair.backup_element_id]
        for scenario in configuration.scenarios:
            if cancellation_token is not None and cancellation_token.cancelled:
                break
            primary_input = scenario.currents_by_element_id[pair.primary_element_id]
            backup_input = scenario.currents_by_element_id[pair.backup_element_id]
            primary_unit = curve_models[pair.primary_element_id].current_unit
            backup_unit = curve_models[pair.backup_element_id].current_unit
            if primary_unit is None or backup_unit is None:
                raise ValueError(
                    "Coordination requires explicit current_unit/pickup_unit on both "
                    f"relay settings: {pair.primary_element_id!r}, {pair.backup_element_id!r}."
                )
            if primary_input.current_unit != primary_unit:
                raise ValueError(
                    f"Scenario {scenario.scenario_id!r} current unit "
                    f"{primary_input.current_unit!r} does not match configured "
                    f"unit {primary_unit!r} for {pair.primary_element_id!r}."
                )
            if backup_input.current_unit != backup_unit:
                raise ValueError(
                    f"Scenario {scenario.scenario_id!r} current unit "
                    f"{backup_input.current_unit!r} does not match configured "
                    f"unit {backup_unit!r} for {pair.backup_element_id!r}."
                )
            result = engine.check_pair_currents(
                primary=primary,
                backup=backup,
                primary_fault_current=primary_input.current,
                backup_fault_current=backup_input.current,
            )
            points.append(
                CoordinationStudyPointResult.from_engine_result(
                    result, scenario, primary_input, backup_input
                )
            )
        if cancellation_token is not None and cancellation_token.cancelled:
            break
    if cancellation_token is not None and cancellation_token.cancelled:
        raise RuntimeError("Protection coordination study cancelled before completion.")
    expected_count = len(configuration.pairs) * len(configuration.scenarios)
    if len(points) != expected_count:
        raise RuntimeError("Coordination study did not evaluate every configured pair/scenario.")
    return CoordinationStudyResult.aggregate(
        configuration=configuration,
        points=tuple(points),
        project_id=project_id,
        activation_generation=activation_generation,
        source_model_revision=source_model_revision,
        source_topology_revision=source_topology_revision,
    )


__all__ = [
    "CoordinationStudyPair",
    "CoordinationRelayCurrent",
    "CoordinationFaultScenario",
    "CoordinationStudyConfiguration",
    "CoordinationStudyPointResult",
    "CoordinationStudyResult",
    "execute_coordination_study",
]
