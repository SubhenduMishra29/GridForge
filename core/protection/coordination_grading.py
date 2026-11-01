"""Explicit multi-relay IEC/IEEE overcurrent coordination grading.

Core numerical policy only: relay relationships and fault-current contributions
are supplied explicitly by the caller. This module does not infer coordination
pairs from graph depth, calculate fault current, apply settings, or operate
breakers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite, inf
from types import MappingProxyType
from typing import Mapping, Iterable

from .ieee_curves import ieee_inverse_time, normalize_ieee_curve
from .relay_functions import iec_time, normalize_iec_curve


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric, not bool.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if not isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _non_empty_id(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    result = value.strip()
    if not result:
        raise ValueError(f"{name} must be non-empty.")
    return result


@dataclass(frozen=True, slots=True)
class CoordinationRelayCharacteristic:
    """One explicitly configured inverse-time relay element.

    pickup_current_a and scenario currents must use the same primary-current
    convention. CT ratio conversion and measurement provenance are upstream
    responsibilities and are never inferred here.
    """

    relay_id: str
    pickup_current_a: float
    curve_standard: str
    curve: str
    time_dial: float

    def __post_init__(self) -> None:
        relay_id = _non_empty_id(self.relay_id, "relay_id")
        pickup = _finite(self.pickup_current_a, "pickup_current_a")
        dial = _finite(self.time_dial, "time_dial")
        if pickup <= 0.0 or dial <= 0.0:
            raise ValueError("pickup_current_a and time_dial must be positive.")
        if not isinstance(self.curve_standard, str):
            raise TypeError("curve_standard must be a string.")
        standard = self.curve_standard.strip().upper()
        if standard == "IEC":
            curve = normalize_iec_curve(self.curve)
        elif standard == "IEEE":
            curve = normalize_ieee_curve(self.curve)
        else:
            raise ValueError("curve_standard must be IEC or IEEE.")
        object.__setattr__(self, "relay_id", relay_id)
        object.__setattr__(self, "pickup_current_a", pickup)
        object.__setattr__(self, "time_dial", dial)
        object.__setattr__(self, "curve_standard", standard)
        object.__setattr__(self, "curve", curve)

    def operating_time(self, current_a: float) -> float:
        """Return nominal characteristic time; infinity means no pickup."""
        current = _finite(current_a, "current_a")
        if self.curve_standard == "IEC":
            return iec_time(
                current=current,
                pickup=self.pickup_current_a,
                curve=self.curve,
                TMS=self.time_dial,
            )
        return ieee_inverse_time(
            current=current,
            pickup=self.pickup_current_a,
            curve=self.curve,
            time_dial=self.time_dial,
        )


@dataclass(frozen=True, slots=True)
class CoordinationPair:
    """An engineer/study-declared downstream to upstream grading pair."""

    downstream_relay_id: str
    upstream_relay_id: str
    downstream_breaker_clearing_time_s: float
    required_cti_s: float
    downstream_breaker_clearing_time_max_s: float | None = None

    def __post_init__(self) -> None:
        downstream = _non_empty_id(self.downstream_relay_id, "downstream_relay_id")
        upstream = _non_empty_id(self.upstream_relay_id, "upstream_relay_id")
        if downstream == upstream:
            raise ValueError("A relay cannot be coordinated against itself.")
        clearing = _finite(
            self.downstream_breaker_clearing_time_s,
            "downstream_breaker_clearing_time_s",
        )
        cti = _finite(self.required_cti_s, "required_cti_s")
        if clearing < 0.0 or cti < 0.0:
            raise ValueError("Breaker clearing time and required CTI cannot be negative.")
        clearing_max = self.downstream_breaker_clearing_time_max_s
        if clearing_max is not None:
            clearing_max = _finite(clearing_max, "downstream_breaker_clearing_time_max_s")
            if clearing_max < clearing:
                raise ValueError("Maximum breaker clearing time cannot be below nominal clearing time.")
        object.__setattr__(self, "downstream_breaker_clearing_time_max_s", clearing_max)
        object.__setattr__(self, "downstream_relay_id", downstream)
        object.__setattr__(self, "upstream_relay_id", upstream)
        object.__setattr__(self, "downstream_breaker_clearing_time_s", clearing)
        object.__setattr__(self, "required_cti_s", cti)


@dataclass(frozen=True, slots=True)
class RelayOperatingTimeEnvelope:
    """Manufacturer/test timing bounds for one relay at one exact fault current."""

    relay_id: str
    current_a: float
    minimum_time_s: float
    maximum_time_s: float
    evidence_reference: str

    def __post_init__(self) -> None:
        relay_id = _non_empty_id(self.relay_id, "relay_id")
        current = _finite(self.current_a, "current_a")
        minimum = _finite(self.minimum_time_s, "minimum_time_s")
        maximum = _finite(self.maximum_time_s, "maximum_time_s")
        evidence = _non_empty_id(self.evidence_reference, "evidence_reference")
        if current < 0.0 or minimum < 0.0 or maximum < minimum:
            raise ValueError("Timing envelope requires non-negative current/time and maximum_time_s >= minimum_time_s.")
        object.__setattr__(self, "relay_id", relay_id)
        object.__setattr__(self, "current_a", current)
        object.__setattr__(self, "minimum_time_s", minimum)
        object.__setattr__(self, "maximum_time_s", maximum)
        object.__setattr__(self, "evidence_reference", evidence)


@dataclass(frozen=True, slots=True)
class FaultCurrentScenario:
    """One named fault case with explicit primary current at each relay."""

    scenario_id: str
    relay_currents_a: Mapping[str, float]
    relay_timing_envelopes: Mapping[str, RelayOperatingTimeEnvelope] = field(default_factory=dict)

    def __post_init__(self) -> None:
        scenario_id = _non_empty_id(self.scenario_id, "scenario_id")
        if not isinstance(self.relay_currents_a, Mapping):
            raise TypeError("relay_currents_a must be a mapping of relay IDs to amperes.")
        currents: dict[str, float] = {}
        for relay_id, current in self.relay_currents_a.items():
            key = _non_empty_id(relay_id, "relay current key")
            if key in currents:
                raise ValueError(f"Duplicate normalized relay ID {key!r} in scenario.")
            value = _finite(current, f"current for relay {key}")
            if value < 0.0:
                raise ValueError("Fault-current magnitudes cannot be negative.")
            currents[key] = value
        if not isinstance(self.relay_timing_envelopes, Mapping):
            raise TypeError("relay_timing_envelopes must map relay IDs to RelayOperatingTimeEnvelope values.")
        envelopes: dict[str, RelayOperatingTimeEnvelope] = {}
        for relay_id, envelope in self.relay_timing_envelopes.items():
            key = _non_empty_id(relay_id, "timing envelope key")
            if key in envelopes:
                raise ValueError(f"Duplicate normalized timing-envelope relay ID {key!r}.")
            if not isinstance(envelope, RelayOperatingTimeEnvelope) or envelope.relay_id != key:
                raise TypeError("Each timing envelope must be typed and match its mapping key.")
            envelopes[key] = envelope
        object.__setattr__(self, "scenario_id", scenario_id)
        object.__setattr__(self, "relay_currents_a", MappingProxyType(currents))
        object.__setattr__(self, "relay_timing_envelopes", MappingProxyType(envelopes))


@dataclass(frozen=True, slots=True)
class CoordinationGrade:
    """Nominal grading outcome for one explicit pair and fault scenario."""

    downstream_relay_id: str
    upstream_relay_id: str
    scenario_id: str
    downstream_current_a: float | None
    upstream_current_a: float | None
    downstream_operating_time_s: float | None
    upstream_operating_time_s: float | None
    downstream_breaker_clearing_time_s: float
    available_cti_s: float | None
    required_cti_s: float
    status: str
    reason: str
    tolerance_available_cti_s: float | None = None
    tolerance_status: str = "NOT_ASSESSED"
    tolerance_reason: str = "Manufacturer/test timing envelopes and maximum breaker clearing time were not supplied."

    def to_dict(self) -> dict[str, object]:
        return {
            "downstream_relay_id": self.downstream_relay_id,
            "upstream_relay_id": self.upstream_relay_id,
            "scenario_id": self.scenario_id,
            "downstream_current_a": self.downstream_current_a,
            "upstream_current_a": self.upstream_current_a,
            "downstream_operating_time_s": self.downstream_operating_time_s,
            "upstream_operating_time_s": self.upstream_operating_time_s,
            "downstream_breaker_clearing_time_s": self.downstream_breaker_clearing_time_s,
            "available_cti_s": self.available_cti_s,
            "required_cti_s": self.required_cti_s,
            "status": self.status,
            "reason": self.reason,
            "tolerance_available_cti_s": self.tolerance_available_cti_s,
            "tolerance_status": self.tolerance_status,
            "tolerance_reason": self.tolerance_reason,
        }


@dataclass(frozen=True, slots=True)
class ProtectionCoordinationReport:
    """Detached immutable report for all requested pairs and scenarios."""

    grades: tuple[CoordinationGrade, ...]

    @property
    def tolerance_assessment_included(self) -> bool:
        return bool(self.grades) and all(
            grade.tolerance_status in {"COORDINATED_WITH_TOLERANCE", "NOT_COORDINATED_WITH_TOLERANCE"}
            for grade in self.grades
        )

    @property
    def all_scenarios_coordinated_with_tolerance(self) -> bool:
        return self.tolerance_assessment_included and all(
            grade.tolerance_status == "COORDINATED_WITH_TOLERANCE"
            for grade in self.grades
        )

    @property
    def fully_evaluable(self) -> bool:
        return bool(self.grades) and all(
            grade.status in {"COORDINATED", "NOT_COORDINATED"}
            for grade in self.grades
        )

    @property
    def all_scenarios_coordinated(self) -> bool:
        return bool(self.grades) and all(
            grade.status == "COORDINATED" for grade in self.grades
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "fully_evaluable": self.fully_evaluable,
            "all_scenarios_coordinated": self.all_scenarios_coordinated,
            "tolerance_assessment_included": self.tolerance_assessment_included,
            "all_scenarios_coordinated_with_tolerance": self.all_scenarios_coordinated_with_tolerance,
            "grades": [grade.to_dict() for grade in self.grades],
        }


def grade_protection_coordination(
    relays: Iterable[CoordinationRelayCharacteristic],
    pairs: Iterable[CoordinationPair],
    scenarios: Iterable[FaultCurrentScenario],
) -> ProtectionCoordinationReport:
    """Grade explicitly declared relay pairs across explicit fault cases.

    Available CTI = upstream relay operating time - downstream relay
    operating time - downstream breaker clearing time. A result is
    COORDINATED only when available CTI meets the pair's required CTI.
    Missing currents or a non-operating relay yield NOT_EVALUABLE, never a
    pass. Manufacturer timing tolerances, breaker tolerance bands, relay
    overshoot and reset characteristics are not included in this nominal
    calculation and are explicitly reported as such.
    """
    relay_items = tuple(relays)
    pair_items = tuple(pairs)
    scenario_items = tuple(scenarios)
    if not relay_items or not pair_items or not scenario_items:
        raise ValueError("At least one relay, coordination pair and fault scenario are required.")
    if any(not isinstance(item, CoordinationRelayCharacteristic) for item in relay_items):
        raise TypeError("relays must contain CoordinationRelayCharacteristic values.")
    if any(not isinstance(item, CoordinationPair) for item in pair_items):
        raise TypeError("pairs must contain CoordinationPair values.")
    if any(not isinstance(item, FaultCurrentScenario) for item in scenario_items):
        raise TypeError("scenarios must contain FaultCurrentScenario values.")

    relay_by_id: dict[str, CoordinationRelayCharacteristic] = {}
    for relay in relay_items:
        if relay.relay_id in relay_by_id:
            raise ValueError(f"Duplicate relay identity {relay.relay_id!r}.")
        relay_by_id[relay.relay_id] = relay

    pair_keys: set[tuple[str, str]] = set()
    for pair in pair_items:
        key = (pair.downstream_relay_id, pair.upstream_relay_id)
        if key in pair_keys:
            raise ValueError(f"Duplicate coordination pair {key!r}.")
        pair_keys.add(key)
        if pair.downstream_relay_id not in relay_by_id:
            raise ValueError(f"Unknown downstream relay {pair.downstream_relay_id!r}.")
        if pair.upstream_relay_id not in relay_by_id:
            raise ValueError(f"Unknown upstream relay {pair.upstream_relay_id!r}.")

    scenario_ids = [scenario.scenario_id for scenario in scenario_items]
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("Fault scenario IDs must be unique.")

    grades: list[CoordinationGrade] = []
    for pair in pair_items:
        downstream = relay_by_id[pair.downstream_relay_id]
        upstream = relay_by_id[pair.upstream_relay_id]
        for scenario in scenario_items:
            downstream_current = scenario.relay_currents_a.get(downstream.relay_id)
            upstream_current = scenario.relay_currents_a.get(upstream.relay_id)
            if downstream_current is None or upstream_current is None:
                missing = [
                    relay_id for relay_id, value in (
                        (downstream.relay_id, downstream_current),
                        (upstream.relay_id, upstream_current),
                    ) if value is None
                ]
                grades.append(CoordinationGrade(
                    downstream.relay_id, upstream.relay_id, scenario.scenario_id,
                    downstream_current, upstream_current, None, None,
                    pair.downstream_breaker_clearing_time_s, None, pair.required_cti_s,
                    "NOT_EVALUABLE",
                    "Missing explicit fault-current magnitude for relay(s): " + ", ".join(missing),
                ))
                continue

            downstream_time = downstream.operating_time(downstream_current)
            upstream_time = upstream.operating_time(upstream_current)
            if downstream_time == inf or upstream_time == inf:
                non_operating = []
                if downstream_time == inf:
                    non_operating.append("downstream")
                if upstream_time == inf:
                    non_operating.append("upstream")
                grades.append(CoordinationGrade(
                    downstream.relay_id, upstream.relay_id, scenario.scenario_id,
                    downstream_current, upstream_current, downstream_time, upstream_time,
                    pair.downstream_breaker_clearing_time_s, None, pair.required_cti_s,
                    "NOT_EVALUABLE",
                    "No finite operating time for " + " and ".join(non_operating) + " relay.",
                ))
                continue

            available = (
                upstream_time
                - downstream_time
                - pair.downstream_breaker_clearing_time_s
            )
            coordinated = available >= pair.required_cti_s
            down_envelope = scenario.relay_timing_envelopes.get(downstream.relay_id)
            up_envelope = scenario.relay_timing_envelopes.get(upstream.relay_id)
            tolerance_available = None
            tolerance_status = "NOT_ASSESSED"
            tolerance_reason = (
                "Manufacturer/test timing envelopes and maximum breaker clearing time were not supplied."
            )
            if (
                down_envelope is not None
                and up_envelope is not None
                and pair.downstream_breaker_clearing_time_max_s is not None
            ):
                current_match = (
                    abs(down_envelope.current_a - downstream_current) <= max(1e-9, abs(downstream_current) * 1e-9)
                    and abs(up_envelope.current_a - upstream_current) <= max(1e-9, abs(upstream_current) * 1e-9)
                )
                if not current_match:
                    tolerance_status = "TOLERANCE_NOT_EVALUABLE"
                    tolerance_reason = "Timing-envelope current does not match this fault scenario."
                else:
                    tolerance_available = (
                        up_envelope.minimum_time_s
                        - down_envelope.maximum_time_s
                        - pair.downstream_breaker_clearing_time_max_s
                    )
                    tolerance_ok = tolerance_available >= pair.required_cti_s
                    tolerance_status = (
                        "COORDINATED_WITH_TOLERANCE"
                        if tolerance_ok else "NOT_COORDINATED_WITH_TOLERANCE"
                    )
                    tolerance_reason = (
                        "Conservative timing bounds meet the required CTI."
                        if tolerance_ok
                        else "Conservative timing bounds do not meet the required CTI."
                    )
            grades.append(CoordinationGrade(
                downstream.relay_id, upstream.relay_id, scenario.scenario_id,
                downstream_current, upstream_current, downstream_time, upstream_time,
                pair.downstream_breaker_clearing_time_s, available, pair.required_cti_s,
                "COORDINATED" if coordinated else "NOT_COORDINATED",
                "Required CTI is met." if coordinated else "Available CTI is below the required CTI.",
                tolerance_available, tolerance_status, tolerance_reason,
            ))

    return ProtectionCoordinationReport(grades=tuple(grades))


__all__ = [
    "CoordinationRelayCharacteristic",
    "CoordinationPair",
    "FaultCurrentScenario",
    "RelayOperatingTimeEnvelope",
    "CoordinationGrade",
    "ProtectionCoordinationReport",
    "grade_protection_coordination",
]
