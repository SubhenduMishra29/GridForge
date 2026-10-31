"""Explicit residual-current configuration and fail-closed phasor resolver.

Residual current is either derived from three phase-current samples at one
explicit measurement point or supplied by a separately configured neutral CT
or core-balance CT. This module never infers a protected zone or combines
unrelated measurement channels.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ResidualCurrentInputConfiguration:
    """Persisted source contract for one 50N/51N residual-current input."""

    mode: str
    measurement_point_id: str
    phase_binding_ids: Mapping[str, str] | None = None
    direct_binding_id: str | None = None

    def __post_init__(self) -> None:
        mode = str(self.mode).strip().upper()
        if mode not in {"THREE_PHASE_SUM", "NEUTRAL_CT", "CBCT"}:
            raise ValueError("Residual-current mode must be THREE_PHASE_SUM, NEUTRAL_CT, or CBCT.")
        point = self.measurement_point_id
        if not isinstance(point, str) or not point.strip():
            raise ValueError("Residual-current configuration requires an explicit measurement_point_id.")
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "measurement_point_id", point.strip())
        if mode == "THREE_PHASE_SUM":
            if not isinstance(self.phase_binding_ids, Mapping):
                raise TypeError("THREE_PHASE_SUM requires explicit phase_binding_ids.")
            phases = dict(self.phase_binding_ids)
            if set(phases) != {"A", "B", "C"}:
                raise ValueError("THREE_PHASE_SUM requires exactly A, B, and C binding identities.")
            if any(not isinstance(value, str) or not value.strip() for value in phases.values()):
                raise ValueError("Every phase binding identity must be non-empty.")
            if len(set(phases.values())) != 3:
                raise ValueError("A, B, and C must use three distinct measurement bindings.")
            if self.direct_binding_id is not None:
                raise ValueError("THREE_PHASE_SUM cannot also declare a direct neutral/CBCT binding.")
            object.__setattr__(self, "phase_binding_ids", MappingProxyType({k: v.strip() for k, v in phases.items()}))
        else:
            if not isinstance(self.direct_binding_id, str) or not self.direct_binding_id.strip():
                raise ValueError(f"{mode} requires one explicit direct_binding_id.")
            if self.phase_binding_ids is not None:
                raise ValueError(f"{mode} cannot declare phase_binding_ids.")
            object.__setattr__(self, "direct_binding_id", self.direct_binding_id.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "measurement_point_id": self.measurement_point_id,
            "phase_binding_ids": dict(self.phase_binding_ids) if self.phase_binding_ids is not None else None,
            "direct_binding_id": self.direct_binding_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ResidualCurrentInputConfiguration":
        if not isinstance(data, Mapping):
            raise TypeError("Residual-current input configuration must be a mapping.")
        return cls(
            mode=data["mode"],
            measurement_point_id=data["measurement_point_id"],
            phase_binding_ids=data.get("phase_binding_ids"),
            direct_binding_id=data.get("direct_binding_id"),
        )


@dataclass(frozen=True, slots=True)
class ResidualCurrentSample:
    """Detached residual-current phasor and its explicit source provenance."""

    value: complex
    unit: str
    scenario_id: str
    measurement_point_id: str
    topology_revision: int
    reference_basis_id: str
    source_mode: str
    source_binding_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        value = complex(self.value)
        if not isfinite(value.real) or not isfinite(value.imag):
            raise ValueError("Residual-current phasor must be finite.")
        if self.unit != "A":
            raise ValueError("Residual-current sample must use canonical amperes.")
        for name in ("scenario_id", "measurement_point_id", "reference_basis_id"):
            item = getattr(self, name)
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"{name} must be non-empty.")
            object.__setattr__(self, name, item.strip())
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int) or self.topology_revision < 0:
            raise ValueError("topology_revision must be a non-negative integer.")
        if self.source_mode not in {"THREE_PHASE_SUM", "NEUTRAL_CT", "CBCT"}:
            raise ValueError("Unsupported residual-current sample source mode.")
        bindings = tuple(self.source_binding_ids)
        if not bindings or any(not isinstance(item, str) or not item.strip() for item in bindings):
            raise ValueError("Residual-current sample requires explicit source binding identities.")
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "source_binding_ids", bindings)


@dataclass(frozen=True, slots=True)
class ResidualCurrentSourceSample:
    """One CT sample normalized to the common primary-current basis."""
    binding_id: str
    scenario_id: str
    phase_or_sequence: str
    value: complex
    unit: str
    reference_basis_id: str
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        for name in ("binding_id", "scenario_id", "phase_or_sequence", "reference_basis_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty.")
            object.__setattr__(self, name, value.strip())
        value = complex(self.value)
        if not isfinite(value.real) or not isfinite(value.imag):
            raise ValueError("Normalized residual-current source must be finite.")
        if self.unit != "A" or self.reference_basis_id != "PRIMARY_AMPS":
            raise ValueError("Residual-current source must use amperes on PRIMARY_AMPS basis.")
        if not isinstance(self.provenance, Mapping) or self.provenance.get("primary_current_normalized") is not True:
            raise ValueError("Primary-current normalization provenance is required.")
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


def normalize_residual_current_source(sample: Any, *, measurement_point_id: str, instrument_ratio: float, channel_scale: float, channel_polarity: float) -> ResidualCurrentSourceSample:
    """Normalize a validated CT-secondary sample to signed primary amperes.
    CT orientation and physical CT polarity must already have been applied.
    This applies channel scale/polarity and CT ratio exactly once.
    """
    if not isinstance(measurement_point_id, str) or not measurement_point_id.strip():
        raise ValueError("An explicit measurement_point_id is required.")
    if getattr(sample, "unit", None) != "A":
        raise ValueError("Residual-current normalization requires CT-secondary amperes.")
    provenance = getattr(sample, "provenance", None)
    if not isinstance(provenance, Mapping):
        raise ValueError("Residual-current source sample requires provenance.")
    revision = provenance.get("topology_revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise ValueError("Residual-current source requires a valid topology revision.")
    try:
        ratio, scale, polarity = float(instrument_ratio), float(channel_scale), float(channel_polarity)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("CT ratio and channel scale/polarity must be numeric.") from exc
    if not all(isfinite(v) for v in (ratio, scale, polarity)) or ratio <= 0.0:
        raise ValueError("CT ratio must be positive and channel scale/polarity finite.")
    primary = complex(sample.value) * scale * polarity * ratio
    if not isfinite(primary.real) or not isfinite(primary.imag):
        raise ValueError("Normalized primary-current phasor is non-finite.")
    normalized_provenance = dict(provenance)
    normalized_provenance.update({"measurement_point_id": measurement_point_id.strip(), "primary_current_normalized": True, "primary_current_basis": "PRIMARY_AMPS", "normalization_instrument_ratio": ratio, "normalization_channel_scale": scale, "normalization_channel_polarity": polarity})
    return ResidualCurrentSourceSample(binding_id=sample.binding_id, scenario_id=sample.scenario_id, phase_or_sequence=sample.phase_or_sequence, value=primary, unit="A", reference_basis_id="PRIMARY_AMPS", provenance=normalized_provenance)


def resolve_residual_current(
    configuration: ResidualCurrentInputConfiguration,
    samples_by_binding: Mapping[str, Any],
) -> ResidualCurrentSample:
    """Resolve a configured residual-current input without source inference.

    Each source sample must expose value, unit, scenario_id, phase_or_sequence,
    reference_basis_id='PRIMARY_AMPS' and provenance containing an explicit
    measurement_point_id, topology_revision, and verified normalization flag.
    CT-secondary samples must be normalized independently before resolution.
    """
    if not isinstance(configuration, ResidualCurrentInputConfiguration):
        raise TypeError("configuration must be ResidualCurrentInputConfiguration.")
    if not isinstance(samples_by_binding, Mapping):
        raise TypeError("samples_by_binding must be a mapping.")

    if configuration.mode == "THREE_PHASE_SUM":
        expected = dict(configuration.phase_binding_ids or {})
        selected = []
        for phase in ("A", "B", "C"):
            binding_id = expected[phase]
            sample = samples_by_binding.get(binding_id)
            if sample is None:
                raise ValueError(f"Missing configured {phase}-phase current sample {binding_id!r}.")
            if str(getattr(sample, "phase_or_sequence", "")).upper() != phase:
                raise ValueError(f"Binding {binding_id!r} is not an explicit {phase}-phase current sample.")
            selected.append((binding_id, sample))
    else:
        binding_id = configuration.direct_binding_id
        sample = samples_by_binding.get(binding_id)
        if sample is None:
            raise ValueError(f"Missing configured direct residual-current sample {binding_id!r}.")
        if str(getattr(sample, "phase_or_sequence", "")).upper() not in {"N", "RESIDUAL"}:
            raise ValueError("Neutral CT/CBCT input must be explicitly classified as N or RESIDUAL.")
        direct_provenance = getattr(sample, "provenance", None)
        if not isinstance(direct_provenance, Mapping) or direct_provenance.get("residual_source_mode") != configuration.mode:
            raise ValueError("Direct neutral/CBCT sample provenance must explicitly declare the configured residual source mode.")
        selected = [(binding_id, sample)]

    values = []
    canonical = None
    for binding_id, sample in selected:
        if getattr(sample, "binding_id", None) != binding_id:
            raise ValueError(f"Residual-current source identity does not match configured binding {binding_id!r}.")
        if getattr(sample, "unit", None) != "A":
            raise ValueError(f"Residual-current source {binding_id!r} is not expressed in amperes.")
        if getattr(sample, "reference_basis_id", None) != "PRIMARY_AMPS":
            raise ValueError(f"Residual-current source {binding_id!r} is not normalized to primary amperes.")
        provenance = getattr(sample, "provenance", None)
        if not isinstance(provenance, Mapping) or provenance.get("primary_current_normalized") is not True:
            raise ValueError(f"Residual-current source {binding_id!r} lacks verified primary-current normalization provenance.")
        current = (
            getattr(sample, "scenario_id", None),
            provenance.get("measurement_point_id"),
            provenance.get("topology_revision"),
            getattr(sample, "reference_basis_id", None),
        )
        if current[1] != configuration.measurement_point_id:
            raise ValueError(f"Residual-current source {binding_id!r} belongs to a different measurement point.")
        if any(value is None for value in current):
            raise ValueError(f"Residual-current source {binding_id!r} has incomplete scenario/topology/basis provenance.")
        if canonical is None:
            canonical = current
        elif current != canonical:
            raise ValueError("Residual-current sources do not share identical scenario, measurement point, topology revision, and primary-current basis.")
        phasor = complex(getattr(sample, "value"))
        if not isfinite(phasor.real) or not isfinite(phasor.imag):
            raise ValueError(f"Residual-current source {binding_id!r} is non-finite.")
        values.append(phasor)

    total = sum(values, 0j)
    if canonical is None:
        raise ValueError("Residual-current resolver received no source samples.")
    return ResidualCurrentSample(
        value=total,
        unit="A",
        scenario_id=canonical[0],
        measurement_point_id=canonical[1],
        topology_revision=canonical[2],
        reference_basis_id=canonical[3],
        source_mode=configuration.mode,
        source_binding_ids=tuple(binding_id for binding_id, _ in selected),
    )


__all__ = [
    "ResidualCurrentInputConfiguration",
    "ResidualCurrentSample",
    "ResidualCurrentSourceSample",
    "normalize_residual_current_source",
    "resolve_residual_current",
]
