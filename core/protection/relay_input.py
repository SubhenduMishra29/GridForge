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
      RelayBase / ProtectionElement
              |
              v
      ProtectionDecision

Architectural Rules
-------------------

RelayInput is a protection-facing reference.

It does NOT:

    * own measurement state;
    * copy measurement values;
    * transform measurement values;
    * scale measurement values;
    * maintain a clock;
    * calculate electrical quantities;
    * perform protection logic;
    * modify MeasurementChannel state;
    * create physical instrumentation;
    * operate breakers;
    * modify network topology;
    * perform persistence;
    * contain GUI state.

MeasurementChannel remains authoritative.

The purpose of RelayInput is to provide a stable, named interface
through which protection functions consume measurements.

Measurement Architecture
------------------------

    CT / PT / CVT
          |
          v
    MeasurementChannel
          |
          v
       RelayInput
          |
          v
    Protection Function

Multiple protection functions may reference the same
MeasurementChannel through separate RelayInput bindings.

Compatibility
-------------

This module intentionally uses a structural runtime contract rather
than importing the concrete MeasurementChannel implementation.

The authoritative measurement implementation remains:

    core.measurement.measurement_channel.MeasurementChannel

The runtime contract is intentionally limited to attributes and
methods actually required by RelayInput.

RelayInput never caches authoritative measurement values.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from core.measurement.measurement_channel import MeasurementChannel


