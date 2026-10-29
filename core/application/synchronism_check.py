"""Fail-closed ANSI 25 synchronism enforcement contract."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import math
import time
from typing import Callable, Mapping
from core.application.errors import DomainError
from core.model.breaker import Breaker

class BusMode(str, Enum):
    LIVE_LIVE = "LIVE_LIVE"
    LIVE_DEAD = "LIVE_DEAD"
    DEAD_LIVE = "DEAD_LIVE"
    DEAD_DEAD = "DEAD_DEAD"

@dataclass(frozen=True, slots=True)
class SynchronismCheckConfiguration:
    max_voltage_difference_kv: float
    max_phase_angle_difference_deg: float
    max_frequency_difference_hz: float
    max_measurement_age_seconds: float
    dead_bus_voltage_max_kv: float
    allowed_modes: Mapping[BusMode, bool]
    bypass_allowed: bool = False
    def __post_init__(self):
        for name in ("max_voltage_difference_kv","max_phase_angle_difference_deg","max_frequency_difference_hz","max_measurement_age_seconds","dead_bus_voltage_max_kv"):
            value=getattr(self,name)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.max_measurement_age_seconds <= 0 or self.max_phase_angle_difference_deg > 180:
            raise ValueError("Invalid ANSI 25 freshness or phase-angle limit")
        if not isinstance(self.allowed_modes,Mapping) or any(mode not in self.allowed_modes or not isinstance(self.allowed_modes[mode],bool) for mode in BusMode):
            raise ValueError("Explicit boolean permission is required for every live/dead bus mode")
        object.__setattr__(self,"allowed_modes",{mode:self.allowed_modes[mode] for mode in BusMode})
        if not isinstance(self.bypass_allowed,bool): raise TypeError("bypass_allowed must be bool")

@dataclass(frozen=True, slots=True)
class PhasorMeasurement:
    voltage_magnitude_kv: float
    phase_angle_deg: float
    frequency_hz: float
    timestamp: float
    quality: str = "VALID"
    def __post_init__(self):
        for name in ("voltage_magnitude_kv","phase_angle_deg","frequency_hz","timestamp"):
            value=getattr(self,name)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.voltage_magnitude_kv<0 or self.frequency_hz<0: raise ValueError("Voltage and frequency must be non-negative")
        if not isinstance(self.quality,str) or not self.quality.strip(): raise ValueError("quality is required")

@dataclass(frozen=True, slots=True)
class BypassAuthorization:
    authorized_by: str
    reason: str
    expires_at: float
    authorization_id: str
    def valid(self, now: float) -> bool:
        return bool(self.authorized_by.strip() and self.reason.strip() and self.authorization_id.strip() and math.isfinite(self.expires_at) and now < self.expires_at)

@dataclass(frozen=True, slots=True)
class SynchronismDecision:
    permitted: bool
    breaker_id: str
    reason_codes: tuple[str,...]
    mode: BusMode | None
    bypassed: bool = False
    authorization_id: str | None = None

class SynchronismCheckGuard:
    """Project providers supply explicit settings, both bus measurements, and optional bypass authorization."""
    def __init__(self, *, configuration_provider: Callable, measurement_provider: Callable, bypass_provider: Callable | None = None, audit_sink: Callable | None = None, clock: Callable[[],float] = time.time):
        if not callable(configuration_provider) or not callable(measurement_provider): raise TypeError("Configuration and measurement providers are required")
        if bypass_provider is not None and not callable(bypass_provider): raise TypeError("bypass_provider must be callable")
        if audit_sink is not None and not callable(audit_sink): raise TypeError("audit_sink must be callable")
        self._configuration_provider=configuration_provider; self._measurement_provider=measurement_provider
        self._bypass_provider=bypass_provider; self._audit_sink=audit_sink; self._clock=clock

    def authorize_close(self, breaker: Breaker) -> SynchronismDecision:
        if not isinstance(breaker,Breaker): raise TypeError("ANSI 25 guard requires a Breaker")
        now=self._clock(); reasons=[]; mode=None
        config=self._configuration_provider(breaker)
        left=right=None
        if not isinstance(config,SynchronismCheckConfiguration):
            reasons.append("ANSI25_CONFIGURATION_MISSING")
        else:
            measurements=self._measurement_provider(breaker)
            if not isinstance(measurements,tuple) or len(measurements)!=2 or not all(isinstance(m,PhasorMeasurement) for m in measurements):
                reasons.append("ANSI25_MEASUREMENT_MISSING")
            else:
                left,right=measurements
                for side,m in (("LEFT",left),("RIGHT",right)):
                    if m.quality.upper()!="VALID": reasons.append(f"ANSI25_{side}_MEASUREMENT_INVALID")
                    age=now-m.timestamp
                    if age<0 or age>config.max_measurement_age_seconds: reasons.append(f"ANSI25_{side}_MEASUREMENT_STALE")
                if not reasons:
                    ll=left.voltage_magnitude_kv>config.dead_bus_voltage_max_kv
                    rl=right.voltage_magnitude_kv>config.dead_bus_voltage_max_kv
                    mode={(True,True):BusMode.LIVE_LIVE,(True,False):BusMode.LIVE_DEAD,(False,True):BusMode.DEAD_LIVE,(False,False):BusMode.DEAD_DEAD}[(ll,rl)]
                    if not config.allowed_modes[mode]: reasons.append("ANSI25_BUS_MODE_NOT_PERMITTED")
                    if ll and rl:
                        if abs(left.voltage_magnitude_kv-right.voltage_magnitude_kv)>config.max_voltage_difference_kv: reasons.append("ANSI25_VOLTAGE_DIFFERENCE_EXCEEDED")
                        angle=abs((left.phase_angle_deg-right.phase_angle_deg+180.0)%360.0-180.0)
                        if angle>config.max_phase_angle_difference_deg: reasons.append("ANSI25_PHASE_ANGLE_DIFFERENCE_EXCEEDED")
                        if abs(left.frequency_hz-right.frequency_hz)>config.max_frequency_difference_hz: reasons.append("ANSI25_FREQUENCY_DIFFERENCE_EXCEEDED")
        if reasons and config is not None and config.bypass_allowed and self._bypass_provider is not None:
            auth=self._bypass_provider(breaker)
            if isinstance(auth,BypassAuthorization) and auth.valid(now):
                decision=SynchronismDecision(True,breaker.id,tuple(reasons),mode,True,auth.authorization_id)
                self._audit(decision); return decision
            reasons.append("ANSI25_BYPASS_UNAUTHORIZED_OR_EXPIRED")
        decision=SynchronismDecision(not reasons,breaker.id,tuple(reasons),mode)
        self._audit(decision)
        if not decision.permitted:
            raise DomainError(code="ANSI25_CLOSE_REJECTED",message="Breaker close rejected by fail-closed ANSI 25 enforcement.",details={"breaker_id":breaker.id,"reason_codes":decision.reason_codes,"mode":mode.value if mode else None})
        return decision
    def _audit(self, decision):
        if self._audit_sink is not None: self._audit_sink(decision)

__all__=["BusMode","SynchronismCheckConfiguration","PhasorMeasurement","BypassAuthorization","SynchronismDecision","SynchronismCheckGuard"]
