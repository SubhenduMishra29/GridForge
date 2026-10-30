"""Application-executable, explicitly configured IDMT coordination studies.

The study consumes relay-input currents supplied for each protection
function. It never infers primary/backup relationships or CT conversions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping

from core.protection.coordination.relay_coordination import (
    CoordinationResult,
    RelayCoordination,
)
from core.protection.relay_functions import iec_time
from core.solver.short_circuit.result import (
    ContributionStatus,
    ShortCircuitResult,
    ShortCircuitStatus,
)


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
    """Explicit primary/backup protection functions and optional SC branch mapping."""

    primary_element_id: str
    backup_element_id: str
    primary_branch_id: str | None = None
    backup_branch_id: str | None = None
    primary_branch_side: str | None = None
    backup_branch_side: str | None = None
    primary_current_scale: float | None = None
    backup_current_scale: float | None = None

    def __post_init__(self) -> None:
        primary = _identity(self.primary_element_id, "primary_element_id")
        backup = _identity(self.backup_element_id, "backup_element_id")
        if primary == backup:
            raise ValueError("Primary and backup protection elements must differ.")
        object.__setattr__(self, "primary_element_id", primary)
        object.__setattr__(self, "backup_element_id", backup)
        for name in ("primary_branch_id", "backup_branch_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _identity(value, name))
        for name in ("primary_branch_side", "backup_branch_side"):
            value = getattr(self, name)
            if value is not None:
                side = _identity(value, name).lower()
                if side not in {"from", "to"}:
                    raise ValueError(f"{name} must be 'from' or 'to'.")
                object.__setattr__(self, name, side)
        for name in ("primary_current_scale", "backup_current_scale"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _positive(value, name))
        if (
            self.primary_branch_id is not None
            and self.primary_branch_id == self.backup_branch_id
            and self.primary_branch_side is not None
            and self.primary_branch_side == self.backup_branch_side
        ):
            raise ValueError("Primary and backup mappings cannot use the same branch side.")


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
    """One manual relay-current set or one completed Short-Circuit Study result."""

    scenario_id: str
    currents_by_element_id: Mapping[str, CoordinationRelayCurrent] = field(default_factory=dict)
    fault_location_id: str = ""
    short_circuit_study_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_id", _identity(self.scenario_id, "scenario_id"))
        source_id = self.short_circuit_study_id
        if source_id is not None:
            object.__setattr__(self, "short_circuit_study_id", _identity(source_id, "short_circuit_study_id"))
        supplied = self.currents_by_element_id or {}
        if not isinstance(supplied, Mapping):
            raise TypeError("currents_by_element_id must be a mapping.")
        currents: dict[str, CoordinationRelayCurrent] = {}
        for element_id, value in supplied.items():
            identity = _identity(element_id, "currents_by_element_id key")
            if not isinstance(value, CoordinationRelayCurrent):
                raise TypeError("currents_by_element_id values must be CoordinationRelayCurrent.")
            if identity in currents:
                raise ValueError(f"Duplicate current record for protection function {identity!r}.")
            currents[identity] = value
        if self.short_circuit_study_id is None and not currents:
            raise ValueError("Manual coordination scenarios require relay-input current records.")
        if self.short_circuit_study_id is not None and currents:
            raise ValueError("Short-Circuit sourced scenarios cannot also provide manual currents.")
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
            if scenario.short_circuit_study_id is not None:
                for pair in pairs:
                    if not all((
                        pair.primary_branch_id,
                        pair.backup_branch_id,
                        pair.primary_branch_side,
                        pair.backup_branch_side,
                        pair.primary_current_scale,
                        pair.backup_current_scale,
                    )):
                        raise ValueError(
                            "Short-Circuit sourced scenarios require explicit branch IDs, "
                            "branch sides, and current conversion scales for every pair."
                        )
                continue
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
    source_study_id: str | None
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
        if result.primary_operates and not result.backup_operates:
            status = "BACKUP_DOES_NOT_OPERATE"
        elif not result.primary_operates and result.backup_operates:
            status = "BACKUP_ONLY_OPERATION"
        elif not result.primary_operates and not result.backup_operates:
            status = "NOT_APPLICABLE"
        elif not result.coordinated:
            status = "CTI_VIOLATION"
        else:
            status = "COORDINATED"
        return cls(
            primary_element_id=str(result.primary),
            backup_element_id=str(result.backup),
            scenario_id=scenario.scenario_id,
            fault_location_id=scenario.fault_location_id,
            source_study_id=scenario.short_circuit_study_id,
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
        if isinstance(self.pair_count, bool) or not isinstance(self.pair_count, int) or self.pair_count < 1:
            raise ValueError("pair_count must be a positive integer.")
        if isinstance(self.scenario_count, bool) or not isinstance(self.scenario_count, int) or self.scenario_count < 1:
            raise ValueError("scenario_count must be a positive integer.")
        if len(points) != self.pair_count * self.scenario_count:
            raise ValueError("Coordination result point count does not match pair_count × scenario_count.")
        identities = [
            (item.primary_element_id, item.backup_element_id, item.scenario_id)
            for item in points
        ]
        if len(set(identities)) != len(identities):
            raise ValueError("Coordination result contains duplicate pair/scenario points.")
        if len({(item.primary_element_id, item.backup_element_id) for item in points}) != self.pair_count:
            raise ValueError("Coordination result pair identities do not match pair_count.")
        if len({item.scenario_id for item in points}) != self.scenario_count:
            raise ValueError("Coordination result scenario identities do not match scenario_count.")
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be a non-empty string.")
        for name in ("activation_generation", "source_model_revision", "source_topology_revision"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer.")
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
        if statuses.intersection({"CTI_VIOLATION", "BACKUP_DOES_NOT_OPERATE", "BACKUP_ONLY_OPERATION"}):
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


def _short_circuit_relay_current(
    result: ShortCircuitResult,
    branch_id: str | None,
    side: str | None,
    scale: float | None,
    current_unit: str | None,
    element_id: str,
) -> CoordinationRelayCurrent:
    """Convert one per-unit branch current using explicit side/base and CT scale."""
    if not branch_id or side not in {"from", "to"} or scale is None:
        raise ValueError(f"Short-Circuit branch mapping is incomplete for {element_id!r}.")
    if current_unit is None:
        raise ValueError(f"Protection function {element_id!r} has no declared current_unit.")
    try:
        branch = result.branch_currents[branch_id]
    except (AttributeError, KeyError, TypeError) as exc:
        raise ValueError(f"Short-Circuit branch current {branch_id!r} is unavailable.") from exc
    if branch.current_unit != "pu":
        raise ValueError(f"Short-Circuit branch {branch_id!r} is not expressed in per-unit.")
    base = branch.current_base_a_from if side == "from" else branch.current_base_a_to
    if base is None:
        raise ValueError(
            f"Short-Circuit branch {branch_id!r} has no {side}-side ampere base; "
            "provide base_mva and nominal bus voltage."
        )
    primary_amperes = float(branch.magnitude) * float(base)
    relay_input_current = primary_amperes * float(scale)
    return CoordinationRelayCurrent(relay_input_current, current_unit)


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
    short_circuit_results: Mapping[str, Any] | None = None,
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
            if scenario.short_circuit_study_id is None:
                primary_input = scenario.currents_by_element_id[pair.primary_element_id]
                backup_input = scenario.currents_by_element_id[pair.backup_element_id]
            else:
                results = short_circuit_results or {}
                short_result = results.get(scenario.short_circuit_study_id)
                if not isinstance(short_result, ShortCircuitResult):
                    raise TypeError("Short-Circuit Study result must be a canonical ShortCircuitResult.")
                if not short_result.success or short_result.status is not ShortCircuitStatus.COMPLETE:
                    raise ValueError("Coordination requires a successful COMPLETE Short-Circuit result.")
                if short_result.contribution_status is not ContributionStatus.COMPLETE:
                    raise ValueError("Coordination requires COMPLETE Short-Circuit branch contribution data.")
                provenance = getattr(short_result, "provenance", {})
                if not isinstance(provenance, Mapping):
                    raise ValueError("Short-Circuit result provenance is unavailable.")
                if (
                    provenance.get("project_id") != project_id
                    or provenance.get("activation_generation") != activation_generation
                    or provenance.get("topology_revision") != source_topology_revision
                ):
                    raise ValueError("Short-Circuit result provenance does not match the active coordination Study Case.")
                if scenario.fault_location_id and str(short_result.fault_bus_id) != scenario.fault_location_id:
                    raise ValueError(
                        f"Scenario fault location {scenario.fault_location_id!r} does not match "
                        f"Short-Circuit result fault bus {short_result.fault_bus_id!r}."
                    )
                primary_input = _short_circuit_relay_current(
                    short_result, pair.primary_branch_id, pair.primary_branch_side,
                    pair.primary_current_scale, curve_models[pair.primary_element_id].current_unit,
                    pair.primary_element_id,
                )
                backup_input = _short_circuit_relay_current(
                    short_result, pair.backup_branch_id, pair.backup_branch_side,
                    pair.backup_current_scale, curve_models[pair.backup_element_id].current_unit,
                    pair.backup_element_id,
                )
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
