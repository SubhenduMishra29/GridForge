"""Time-series inverse-time relay coordination with evidence-bound reset memory.

Current traces are piecewise-constant between explicit timestamps. The evaluator
uses the selected IEC/IEEE characteristic to accumulate normalized operating
progress and applies reset-memory curves only at an exact measured dropout
current multiple. It does not synthesize overshoot behaviour or extrapolate
manufacturer evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Iterable, Mapping

from .coordination_grading import (
    CoordinationPair,
    CoordinationRelayCharacteristic,
)
from .relay_dynamic_characteristics import RelayDynamicEvidence


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric, not boolean.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if not isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


@dataclass(frozen=True, slots=True)
class RelayCurrentSample:
    """Current magnitude held from this timestamp up to the next sample."""

    time_s: float
    current_a: float

    def __post_init__(self) -> None:
        timestamp = _finite(self.time_s, "time_s")
        current = _finite(self.current_a, "current_a")
        if timestamp < 0.0 or current < 0.0:
            raise ValueError("Sample time and current cannot be negative.")
        object.__setattr__(self, "time_s", timestamp)
        object.__setattr__(self, "current_a", current)


@dataclass(frozen=True, slots=True)
class RelayCurrentTrace:
    """Ordered, explicit current-magnitude time series for one protection function."""

    function_id: str
    samples: tuple[RelayCurrentSample, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.function_id, str) or not self.function_id.strip():
            raise ValueError("function_id must be a non-empty string.")
        samples = tuple(self.samples)
        if len(samples) < 2 or any(not isinstance(item, RelayCurrentSample) for item in samples):
            raise ValueError("A current trace requires at least two typed samples.")
        times = tuple(item.time_s for item in samples)
        if any(right <= left for left, right in zip(times, times[1:])):
            raise ValueError("Current trace timestamps must be strictly increasing.")
        object.__setattr__(self, "function_id", self.function_id.strip())
        object.__setattr__(self, "samples", samples)


@dataclass(frozen=True, slots=True)
class TransientRelayOutcome:
    """One function's operation result over the supplied observation window."""

    function_id: str
    status: str
    operation_time_s: float | None
    final_operating_progress: float | None
    reset_memory_used: bool
    overshoot_assessment: str
    reason: str


@dataclass(frozen=True, slots=True)
class TransientCoordinationGrade:
    """Transient CTI result for one declared pair and common fault record."""

    downstream_function_id: str
    upstream_function_id: str
    downstream_operation_time_s: float | None
    upstream_operation_time_s: float | None
    downstream_breaker_clearing_time_s: float
    available_cti_s: float | None
    required_cti_s: float
    status: str
    reason: str
    downstream_overshoot_assessment: str
    upstream_overshoot_assessment: str


