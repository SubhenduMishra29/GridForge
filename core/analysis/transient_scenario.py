"""Immutable transient-study input evidence captured before solver execution.

This module contains detached engineering input records only. Runtime callbacks,
closures, Qt objects and live Core model references are deliberately excluded.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Transient scenario evidence must contain only finite floats.")
    return value


@dataclass(frozen=True, slots=True)
class PowerFlowOperatingPointSnapshot:
    """Exact detached Power Flow input/output identity used to initialize a transient run."""

    snapshot_id: str
    project_id: str
    activation_generation: int
    source_revision: tuple[int, int, int, int]
    topology_revision: int
    bus_ids: tuple[str, ...]
    input_data: Mapping[str, Any]
    solved_voltage_magnitudes: tuple[float, ...]
    solved_voltage_angles: tuple[float, ...]
    solver_iterations: int
    solver_error: float
    solver_history: tuple[float, ...]
    pv_to_pq_transitions: tuple[Mapping[str, Any], ...]
    solver_message: str
    base_mva: float
    bus_voltage_bases_kv: Mapping[str, float]
    nominal_frequency_hz: float
    canonical_topology_fingerprint: str
    network_model: Mapping[str, Any] = field(default_factory=dict)
    ybus_fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.snapshot_id or not self.project_id:
            raise ValueError("Power Flow operating-point snapshot identity is required.")
        if isinstance(self.activation_generation, bool) or self.activation_generation < 1:
            raise ValueError("Power Flow activation generation must be positive.")
        revision = tuple(self.source_revision)
        if len(revision) != 4 or any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in revision):
            raise ValueError("Power Flow source revision must contain four non-negative integers.")
        if isinstance(self.topology_revision, bool) or self.topology_revision < 0:
            raise ValueError("Power Flow topology revision must be non-negative.")
        buses = tuple(self.bus_ids)
        if not buses or len(set(buses)) != len(buses):
            raise ValueError("Power Flow operating point requires unique Bus identities.")
        vm = tuple(float(v) for v in self.solved_voltage_magnitudes)
        va = tuple(float(v) for v in self.solved_voltage_angles)
        if len(vm) != len(buses) or len(va) != len(buses):
            raise ValueError("Power Flow solved voltage arrays must match the canonical Bus ordering.")
        if any(not math.isfinite(v) or v <= 0.0 for v in vm) or any(not math.isfinite(v) for v in va):
            raise ValueError("Power Flow solved voltages must be finite and voltage magnitudes positive.")
        if isinstance(self.solver_iterations, bool) or not isinstance(self.solver_iterations, int) or self.solver_iterations < 0:
            raise ValueError("Power Flow solver iteration count must be a non-negative integer.")
        error = float(self.solver_error)
        history = tuple(float(value) for value in self.solver_history)
        if not math.isfinite(error) and error != float("inf"):
            raise ValueError("Power Flow solver error must be finite or positive infinity.")
        if any(not math.isfinite(value) for value in history):
            raise ValueError("Power Flow solver history must contain finite values.")
        if not isinstance(self.solver_message, str):
            raise TypeError("Power Flow solver message must be a string.")
        object.__setattr__(self, "solver_error", error)
        object.__setattr__(self, "solver_history", history)
        object.__setattr__(self, "pv_to_pq_transitions", tuple(_freeze(item) for item in self.pv_to_pq_transitions))
        base = float(self.base_mva)
        frequency = float(self.nominal_frequency_hz)
        if not math.isfinite(base) or base <= 0 or not math.isfinite(frequency) or frequency <= 0:
            raise ValueError("Power Flow base MVA and nominal frequency must be positive and finite.")
        bases = {str(k): float(v) for k, v in self.bus_voltage_bases_kv.items()}
        if set(bases) != set(buses) or any(not math.isfinite(v) or v <= 0 for v in bases.values()):
            raise ValueError("Power Flow voltage bases must cover every Bus with positive finite values.")
        if len(self.canonical_topology_fingerprint) != 64:
            raise ValueError("Canonical topology fingerprint must be a SHA-256 digest.")
        if self.ybus_fingerprint and len(self.ybus_fingerprint) != 64:
            raise ValueError("YBus fingerprint must be a SHA-256 digest.")
        object.__setattr__(self, "source_revision", revision)
        object.__setattr__(self, "bus_ids", buses)
        object.__setattr__(self, "solved_voltage_magnitudes", vm)
        object.__setattr__(self, "solved_voltage_angles", va)
        object.__setattr__(self, "base_mva", base)
        object.__setattr__(self, "nominal_frequency_hz", frequency)
        object.__setattr__(self, "bus_voltage_bases_kv", _freeze(bases))
        object.__setattr__(self, "input_data", _freeze(self.input_data))
        object.__setattr__(self, "network_model", _freeze(self.network_model))

    def as_dict(self) -> Mapping[str, Any]:
        return _freeze({
            "schema_version": 1,
            "snapshot_id": self.snapshot_id,
            "project_id": self.project_id,
            "activation_generation": self.activation_generation,
            "source_revision": self.source_revision,
            "topology_revision": self.topology_revision,
            "bus_ids": self.bus_ids,
            "input_data": self.input_data,
            "solved_voltage_magnitudes": self.solved_voltage_magnitudes,
            "solved_voltage_angles": self.solved_voltage_angles,
            "solver_iterations": self.solver_iterations,
            "solver_error": self.solver_error,
            "solver_history": self.solver_history,
            "pv_to_pq_transitions": self.pv_to_pq_transitions,
            "solver_message": self.solver_message,
            "base_mva": self.base_mva,
            "bus_voltage_bases_kv": self.bus_voltage_bases_kv,
            "nominal_frequency_hz": self.nominal_frequency_hz,
            "canonical_topology_fingerprint": self.canonical_topology_fingerprint,
            "network_model": self.network_model,
            "ybus_fingerprint": self.ybus_fingerprint,
        })


@dataclass(frozen=True, slots=True)
class TransientEventScenarioItem:
    """Serializable event intent; deliberately contains no executable action."""

    event_id: str
    event_type: str
    time: float
    priority: int = 0
    enabled: bool = True
    description: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    operation: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("Scenario event_id must be non-empty.")
        if not isinstance(self.event_type, str) or not self.event_type.strip():
            raise ValueError("Scenario event_type must be non-empty.")
        time = float(self.time)
        if not math.isfinite(time) or time < 0:
            raise ValueError("Scenario event time must be finite and non-negative.")
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise TypeError("Scenario event priority must be an integer.")
        if type(self.enabled) is not bool:
            raise TypeError("Scenario event enabled must be bool.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("Scenario event metadata must be a mapping.")
        if self.operation is not None and not isinstance(self.operation, Mapping):
            raise TypeError("Scenario event operation must be a mapping when supplied.")
        object.__setattr__(self, "event_id", self.event_id.strip())
        object.__setattr__(self, "event_type", self.event_type.strip())
        object.__setattr__(self, "time", time)
        object.__setattr__(self, "metadata", _freeze(self.metadata))
        if self.operation is not None:
            object.__setattr__(self, "operation", _freeze(self.operation))
        if not isinstance(self.description, str):
            raise TypeError("Scenario event description must be a string.")

    def as_dict(self) -> Mapping[str, Any]:
        return _freeze({
            "event_id": self.event_id, "event_type": self.event_type,
            "time": self.time, "priority": self.priority, "enabled": self.enabled,
            "description": self.description, "metadata": self.metadata,
            "operation": self.operation,
        })


@dataclass(frozen=True, slots=True)
class TransientEventScenario:
    """Canonical ordered scenario definition captured before execution."""

    events: tuple[TransientEventScenarioItem, ...] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        events = tuple(self.events)
        if any(not isinstance(item, TransientEventScenarioItem) for item in events):
            raise TypeError("Transient scenario events must be TransientEventScenarioItem records.")
        ids = tuple(item.event_id for item in events)
        if len(ids) != len(set(ids)):
            raise ValueError("Transient scenario event identities must be unique.")
        if isinstance(self.schema_version, bool) or self.schema_version != 1:
            raise ValueError("Unsupported transient scenario schema version.")
        object.__setattr__(self, "events", tuple(sorted(events, key=lambda item: (item.time, item.priority, item.event_id))))

    def as_dict(self) -> Mapping[str, Any]:
        return _freeze({
            "schema_version": self.schema_version,
            "events": tuple(item.as_dict() for item in self.events),
        })


__all__ = [
    "PowerFlowOperatingPointSnapshot",
    "TransientEventScenarioItem",
    "TransientEventScenario",
]
