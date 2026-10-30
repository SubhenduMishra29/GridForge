# ============================================================
# File: core/application/services/measurement_channel_service.py
# GridForge V2 — Application Measurement Channel Lifecycle Service
# Author: Subhendu Mishra
# ============================================================

"""Application-owned, project-scoped logical measurement lifecycle."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
from functools import wraps
from threading import RLock
from typing import Any

from core.application.endpoint_resolver import resolve_terminal_reference
from core.model import EndpointReference, EquipmentType
from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementQuality,
    MeasurementPhase,
    MeasurementSignalType,
)
from core.measurement.measurement_provisioning import MeasurementProvisioning
from core.network.network import Network


def _serialized_measurement_mutation(method):
    """Serialize measurement-registry lifecycle operations with Application."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._execution_lock:
            return method(self, *args, **kwargs)
    return wrapped


class MeasurementChannelService:
    """Own the active project's authoritative MeasurementChannel collection.

    This service owns lifecycle/orchestration only. Core construction remains
    exclusively behind MeasurementProvisioning and the physical Network owns
    the source equipment and terminals.
    """

    def __init__(self, *, execution_lock: Any | None = None) -> None:
        self._execution_lock = execution_lock if execution_lock is not None else RLock()
        if not callable(getattr(self._execution_lock, "__enter__", None)) or not callable(getattr(self._execution_lock, "__exit__", None)):
            raise TypeError("execution_lock must be a context-manager lock.")
        self._project_id: str | None = None
        self._activation_generation = 0
        self._network: Network | None = None
        self._channels: dict[str, MeasurementChannel] = {}

    def bind_execution_lock(self, execution_lock: Any) -> None:
        """Bind the same lock used by Application commands and project lifecycle."""
        if not callable(getattr(execution_lock, "__enter__", None)) or not callable(getattr(execution_lock, "__exit__", None)):
            raise TypeError("execution_lock must be a context-manager lock.")
        if self._execution_lock is not execution_lock:
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

    @_serialized_measurement_mutation
    def publish_sample(
        self,
        channel_id: str,
        value: float | complex,
        *,
        timestamp: float,
        timestamp_domain: str,
        quality: MeasurementQuality,
        sample_sequence: int,
        available: bool = True,
    ) -> None:
        """Publish one source-timestamped sample under the Application mutation lock.

        Live measurement producers must use this boundary so sample publication
        cannot interleave with a breaker-close command's ANSI 25 evaluation and
        state mutation. Timestamp and sequence provenance are mandatory.
        """
        channel = self.require(channel_id)
        if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp):
            raise ValueError("Measurement sample timestamp must be finite.")
        if not isinstance(timestamp_domain, str) or not timestamp_domain.strip():
            raise ValueError("Measurement sample timestamp_domain is required.")
        if channel.timestamp_domain != timestamp_domain:
            raise ValueError(
                f"Measurement channel {channel.id!r} is configured for timestamp domain "
                f"{channel.timestamp_domain!r}, not {timestamp_domain!r}."
            )
        if not isinstance(quality, MeasurementQuality):
            raise TypeError("Measurement sample quality must be MeasurementQuality.")
        if isinstance(sample_sequence, bool) or not isinstance(sample_sequence, int) or sample_sequence < 0:
            raise ValueError("Measurement sample_sequence must be a non-negative integer.")
        if not isinstance(available, bool):
            raise TypeError("Measurement sample availability must be bool.")
        previous_sequence = channel.sample_sequence
        previous_timestamp = channel.timestamp
        if previous_sequence is not None and sample_sequence <= previous_sequence:
            raise ValueError("Measurement sample_sequence must increase monotonically.")
        if previous_timestamp is not None and timestamp < previous_timestamp:
            raise ValueError("Measurement sample timestamp cannot move backwards.")
        channel.update(
            value,
            timestamp=float(timestamp),
            timestamp_domain=timestamp_domain,
            quality=quality,
            available=available,
            sample_sequence=sample_sequence,
        )

    @_serialized_measurement_mutation
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

    @_serialized_measurement_mutation
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

    @_serialized_measurement_mutation
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
        }


__all__ = ["MeasurementChannelService"]
