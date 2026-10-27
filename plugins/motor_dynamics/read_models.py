"""Thread-safe, immutable snapshots for UI projections; never exposes solver ownership."""
from __future__ import annotations
from dataclasses import dataclass
from threading import RLock
from typing import Any, Mapping
import numpy as np

@dataclass(frozen=True)
class SimulationSummary:
    motor_id: str
    status: str
    sample_count: int
    sample_period_s: float
    channels: tuple[str, ...]
    fault: str | None = None

class MotorSimulationReadModelStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._summaries: dict[str, SimulationSummary] = {}
        self._channels: dict[tuple[str, str], np.ndarray] = {}
    def publish(self, motor_id: str, channels: Mapping[str, Any], sample_period_s: float, status: str = "completed", fault: str | None = None) -> None:
        if not isinstance(motor_id, str) or not motor_id.strip():
            raise ValueError("motor_id must be a non-empty string")
        motor_id = motor_id.strip()
        if isinstance(sample_period_s, bool) or not isinstance(sample_period_s, (int, float)):
            raise TypeError("sample_period_s must be numeric")
        if not np.isfinite(float(sample_period_s)) or float(sample_period_s) <= 0:
            raise ValueError("sample_period_s must be finite and positive")
        if not isinstance(channels, Mapping):
            raise TypeError("channels must be a mapping")
        if not isinstance(status, str) or not status.strip():
            raise ValueError("status must be a non-empty string")
        if fault is not None and not isinstance(fault, str):
            raise TypeError("fault must be a string or None")

        frozen: dict[tuple[str, str], np.ndarray] = {}
        for name, values in channels.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("channel names must be non-empty strings")
            raw = np.asarray(values)
            if not np.issubdtype(raw.dtype, np.number) or not np.isrealobj(raw):
                raise TypeError(f"channel {name!r} must contain real numeric values")
            arr = np.asarray(raw, dtype=np.float64).reshape(-1).copy()
            if not np.isfinite(arr).all():
                raise ValueError(f"channel {name!r} contains non-finite values")
            arr.setflags(write=False)
            frozen[(motor_id, name)] = arr

        summary = SimulationSummary(
            motor_id=motor_id,
            status=status.strip(),
            sample_count=max((arr.size for arr in frozen.values()), default=0),
            sample_period_s=float(sample_period_s),
            channels=tuple(sorted(name for _, name in frozen)),
            fault=fault,
        )
        with self._lock:
            # A new publication replaces this motor's complete snapshot. Keeping
            # omitted old channels would mix results from different simulations.
            stale_keys = [key for key in self._channels if key[0] == motor_id]
            for key in stale_keys:
                del self._channels[key]
            self._channels.update(frozen)
            self._summaries[motor_id] = summary
    def get_simulation_summary(self, motor_id: str) -> SimulationSummary | None:
        with self._lock: return self._summaries.get(motor_id)
    def get_raw_channel_vector(self, motor_id: str, channel: str) -> np.ndarray | None:
        with self._lock:
            arr = self._channels.get((motor_id, channel))
            if arr is None: return None
            # Read-only backing array; callers cannot mutate cached simulation results.
            view = arr.view(); view.setflags(write=False); return view
    def snapshot(self) -> tuple[SimulationSummary, ...]:
        with self._lock: return tuple(self._summaries.values())
