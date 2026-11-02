# ============================================================
# File: core/application/services/measurement_channel_service.py
# GridForge V2 — Application Measurement Channel Lifecycle Service
# Author: Subhendu Mishra
# ============================================================

"""Application-owned, project-scoped logical measurement lifecycle."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from threading import RLock
from typing import Any, Callable

from core.application.endpoint_resolver import resolve_terminal_reference
from core.model import EndpointReference, EquipmentType
from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementPhase,
    MeasurementQuality,
    MeasurementSignalType,
)
from core.measurement.measurement_provisioning import MeasurementProvisioning
from core.network.network import Network


@dataclass(frozen=True, slots=True)
class MeasurementSampleAttestation:
    """Signed producer envelope; verification is delegated to a deployment trust adapter."""

    producer_id: str
    project_id: str
    activation_generation: int
    timestamp: float
    timestamp_domain: str
    sample_sequence: int
    signature: str
    channel_id: str
    quality: MeasurementQuality
    available: bool

    def __post_init__(self) -> None:
        for name in ("producer_id", "project_id", "timestamp_domain", "signature", "channel_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be a canonical non-empty string.")
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if isinstance(self.sample_sequence, bool) or not isinstance(self.sample_sequence, int) or self.sample_sequence < 0:
            raise ValueError("sample_sequence must be a non-negative integer.")
        if isinstance(self.timestamp, bool) or not isinstance(self.timestamp, (int, float)) or not math.isfinite(self.timestamp):
            raise ValueError("timestamp must be finite.")
        if not isinstance(self.quality, MeasurementQuality):
            raise TypeError("quality must be a MeasurementQuality.")
        if not isinstance(self.available, bool):
            raise TypeError("available must be bool.")


class MeasurementChannelService:
    """Own the active project's authoritative MeasurementChannel collection.

    This service owns lifecycle/orchestration only. Core construction remains
    exclusively behind MeasurementProvisioning and the physical Network owns
    the source equipment and terminals.
    """

    def __init__(
        self,
        *,
        source_verifier: Callable[[MeasurementSampleAttestation, MeasurementChannel, float | complex], bool] | None = None,
        clock: Callable[[], float] | None = None,
        clock_domain: str | None = None,
        max_source_clock_skew_seconds: float = 2.0,
        execution_lock: Any | None = None,
    ) -> None:
        if source_verifier is not None and not callable(source_verifier):
            raise TypeError("source_verifier must be callable when provided.")
        if clock is not None and not callable(clock):
            raise TypeError("clock must be callable when provided.")
        if clock_domain is not None and (not isinstance(clock_domain, str) or not clock_domain.strip() or clock_domain != clock_domain.strip()):
            raise ValueError("clock_domain must be a canonical non-empty string.")
        if isinstance(max_source_clock_skew_seconds, bool) or not isinstance(max_source_clock_skew_seconds, (int, float)) or not math.isfinite(max_source_clock_skew_seconds) or max_source_clock_skew_seconds <= 0:
            raise ValueError("max_source_clock_skew_seconds must be finite and positive.")
        self._source_verifier = source_verifier
        self._clock = clock
        self._clock_domain = clock_domain
        self._max_source_clock_skew_seconds = float(max_source_clock_skew_seconds)
        self._execution_lock = execution_lock if execution_lock is not None else RLock()
        self._sample_update_authority = object()
        self._project_id: str | None = None
        self._activation_generation = 0
        self._network: Network | None = None
        self._channels: dict[str, MeasurementChannel] = {}
        self._sample_subscribers: dict[str, Callable[[MeasurementSampleAttestation, MeasurementChannel], Any]] = {}

    def bind_execution_lock(self, execution_lock: Any) -> None:
        """Use the Application command lock so publication cannot race breaker authorization."""
        if not callable(getattr(execution_lock, "__enter__", None)) or not callable(getattr(execution_lock, "__exit__", None)):
            raise TypeError("execution_lock must be a context-manager lock.")
        self._execution_lock = execution_lock

    @property
    def project_id(self) -> str | None:
        return self._project_id

    @property
    def activation_generation(self) -> int:
        return self._activation_generation

    @property
    def network(self) -> Network | None:
        """Network identity to which the active channel registry was provisioned."""
        return self._network

    @property
    def channels(self) -> Mapping[str, MeasurementChannel]:
        return dict(self._channels)

    def get(self, channel_id: str) -> MeasurementChannel | None:
        return self._channels.get(self._normalize_id(channel_id))

    def require(self, channel_id: str) -> MeasurementChannel:
        normalized = self._normalize_id(channel_id)
        try:
            return self._channels[normalized]
        except KeyError as exc:
            raise KeyError(f"PROTECTION_CHANNEL_NOT_FOUND: MeasurementChannel '{normalized}' is not available.") from exc

    def validate_references(self, channel_ids: Sequence[str]) -> None:
        for channel_id in channel_ids:
            self.require(channel_id)

    def subscribe_samples(
        self,
        callback: Callable[[MeasurementSampleAttestation, MeasurementChannel], Any],
        *,
        subscriber_id: str,
    ) -> Callable[[], None]:
        """Register one Application-owned callback for authenticated sample publication."""
        if not isinstance(subscriber_id, str) or not subscriber_id.strip():
            raise ValueError("subscriber_id must be a non-empty string.")
        if not callable(callback):
            raise TypeError("sample publication callback must be callable.")
        key = subscriber_id.strip()
        if key in self._sample_subscribers:
            raise ValueError(f"Measurement sample subscriber already registered: {key!r}.")
        self._sample_subscribers[key] = callback

        def unsubscribe() -> None:
            if self._sample_subscribers.get(key) is callback:
                self._sample_subscribers.pop(key, None)

        return unsubscribe

    def publish_sample(
        self,
        channel_id: str,
        value: float | complex,
        *,
        attestation: MeasurementSampleAttestation,
        quality: MeasurementQuality,
        available: bool = True,
    ) -> tuple[Any, ...]:
        """Publish only a signed, project-bound sample with trusted clock validation.

        The deployment verifier must authenticate producer identity and the
        complete attestation/value tuple (for example, using a device certificate
        and signature). Caller-supplied clock labels alone are never trusted.
        """
        with self._execution_lock:
            if self._source_verifier is None or self._clock is None or self._clock_domain is None:
                raise PermissionError("Trusted measurement source verification and clock authority are not configured.")
            if not isinstance(attestation, MeasurementSampleAttestation):
                raise TypeError("attestation must be MeasurementSampleAttestation.")
            if not isinstance(quality, MeasurementQuality):
                raise TypeError("quality must be MeasurementQuality.")
            if not isinstance(available, bool):
                raise TypeError("available must be bool.")
            channel = self.require(channel_id)
            if attestation.channel_id != channel.id:
                raise PermissionError("Measurement attestation is bound to a different channel identity.")
            if attestation.quality is not quality or attestation.available is not available:
                raise PermissionError("Published quality/availability must exactly match the signed measurement attestation.")
            if getattr(channel, "producer_id", None) != attestation.producer_id:
                raise PermissionError("Measurement producer identity does not match the configured channel producer.")
            if attestation.project_id != self._project_id or attestation.activation_generation != self._activation_generation:
                raise PermissionError("Measurement attestation belongs to a different project activation.")
            if attestation.timestamp_domain != self._clock_domain or channel.timestamp_domain != self._clock_domain:
                raise PermissionError("Measurement source clock domain does not match the trusted Application clock domain.")
            try:
                trusted_now = self._clock()
            except Exception as exc:
                raise PermissionError("Trusted measurement clock is unavailable.") from exc
            if isinstance(trusted_now, bool) or not isinstance(trusted_now, (int, float)) or not math.isfinite(trusted_now):
                raise PermissionError("Trusted measurement clock returned an invalid timestamp.")
            if attestation.timestamp > trusted_now + self._max_source_clock_skew_seconds:
                raise PermissionError("Measurement source timestamp is too far ahead of the trusted clock.")
            try:
                verified = self._source_verifier(attestation, channel, value)
            except Exception as exc:
                raise PermissionError("Measurement source attestation verification failed.") from exc
            if verified is not True:
                raise PermissionError("Measurement source attestation was not authenticated.")
            if channel.sample_sequence is not None and attestation.sample_sequence <= channel.sample_sequence:
                raise ValueError("Measurement sample sequence must increase monotonically.")
            if channel.timestamp is not None and attestation.timestamp < channel.timestamp:
                raise ValueError("Measurement source timestamp cannot move backwards.")
            channel.update(
                value,
                _authority=self._sample_update_authority,
                timestamp=float(attestation.timestamp),
                timestamp_domain=attestation.timestamp_domain,
                quality=quality,
                available=available,
                sample_sequence=attestation.sample_sequence,
            )

        # The sample is authenticated and committed before consumers are
        # notified. Callbacks run outside the measurement lock so Application
        # evaluation cannot hold the producer publication critical section.
        outcomes = []
        for subscriber_id, callback in tuple(sorted(self._sample_subscribers.items())):
            outcomes.append((subscriber_id, callback(attestation, channel)))
        return tuple(outcomes)

    def activate(
        self,
        context: Any | None,
        network: Network,
        definitions: Sequence[Mapping[str, Any]] = (),
        generation: int = 0,
    ) -> Any:
        """Reconstruct candidate project channels and return one rollback callback."""
        if context is None:
            if definitions:
                raise ValueError("A project-less measurement activation cannot contain channel definitions.")
            next_channels: dict[str, MeasurementChannel] = {}
            next_project_id = None
        else:
            if not isinstance(network, Network):
                raise TypeError("network must be a Network.")
            next_channels = {}
            next_project_id = context.project_id
            for definition in definitions:
                channel = self._provision_definition(context, network, definition)
                if channel.id in next_channels:
                    raise ValueError(f"Duplicate measurement channel ID: {channel.id}")
                # Bind immutable producer identity before sealing the channel.
                channel.producer_id = self._normalize_optional_id(definition.get("producer_id"))
                channel._bind_sample_update_authority(self._sample_update_authority)
                next_channels[channel.id] = channel

        previous = self.snapshot_state()
        self._project_id = next_project_id
        self._activation_generation = generation if context is not None else 0
        self._network = network if context is not None else None
        self._channels = next_channels

        def rollback() -> None:
            self.restore_state(previous)

        return rollback

    def snapshot_state(self) -> tuple[str | None, int, Network | None, dict[str, MeasurementChannel]]:
        """Capture the exact live channel authority for transactional compensation.

        The registry and channel objects are retained by reference. This is
        intentionally not a serialized definition snapshot: channel identity,
        live sample values, quality, timestamps, availability and sequence state
        remain untouched and are restored together with project provenance.
        """
        return (
            self._project_id,
            self._activation_generation,
            self._network,
            self._channels,
        )

    def restore_state(
        self,
        snapshot: tuple[str | None, int, Network | None, dict[str, MeasurementChannel]],
    ) -> None:
        """Restore an exact previously captured authority; safe to repeat."""
        if not isinstance(snapshot, tuple) or len(snapshot) != 4:
            raise TypeError("Measurement channel snapshot must be a four-item state tuple.")
        project_id, generation, network, channels = snapshot
        if project_id is not None and not isinstance(project_id, str):
            raise TypeError("Measurement channel snapshot project identity is invalid.")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
            raise TypeError("Measurement channel snapshot activation generation is invalid.")
        if not isinstance(channels, dict):
            raise TypeError("Measurement channel snapshot registry is invalid.")
        if project_id is not None and not isinstance(network, Network):
            raise TypeError("Active measurement channel snapshot requires its original Network.")
        self._project_id = project_id
        self._activation_generation = generation
        self._network = network
        self._channels = channels

    def deactivate(self) -> None:
        self._project_id = None
        self._activation_generation = 0
        self._network = None
        self._channels = {}

    def serialize_definitions(self) -> list[dict[str, Any]]:
        """Return persistent configuration only; live sample state is excluded."""
        return [self._serialize_channel(channel) for channel in self._channels.values()]

    def _provision_definition(self, context: Any, network: Network, definition: Mapping[str, Any]) -> MeasurementChannel:
        if not isinstance(definition, Mapping):
            raise TypeError("Measurement channel definition must be a mapping.")
        channel_id = self._normalize_id(definition.get("channel_id", definition.get("id")))
        source_id = self._normalize_id(definition.get("source", definition.get("source_id")))
        terminal_data = definition.get("source_terminal", definition.get("source_terminal_reference"))
        if not isinstance(terminal_data, Mapping):
            raise ValueError(f"MeasurementChannel '{channel_id}' requires a source_terminal EndpointReference mapping.")
        reference = self._endpoint_reference(terminal_data)
        source = network.get_by_identity(source_id)
        if getattr(source, "id", None) != source_id:
            raise ValueError(f"Measurement source '{source_id}' could not be resolved.")
        signal_type = self._enum_value(MeasurementSignalType, definition.get("signal_type"), "signal_type")
        phase = self._enum_value(MeasurementPhase, definition.get("phase", MeasurementPhase.NONE.value), "phase")
        terminal = resolve_terminal_reference(context, reference)
        return MeasurementProvisioning.provision_channel(
            source=source,
            source_terminal=terminal,
            source_terminal_reference=reference,
            channel_id=channel_id,
            signal_type=signal_type,
            name=str(definition.get("name", "")),
            phase=phase,
            unit=str(definition.get("unit", "")),
            nominal_value=float(definition.get("nominal_value", 0.0)),
            scale=float(definition.get("scale", 1.0)),
            polarity=float(definition.get("polarity", 1.0)),
            timestamp_domain=definition.get("timestamp_domain"),
        )

    @staticmethod
    def _endpoint_reference(data: Mapping[str, Any]) -> EndpointReference:
        if data.get("kind") != "terminal":
            raise ValueError("Measurement channel source must use a terminal EndpointReference.")
        equipment_type = data.get("equipment_type")
        try:
            equipment_type = EquipmentType(equipment_type)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid measurement source equipment_type: {equipment_type!r}") from exc
        return EndpointReference.terminal(
            equipment_type=equipment_type,
            equipment_id=str(data["object_id"]),
            terminal_role=str(data["terminal_role"]),
        )

    @staticmethod
    def _enum_value(enum_type: type, value: Any, field: str) -> Any:
        try:
            return value if isinstance(value, enum_type) else enum_type(str(value).strip().upper())
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid measurement {field}: {value!r}") from exc

    @staticmethod
    def _normalize_optional_id(value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ValueError("Measurement producer_id must be a canonical non-empty string.")
        return value

    @staticmethod
    def _normalize_id(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Measurement channel IDs and source IDs must be non-empty strings.")
        return value.strip()

    @staticmethod
    def _serialize_channel(channel: MeasurementChannel) -> dict[str, Any]:
        source_reference = channel.source_terminal
        if not isinstance(source_reference, EndpointReference):
            raise ValueError(f"MeasurementChannel '{channel.id}' has no canonical source EndpointReference.")
        return {
            "channel_id": channel.id,
            "signal_type": channel.signal_type.value,
            "name": channel.name,
            "source": channel.source_id,
            "source_terminal": dict(source_reference.to_mapping()),
            "phase": channel.phase.value,
            "unit": channel.unit,
            "nominal_value": channel.nominal_value,
            "scale": channel.scale,
            "polarity": channel.polarity,
            "timestamp_domain": channel.timestamp_domain,
            "producer_id": getattr(channel, "producer_id", None),
        }


__all__ = ["MeasurementChannelService"]
