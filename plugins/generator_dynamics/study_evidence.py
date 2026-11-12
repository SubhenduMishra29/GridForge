"""Detached, archive-safe evidence for augmented generator transient studies.

The value implements Mapping so the canonical StudyResultArchive can persist
its primitive payload without importing plugin dataclasses. Its provenance
attribute also participates in StudyService's existing partial-result retention
contract when a cooperative cancellation returns an interrupted trajectory.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from types import MappingProxyType
from typing import Any

from .integrator_adapter import GeneratorAugmentedStepResult


class GeneratorAugmentedStudyEvidence(Mapping[str, object]):
    """Immutable accepted-step trajectory evidence returned by a host solver.

    Only accepted step results are included. Derivative-stage trial evaluations
    remain nested inside each step payload and are explicitly labelled there.
    The host supplies execution/trajectory status; Application still decides
    the terminal StudyResult status and owns durable persistence.
    """

    __slots__ = ("_payload", "provenance", "time")

    def __init__(
        self,
        accepted_steps: Sequence[GeneratorAugmentedStepResult],
        *,
        execution_status: str,
        trajectory_status: str,
        termination: Mapping[str, object] | None = None,
        event_schedule: Sequence[Mapping[str, object]] = (),
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
        provenance_data: dict[str, object] = {
            "execution_status": execution_status,
            "trajectory_status": trajectory_status,
            "termination": dict(termination or {}),
            "event_schedule": tuple(dict(item) for item in event_schedule),
        }
        self.provenance = MappingProxyType(provenance_data)
        self.time = times
        self._payload = MappingProxyType({
            "schema": "gridforge.generator_augmented_study",
            "schema_version": 1,
            "provenance": provenance_data,
            "accepted_steps": tuple(step.to_archive_payload() for step in steps),
        })

    def __getitem__(self, key: str) -> object:
        return self._payload[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._payload)

    def __len__(self) -> int:
        return len(self._payload)


__all__ = ["GeneratorAugmentedStudyEvidence"]
