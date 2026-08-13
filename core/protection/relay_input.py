"""
GridForge V2 Relay Input.

File
----
core/protection/relay_input.py

Purpose
-------
Defines the protection-facing binding between a protection function
and an authoritative MeasurementChannel.

Architectural Position
----------------------

    Physical Instrument
        |
        v
    Measurement Interface
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

MeasurementChannel is authoritative for the logical measurement.

RelayInput does not duplicate measurement state and does not perform
measurement conversion.

Responsibilities
-----------------
RelayInput:

    * identifies a named protection input
    * references one MeasurementChannel
    * exposes the channel's engineering value
    * exposes channel availability and quality
    * exposes measurement metadata required by protection functions
    * provides a stable protection-facing binding

RelayInput does NOT:

    * model CT/PT/CVT equipment
    * calculate CT/PT/CVT ratios
    * perform scaling
    * perform polarity transformation
    * simulate measurements
    * own measurement state
    * implement protection logic
    * operate breakers
    * modify network topology
    * contain GUI state
    * perform persistence

The authoritative measurement implementation is:

    core/measurement/measurement_channel.py
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from core.measurement.measurement_channel import (
        MeasurementChannel,
    )


class RelayInput:
    """
    Protection-facing binding to one MeasurementChannel.

    A RelayInput is intentionally a lightweight reference object.

    Examples
    --------
    A 50/51 function may receive:

        IA -> MeasurementChannel
        IB -> MeasurementChannel
        IC -> MeasurementChannel

    A voltage function may receive:

        VA -> MeasurementChannel

    A frequency function may receive:

        FREQ -> MeasurementChannel

    The protection function consumes RelayInput rather than reaching
    directly into CT/PT/CVT implementation details.
    """

    def __init__(
        self,
        name: str,
        channel: MeasurementChannel,
        *,
        description: str = "",
        required: bool = True,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """
        Create a protection input binding.

        Parameters
        ----------
        name:
            Function-local input name.

            Examples:
                IA
                IB
                IC
                IN
                VA
                VB
                VC
                FREQ
                P
                Q

        channel:
            Authoritative MeasurementChannel providing the signal.

        description:
            Optional human-readable description.

        required:
            Whether the input is required by the consuming protection
            function.

        metadata:
            Optional non-authoritative input metadata.
        """

        if not isinstance(name, str):
            raise TypeError(
                "RelayInput name must be a string."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "RelayInput name cannot be empty."
            )

        if channel is None:
            raise ValueError(
                f"RelayInput '{name}' requires a "
                "MeasurementChannel."
            )

        # Avoid importing the concrete MeasurementChannel at runtime
        # solely for type checking. The authoritative object contract
        # is nevertheless explicitly defined in:
        #
        #     core.measurement.measurement_channel
        #
        # A runtime structural check is used only for a clear failure
        # message if an incompatible object is supplied.
        required_attributes = (
            "id",
            "engineering_value",
            "available",
            "quality",
            "is_usable",
            "validity",
        )

        missing = [
            attribute
            for attribute in required_attributes
            if not hasattr(channel, attribute)
        ]

        if missing:
            raise TypeError(
                f"RelayInput '{name}' requires a "
                "MeasurementChannel-compatible object; "
                f"missing attributes: {missing}."
            )

        self.name = name
        self.channel = channel
        self.description = str(description).strip()
        self.required = bool(required)

        self._metadata = dict(
            metadata or {}
        )

    # ==================================================================
    # IDENTITY
    # ==================================================================

    @property
    def id(self) -> str:
        """
        Return the input identity within its consuming protection
        function.

        RelayInput identity is deliberately separate from the
        MeasurementChannel identity.
        """
        return self.name

    @property
    def channel_id(self) -> str:
        """
        Return the authoritative MeasurementChannel identity.
        """
        return self.channel.id

    # ==================================================================
    # CHANNEL
    # ==================================================================

    @property
    def measurement_channel(self) -> MeasurementChannel:
        """
        Return the authoritative MeasurementChannel.

        This property makes the architectural relationship explicit
        without copying channel state.
        """
        return self.channel

    # ==================================================================
    # VALUE
    # ==================================================================

    @property
    def value(self) -> float | complex:
        """
        Return the current engineering value.

        MeasurementChannel is authoritative for scaling and polarity.
        """
        return self.channel.engineering_value

    @property
    def engineering_value(self) -> float | complex:
        """
        Return the current engineering value.

        This is the preferred semantic property for protection code.
        """
        return self.channel.engineering_value

    @property
    def signal(self) -> float | complex:
        """
        Return the current engineering signal.

        Delegates directly to MeasurementChannel.signal.
        """
        return self.channel.signal

    # ==================================================================
    # SIGNAL INFORMATION
    # ==================================================================

    @property
    def signal_type(self) -> Any:
        """
        Return the MeasurementChannel signal type.
        """
        return self.channel.signal_type

    @property
    def phase(self) -> Any:
        """
        Return the MeasurementChannel phase/sequence designation.
        """
        return self.channel.phase

    @property
    def unit(self) -> str:
        """
        Return the engineering unit of the measurement.
        """
        return self.channel.unit

    @property
    def nominal_value(self) -> float:
        """
        Return the channel nominal engineering magnitude.
        """
        return self.channel.nominal_value

    # ==================================================================
    # QUALITY / AVAILABILITY
    # ==================================================================

    @property
    def available(self) -> bool:
        """
        Return whether the logical measurement path is available.
        """
        return self.channel.available

    @property
    def quality(self) -> Any:
        """
        Return the current MeasurementQuality.
        """
        return self.channel.quality

    @property
    def usable(self) -> bool:
        """
        Return whether the channel currently provides a usable
        measurement.

        This delegates to the authoritative MeasurementChannel
        usability contract.
        """
        return self.channel.is_usable

    @property
    def valid(self) -> bool:
        """
        Return basic measurement validity.

        This delegates to MeasurementChannel.is_valid.
        """
        return self.channel.is_valid

    def validity(
        self,
        *,
        current_time: float | None = None,
    ) -> Any:
        """
        Return the authoritative MeasurementValidity state.

        ``current_time`` is supplied by the protection execution
        context when staleness evaluation is required.

        RelayInput does not maintain its own clock or validity state.
        """
        return self.channel.validity(
            current_time=current_time,
        )

    def is_valid_at(
        self,
        current_time: float | None = None,
    ) -> bool:
        """
        Return whether the measurement is valid at a specified time.
        """
        return self.channel.is_valid_at(
            current_time,
        )

    # ==================================================================
    # SOURCE INFORMATION
    # ==================================================================

    @property
    def source(self) -> Any:
        """
        Return the channel's measurement source reference.
        """
        return self.channel.source

    @property
    def source_id(self) -> str | None:
        """
        Return the source equipment identifier, if available.
        """
        return self.channel.source_id

    @property
    def source_terminal(self) -> Any:
        """
        Return the channel's source-terminal reference.
        """
        return self.channel.source_terminal

    @property
    def source_terminal_id(self) -> str | None:
        """
        Return the source-terminal identifier, if available.
        """
        return self.channel.source_terminal_id

    # ==================================================================
    # TIME / SAMPLE INFORMATION
    # ==================================================================

    @property
    def timestamp(self) -> float | None:
        """
        Return the channel's latest sample timestamp.
        """
        return self.channel.timestamp

    @property
    def sample_sequence(self) -> int | None:
        """
        Return the channel's latest sample/update sequence number.
        """
        return self.channel.sample_sequence

    # ==================================================================
    # METADATA
    # ==================================================================

    @property
    def metadata(self) -> Mapping[str, Any]:
        """
        Return read-only input metadata.

        Metadata is descriptive information and is not authoritative
        measurement state.
        """
        return MappingProxyType(
            self._metadata
        )

    # ==================================================================
    # DIAGNOSTICS
    # ==================================================================

    def status(
        self,
        *,
        current_time: float | None = None,
    ) -> dict[str, Any]:
        """
        Return diagnostic information for this RelayInput.

        This is intended for inspection and diagnostics, not as the
        authoritative persistence representation.
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
            "signal_type": (
                self.channel.signal_type.value
            ),
            "phase": (
                self.channel.phase.value
            ),
            "unit": self.unit,
            "nominal_value": self.nominal_value,
            "engineering_value": (
                self.engineering_value
                if self.available
                else None
            ),
            "available": self.available,
            "quality": self.quality.value,
            "valid": self.valid,
            "usable": self.usable,
            "validity": validity.value,
            "timestamp": self.timestamp,
            "sample_sequence": self.sample_sequence,
            "source_id": self.source_id,
            "source_terminal_id": (
                self.source_terminal_id
            ),
            "metadata": dict(self._metadata),
        }

    # ==================================================================
    # REPRESENTATION
    # ==================================================================

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


__all__ = [
    "RelayInput",
]
