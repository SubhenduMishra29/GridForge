"""Detached, archive-safe evidence for augmented generator transient studies.

The value implements Mapping so the canonical StudyResultArchive can persist
its primitive payload without importing plugin dataclasses. Its provenance
attribute also participates in StudyService's existing partial-result retention
contract when a cooperative cancellation returns an interrupted trajectory.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
import math
from types import MappingProxyType
from typing import Any

from .integrator_adapter import GeneratorAugmentedStepResult


def _freeze_archive_value(value: object, *, path: str = "value") -> object:
    """Validate and recursively freeze the primitive archive contract."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} must not contain non-finite numbers")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} mapping keys must be strings")
            frozen[key] = _freeze_archive_value(item, path=f"{path}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_archive_value(item, path=f"{path}[{index}]") for index, item in enumerate(value))
    raise TypeError(f"{path} contains unsupported archive value {type(value).__name__}")


class GeneratorAugmentedStudyEvidence(Mapping[str, object]):
    """Immutable accepted-step trajectory evidence returned by a host solver.

    Only accepted step results are included. Derivative-stage trial evaluations
    remain nested inside each step payload and are explicitly labelled there.
    The host supplies execution/trajectory status; Application still decides
    the terminal StudyResult status and owns durable persistence.
    """

    __slots__ = ("_payload", "_accepted_steps", "provenance", "time")

    def __init__(
        self,
        accepted_steps: Sequence[GeneratorAugmentedStepResult],
        *,
        execution_status: str,
        trajectory_status: str,
        termination: Mapping[str, object] | None = None,
        event_schedule: Sequence[Mapping[str, object]] = (),
        resume_provenance: Mapping[str, object] | None = None,
    ) -> None:
        if isinstance(accepted_steps, (str, bytes)) or not isinstance(accepted_steps, Sequence):
            raise TypeError("accepted_steps must be an ordered sequence")
        steps = tuple(accepted_steps)
        if any(not isinstance(step, GeneratorAugmentedStepResult) for step in steps):
            raise TypeError("accepted_steps must contain GeneratorAugmentedStepResult values")
        if execution_status not in {"completed", "cancelled", "failed"}:
            raise ValueError("execution_status must be completed, cancelled, or failed")
        if trajectory_status not in {"complete", "interrupted", "incomplete"}:
            raise ValueError("trajectory_status must be complete, interrupted, or incomplete")
        if execution_status == "completed" and trajectory_status != "complete":
            raise ValueError("completed execution requires a complete trajectory")
        if execution_status == "cancelled" and trajectory_status != "interrupted":
            raise ValueError("cancelled execution requires an interrupted trajectory")
        times = tuple(step.simulation_time_s for step in steps)
        if any(right <= left for left, right in zip(times, times[1:])):
            raise ValueError("accepted step times must be strictly increasing")
        if any(not isinstance(item, Mapping) for item in event_schedule):
            raise TypeError("event_schedule entries must be mappings")
        if resume_provenance is not None and not isinstance(resume_provenance, Mapping):
            raise TypeError("resume_provenance must be a mapping when supplied")
        provenance_data = _freeze_archive_value({
            "execution_status": execution_status,
            "trajectory_status": trajectory_status,
            "termination": dict(termination or {}),
            "event_schedule": tuple(dict(item) for item in event_schedule),
            "resume": dict(resume_provenance or {}),
        }, path="provenance")
        payload = _freeze_archive_value({
            "schema": "gridforge.generator_augmented_study",
            "schema_version": 1,
            "provenance": provenance_data,
            "accepted_steps": tuple(step.to_archive_payload() for step in steps),
        }, path="study_evidence")
        if not isinstance(provenance_data, Mapping) or not isinstance(payload, Mapping):
            raise TypeError("study evidence payload must be a mapping")
        self.provenance = provenance_data
        self.time = times
        self._payload = payload
        self._accepted_steps = steps

    @classmethod
    def resume_from_checkpoint(
        cls,
        previous: "GeneratorAugmentedStudyEvidence",
        resumed_steps: Sequence[GeneratorAugmentedStepResult],
        *,
        resume_state: Sequence[float],
        execution_status: str,
        trajectory_status: str,
        termination: Mapping[str, object] | None = None,
        event_schedule: Sequence[Mapping[str, object]] = (),
    ) -> "GeneratorAugmentedStudyEvidence":
        """Build a continued trajectory only from the exact last accepted state."""
        if not isinstance(previous, cls):
            raise TypeError("previous must be GeneratorAugmentedStudyEvidence")
        if previous.provenance.get("execution_status") not in {"cancelled", "failed"}:
            raise ValueError("only interrupted or failed evidence can be resumed")
        if not previous.time:
            raise ValueError("cannot resume evidence without an accepted checkpoint")
        if isinstance(resume_state, (str, bytes)) or not isinstance(resume_state, Sequence):
            raise TypeError("resume_state must be an ordered numeric sequence")
        prior_steps = previous._payload.get("accepted_steps")
        if not isinstance(prior_steps, tuple) or not prior_steps:
            raise ValueError("previous evidence has no archived accepted-step payload")
        last_payload = prior_steps[-1]
        if not isinstance(last_payload, Mapping):
            raise ValueError("previous checkpoint payload is malformed")
        accepted_state = last_payload.get("accepted_state")
        if not isinstance(accepted_state, tuple):
            raise ValueError("previous checkpoint has no accepted state vector")
        supplied_state = tuple(resume_state)
        if supplied_state != accepted_state:
            raise ValueError("resume_state must exactly match the last accepted checkpoint state")
        continuation = tuple(resumed_steps)
        if not continuation:
            raise ValueError("resumed_steps must contain at least one accepted step")
        if any(not isinstance(step, GeneratorAugmentedStepResult) for step in continuation):
            raise TypeError("resumed_steps must contain GeneratorAugmentedStepResult values")
        if continuation[0].simulation_time_s <= previous.time[-1]:
            raise ValueError("resumed steps must begin after the prior checkpoint time")
        return cls(
            (*previous._accepted_steps, *continuation),
            execution_status=execution_status,
            trajectory_status=trajectory_status,
            termination=termination,
            event_schedule=event_schedule,
            resume_provenance={
                "previous_schema": "gridforge.generator_augmented_study",
                "previous_schema_version": 1,
                "previous_execution_status": previous.provenance["execution_status"],
                "checkpoint_time_s": previous.time[-1],
                "resumed_step_count": len(continuation),
            },
        )

    @classmethod
    def from_checkpoint_publication_failure(
        cls,
        accepted_steps: Sequence[GeneratorAugmentedStepResult],
        failure: BaseException,
        *,
        termination: Mapping[str, object] | None = None,
        event_schedule: Sequence[Mapping[str, object]] = (),
    ) -> "GeneratorAugmentedStudyEvidence":
        """Retain a numerically accepted step when its checkpoint observer fails."""
        if not isinstance(failure, BaseException):
            raise TypeError("failure must be an exception")
        accepted_step = getattr(failure, "accepted_step_result", None)
        if not isinstance(accepted_step, GeneratorAugmentedStepResult):
            raise ValueError(
                "failure does not carry an accepted GeneratorAugmentedStepResult"
            )
        prior_steps = tuple(accepted_steps)
        if any(not isinstance(step, GeneratorAugmentedStepResult) for step in prior_steps):
            raise TypeError("accepted_steps must contain GeneratorAugmentedStepResult values")
        if prior_steps and accepted_step.simulation_time_s <= prior_steps[-1].simulation_time_s:
            raise ValueError("failed checkpoint time must follow all previously accepted steps")
        if termination is not None and not isinstance(termination, Mapping):
            raise TypeError("termination must be a mapping when supplied")
        details = dict(termination or {})
        details.update({
            "reason": "checkpoint_publication_failed",
            "failing_time": accepted_step.simulation_time_s,
            "cause_type": str(getattr(failure, "cause_type", type(failure).__name__)),
            "diagnostic_message": str(failure),
        })
        return cls(
            (*prior_steps, accepted_step),
            execution_status="failed",
            trajectory_status="incomplete",
            termination=details,
            event_schedule=event_schedule,
        )
    def __getitem__(self, key: str) -> object:
        return self._payload[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._payload)

    def __len__(self) -> int:
        return len(self._payload)


__all__ = ["GeneratorAugmentedStudyEvidence"]
