"""Canonical SC/protection measurement binding contract.

The binding is the explicit correlation point between an analysis result,
physical measurement instrumentation, a logical MeasurementChannel, and a
protection RelayInput.  It owns no electrical state and performs no
conversion or equipment mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ProtectionMeasurementBinding:
    """Immutable, correlation-complete protection measurement binding."""

    binding_id: str
    source_equipment_id: str
    source_terminal_id: str
    electrical_side: str
    measurement_type: str
    phase_or_sequence: str
    result_quantity: str
    instrument_id: str
    instrument_ratio: float
    channel_id: str
    relay_input_id: str
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for name in (
            "binding_id",
            "source_equipment_id",
            "source_terminal_id",
            "electrical_side",
            "measurement_type",
            "phase_or_sequence",
            "result_quantity",
            "instrument_id",
            "channel_id",
            "relay_input_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())

        ratio = float(self.instrument_ratio)
        if ratio <= 0.0:
            raise ValueError("instrument_ratio must be positive.")
        object.__setattr__(self, "instrument_ratio", ratio)

        metadata = self.metadata
        if metadata == ():
            metadata = {}
        if not isinstance(metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(metadata)))

    @classmethod
    def from_explicit_references(
        cls,
        *,
        binding_id: str,
        source_equipment: Any,
        source_terminal: Any,
        electrical_side: str,
        measurement_type: str,
        phase_or_sequence: str,
        result_quantity: str,
        instrument: Any,
        channel: Any,
        relay_input: Any,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionMeasurementBinding":
        """Build a binding only from explicitly identified objects.

        No collection position, terminal ordering, or instrument ratio is
        inferred.  Every referenced object must expose a stable ``id``.
        """
        refs = {
            "source_equipment": source_equipment,
            "source_terminal": source_terminal,
            "instrument": instrument,
            "channel": channel,
            "relay_input": relay_input,
        }
        ids: dict[str, str] = {}
        for name, obj in refs.items():
            object_id = getattr(obj, "id", None)
            if not isinstance(object_id, str) or not object_id.strip():
                raise ValueError(f"{name} must expose a non-empty stable id.")
            ids[name] = object_id.strip()

        ratio = getattr(instrument, "ratio", None)
        if ratio is None:
            ratio = getattr(instrument, "ct_ratio", None)
        if ratio is None:
            ratio = getattr(instrument, "pt_ratio", None)
        if ratio is None:
            raise ValueError("instrument ratio must be explicitly declared; inference is not permitted.")

        return cls(
            binding_id=binding_id,
            source_equipment_id=ids["source_equipment"],
            source_terminal_id=ids["source_terminal"],
            electrical_side=electrical_side,
            measurement_type=measurement_type,
            phase_or_sequence=phase_or_sequence,
            result_quantity=result_quantity,
            instrument_id=ids["instrument"],
            instrument_ratio=float(ratio),
            channel_id=ids["channel"],
            relay_input_id=ids["relay_input"],
            metadata=metadata or {},
        )

    def correlation_key(self) -> tuple[str, str, str, str, str]:
        """Return the stable correlation identity for result mapping."""
        return (
            self.source_equipment_id,
            self.source_terminal_id,
            self.electrical_side,
            self.measurement_type,
            self.result_quantity,
        )


__all__ = ["ProtectionMeasurementBinding"]
