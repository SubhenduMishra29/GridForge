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

from core.model import EndpointReference
from core.measurement.measurement_channel import MeasurementChannel, MeasurementSignalType


class MeasurementProvisioning:
    """Create logical measurement channels from explicit Core endpoint identity."""

    @staticmethod
    def provision_channel(
        *,
        source: Any,
        source_terminal: Any,
        source_terminal_reference: EndpointReference,
        channel_id: str,
        signal_type: MeasurementSignalType,
        name: str = "",
        **channel_kwargs: Any,
    ) -> MeasurementChannel:
        """Provision one channel from an already-resolved Core terminal.

        Application resolves the EndpointReference before entering this
        Core boundary. Provisioning therefore consumes the authoritative
        Core Terminal and its canonical EndpointReference without reaching
        back into Application services or project context.
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

        if source_terminal is None:
            raise TypeError("source_terminal must be an authoritative Core Terminal.")
        if getattr(source_terminal, "owner", None) is not source:
            raise ValueError(
                "source_terminal does not belong to the supplied source equipment."
            )
        terminal_role = getattr(source_terminal, "role", None)
        if terminal_role != source_terminal_reference.terminal_role:
            raise ValueError(
                "source_terminal role must match source_terminal_reference.terminal_role."
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
