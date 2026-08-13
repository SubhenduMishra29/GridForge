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
-----------------------

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

Example
-------

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
than importing the concrete MeasurementChannel implementation.

The authoritative measurement implementation remains:

    core.measurement.measurement_channel.MeasurementChannel

This avoids unnecessary coupling and circular imports.

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
            Whether the consuming protection function requires this
            input.

        metadata:
            Optional binding-local descriptive metadata.
        """

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

        elif not isinstance(
            metadata,
            Mapping,
        ):
            raise TypeError(
                "RelayInput metadata must be a mapping."
            )

        else:
            self._metadata = dict(
                metadata
            )

    # ==================================================================
    # VALIDATION
    # ==================================================================

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

    # ------------------------------------------------------------------

    @staticmethod
    def _validate_channel(
        channel: Any,
    ) -> None:
        """
        Validate the minimum structural MeasurementChannel contract.

        Only the attributes fundamentally required by RelayInput are
        mandatory.

        Additional MeasurementChannel information is accessed
        defensively when available.
        """

        required_attributes = (
            "id",
            "engineering_value",
            "available",
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
    def measurement_channel(
        self,
    ) -> MeasurementChannel:
        """
        Explicit alias for ``channel``.
        """

        return self._channel

    # ==================================================================
    # LOCAL CONFIGURATION
    # ==================================================================

    @property
    def description(self) -> str:
        """
        Return the binding description.
        """

        return self._description

    # ------------------------------------------------------------------

    @property
    def required(self) -> bool:
        """
        Return whether the input is required by its consumer.
        """

        return self._required

    # ==================================================================
    # MEASUREMENT ACCESS
    # ==================================================================

    @property
    def value(self) -> Any:
        """
        Return the current engineering value.

        MeasurementChannel remains authoritative.
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
        Return whether the authoritative MeasurementChannel considers
        the measurement usable.
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
        Return the channel validity state when available.

        If the channel does not expose ``is_valid``, usability is used
        as the fallback protection-facing validity indication.
        """

        value = getattr(
            self._channel,
            "is_valid",
            None,
        )

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
        Return the engineering unit when available.
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
        Return the channel nominal engineering value when available.
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
        Return the authoritative channel validity state.

        RelayInput does not calculate validity.
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
            current_time=current_time
        )

    # ------------------------------------------------------------------

    def is_valid_at(
        self,
        current_time: float | None = None,
    ) -> bool:
        """
        Return whether the channel is valid at the specified
        evaluation time.

        If the MeasurementChannel does not provide an explicit
        ``is_valid_at`` method, the current ``valid`` state is used.
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
        Return the source identifier when available.
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
        Return the source terminal reference when available.
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
        Return the source terminal identifier when available.
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

        This metadata is not authoritative measurement state.
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

        This must not be used to duplicate measurement state.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Metadata name must be a string."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Metadata name cannot be empty."
            )

        self._metadata[
            normalized_name
        ] = value

    # ==================================================================
    # DIAGNOSTICS
    # ==================================================================

    @staticmethod
    def _enum_value(
        value: Any,
    ) -> Any:
        """
        Return the underlying value of an enum when applicable.
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

        This is not the persistence representation.
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
