"""Application orchestration for freshness-validated Dynamic Control inputs.

This adapter keeps measurement discovery and sample validity in Application.
The Core DynamicControlRuntime receives only detached, resolved input values.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from core.control.dynamic.runtime import (
    DynamicControlRuntime,
    GlobalStateLayout,
)
from .control_signal_mapping import (
    ControlSignalMapping,
    ControlSignalResolution,
)
from .read_service import ReadService


@dataclass(frozen=True, slots=True)
class DynamicControlCycleResult:
    """Numerical Dynamic Control result paired with its input provenance."""

    derivatives: np.ndarray
    outputs: Mapping[str, Mapping[str, Any]]
    resolution: ControlSignalResolution

    def __post_init__(self) -> None:
        values = np.asarray(self.derivatives, dtype=float).copy()
        values.setflags(write=False)
        object.__setattr__(self, "derivatives", values)
        frozen_outputs = {
            str(controller_id): MappingProxyType(dict(values))
            for controller_id, values in self.outputs.items()
        }
        object.__setattr__(self, "outputs", MappingProxyType(frozen_outputs))


class DynamicControlCycleService:
    """Resolve validated Application inputs before invoking dynamic runtime."""

    def __init__(
        self,
        runtime: DynamicControlRuntime,
        signal_mapping: ControlSignalMapping,
        *,
        read_service: ReadService,
        measurement_read_service: Any | None = None,
    ) -> None:
        if not isinstance(runtime, DynamicControlRuntime):
            raise TypeError("runtime must be a DynamicControlRuntime.")
        if not isinstance(signal_mapping, ControlSignalMapping):
            raise TypeError("signal_mapping must be a ControlSignalMapping.")
        if not isinstance(read_service, ReadService):
            raise TypeError("read_service must implement ReadService.")
        if any(binding.source.domain == "measurement" for binding in signal_mapping.bindings):
            raise ValueError(
                "Offline/transient Dynamic Control cannot consume live MeasurementChannel samples; "
                "a study-scoped simulation-clock measurement snapshot contract is required."
            )
        if measurement_read_service is not None and not callable(
            getattr(measurement_read_service, "channel", None)
        ):
            raise TypeError("measurement_read_service must provide channel(channel_id).")
        self._runtime = runtime
        self._signal_mapping = signal_mapping
        self._read_service = read_service
        self._measurement_read_service = measurement_read_service

    def resolve_inputs(
        self,
        *,
        simulation_time: float,
        timestamp_domain: str | None = None,
    ) -> ControlSignalResolution:
        """Resolve all controller inputs against one authoritative cycle time."""
        return self._signal_mapping.resolve(
            self._read_service,
            measurement_read_service=self._measurement_read_service,
            current_time=simulation_time,
            timestamp_domain=timestamp_domain,
        )

    def derivatives(
        self,
        global_state: np.ndarray,
        layout: GlobalStateLayout,
        associations: Sequence[Any],
        *,
        simulation_time: float,
        timestamp_domain: str | None = None,
    ) -> DynamicControlCycleResult:
        """Evaluate dynamic controllers with one immutable resolved input snapshot."""
        resolution = self.resolve_inputs(
            simulation_time=simulation_time,
            timestamp_domain=timestamp_domain,
        )
        derivatives, outputs = self._runtime.derivatives(
            global_state,
            layout,
            associations,
            resolution.external_inputs,
            simulation_time,
        )
        return DynamicControlCycleResult(
            derivatives=derivatives,
            outputs=outputs,
            resolution=resolution,
        )

    def initial_controller_state(
        self,
        associations: Sequence[Any],
        *,
        simulation_time: float,
        timestamp_domain: str | None = None,
    ) -> Mapping[str, tuple[float, ...]]:
        """Initialize dynamic controllers from the same validated input boundary."""
        resolution = self.resolve_inputs(
            simulation_time=simulation_time,
            timestamp_domain=timestamp_domain,
        )
        return self._runtime.initial_controller_state(
            associations,
            resolution.external_inputs,
        )


__all__ = ["DynamicControlCycleResult", "DynamicControlCycleService"]