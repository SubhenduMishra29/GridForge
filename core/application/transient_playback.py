"""Immutable Application presentation frames for transient-result playback.

Playback is a read-only projection of recorded samples. This module never
invokes a solver, interpolates a sample, or dispatches a control action.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping
from uuid import UUID

from .read_models import (
    TransientDiscontinuityReadModel,
    TransientEventReadModel,
    TransientResultPresentationReadModel,
)
from .revision import ProjectRevision


@dataclass(frozen=True, slots=True)
class TransientPlaybackFrameReadModel:
    """One exact source sample plus evidence recorded at the same timestamp."""

    study_id: UUID
    project_id: str
    activation_generation: int
    source_revision: ProjectRevision
    record_id: UUID | None
    sample_index: int
    time_s: float
    sample_values: Mapping[str, float]
    signal_targets: Mapping[str, Mapping[str, str | None]]
    events: tuple[TransientEventReadModel, ...]
    discontinuity: TransientDiscontinuityReadModel | None
    live_projection_eligible: bool

    def __post_init__(self) -> None:
        if not isinstance(self.study_id, UUID):
            raise TypeError("study_id must be UUID.")
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be non-empty.")
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int) or self.activation_generation < 1:
            raise ValueError("activation_generation must be positive.")
        if not isinstance(self.source_revision, ProjectRevision):
            raise TypeError("source_revision must be ProjectRevision.")
        if self.record_id is not None and not isinstance(self.record_id, UUID):
            raise TypeError("record_id must be UUID or None.")
        if not isinstance(self.sample_values, Mapping) or not isinstance(self.signal_targets, Mapping):
            raise TypeError("sample_values and signal_targets must be mappings.")
        if isinstance(self.sample_index, bool) or not isinstance(self.sample_index, int) or self.sample_index < 0:
            raise ValueError("sample_index must be a non-negative integer.")
        if not isinstance(self.time_s, (int, float)) or isinstance(self.time_s, bool):
            raise TypeError("time_s must be numeric.")
        if not math.isfinite(float(self.time_s)) or float(self.time_s) < 0.0:
            raise ValueError("time_s must be finite and non-negative.")
        values = {str(key): float(value) for key, value in self.sample_values.items()}
        if any(not math.isfinite(value) for value in values.values()):
            raise ValueError("Playback sample values must be finite.")
        targets = {
            str(key): MappingProxyType(dict(value))
            for key, value in self.signal_targets.items()
        }
        object.__setattr__(self, "sample_values", MappingProxyType(values))
        object.__setattr__(self, "signal_targets", MappingProxyType(targets))
        events = tuple(self.events)
        if any(not isinstance(event, TransientEventReadModel) for event in events):
            raise TypeError("events must contain TransientEventReadModel values.")
        object.__setattr__(self, "events", events)
        if self.discontinuity is not None and not isinstance(self.discontinuity, TransientDiscontinuityReadModel):
            raise TypeError("discontinuity must be a TransientDiscontinuityReadModel or None.")
        if not isinstance(self.live_projection_eligible, bool):
            raise TypeError("live_projection_eligible must be bool.")


def build_transient_playback_frame(
    model: TransientResultPresentationReadModel,
    sample_index: int,
) -> TransientPlaybackFrameReadModel:
    """Build one exact frame; simultaneous events retain source dispatch order."""
    if not isinstance(model, TransientResultPresentationReadModel):
        raise TypeError("model must be TransientResultPresentationReadModel.")
    if model.status != "completed":
        raise ValueError("Only completed transient results can be played.")
    if isinstance(sample_index, bool) or not isinstance(sample_index, int):
        raise TypeError("sample_index must be an integer.")
    if sample_index < 0 or sample_index >= model.sample_count:
        raise IndexError(sample_index)
    time_s = model.time_s[sample_index]
    values = {
        signal.signal_id: signal.values[sample_index]
        for signal in model.signals
    }
    targets = {
        signal.signal_id: {
            "label": signal.label,
            "quantity": signal.quantity,
            "unit": signal.unit,
            "machine_id": signal.machine_id,
            "bus_id": signal.bus_id,
            "component": signal.component,
        }
        for signal in model.signals
    }
    tolerance = 1e-12
    events = tuple(
        event for event in model.events
        if abs(event.marker_time - time_s) <= tolerance
    )
    discontinuity = next(
        (item for item in model.discontinuities if abs(item.time_s - time_s) <= tolerance),
        None,
    )
    return TransientPlaybackFrameReadModel(
        study_id=model.study_id,
        project_id=model.project_id,
        activation_generation=model.activation_generation,
        source_revision=model.source_revision,
        record_id=model.record_id,
        sample_index=sample_index,
        time_s=time_s,
        sample_values=values,
        signal_targets=targets,
        events=events,
        discontinuity=discontinuity,
        live_projection_eligible=bool(model.current and not model.historical),
    )


__all__ = ["TransientPlaybackFrameReadModel", "build_transient_playback_frame"]
