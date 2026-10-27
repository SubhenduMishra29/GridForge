"""Headless signal features for induction motor diagnostic channels."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from scipy.signal import periodogram

@dataclass(frozen=True)
class DiagnosticVerdict:
    motor_id: str
    fundamental_hz: float
    fundamental_rms: float
    thd_percent: float
    sideband_ratio: float
    classification: str
    confidence: float
    def to_dict(self): return asdict(self)

class MotorAIDiagnosticNode:
    def __init__(self, supply_hz: float = 50.0, harmonics: int = 10) -> None:
        if supply_hz <= 0 or harmonics < 2: raise ValueError("invalid diagnostic configuration")
        self.supply_hz, self.harmonics = float(supply_hz), int(harmonics)
    def analyze(self, motor_id: str, current: np.ndarray, sample_period_s: float, slip_hz: float | None = None) -> DiagnosticVerdict:
        x = np.asarray(current, dtype=np.float64).reshape(-1)
        if x.size < 32 or sample_period_s <= 0 or not np.isfinite(x).all(): raise ValueError("finite current window of >=32 samples and positive sample period required")
        # Analyze the stable tail; do not infer electrical truth from graphics.
        x = x[x.size // 2:]; x = x - x.mean()
        f, p = periodogram(x, fs=1.0 / sample_period_s, window="hann", scaling="spectrum")
        band = (f >= self.supply_hz * .8) & (f <= self.supply_hz * 1.2)
        if not band.any(): raise ValueError("sampling rate/window cannot resolve 50 Hz fundamental")
        k = np.flatnonzero(band)[np.argmax(p[band])]; f0 = float(f[k]); fundamental = float(np.sqrt(max(p[k], 0.0)))
        harmonic_power = 0.0
        for h in range(2, self.harmonics + 1):
            m = (f >= h*f0*.98) & (f <= h*f0*1.02)
            if m.any(): harmonic_power += float(np.max(p[m]))
        thd = 100.0 * np.sqrt(harmonic_power) / max(fundamental, 1e-12)
        sb = np.zeros_like(f, dtype=bool)
        if slip_hz is not None and slip_hz > 0: sb |= (np.abs(f-(self.supply_hz-2*slip_hz)) < max(1.0, slip_hz*.15)) | (np.abs(f-(self.supply_hz+2*slip_hz)) < max(1.0, slip_hz*.15))
        sideband = float(np.sqrt(p[sb].sum()) / max(fundamental, 1e-12)) if sb.any() else 0.0
        label = "bearing_or_rotor_review" if sideband > .12 else ("harmonic_distortion_review" if thd > 8.0 else "nominal")
        confidence = float(np.clip(max(sideband/.25, thd/15.0), .0, .99)) if label != "nominal" else .8
        return DiagnosticVerdict(motor_id, f0, fundamental, float(thd), sideband, label, confidence)