class RelayInput:
    """
    Protection-facing binding to one authoritative
    MeasurementChannel.

    RelayInput owns only protection-local binding information:

        name
        description
        required
        metadata

    The MeasurementChannel itself remains externally owned and
    authoritative.

    Every measurement-related property is a live read-through to the
    authoritative channel. No measurement value is cached locally.
    """

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

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
        Create a protection-facing measurement binding.

        Parameters
        ----------
        name:
            Protection-local input name.

        channel:
            Authoritative MeasurementChannel reference.

        description:
            Optional human-readable description.

        required:
            Whether the input is required by its consuming
            protection function.

        metadata:
            Optional binding-local metadata.

        Notes
        -----
        The channel reference is retained but never copied.

        Measurement values, validity, quality, timestamps, and source
        information remain authoritative in MeasurementChannel.
        """

        normalized_name = self._normalize_name(name)

        self._validate_channel(channel)

        if not isinstance(required, bool):
            raise TypeError(
                "RelayInput required must be a boolean."
            )

        if not isinstance(description, str):
            raise TypeError(
                "RelayInput description must be a string."
            )

        if metadata is None:
            normalized_metadata: dict[str, Any] = {}

        elif not isinstance(metadata, Mapping):
            raise TypeError(
                "RelayInput metadata must be a mapping."
            )

        else:
            normalized_metadata = dict(metadata)

        # --------------------------------------------------------------
        # Binding-local state
        # --------------------------------------------------------------

        self._name = normalized_name
        self._description = description.strip()
        self._required = required
        self._metadata = normalized_metadata

        # --------------------------------------------------------------
        # Authoritative external reference
        # --------------------------------------------------------------

        self._channel = channel

    # ==================================================================
    # VALIDATION
    # ==================================================================

    @staticmethod
    def _normalize_name(value: str) -> str:
        """
        Validate and normalize a protection-local input name.
        """

        if not isinstance(value, str):
            raise TypeError(
                "RelayInput name must be a string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "RelayInput name cannot be empty."
            )

        return normalized

    # ------------------------------------------------------------------

    @staticmethod
    def _validate_channel(
        channel: Any,
    ) -> None:
        """
        Validate the minimum structural MeasurementChannel contract.

        RelayInput deliberately uses a structural runtime contract to
        avoid unnecessary coupling and circular imports.

        Required channel members are limited to the authoritative
        identity and the basic protection-facing measurement state.

        Optional channel members are accessed defensively.
        """

        if channel is None:
            raise ValueError(
                "RelayInput requires a MeasurementChannel."
            )

        required_attributes = (
            "id",
            "engineering_value",
            "available",
            "is_usable",
        )

        missing = [
            attribute
            for attribute in required_attributes
            if not hasattr(channel, attribute)
        ]

        if missing:
            raise TypeError(
                "channel is not compatible with the "
                "MeasurementChannel protection-facing contract. "
                f"Missing attributes: {missing}."
            )

    # ==================================================================
    # IDENTITY
    # ==================================================================

    @property
    def id(self) -> str:
        """
        Return the stable protection-local input identity.
        """

        return self._name

    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """
        Return the protection-local input name.
        """

        return self._name

    # ------------------------------------------------------------------

    @property
    def channel_id(self) -> Any:
        """
        Return the authoritative MeasurementChannel identity.
        """

        return getattr(
            self._channel,
            "id",
            None,
        )

    # ==================================================================
    # BINDING
    # ==================================================================

    @property
    def channel(self) -> MeasurementChannel:
        """
        Return the authoritative MeasurementChannel reference.

        The channel is referenced, never copied.
        """

        return self._channel

    # ------------------------------------------------------------------

    @property
    def measurement_channel(self) -> MeasurementChannel:
        """
        Explicit semantic alias for ``channel``.
        """

        return self._channel

    # ==================================================================
    # LOCAL CONFIGURATION
    # ==================================================================

    @property
    def description(self) -> str:
        """
        Return the binding-local description.
        """

        return self._description

    # ------------------------------------------------------------------

    @property
    def required(self) -> bool:
        """
        Return whether this input is required by its consumer.
        """

        return self._required

    # ==================================================================
    # MEASUREMENT ACCESS
    # ==================================================================

    @property
    def value(self) -> Any:
        """
        Return the current authoritative engineering value.

        This is a live read-through and is never cached.
        """

        return self.engineering_value

    # ------------------------------------------------------------------

    @property
    def engineering_value(self) -> Any:
        """
        Return the current engineering value directly from the
        authoritative MeasurementChannel.
        """

        return getattr(
            self._channel,
            "engineering_value",
            None,
        )

    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        """
        Return the authoritative channel availability state.
        """

        return bool(
            getattr(
                self._channel,
                "available",
                False,
            )
        )

    # ------------------------------------------------------------------

    @property
    def usable(self) -> bool:
        """
        Return the authoritative channel usability state.
        """

        return bool(
            getattr(
                self._channel,
                "is_usable",
                False,
            )
        )

    # ------------------------------------------------------------------

    @property
    def valid(self) -> bool:
        """
        Return the authoritative channel validity state.

        ``is_valid`` may be either a boolean property or a callable
        method depending on the MeasurementChannel implementation.

        When unavailable, usability is used as the protection-facing
        fallback.
        """

        value = getattr(
            self._channel,
            "is_valid",
            None,
        )

        if callable(value):
            try:
                value = value()
            except TypeError:
                return self.usable

        if value is None:
            return self.usable

        return bool(value)

    # ------------------------------------------------------------------

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

    # ==================================================================
    # SIGNAL INFORMATION
    # ==================================================================

    @property
    def signal_type(self) -> Any:
        """
        Return the authoritative signal type when available.
        """

        return getattr(
            self._channel,
            "signal_type",
            None,
        )

    # ------------------------------------------------------------------

    @property
    def phase(self) -> Any:
        """
        Return the authoritative phase or sequence designation when
        available.
        """

        return getattr(
            self._channel,
            "phase",
            None,
        )

    # ------------------------------------------------------------------

    @property
    def unit(self) -> Any:
        """
        Return the authoritative engineering unit when available.
        """

        return getattr(
            self._channel,
            "unit",
            None,
        )

    # ------------------------------------------------------------------

    @property
    def nominal_value(self) -> Any:
        """
        Return the authoritative nominal engineering value when
        available.
        """

        return getattr(
            self._channel,
            "nominal_value",
            None,
        )

    # ==================================================================
    # VALIDITY
    # ==================================================================

    def validity(
        self,
        *,
        current_time: float | None = None,
    ) -> Any:
        """
        Return authoritative channel validity information.

        RelayInput does not calculate validity.

        If the channel exposes a ``validity`` method, it is called
        using the supported evaluation-time form.

        If no such method exists, ``None`` is returned.
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

        try:
            return method(
                current_time=current_time
            )
        except TypeError:
            # Compatibility with a channel implementation exposing
            # the evaluation time positionally.
            return method(current_time)

    # ------------------------------------------------------------------

    def is_valid_at(
        self,
        current_time: float | None = None,
    ) -> bool:
        """
        Return whether the channel is valid at the specified
        evaluation time.

        The MeasurementChannel remains authoritative.

        If an explicit ``is_valid_at`` method is unavailable, the
        current channel validity state is used.
        """

        method = getattr(
            self._channel,
            "is_valid_at",
            None,
        )

        if callable(method):

            if current_time is None:
                return bool(method())

            try:
                return bool(
                    method(
                        current_time=current_time
                    )
                )
            except TypeError:
                return bool(
                    method(current_time)
                )

        return self.valid

    # ==================================================================
    # SOURCE INFORMATION
    # ==================================================================

    @property
    def source(self) -> Any:
        """
        Return the authoritative measurement source reference when
        available.
        """

        return getattr(
            self._channel,
            "source",
            None,
        )

    # ------------------------------------------------------------------

    @property
    def source_id(self) -> Any:
        """
        Return the authoritative source identifier when available.
        """

        return getattr(
            self._channel,
            "source_id",
            None,
        )

    # ------------------------------------------------------------------

    @property
    def source_terminal(self) -> Any:
        """
        Return the authoritative source terminal reference when
        available.
        """

        return getattr(
            self._channel,
            "source_terminal",
            None,
        )

    # ------------------------------------------------------------------

    @property
    def source_terminal_id(self) -> Any:
        """
        Return the authoritative source terminal identifier when
        available.
        """

        return getattr(
            self._channel,
            "source_terminal_id",
            None,
        )

    # ==================================================================
    # SAMPLE INFORMATION
    # ==================================================================

    @property
    def timestamp(self) -> Any:
        """
        Return the latest authoritative measurement timestamp.
        """

        return getattr(
            self._channel,
            "timestamp",
            None,
        )

    # ------------------------------------------------------------------

    @property
    def sample_sequence(self) -> Any:
        """
        Return the latest authoritative sample sequence when
        available.
        """

        return getattr(
            self._channel,
            "sample_sequence",
            None,
        )

    # ==================================================================
    # METADATA
    # ==================================================================

    @property
    def metadata(self) -> Mapping[str, Any]:
        """
        Return read-only binding-local metadata.

        Metadata belongs to RelayInput and is never authoritative
        measurement state.
        """

        return MappingProxyType(
            self._metadata
        )

    # ------------------------------------------------------------------

    def set_metadata(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Set binding-local metadata.

        This operation affects RelayInput metadata only.

        It must never be used to mirror or override
        MeasurementChannel state.
        """

        normalized_name = self._normalize_metadata_name(
            name
        )

        self._metadata[
            normalized_name
        ] = value

    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_metadata_name(
        name: str,
    ) -> str:
        """
        Validate and normalize a metadata key.
        """

        if not isinstance(name, str):
            raise TypeError(
                "Metadata name must be a string."
            )

        normalized = name.strip()

        if not normalized:
            raise ValueError(
                "Metadata name cannot be empty."
            )

        return normalized

    # ==================================================================
    # DIAGNOSTICS
    # ==================================================================

    @staticmethod
    def _enum_value(
        value: Any,
    ) -> Any:
        """
        Return an enum's underlying value when applicable.

        Ordinary values are returned unchanged.
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

    # ------------------------------------------------------------------

    def status(
        self,
        *,
        current_time: float | None = None,
    ) -> dict[str, Any]:
        """
        Return diagnostic information.

        This is a detached diagnostic representation.

        It is not the persistence representation and does not
        serialize the authoritative MeasurementChannel.
        """

        validity = self.validity(
            current_time=current_time
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


# ======================================================================
# PUBLIC API
# ======================================================================

__all__ = [
    "RelayInput",
]
