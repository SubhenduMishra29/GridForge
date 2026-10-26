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
        if not motor_id or sample_period_s <= 0: raise ValueError("motor_id and positive sample period required")
        frozen = {}
        for name, values in channels.items():
            arr = np.asarray(values, dtype=np.float64).reshape(-1).copy()
            arr.setflags(write=False); frozen[(motor_id, str(name))] = arr
        with self._lock:
            self._channels.update(frozen)
            self._summaries[motor_id] = SimulationSummary(motor_id, status, max((a.size for a in frozen.values()), default=0), float(sample_period_s), tuple(sorted(channels)), fault)
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
