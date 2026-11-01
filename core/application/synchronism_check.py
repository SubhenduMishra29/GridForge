"""Fail-closed ANSI 25 synchronism enforcement contract."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
import math
import time
from typing import Callable, Mapping
from threading import Lock
from core.application.errors import DomainError
from core.model.breaker import Breaker
from core.measurement.measurement_channel import MeasurementChannel, MeasurementQuality, MeasurementSignalType
from core.model.endpoint_reference import EndpointReference, EquipmentType
from core.network.connectivity import ConnectivityResolver

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
    max_measurement_skew_seconds: float
    dead_bus_voltage_max_kv: float
    allowed_modes: Mapping[BusMode, bool]
    measurement_channel_ids: Mapping[str, str]
    bypass_allowed: bool
    def __post_init__(self):
        for name in ("max_voltage_difference_kv","max_phase_angle_difference_deg","max_frequency_difference_hz","max_measurement_age_seconds","max_measurement_skew_seconds","dead_bus_voltage_max_kv"):
            value=getattr(self,name)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.max_measurement_age_seconds <= 0 or self.max_measurement_skew_seconds <= 0 or self.max_measurement_skew_seconds > self.max_measurement_age_seconds or self.max_phase_angle_difference_deg > 180:
            raise ValueError("Invalid ANSI 25 freshness, sample-skew, or phase-angle limit")
        if not isinstance(self.allowed_modes, Mapping):
            raise ValueError("Explicit boolean permission is required for every live/dead bus mode")
        supplied = {}
        for key, value in self.allowed_modes.items():
            try:
                mode = key if isinstance(key, BusMode) else BusMode(key)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Unknown live/dead bus mode: {key!r}") from exc
            if not isinstance(value, bool):
                raise ValueError(f"Permission for {mode.value} must be bool")
            supplied[mode] = value
        if any(mode not in supplied for mode in BusMode):
            raise ValueError("Explicit boolean permission is required for every live/dead bus mode")
        object.__setattr__(self, "allowed_modes", MappingProxyType({mode: supplied[mode] for mode in BusMode}))
        channel_keys = {
            "left_voltage", "left_phase_angle", "left_frequency",
            "right_voltage", "right_phase_angle", "right_frequency",
        }
        if not isinstance(self.measurement_channel_ids, Mapping):
            raise ValueError("Explicit measurement-channel IDs are required for both bus sides.")
        if set(self.measurement_channel_ids) != channel_keys:
            raise ValueError(
                "ANSI 25 requires exactly six measurement-channel IDs: "
                + ", ".join(sorted(channel_keys))
            )
        normalized_channels = {}
        for key, channel_id in self.measurement_channel_ids.items():
            if not isinstance(channel_id, str) or not channel_id.strip() or channel_id != channel_id.strip():
                raise ValueError(f"Measurement channel ID for {key} must be a canonical non-empty string.")
            normalized_channels[key] = channel_id
        if len(set(normalized_channels.values())) != 6:
            raise ValueError("ANSI 25 voltage, phase-angle and frequency channels must be six distinct IDs.")
        object.__setattr__(self, "measurement_channel_ids", MappingProxyType(normalized_channels))
        if not isinstance(self.bypass_allowed,bool): raise TypeError("bypass_allowed must be bool")
    def to_dict(self) -> dict:
        """Return a JSON-compatible, explicit project-persistence representation."""
        return {
            "max_voltage_difference_kv": self.max_voltage_difference_kv,
            "max_phase_angle_difference_deg": self.max_phase_angle_difference_deg,
            "max_frequency_difference_hz": self.max_frequency_difference_hz,
            "max_measurement_age_seconds": self.max_measurement_age_seconds,
            "max_measurement_skew_seconds": self.max_measurement_skew_seconds,
            "dead_bus_voltage_max_kv": self.dead_bus_voltage_max_kv,
            "allowed_modes": {mode.value: self.allowed_modes[mode] for mode in BusMode},
            "measurement_channel_ids": dict(self.measurement_channel_ids),
            "bypass_allowed": self.bypass_allowed,
        }

    @classmethod
    def from_dict(cls, data: Mapping) -> "SynchronismCheckConfiguration":
        """Reconstruct configuration without silently filling missing settings."""
        if not isinstance(data, Mapping):
            raise TypeError("ANSI 25 configuration must be a mapping")
        required = {
            "max_voltage_difference_kv", "max_phase_angle_difference_deg",
            "max_frequency_difference_hz", "max_measurement_age_seconds",
            "max_measurement_skew_seconds", "dead_bus_voltage_max_kv", "allowed_modes", "measurement_channel_ids", "bypass_allowed",
        }
        missing = required.difference(data)
        extra = set(data).difference(required)
        if missing or extra:
            raise ValueError(
                f"ANSI 25 configuration keys invalid; missing={sorted(missing)}, "
                f"unexpected={sorted(extra)}"
            )
        return cls(
            max_voltage_difference_kv=data["max_voltage_difference_kv"],
            max_phase_angle_difference_deg=data["max_phase_angle_difference_deg"],
            max_frequency_difference_hz=data["max_frequency_difference_hz"],
            max_measurement_age_seconds=data["max_measurement_age_seconds"],
            max_measurement_skew_seconds=data["max_measurement_skew_seconds"],
            dead_bus_voltage_max_kv=data["dead_bus_voltage_max_kv"],
            allowed_modes=data["allowed_modes"],
            measurement_channel_ids=data["measurement_channel_ids"],
            bypass_allowed=data["bypass_allowed"],
        )


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
    """Short-lived, single-use authorization scoped to one project breaker activation."""

    authorized_by: str
    reason: str
    authorization_id: str
    breaker_id: str
    project_id: str
    activation_generation: int
    issued_at: float
    expires_at: float

    def __post_init__(self):
        for name in ("authorized_by", "reason", "authorization_id", "breaker_id", "project_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer")
        for name in ("issued_at", "expires_at"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{name} must be a finite timestamp")
        if self.expires_at <= self.issued_at:
            raise ValueError("Bypass authorization expiry must follow its issue time")
        if self.expires_at - self.issued_at > 300.0:
            raise ValueError("ANSI 25 bypass authorization lifetime cannot exceed five minutes")

    def valid_for(self, *, now: float, breaker_id: str, project_id: str, activation_generation: int) -> bool:
        return (
            self.issued_at <= now < self.expires_at
            and self.breaker_id == breaker_id
            and self.project_id == project_id
            and self.activation_generation == activation_generation
        )

@dataclass(frozen=True, slots=True)
class SynchronismDecision:
    permitted: bool
    breaker_id: str
    reason_codes: tuple[str,...]
    mode: BusMode | None
    bypassed: bool = False
    authorization_id: str | None = None
    bypass_authorized_by: str | None = None
    bypass_reason: str | None = None
    bypass_expires_at: float | None = None
    bypass_issued_at: float | None = None
    bypass_project_id: str | None = None
    bypass_activation_generation: int | None = None

@dataclass(frozen=True, slots=True)
class SynchronismCheckProjectConfiguration:
    """Explicit per-breaker ANSI 25 policy registry for one project."""

    breakers: Mapping[str, SynchronismCheckConfiguration]

    def __post_init__(self) -> None:
        if not isinstance(self.breakers, Mapping):
            raise TypeError("ANSI 25 project configuration breakers must be a mapping.")
        normalized: dict[str, SynchronismCheckConfiguration] = {}
        for breaker_id, configuration in self.breakers.items():
            if not isinstance(breaker_id, str) or not breaker_id.strip() or breaker_id != breaker_id.strip():
                raise ValueError("ANSI 25 breaker IDs must be canonical non-empty strings.")
            if not isinstance(configuration, SynchronismCheckConfiguration):
                raise TypeError(f"ANSI 25 policy for breaker {breaker_id!r} is not typed.")
            normalized[breaker_id] = configuration
        object.__setattr__(self, "breakers", MappingProxyType(normalized))

    def for_breaker(self, breaker_id: str) -> SynchronismCheckConfiguration | None:
        return self.breakers.get(breaker_id)

    def to_dict(self) -> dict:
        return {
            "schema": 2,
            "breakers": {
                breaker_id: configuration.to_dict()
                for breaker_id, configuration in self.breakers.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping) -> "SynchronismCheckProjectConfiguration":
        if not isinstance(data, Mapping) or set(data) != {"schema", "breakers"} or data.get("schema") != 2:
            raise ValueError("ANSI 25 project configuration requires exactly schema=2 and breakers; legacy policies require explicit migration.")
        raw_breakers = data["breakers"]
        if not isinstance(raw_breakers, Mapping):
            raise TypeError("ANSI 25 project configuration breakers must be an object.")
        return cls({
            breaker_id: SynchronismCheckConfiguration.from_dict(configuration)
            for breaker_id, configuration in raw_breakers.items()
        })


def phasor_measurements_from_channels(
    configuration: SynchronismCheckConfiguration,
    channels: Mapping[str, MeasurementChannel],
    *,
    now: float,
) -> tuple[PhasorMeasurement, PhasorMeasurement]:
    """Build ANSI 25 side measurements from six explicitly bound logical channels.

    Channel timestamps and ``now`` must use the same time domain as the guard
    clock. Wall-clock and simulation-time timestamps must never be mixed.
    Only canonical engineering units are accepted; this adapter never guesses or
    silently converts units.
    """
    if not isinstance(configuration, SynchronismCheckConfiguration):
        raise TypeError("ANSI 25 configuration is required.")
    if not isinstance(channels, Mapping):
        raise TypeError("Measurement channel registry must be a mapping.")
    if isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(now):
        raise ValueError("ANSI 25 evaluation time must be a finite timestamp.")

    specifications = {
        "left_voltage": (MeasurementSignalType.VOLTAGE, {"kv"}, "voltage_magnitude_kv"),
        "left_phase_angle": (MeasurementSignalType.PHASE_ANGLE, {"deg", "°"}, "phase_angle_deg"),
        "left_frequency": (MeasurementSignalType.FREQUENCY, {"hz"}, "frequency_hz"),
        "right_voltage": (MeasurementSignalType.VOLTAGE, {"kv"}, "voltage_magnitude_kv"),
        "right_phase_angle": (MeasurementSignalType.PHASE_ANGLE, {"deg", "°"}, "phase_angle_deg"),
        "right_frequency": (MeasurementSignalType.FREQUENCY, {"hz"}, "frequency_hz"),
    }
    values: dict[str, tuple[float, float, str]] = {}
    for key, (expected_type, accepted_units, field_name) in specifications.items():
        channel_id = configuration.measurement_channel_ids[key]
        channel = channels.get(channel_id)
        if not isinstance(channel, MeasurementChannel):
            raise ValueError(f"ANSI 25 channel {key!r} ({channel_id!r}) is missing.")
        if channel.signal_type is not expected_type:
            raise ValueError(f"ANSI 25 channel {channel_id!r} has the wrong signal type.")
        if not isinstance(channel.unit, str) or channel.unit.strip().lower() not in accepted_units:
            raise ValueError(f"ANSI 25 channel {channel_id!r} has an unsupported or missing engineering unit.")
        if not channel.available or channel.quality is not MeasurementQuality.GOOD:
            raise ValueError(f"ANSI 25 channel {channel_id!r} is unavailable or quality is not GOOD.")
        if channel.timestamp is None or isinstance(channel.timestamp, bool) or not isinstance(channel.timestamp, (int, float)) or not math.isfinite(channel.timestamp):
            raise ValueError(f"ANSI 25 channel {channel_id!r} has no valid sample timestamp.")
        age = now - channel.timestamp
        if age < 0 or age > configuration.max_measurement_age_seconds:
            raise ValueError(f"ANSI 25 channel {channel_id!r} is future-dated or stale.")
        value = channel.engineering_value
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"ANSI 25 channel {channel_id!r} has a non-finite or non-scalar engineering value.")
        values[key] = (float(value), float(channel.timestamp), field_name)

    sample_timestamps = tuple(timestamp for _, timestamp, _ in values.values())
    sample_skew = max(sample_timestamps) - min(sample_timestamps)
    if sample_skew > configuration.max_measurement_skew_seconds:
        raise ValueError(
            "ANSI 25 six-channel phasor snapshot exceeds max_measurement_skew_seconds."
        )
    left_timestamp = min(values["left_voltage"][1], values["left_phase_angle"][1], values["left_frequency"][1])
    right_timestamp = min(values["right_voltage"][1], values["right_phase_angle"][1], values["right_frequency"][1])
    left = PhasorMeasurement(
        voltage_magnitude_kv=values["left_voltage"][0],
        phase_angle_deg=values["left_phase_angle"][0],
        frequency_hz=values["left_frequency"][0],
        timestamp=left_timestamp,
        quality="VALID",
    )
    right = PhasorMeasurement(
        voltage_magnitude_kv=values["right_voltage"][0],
        phase_angle_deg=values["right_phase_angle"][0],
        frequency_hz=values["right_frequency"][0],
        timestamp=right_timestamp,
        quality="VALID",
    )
    return left, right


class SynchronismCheckGuard:
    """Project providers supply explicit settings, both bus measurements, and optional bypass authorization."""
    def __init__(self, *, configuration_provider: Callable, measurement_provider: Callable, bypass_provider: Callable | None = None, audit_sink: Callable, clock: Callable[[],float] = time.time, bypass_project_id: str | None = None, bypass_activation_generation: int | None = None):
        if not callable(configuration_provider) or not callable(measurement_provider): raise TypeError("Configuration and measurement providers are required")
        if bypass_provider is not None and not callable(bypass_provider): raise TypeError("bypass_provider must be callable")
        if not callable(audit_sink): raise TypeError("audit_sink is required and must be callable")
        if not callable(clock): raise TypeError("clock must be callable")
        if bypass_provider is not None and (not isinstance(bypass_project_id, str) or not bypass_project_id.strip() or isinstance(bypass_activation_generation, bool) or not isinstance(bypass_activation_generation, int) or bypass_activation_generation < 1):
            raise ValueError("A bypass provider requires explicit project and activation-generation scope.")
        self._configuration_provider=configuration_provider; self._measurement_provider=measurement_provider
        self._bypass_provider=bypass_provider; self._audit_sink=audit_sink; self._clock=clock
        self._bypass_project_id=bypass_project_id; self._bypass_activation_generation=bypass_activation_generation
        self._consumed_bypass_ids: set[str] = set(); self._bypass_lock = Lock()
        self._durable_bypass_consumer = getattr(audit_sink, "consume_bypass_authorization", None)

    def authorize_close(self, breaker: Breaker) -> SynchronismDecision:
        if not isinstance(breaker,Breaker): raise TypeError("ANSI 25 guard requires a Breaker")
        try:
            now = self._clock()
        except Exception:
            now = None
        if (
            isinstance(now, bool)
            or not isinstance(now, (int, float))
            or not math.isfinite(now)
        ):
            decision = SynchronismDecision(
                False,
                breaker.id,
                ("ANSI25_CLOCK_UNAVAILABLE",),
                None,
            )
            self._audit(decision)
            raise DomainError(
                code="ANSI25_CLOCK_UNAVAILABLE",
                message="Breaker close denied: ANSI 25 evaluation clock is unavailable or invalid.",
                details={"breaker_id": breaker.id, "reason_codes": decision.reason_codes},
            )
        reasons=[]; mode=None
        try:
            config=self._configuration_provider(breaker)
        except Exception:
            config=None
            reasons.append("ANSI25_CONFIGURATION_PROVIDER_FAILED")
        left=right=None
        if not isinstance(config,SynchronismCheckConfiguration):
            if not reasons: reasons.append("ANSI25_CONFIGURATION_MISSING")
        else:
            try:
                measurements=self._measurement_provider(breaker, config)
            except Exception:
                measurements=None
                reasons.append("ANSI25_MEASUREMENT_PROVIDER_FAILED")
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
        bypassable_reasons = {
            "ANSI25_VOLTAGE_DIFFERENCE_EXCEEDED",
            "ANSI25_PHASE_ANGLE_DIFFERENCE_EXCEEDED",
            "ANSI25_FREQUENCY_DIFFERENCE_EXCEEDED",
        }
        # Bypass may override only measured synchronism-limit exceedances.
        # It can never override absent configuration, bad/stale samples, or
        # an explicitly disallowed live/dead operating mode.
        if reasons and set(reasons).issubset(bypassable_reasons) and config is not None and config.bypass_allowed and self._bypass_provider is not None:
            try:
                auth=self._bypass_provider(breaker)
            except Exception:
                auth=None
            if isinstance(auth, BypassAuthorization) and auth.valid_for(
                now=now,
                breaker_id=breaker.id,
                project_id=self._bypass_project_id,
                activation_generation=self._bypass_activation_generation,
            ):
                if callable(self._durable_bypass_consumer):
                    # The project-scoped audit sink atomically claims the token
                    # using a persistent O_EXCL marker. This survives guard
                    # reconstruction, process restarts, and concurrent callers.
                    try:
                        consumed = self._durable_bypass_consumer(auth)
                    except Exception:
                        consumed = False
                    if consumed is not True:
                        auth = None
                else:
                    # Non-persistent sinks retain process-local replay protection.
                    with self._bypass_lock:
                        if auth.authorization_id in self._consumed_bypass_ids:
                            auth = None
                        else:
                            self._consumed_bypass_ids.add(auth.authorization_id)
                if auth is not None:
                    decision=SynchronismDecision(
                        True, breaker.id, tuple(reasons), mode, True,
                        auth.authorization_id, auth.authorized_by, auth.reason,
                        auth.expires_at,
                        auth.issued_at,
                        auth.project_id,
                        auth.activation_generation,
                    )
                    self._audit(decision); return decision
            reasons.append("ANSI25_BYPASS_UNAUTHORIZED_OR_EXPIRED")
        decision=SynchronismDecision(not reasons,breaker.id,tuple(reasons),mode)
        self._audit(decision)
        if not decision.permitted:
            raise DomainError(code="ANSI25_CLOSE_REJECTED",message="Breaker close rejected by fail-closed ANSI 25 enforcement.",details={"breaker_id":breaker.id,"reason_codes":decision.reason_codes,"mode":mode.value if mode else None})
        return decision
    def _audit(self, decision):
        self._audit_sink(decision)



class ProjectScopedSynchronismAuditSink:
    """Append-only ANSI 25 audit stored beside, never inside, a project package.

    The caller must construct one sink per candidate project activation and
    supply a clock in the measurement timestamp domain. Unsaved projects are
    rejected: an in-memory fallback would make breaker-close authorization
    unauditable. File or fsync errors propagate and therefore block close.
    """

    def __init__(self, *, project_id: str, activation_generation: int, project_path, clock: Callable[[], float], clock_domain: str):
        from pathlib import Path
        from core.persistence.project_package import normalize_package_path

        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("A non-empty project_id is required for ANSI 25 audit.")
        if isinstance(activation_generation, bool) or not isinstance(activation_generation, int) or activation_generation < 1:
            raise ValueError("A positive activation_generation is required for ANSI 25 audit.")
        if project_path is None:
            raise ValueError("ANSI 25 requires a saved project path; unsaved projects cannot authorize breaker close.")
        if not callable(clock):
            raise TypeError("An explicit audit clock is required.")
        if not isinstance(clock_domain, str) or not clock_domain.strip():
            raise ValueError("An explicit audit clock domain is required.")
        package = normalize_package_path(Path(project_path))
        if not package.parent.is_dir():
            raise OSError("ANSI 25 audit directory does not exist; refusing to create an untracked audit location.")
        import hashlib

        self._project_id = project_id
        self._activation_generation = activation_generation
        self._path = package.with_name(package.name + ".ansi25-audit.jsonl")
        # Replay protection follows immutable project identity, not the
        # package path, so Save As and project moves cannot reset consumption.
        project_scope = hashlib.sha256(project_id.encode("utf-8")).hexdigest()
        self._bypass_registry_dir = Path.home() / ".gridforge" / "ansi25-bypass" / project_scope
        self._clock = clock
        self._clock_domain = clock_domain.strip()

    @property
    def clock_domain(self) -> str:
        """Return the explicitly declared timestamp domain used by this sink."""
        return self._clock_domain

    @property
    def path(self):
        """Return the external sidecar path for operational diagnostics."""
        return self._path

    def consume_bypass_authorization(self, authorization: BypassAuthorization) -> bool:
        """Atomically claim a bypass token in a project-identity registry.

        The registry lives under the user profile rather than beside the
        package, so Save As and moving the project do not reset replay state.
        """
        import hashlib
        import json
        import os

        if not isinstance(authorization, BypassAuthorization):
            raise TypeError("ANSI 25 bypass consumer requires BypassAuthorization.")
        if (
            authorization.project_id != self._project_id
            or authorization.activation_generation != self._activation_generation
        ):
            return False
        digest = hashlib.sha256(authorization.authorization_id.encode("utf-8")).hexdigest()
        self._bypass_registry_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        marker = self._bypass_registry_dir / (digest + ".used")
        record = {
            "schema": 1,
            "authorization_id": authorization.authorization_id,
            "project_id": authorization.project_id,
            "activation_generation": authorization.activation_generation,
            "breaker_id": authorization.breaker_id,
            "authorized_by": authorization.authorized_by,
            "issued_at": authorization.issued_at,
            "expires_at": authorization.expires_at,
        }
        payload = (json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
        try:
            descriptor = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            return False
        try:
            remaining = memoryview(payload)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise OSError("Incomplete ANSI 25 bypass-consumption record write.")
                remaining = remaining[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        # Persist the directory entry on filesystems that support directory
        # fsync. Windows exposes file flushing but not portable directory fsync.
        if os.name != "nt":
            directory_descriptor = os.open(self._bypass_registry_dir, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
        return True

    def __call__(self, decision: SynchronismDecision) -> None:
        import json
        import os

        if not isinstance(decision, SynchronismDecision):
            raise TypeError("ANSI 25 audit sink accepts SynchronismDecision values only.")
        timestamp = self._clock()
        if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp):
            raise ValueError("ANSI 25 audit clock returned an invalid timestamp.")
        record = {
            "schema": 1,
            "timestamp": timestamp,
            "project_id": self._project_id,
            "activation_generation": self._activation_generation,
            "breaker_id": decision.breaker_id,
            "permitted": decision.permitted,
            "reason_codes": list(decision.reason_codes),
            "mode": decision.mode.value if decision.mode is not None else None,
            "bypassed": decision.bypassed,
            "authorization_id": decision.authorization_id,
            "bypass_authorized_by": decision.bypass_authorized_by,
            "bypass_reason": decision.bypass_reason,
            "bypass_expires_at": decision.bypass_expires_at,
            "bypass_issued_at": decision.bypass_issued_at,
            "bypass_project_id": decision.bypass_project_id,
            "bypass_activation_generation": decision.bypass_activation_generation,
        }
        payload = (json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        descriptor = os.open(self._path, flags, 0o600)
        try:
            remaining = memoryview(payload)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise OSError("Incomplete ANSI 25 audit record write.")
                remaining = remaining[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

def validate_synchronism_instrument_topology(
    *,
    network: object,
    breaker: Breaker,
    configuration: SynchronismCheckConfiguration,
    channels: Mapping[str, MeasurementChannel],
) -> None:
    """Require all six PT/CVT measurements to be physically sourced from the
    two distinct buses on the configured breaker's actual terminal sides.

    This is an Application-side topology resolver. It reads Core equipment and
    ConnectivityResolver output; it does not mutate topology or infer a missing
    connection.
    """
    if network is None or not isinstance(breaker, Breaker):
        raise ValueError("ANSI 25 physical topology requires an active Network and Breaker.")
    resolver = ConnectivityResolver(network)
    breaker_sides = {}
    for side, role in (("left", "from"), ("right", "to")):
        reference = EndpointReference.terminal(
            equipment_type=EquipmentType.BREAKER,
            equipment_id=breaker.id,
            terminal_role=role,
        )
        bus_id = resolver.bus_for_terminal(reference)
        if not isinstance(bus_id, str) or not bus_id:
            raise ValueError(f"Breaker {breaker.id!r} {side} terminal is not connected to exactly one Bus.")
        breaker_sides[side] = bus_id
    if breaker_sides["left"] == breaker_sides["right"]:
        raise ValueError("ANSI 25 breaker terminals do not resolve to two distinct Bus sides.")

    for key, channel_id in configuration.measurement_channel_ids.items():
        side = "left" if key.startswith("left_") else "right"
        channel = channels.get(channel_id)
        if not isinstance(channel, MeasurementChannel):
            raise ValueError(f"ANSI 25 channel {channel_id!r} is missing.")
        source = getattr(channel, "source", None)
        source_type = str(getattr(source, "element_type", "")).strip().upper()
        if source is None or source_type not in {"PT", "CVT"}:
            raise ValueError(
                f"ANSI 25 channel {channel_id!r} must originate from a physical PT or CVT."
            )
        if getattr(source, "in_service", None) is not True:
            raise ValueError(f"ANSI 25 instrument {getattr(source, 'id', None)!r} is not in service.")
        source_reference = getattr(channel, "source_terminal", None)
        if not isinstance(source_reference, EndpointReference) or not source_reference.is_terminal:
            raise ValueError(f"ANSI 25 channel {channel_id!r} has no canonical secondary-terminal source reference.")
        expected_equipment_type = EquipmentType.PT if source_type == "PT" else EquipmentType.CVT
        if (
            source_reference.equipment_id != getattr(source, "id", None)
            or source_reference.equipment_type is not expected_equipment_type
        ):
            raise ValueError(f"ANSI 25 channel {channel_id!r} source identity/type does not match its PT/CVT.")
        secondary_roles = {"PT": {"secondary_a", "secondary_b"}, "CVT": {"X1", "X2"}}
        if source_reference.terminal_role not in secondary_roles[source_type]:
            raise ValueError(f"ANSI 25 channel {channel_id!r} is not sourced from a PT/CVT secondary terminal.")
        primary_terminals = getattr(source, "primary_terminals", None)
        if not isinstance(primary_terminals, (tuple, list)) or len(primary_terminals) != 2:
            raise ValueError(f"ANSI 25 instrument {source.id!r} does not expose its two primary terminals.")
        resolved_buses = set()
        for terminal in primary_terminals:
            if getattr(terminal, "owner", None) is not source:
                raise ValueError(f"ANSI 25 instrument {source.id!r} has a foreign primary terminal.")
            role = getattr(terminal, "role", None)
            reference = EndpointReference.terminal(
                equipment_type=EquipmentType.PT if source_type == "PT" else EquipmentType.CVT,
                equipment_id=source.id,
                terminal_role=role,
            )
            resolved_buses.update(resolver.bus_ids_for_terminal(reference))
        expected_bus = breaker_sides[side]
        if resolved_buses != {expected_bus}:
            raise ValueError(
                f"ANSI 25 channel {channel_id!r} instrument primary topology resolves to "
                f"{sorted(resolved_buses)!r}; expected only breaker {side} Bus {expected_bus!r}."
            )


def create_project_synchronism_guard(
    *,
    project_id: str,
    activation_generation: int,
    project_configuration_provider: Callable[[], Mapping | SynchronismCheckProjectConfiguration | None],
    measurement_channel_service: object,
    audit_sink: Callable[[SynchronismDecision], None],
    clock: Callable[[], float],
    clock_domain: str,
    bypass_provider: Callable[[Breaker], BypassAuthorization | None] | None = None,
    topology_validator: Callable[[Breaker, SynchronismCheckConfiguration, Mapping[str, MeasurementChannel]], None] | None = None,
) -> SynchronismCheckGuard:
    """Compose ANSI 25 for one candidate project activation.

    The expected project identity and generation are immutable for this guard.
    Before policy or measurements are consumed, the live channel service must
    match both values. A guard captured from an earlier project activation is
    therefore rejected rather than authorizing against another project's data.

    Callers must provide a durable, project-scoped audit sink and a clock in
    the same time domain as channel timestamps. Neither dependency is guessed.
    """
    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("A non-empty candidate project_id is required.")
    if isinstance(activation_generation, bool) or not isinstance(activation_generation, int) or activation_generation < 1:
        raise ValueError("A positive candidate activation_generation is required.")
    if not callable(project_configuration_provider):
        raise TypeError("project_configuration_provider is required.")
    if topology_validator is not None and not callable(topology_validator):
        raise TypeError("topology_validator must be callable when supplied.")
    if not callable(audit_sink):
        raise TypeError("A durable audit sink is required.")
    if not callable(clock):
        raise TypeError("An explicit clock in the channel timestamp domain is required.")
    if not isinstance(clock_domain, str) or not clock_domain.strip():
        raise ValueError("An explicit measurement timestamp domain is required.")
    clock_domain = clock_domain.strip()
    if getattr(audit_sink, "clock_domain", None) != clock_domain:
        raise ValueError("ANSI 25 audit sink clock domain must match the measurement timestamp domain.")

    def validate_active_provenance() -> None:
        active_project_id = getattr(measurement_channel_service, "project_id", None)
        active_generation = getattr(measurement_channel_service, "activation_generation", None)
        if active_project_id != project_id or active_generation != activation_generation:
            raise DomainError(
                code="ANSI25_PROJECT_PROVENANCE_MISMATCH",
                message="Breaker close denied: ANSI 25 guard project or activation generation does not match the active measurement context.",
                details={
                    "expected_project_id": project_id,
                    "active_project_id": active_project_id,
                    "expected_activation_generation": activation_generation,
                    "active_activation_generation": active_generation,
                },
            )

    def resolve_policy(breaker: Breaker) -> SynchronismCheckConfiguration | None:
        validate_active_provenance()
        raw = project_configuration_provider()
        if raw is None:
            return None
        registry = raw if isinstance(raw, SynchronismCheckProjectConfiguration) else SynchronismCheckProjectConfiguration.from_dict(raw)
        return registry.for_breaker(breaker.id)

    def resolve_measurements(breaker: Breaker, configuration: SynchronismCheckConfiguration) -> tuple[PhasorMeasurement, PhasorMeasurement]:
        validate_active_provenance()
        channels = getattr(measurement_channel_service, "channels", None)
        if callable(channels):
            channels = channels()
        if not isinstance(channels, Mapping):
            raise TypeError("Active measurement channel service must expose a channels mapping.")
        if topology_validator is None:
            raise DomainError(
                code="ANSI25_TOPOLOGY_VALIDATOR_MISSING",
                message="Breaker close denied: physical PT/CVT topology validation is not composed.",
                details={"breaker_id": breaker.id},
            )
        topology_validator(breaker, configuration, channels)
        for channel_id in configuration.measurement_channel_ids.values():
            channel = channels.get(channel_id)
            if channel is None:
                raise ValueError(f"ANSI 25 channel {channel_id!r} is unavailable.")
            channel_domain = getattr(channel, "timestamp_domain", None)
            if channel_domain != clock_domain:
                raise DomainError(
                    code="ANSI25_TIMESTAMP_DOMAIN_MISMATCH",
                    message="Breaker close denied: measurement timestamp domain is missing or differs from the configured ANSI 25 clock domain.",
                    details={
                        "channel_id": channel_id,
                        "expected_timestamp_domain": clock_domain,
                        "active_timestamp_domain": channel_domain,
                    },
                )
        return phasor_measurements_from_channels(configuration, channels, now=clock())

    return SynchronismCheckGuard(
        configuration_provider=resolve_policy,
        measurement_provider=resolve_measurements,
        bypass_provider=bypass_provider,
        audit_sink=audit_sink,
        clock=clock,
        bypass_project_id=project_id if bypass_provider is not None else None,
        bypass_activation_generation=activation_generation if bypass_provider is not None else None,
    )

__all__=["BusMode","SynchronismCheckConfiguration","SynchronismCheckProjectConfiguration","PhasorMeasurement","BypassAuthorization","SynchronismDecision","SynchronismCheckGuard","phasor_measurements_from_channels","validate_synchronism_instrument_topology","create_project_synchronism_guard","ProjectScopedSynchronismAuditSink"]