@dataclass(frozen=True, slots=True)
class TransientCoordinationReport:
    """Detached outcomes and pair grades for one transient event."""

    event_id: str
    relay_outcomes: Mapping[str, TransientRelayOutcome]
    grades: tuple[TransientCoordinationGrade, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id must be a non-empty string.")
        outcomes = dict(self.relay_outcomes)
        if any(key != value.function_id for key, value in outcomes.items()):
            raise ValueError("Outcome mapping keys must match function identities.")
        object.__setattr__(self, "event_id", self.event_id.strip())
        object.__setattr__(self, "relay_outcomes", MappingProxyType(outcomes))
        object.__setattr__(self, "grades", tuple(self.grades))

    @property
    def fully_evaluable(self) -> bool:
        return bool(self.grades) and all(
            item.status in {"COORDINATED", "NOT_COORDINATED"}
            for item in self.grades
        )

    @property
    def all_coordinated(self) -> bool:
        return self.fully_evaluable and all(
            item.status == "COORDINATED" for item in self.grades
        )


def evaluate_relay_current_trace(
    characteristic: CoordinationRelayCharacteristic,
    trace: RelayCurrentTrace,
    dynamic_evidence: RelayDynamicEvidence | None = None,
) -> TransientRelayOutcome:
    """Integrate inverse-time progress over a trace, applying measured reset memory.

    Progress increment for each above-pickup interval is dt / t_operating(I).
    Below-pickup intervals retain progress according to a reset curve selected
    at the exact pre-dropout current multiple. If that evidence is absent or
    the dropout duration is outside its measured range, evaluation fails closed.
    """
    if not isinstance(characteristic, CoordinationRelayCharacteristic):
        raise TypeError("characteristic must be CoordinationRelayCharacteristic.")
    if not isinstance(trace, RelayCurrentTrace):
        raise TypeError("trace must be RelayCurrentTrace.")
    if characteristic.function_id != trace.function_id:
        raise ValueError("Characteristic and current trace function IDs must match.")
    if dynamic_evidence is not None:
        if not isinstance(dynamic_evidence, RelayDynamicEvidence):
            raise TypeError("dynamic_evidence must be RelayDynamicEvidence or None.")
        if dynamic_evidence.function_id != trace.function_id:
            raise ValueError("Dynamic evidence function ID does not match current trace.")

    progress = 0.0
    last_overcurrent_multiple: float | None = None
    dropout_start: float | None = None
    progress_at_dropout = 0.0
    reset_used = False
    samples = trace.samples

    for index, sample in enumerate(samples[:-1]):
        next_sample = samples[index + 1]
        interval = next_sample.time_s - sample.time_s
        multiple = sample.current_a / characteristic.pickup_current_a
        if multiple > 1.0:
            if dropout_start is not None:
                duration = sample.time_s - dropout_start
                curve = (
                    dynamic_evidence.reset_curve_at(last_overcurrent_multiple)
                    if dynamic_evidence is not None and last_overcurrent_multiple is not None
                    else None
                )
                if curve is None:
                    return TransientRelayOutcome(
                        trace.function_id, "NOT_EVALUABLE", None, None, reset_used,
                        "NOT_ASSESSED",
                        "Current recovered after dropout, but no reset-memory curve exists at the exact pre-dropout current multiple.",
                    )
                retained = curve.retained_progress(progress_at_dropout, duration)
                if retained is None:
                    return TransientRelayOutcome(
                        trace.function_id, "NOT_EVALUABLE", None, None, reset_used,
                        "NOT_ASSESSED",
                        "Dropout duration lies outside the supplied reset-memory evidence domain.",
                    )
                progress = retained
                reset_used = True
                dropout_start = None
                last_overcurrent_multiple = None

            operating_time = characteristic.operating_time(sample.current_a)
            if not isfinite(operating_time) or operating_time <= 0.0:
                return TransientRelayOutcome(
                    trace.function_id, "NOT_EVALUABLE", None, progress, reset_used,
                    "NOT_ASSESSED", "Inverse-time characteristic did not return a finite positive operating time.",
                )
            remaining_time = max(0.0, (1.0 - progress) * operating_time)
            if remaining_time <= interval:
                operation_time = sample.time_s + remaining_time
                return TransientRelayOutcome(
                    trace.function_id, "OPERATED", operation_time, 1.0, reset_used,
                    "NOT_ASSESSED",
                    "Accumulated inverse-time operating progress reached unity.",
                )
            progress += interval / operating_time
            progress = min(progress, 1.0)
            last_overcurrent_multiple = multiple
        else:
            if dropout_start is None and progress > 0.0:
                dropout_start = sample.time_s
                progress_at_dropout = progress
                # Retain the current multiple immediately before dropout.
                last_overcurrent_multiple = last_overcurrent_multiple
            elif dropout_start is not None and progress_at_dropout > 0.0:
                # Keep the original dropout state; evaluate the full interval
                # from dropout onset when current returns.
                pass

    return TransientRelayOutcome(
        trace.function_id,
        "NOT_OPERATED_WITHIN_WINDOW",
        None,
        progress,
        reset_used,
        "NOT_ASSESSED",
        "No operation occurred within the supplied current-trace observation window.",
    )


def grade_transient_protection_coordination(
    *,
    event_id: str,
    functions: Iterable[CoordinationRelayCharacteristic],
    pairs: Iterable[CoordinationPair],
    traces: Iterable[RelayCurrentTrace],
    dynamic_evidence: Iterable[RelayDynamicEvidence] = (),
) -> TransientCoordinationReport:
    """Grade transient pair CTI using operation times from explicit current traces.

    Relay overshoot is reported as NOT_ASSESSED. Although overshoot evidence
    contracts exist, the engineering meaning and test protocol must be mapped
    before a timing correction is applied; the evaluator does not guess.
    """
    function_items = tuple(functions)
    pair_items = tuple(pairs)
    trace_items = tuple(traces)
    evidence_items = tuple(dynamic_evidence)
    if not event_id or not str(event_id).strip():
        raise ValueError("event_id must be non-empty.")
    if not function_items or not pair_items or not trace_items:
        raise ValueError("Functions, coordination pairs and current traces are required.")
    function_map = {item.function_id: item for item in function_items}
    if len(function_map) != len(function_items):
        raise ValueError("Function IDs must be unique.")
    trace_map = {item.function_id: item for item in trace_items}
    if len(trace_map) != len(trace_items):
        raise ValueError("Current traces must have unique function IDs.")
    evidence_map = {item.function_id: item for item in evidence_items}
    if len(evidence_map) != len(evidence_items):
        raise ValueError("Dynamic evidence must have unique function IDs.")

    outcomes: dict[str, TransientRelayOutcome] = {}
    for function_id, trace in trace_map.items():
        characteristic = function_map.get(function_id)
        if characteristic is None:
            raise ValueError(f"Current trace references unknown function {function_id!r}.")
        outcomes[function_id] = evaluate_relay_current_trace(
            characteristic, trace, evidence_map.get(function_id)
        )

    grades: list[TransientCoordinationGrade] = []
    seen_pairs: set[tuple[str, str]] = set()
    for pair in pair_items:
        key = (pair.downstream_function_id, pair.upstream_function_id)
        if key in seen_pairs:
            raise ValueError(f"Duplicate coordination pair {key!r}.")
        seen_pairs.add(key)
        downstream = outcomes.get(pair.downstream_function_id)
        upstream = outcomes.get(pair.upstream_function_id)
        if downstream is None or upstream is None:
            reason = "A required relay current trace is missing."
            grades.append(TransientCoordinationGrade(
                pair.downstream_function_id, pair.upstream_function_id,
                None, None, pair.downstream_breaker_clearing_time_s, None,
                pair.required_cti_s, "NOT_EVALUABLE", reason,
                "NOT_ASSESSED", "NOT_ASSESSED",
            ))
            continue
        if downstream.status != "OPERATED" or upstream.status != "OPERATED":
            reason = (
                "Both relay operation times must be observed in the supplied traces; "
                f"downstream={downstream.status}, upstream={upstream.status}."
            )
            grades.append(TransientCoordinationGrade(
                pair.downstream_function_id, pair.upstream_function_id,
                downstream.operation_time_s, upstream.operation_time_s,
                pair.downstream_breaker_clearing_time_s, None,
                pair.required_cti_s, "NOT_EVALUABLE", reason,
                downstream.overshoot_assessment, upstream.overshoot_assessment,
            ))
            continue
        available = (
            upstream.operation_time_s
            - downstream.operation_time_s
            - pair.downstream_breaker_clearing_time_s
        )
        coordinated = available >= pair.required_cti_s
        grades.append(TransientCoordinationGrade(
            pair.downstream_function_id, pair.upstream_function_id,
            downstream.operation_time_s, upstream.operation_time_s,
            pair.downstream_breaker_clearing_time_s, available,
            pair.required_cti_s,
            "COORDINATED" if coordinated else "NOT_COORDINATED",
            "Transient CTI meets the required margin." if coordinated
            else "Transient CTI is below the required margin.",
            downstream.overshoot_assessment, upstream.overshoot_assessment,
        ))
    return TransientCoordinationReport(
        event_id=str(event_id).strip(),
        relay_outcomes=outcomes,
        grades=tuple(grades),
    )


__all__ = [
    "RelayCurrentSample",
    "RelayCurrentTrace",
    "TransientRelayOutcome",
    "TransientCoordinationGrade",
    "TransientCoordinationReport",
    "evaluate_relay_current_trace",
    "grade_transient_protection_coordination",
]
