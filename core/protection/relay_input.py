"""
GridForge V2 Relay Input
========================

File
----
core/protection/relay_input.py

Purpose
-------
Defines the protection-facing binding between a protection function
and one authoritative MeasurementChannel.

Architectural Position
----------------------

    Physical Measurement Source
              |
              v
      MeasurementChannel
              |
              v
          RelayInput
              |
              v
          RelayBase
              |
              v
      ProtectionDecision

MeasurementChannel owns the authoritative measurement state.

RelayInput is only a protection-facing reference/binding. It does not
copy, transform, scale, validate, or simulate the measurement.

Architectural Principles
------------------------

1. MeasurementChannel is authoritative for measurement state.

2. RelayInput does not own measurement state.

3. Protection functions consume RelayInput objects rather than
   reaching into CT/PT/CVT implementation details.

4. RelayInput does not perform electrical calculations.

5. RelayInput does not maintain its own clock.

6. RelayInput does not modify MeasurementChannel state.

7. RelayInput does not create physical instrumentation.

8. RelayInput does not perform protection logic.

9. RelayInput does not operate breakers.

10. RelayInput does not perform persistence.

Typical Usage
-------------

    RelayInput("IA", current_channel)
    RelayInput("IB", current_channel_b)
    RelayInput("IC", current_channel_c)

A protection function can therefore declare its required inputs
without owning the underlying measurement infrastructure.

Example
-------

    Relay
      |
      +-- ProtectionElement OC51
              |
              +-- RelayBase
                    |
                    +-- IA -> RelayInput -> MeasurementChannel
                    +-- IB -> RelayInput -> MeasurementChannel
                    +-- IC -> RelayInput -> MeasurementChannel

Multifunction relays may share MeasurementChannels:

    Relay R1
       |
       +-- OC51
       |     |
       |     +-- IA -> MeasurementChannel IA
       |
       +-- 67
       |     |
       |     +-- IA -> MeasurementChannel IA
       |     +-- VA -> MeasurementChannel VA
       |
       +-- 21
             |
             +-- IA -> MeasurementChannel IA
             +-- VA -> MeasurementChannel VA

No measurement state is duplicated.

Compatibility
-------------
This module intentionally uses a structural runtime contract rather
than importing the concrete MeasurementChannel implementation at
runtime. This prevents unnecessary coupling and circular imports
while keeping the expected interface explicit.

The authoritative implementation remains:

    core.measurement.measurement_channel.MeasurementChannel

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from core.measurement.measurement_channel import MeasurementChannel


# =====================================================================
# RELAY INPUT
# =====================================================================


class RelayInput:
    """
    Protection-facing binding to one MeasurementChannel.

    RelayInput provides a stable named interface between the
    measurement subsystem and a protection function.

    It does not become an owner of the MeasurementChannel state.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        name: str,
        channel: MeasurementChannel,
        *,
        description: str = "",
        required: bool = True,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:

        self._validate_name(name)

        if channel is None:
            raise ValueError(
                f"RelayInput '{name}' requires a "
                "MeasurementChannel."
            )

        self._validate_channel(channel)

        self._name = name.strip()
        self._channel = channel
        self._description = str(
            description
        ).strip()

        self._required = bool(
            required
        )

        if metadata is None:
            self._metadata: dict[str, Any] = {}
        else:
            if not isinstance(
                metadata,
                Mapping,
            ):
                raise TypeError(
                    "metadata must be a mapping."
                )

            self._metadata = dict(
                metadata
            )

    # =================================================================
    # VALIDATION
    # =================================================================

    @staticmethod
    def _validate_name(
        value: str,
    ) -> None:
        """
        Validate the protection-local input name.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "RelayInput name must be a string."
            )

        if not value.strip():
            raise ValueError(
                "RelayInput name cannot be empty."
            )

    # -----------------------------------------------------------------

    @staticmethod
    def _validate_channel(
        channel: Any,
    ) -> None:
        """
        Validate the minimum structural MeasurementChannel contract.

        RelayInput deliberately does not require a concrete
        MeasurementChannel import at runtime.
        """

        required_attributes = (
            "id",
            "engineering_value",
            "available",
            "quality",
            "is_usable",
        )

        missing = [
            attribute
            for attribute in required_attributes
            if not hasattr(
                channel,
                attribute,
            )
        ]

        if missing:
            raise TypeError(
                "channel is not compatible with the "
                "MeasurementChannel protection-facing contract. "
                f"Missing attributes: {missing}."
            )

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def id(self) -> str:
        """
        Return the protection-local input identifier.

        This is distinct from MeasurementChannel.id.
        """

        return self._name

    # -----------------------------------------------------------------

    @property
    def name(self) -> str:
        """
        Return the protection-local input name.
        """

        return self._name

    # -----------------------------------------------------------------

    @property
    def description(self) -> str:
        """
        Return the human-readable input description.
        """

        return self._description

    # -----------------------------------------------------------------

    @property
    def required(self) -> bool:
        """
        Return whether the consuming function requires this input.
        """

        return self._required

    # =================================================================
    # MEASUREMENT CHANNEL
    # =================================================================

    @property
    def channel(self) -> MeasurementChannel:
        """
        Return the authoritative MeasurementChannel reference.

        No channel state is copied.
        """

        return self._channel

    # -----------------------------------------------------------------

    @property
    def measurement_channel(
        self,
    ) -> MeasurementChannel:
        """
        Explicit alias for the authoritative MeasurementChannel.
        """

        return self._channel

    # -----------------------------------------------------------------

    @property
    def channel_id(self) -> Any:
        """
        Return the authoritative MeasurementChannel identifier.
        """

        return getattr(
            self._channel,
            "id",
            None,
        )

    # =================================================================
    # VALUE
    # =================================================================

    @property
    def value(self) -> Any:
        """
        Return the current engineering value.

        MeasurementChannel remains authoritative.
        """

        return self.engineering_value

    # -----------------------------------------------------------------

    @property
    def engineering_value(self) -> Any:
        """
        Return the current engineering value from the channel.
        """

        return getattr(
            self._channel,
            "engineering_value",
            None,
        )

    # =================================================================
    # AVAILABILITY / QUALITY
    # =================================================================

    @property
    def available(self) -> bool:
        """
        Return the current channel availability.
        """

        return bool(
            getattr(
                self._channel,
                "available",
                False,
            )
        )

    # -----------------------------------------------------------------

    @property
    def quality(self) -> Any:
        """
        Return the authoritative measurement quality.
        """

        return getattr(
            self._channel,
            "quality",
            None,
        )

    # -----------------------------------------------------------------

    @property
    def usable(self) -> bool:
        """
        Return whether the measurement is currently usable.

        MeasurementChannel remains authoritative for this decision.
        """

        return bool(
            getattr(
                self._channel,
                "is_usable",
                False,
            )
        )

    # -----------------------------------------------------------------

    @property
    def valid(self) -> bool:
        """
        Return the channel's current basic validity state when
        available.

        If the MeasurementChannel does not expose ``is_valid``,
        validity falls back to usability.
        """

        value = getattr(
            self._channel,
            "is_valid",
            None,
        )

        if value is None:
            return self.usable

        return bool(value)

    # =================================================================
    # SIGNAL INFORMATION
    # =================================================================

    @property
    def signal_type(self) -> Any:
        """
        Return the authoritative signal type.
        """

        return getattr(
            self._channel,
            "signal_type",
            None,
        )

    # -----------------------------------------------------------------

    @property
    def phase(self) -> Any:
        """
        Return the authoritative phase/sequence designation.
        """

        return getattr(
            self._channel,
            "phase",
            None,
        )

    # -----------------------------------------------------------------

    @property
    def unit(self) -> Any:
        """
        Return the engineering unit.
        """

        return getattr(
            self._channel,
            "unit",
            None,
        )

    # -----------------------------------------------------------------

    @property
    def nominal_value(self) -> Any:
        """
        Return the channel nominal engineering value.
        """

        return getattr(
            self._channel,
            "nominal_value",
            None,
        )

    # =================================================================
    # VALIDITY
    # =================================================================

    def validity(
        self,
        *,
        current_time: float | None = None,
    ) -> Any:
        """
        Return the authoritative MeasurementChannel validity state.

        RelayInput does not maintain or calculate validity state.
        """

        method = getattr(
            self._channel,
            "validity",
            None,
        )

        if not callable(method):
            return None

        if current_time is None:
            return method()

        return method(
            current_time=current_time,
        )

    # -----------------------------------------------------------------

    def is_valid_at(
        self,
        current_time: float | None = None,
    ) -> bool:
        """
        Return channel validity at the requested evaluation time.

        If the channel does not provide ``is_valid_at()``, the current
        ``valid`` state is returned.
        """

        method = getattr(
            self._channel,
            "is_valid_at",
            None,
        )

        if callable(method):
            if current_time is None:
                return bool(
                    method()
                )

            return bool(
                method(current_time)
            )

        return self.valid

    # =================================================================
    # SOURCE INFORMATION
    # =================================================================

    @property
    def source(self) -> Any:
        """
        Return the channel's source reference.
        """

        return getattr(
            self._channel,
            "source",
            None,
        )

    # -----------------------------------------------------------------

    @property
    def source_id(self) -> Any:
        """
        Return the channel's source identifier.
        """

        return getattr(
            self._channel,
            "source_id",
            None,
        )

    # -----------------------------------------------------------------

    @property
    def source_terminal(self) -> Any:
        """
        Return the source terminal reference.
        """

        return getattr(
            self._channel,
            "source_terminal",
            None,
        )

    # -----------------------------------------------------------------

    @property
    def source_terminal_id(self) -> Any:
        """
        Return the source terminal identifier.
        """

        return getattr(
            self._channel,
            "source_terminal_id",
            None,
        )

    # =================================================================
    # SAMPLE / TIME INFORMATION
    # =================================================================

    @property
    def timestamp(self) -> Any:
        """
        Return the latest channel sample timestamp.
        """

        return getattr(
            self._channel,
            "timestamp",
            None,
        )

    # -----------------------------------------------------------------

    @property
    def sample_sequence(self) -> Any:
        """
        Return the latest channel sample sequence.
        """

        return getattr(
            self._channel,
            "sample_sequence",
            None,
        )

    # =================================================================
    # METADATA
    # =================================================================

    @property
    def metadata(self) -> Mapping[str, Any]:
        """
        Return read-only RelayInput metadata.

        This metadata is descriptive only and is not authoritative
        measurement state.
        """

        return MappingProxyType(
            dict(self._metadata)
        )

    # -----------------------------------------------------------------

    def set_metadata(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Set RelayInput-local metadata.

        This must not be used to duplicate MeasurementChannel state.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Metadata name must be a string."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "Metadata name cannot be empty."
            )

        self._metadata[name] = value

    # =================================================================
    # STATUS
    # =================================================================

    @staticmethod
    def _enum_value(
        value: Any,
    ) -> Any:
        """
        Return an enum's value when applicable.

        This keeps diagnostics tolerant of either enum-based or
        string-based MeasurementChannel APIs.
        """

        enum_value = getattr(
            value,
            "value",
            None,
        )

        return (
            enum_value
            if enum_value is not None
            else value
        )

    # -----------------------------------------------------------------

    def status(
        self,
        *,
        current_time: float | None = None,
    ) -> dict[str, Any]:
        """
        Return diagnostic information for this RelayInput.

        This is not the persistence representation.
        """

        validity = self.validity(
            current_time=current_time,
        )

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "channel_id": self.channel_id,
            "signal_type": self._enum_value(
                self.signal_type
            ),
            "phase": self._enum_value(
                self.phase
            ),
            "unit": self.unit,
            "nominal_value": self.nominal_value,
            "engineering_value": (
                self.engineering_value
                if self.available
                else None
            ),
            "available": self.available,
            "quality": self._enum_value(
                self.quality
            ),
            "valid": self.valid,
            "usable": self.usable,
            "validity": self._enum_value(
                validity
            ),
            "timestamp": self.timestamp,
            "sample_sequence": self.sample_sequence,
            "source_id": self.source_id,
            "source_terminal_id": (
                self.source_terminal_id
            ),
            "metadata": dict(
                self._metadata
            ),
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<RelayInput "
            f"name={self.name!r}, "
            f"channel={self.channel_id!r}, "
            f"value={self.engineering_value!r}, "
            f"usable={self.usable}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "RelayInput",
]
