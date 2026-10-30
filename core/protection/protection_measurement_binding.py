# Author: Subhendu Mishra
"""Canonical SC/protection measurement binding contract.

The binding is the explicit correlation point between an analysis result,
physical measurement instrumentation, a logical MeasurementChannel, and a
protection RelayInput. It owns no electrical state and performs no conversion
or equipment mutation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping

from core.model import EndpointReference, EquipmentType


@dataclass(frozen=True, slots=True)
class ProtectionMeasurementBinding:
    """Immutable, correlation-complete protection measurement binding."""

    binding_id: str
    protection_element_id: str
    source_equipment_id: str
    source_terminal_reference: EndpointReference
    electrical_side: str
    measurement_type: str
    phase_or_sequence: str
    result_quantity: str
    instrument_id: str
    instrument_ratio: float
    channel_id: str
    relay_input_id: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "binding_id", "protection_element_id", "source_equipment_id",
            "electrical_side", "measurement_type", "phase_or_sequence",
            "result_quantity", "instrument_id", "channel_id", "relay_input_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())

        if not isinstance(self.source_terminal_reference, EndpointReference) or not self.source_terminal_reference.is_terminal:
            raise TypeError("source_terminal_reference must be a terminal EndpointReference.")
        if self.source_terminal_reference.equipment_id != self.source_equipment_id:
            raise ValueError("source_terminal_reference equipment identity must match source_equipment_id.")

        ratio = float(self.instrument_ratio)
        if not isfinite(ratio) or ratio <= 0.0:
            raise ValueError("instrument_ratio must be positive.")
        object.__setattr__(self, "instrument_ratio", ratio)

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def source_terminal_id(self) -> str:
        """Compatibility identity derived from the canonical endpoint reference."""
        return str(self.source_terminal_reference)

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
        protection_element_id: str,
        instrument_ratio: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionMeasurementBinding":
        """Build a binding from explicitly supplied identities and ratio.

        The ratio is an explicit input to the binding factory. It is never
        inferred from CT/PT/CVT class names, terminal ordering, or collection
        position.
        """
        source_equipment_id = getattr(source_equipment, "id", None)
        if not isinstance(source_equipment_id, str) or not source_equipment_id.strip():
            raise ValueError("source_equipment must expose a non-empty stable id.")

        if isinstance(source_terminal, EndpointReference):
            endpoint = source_terminal
        else:
            owner = getattr(source_terminal, "owner", None)
            owner_id = getattr(owner, "id", None)
            owner_type = getattr(owner, "TYPE", None)
            role = getattr(source_terminal, "role", None)
            if not isinstance(owner_id, str) or not owner_id.strip() or not isinstance(role, str) or not role.strip():
                raise ValueError("source_terminal must expose owner identity and explicit role.")
            try:
                endpoint = EndpointReference.terminal(
                    equipment_type=EquipmentType(str(owner_type).strip().lower()),
                    equipment_id=owner_id,
                    terminal_role=role,
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Unsupported source terminal equipment type: {owner_type!r}") from exc

        ids: dict[str, str] = {}
        for name, obj in {"instrument": instrument, "channel": channel, "relay_input": relay_input}.items():
            object_id = getattr(obj, "id", None)
            if not isinstance(object_id, str) or not object_id.strip():
                raise ValueError(f"{name} must expose a non-empty stable id.")
            ids[name] = object_id.strip()

        if endpoint.equipment_id != source_equipment_id.strip():
            raise ValueError("source_terminal does not belong to source_equipment.")

        if instrument_ratio is None:
            raise ValueError("instrument_ratio must be explicitly supplied; inference is not permitted.")

        return cls(
            binding_id=binding_id,
            protection_element_id=protection_element_id,
            source_equipment_id=source_equipment_id.strip(),
            source_terminal_reference=endpoint,
            electrical_side=electrical_side,
            measurement_type=measurement_type,
            phase_or_sequence=phase_or_sequence,
            result_quantity=result_quantity,
            instrument_id=ids["instrument"],
            instrument_ratio=instrument_ratio,
            channel_id=ids["channel"],
            relay_input_id=ids["relay_input"],
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a detached persistence representation."""
        return {
            "binding_id": self.binding_id,
            "protection_element_id": self.protection_element_id,
            "source_equipment_id": self.source_equipment_id,
            "source_terminal_reference": dict(self.source_terminal_reference.to_mapping()),
            "electrical_side": self.electrical_side,
            "measurement_type": self.measurement_type,
            "phase_or_sequence": self.phase_or_sequence,
            "result_quantity": self.result_quantity,
            "instrument_id": self.instrument_id,
            "instrument_ratio": self.instrument_ratio,
            "channel_id": self.channel_id,
            "relay_input_id": self.relay_input_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProtectionMeasurementBinding":
        """Restore a binding without resolving or guessing live equipment."""
        if not isinstance(data, Mapping):
            raise TypeError("protection measurement binding must be a mapping.")
        endpoint_data = data.get("source_terminal_reference")
        if not isinstance(endpoint_data, Mapping):
            raise TypeError("source_terminal_reference must be a mapping.")
        from core.model.endpoint_reference import EndpointReferenceKind

        kind = EndpointReferenceKind(endpoint_data["kind"])
        if kind is not EndpointReferenceKind.TERMINAL:
            raise ValueError("Protection measurement source must reference a physical equipment terminal.")
        endpoint = EndpointReference.terminal(
            equipment_type=EquipmentType(endpoint_data["equipment_type"]),
            equipment_id=endpoint_data["object_id"],
            terminal_role=endpoint_data["terminal_role"],
        )
        return cls(
            binding_id=data["binding_id"],
            protection_element_id=data["protection_element_id"],
            source_equipment_id=data["source_equipment_id"],
            source_terminal_reference=endpoint,
            electrical_side=data["electrical_side"],
            measurement_type=data["measurement_type"],
            phase_or_sequence=data["phase_or_sequence"],
            result_quantity=data["result_quantity"],
            instrument_id=data["instrument_id"],
            instrument_ratio=data["instrument_ratio"],
            channel_id=data["channel_id"],
            relay_input_id=data["relay_input_id"],
            metadata=data.get("metadata", {}),
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
