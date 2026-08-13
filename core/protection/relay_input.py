"""
GridForge V2 Relay Input.

File
----
core/protection/relay_input.py

Purpose
-------
Defines the protection-side input interface through which a protection
function consumes a measurement.

Architectural Boundary
----------------------
Physical measurement chain:

    CT / PT / VT / CVT / Sensor
                |
                v
        MeasurementChannel
                |
                v
            RelayInput
                |
                v
        Protection Function
                |
                v
      ProtectionDecision

RelayInput is the protection-facing binding to a measurement source.

It does NOT:

    * model a CT/PT/CVT
    * perform network calculations
    * own the physical relay
    * implement protection logic
    * contain GUI state
    * perform persistence
    * directly operate equipment

A RelayInput identifies what measurement a protection function expects
and provides a controlled interface to the current measurement value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from .measurement_channel import MeasurementChannel


@dataclass(frozen=True, slots=True)
class RelayInput:
    """
    Protection-facing binding to a MeasurementChannel.

    A RelayInput represents one named input of a protection function.

    Examples
    --------
    ``IA``
        Phase-A current input.

    ``IB``
        Phase-B current input.

    ``IC``
        Phase-C current input.

    ``IN``
        Residual/neutral current input.

    ``VA``
        Phase-A voltage input.

    ``VAB``
        Phase-to-phase voltage input.

    ``FREQ``
        Frequency input.

    ``P``
        Active-power input.

    ``Q``
        Reactive-power input.

    The actual measurement acquisition and engineering-unit semantics
    remain the responsibility of MeasurementChannel.
    """

    name: str
    channel: MeasurementChannel
    description: str = ""
    required: bool = True
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        """
        Validate the protection-input binding.
        """

        name = str(self.name).strip()

        if not name:
            raise ValueError(
                "RelayInput.name cannot be empty."
            )

        if self.channel is None:
            raise ValueError(
                f"RelayInput '{name}' requires a measurement channel."
            )

        object.__setattr__(
            self,
            "name",
            name,
        )

        object.__setattr__(
            self,
            "description",
            str(self.description).strip(),
        )

        object.__setattr__(
            self,
            "required",
            bool(self.required),
        )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata or {}),
        )

    # ==================================================================
    # Identity
    # ==================================================================

    @property
    def channel_id(self) -> Any:
        """
        Return the identity of the underlying measurement channel.
        """
        return getattr(
            self.channel,
            "id",
            None,
        )

    # ==================================================================
    # Measurement access
    # ==================================================================

    @property
    def value(self) -> Any:
        """
        Return the current engineering value supplied by the
        measurement channel.

        MeasurementChannel remains authoritative for measurement
        acquisition, scaling, validation, and engineering units.
        """

        if hasattr(self.channel, "engineering_value"):
            return self.channel.engineering_value

        if hasattr(self.channel, "value"):
            value = self.channel.value

            return (
                value()
                if callable(value)
                else value
            )

        raise AttributeError(
            f"Measurement channel for RelayInput '{self.name}' "
            "does not provide a supported value interface."
        )

    @property
    def engineering_value(self) -> Any:
        """
        Alias for the current engineering value.

        This is provided as the protection-facing semantic name.
        """
        return self.value

    # ==================================================================
    # Measurement validity
    # ==================================================================

    @property
    def valid(self) -> bool:
        """
        Return whether the underlying measurement is currently valid.

        If MeasurementChannel exposes an explicit validity property,
        that property is authoritative.

        If no validity property exists, the input is considered valid
        unless its value access raises an exception.
        """

        if hasattr(self.channel, "valid"):
            valid = self.channel.valid

            return (
                bool(valid())
                if callable(valid)
                else bool(valid)
            )

        try:
            self.value
        except (AttributeError, TypeError, ValueError):
            return False

        return True

    # ==================================================================
    # Quality
    # ==================================================================

    @property
    def quality(self) -> Any:
        """
        Return the underlying measurement quality information when
        available.

        Quality semantics remain defined by MeasurementChannel.
        """
        if hasattr(self.channel, "quality"):
            quality = self.channel.quality

            return (
                quality()
                if callable(quality)
                else quality
            )

        return None

    # ==================================================================
    # Units
    # ==================================================================

    @property
    def unit(self) -> Any:
        """
        Return the engineering unit supplied by the measurement
        channel, when available.
        """
        if hasattr(self.channel, "unit"):
            unit = self.channel.unit

            return (
                unit()
                if callable(unit)
                else unit
            )

        if hasattr(self.channel, "engineering_unit"):
            unit = self.channel.engineering_unit

            return (
                unit()
                if callable(unit)
                else unit
            )

        return None

    # ==================================================================
    # Availability
    # ==================================================================

    @property
    def available(self) -> bool:
        """
        Return whether the input can currently provide a usable
        measurement.
        """
        if hasattr(self.channel, "available"):
            available = self.channel.available

            return (
                bool(available())
                if callable(available)
                else bool(available)
            )

        return self.valid

    # ==================================================================
    # Diagnostics
    # ==================================================================

    def status(self) -> dict[str, Any]:
        """
        Return diagnostic information about this relay input.

        This is not the authoritative persistence representation.
        """
        return {
            "name": self.name,
            "channel_id": self.channel_id,
            "description": self.description,
            "required": self.required,
            "value": self.value if self.valid else None,
            "valid": self.valid,
            "available": self.available,
            "quality": self.quality,
            "unit": self.unit,
            "metadata": dict(self.metadata or {}),
        }


__all__ = [
    "RelayInput",
]
