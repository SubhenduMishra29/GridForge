# Author: Subhendu Mishra
"""Canonical measurement-channel provisioning boundary.

This module owns orchestration of logical MeasurementChannel creation from
an authoritative physical measurement source and an explicit terminal
EndpointReference. It does not own Core terminals, topology, or protection.

    physical source + EndpointReference
                 |
                 v
        MeasurementProvisioning
                 |
                 v
        MeasurementChannel
"""
from __future__ import annotations

from typing import Any

from core.application.endpoint_reference import EndpointReference
from core.application.endpoint_resolver import resolve_terminal_reference
from core.measurement.measurement_channel import MeasurementChannel, MeasurementSignalType


class MeasurementProvisioning:
    """Create logical measurement channels from explicit Core endpoint identity."""

    @staticmethod
    def provision_channel(
        context: Any,
        *,
        source: Any,
        source_terminal_reference: EndpointReference,
        channel_id: str,
        signal_type: MeasurementSignalType,
        name: str = "",
        **channel_kwargs: Any,
    ) -> MeasurementChannel:
        """Provision one channel from an authoritative physical terminal.

        The endpoint reference is resolved through the existing canonical
        resolver. No terminal registry or semantic identity map is created
        here. The resolved Core Terminal remains authoritative.
        """
        if not isinstance(source_terminal_reference, EndpointReference):
            raise TypeError(
                "source_terminal_reference must be an EndpointReference."
            )
        if not source_terminal_reference.is_terminal:
            raise ValueError(
                "source_terminal_reference must identify a terminal."
            )
        if source is None or not hasattr(source, "id"):
            raise TypeError("source must expose a stable id.")
        source_id = getattr(source, "id")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source.id must be a non-empty string.")
        if source_terminal_reference.equipment_id != source_id.strip():
            raise ValueError(
                "source_terminal_reference equipment identity must match source.id."
            )

        terminal = resolve_terminal_reference(
            context,
            source_terminal_reference,
        )
        if getattr(terminal, "owner", None) is not source:
            raise ValueError(
                "Resolved source terminal does not belong to the supplied source equipment."
            )

        return MeasurementChannel(
            id=channel_id,
            signal_type=signal_type,
            name=name,
            source=source,
            source_terminal=source_terminal_reference,
            **channel_kwargs,
        )


__all__ = ["MeasurementProvisioning"]
