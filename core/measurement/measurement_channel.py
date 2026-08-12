"""
GridForge Measurement Channel
=============================

File:
    core/measurement/measurement_channel.py

Purpose
-------
Defines the canonical GridForge V2 measurement-channel abstraction.

A MeasurementChannel represents a logical measurement signal produced
from a physical measurement interface and made available to consuming
systems such as:

    - protection
    - metering
    - control
    - SCADA
    - synchronization
    - monitoring
    - analysis

Architectural position
----------------------

    Physical Instrument
        │
        ├── CT
        ├── PT
        └── CVT
             │
             │ secondary interface
             ▼
    MeasurementChannel
             │
             ├── Protection
             ├── Metering
             ├── Control
             └── Monitoring

The MeasurementChannel is a CORE GridForge V2 abstraction.

It is NOT a protection plugin.

Specialized measurement-generation behaviour, such as:

    - CT saturation
    - instrument error
    - transient response
    - filtering
    - frequency response
    - burden effects

may be implemented by plugins, while this channel contract remains
stable.

Architectural Responsibilities
------------------------------

MeasurementChannel is responsible for:

    - channel identity
    - source equipment association
    - source interface association
    - signal classification
    - phase identification
    - engineering unit
    - nominal/rated value
    - scaling
    - polarity
    - measured value
    - signal quality
    - availability
    - timestamp/sample information
    - local validation
    - measurement diagnostics

MeasurementChannel does NOT:

    - build network topology
    - create Bus objects
    - build Y-bus
    - calculate load flow
    - calculate short circuit
    - implement relay logic
    - perform protection coordination
    - calculate TCC curves
    - operate breakers
    - own physical CT/PT/CVT equipment
    - determine system-wide electrical quantities
    - manage GUI state

Authoritative Ownership
-----------------------

Physical equipment remains authoritative for physical equipment
identity and nameplate data:

    core/model/ct.py
    core/model/pt.py
    core/model/cvt.py

The MeasurementChannel is authoritative only for the logical
measurement signal it represents.

A channel may reference its source equipment and source terminal,
but it does not duplicate that equipment's state.

Relay Architecture
------------------

The V2 Relay should consume MeasurementChannel objects.

For example:

    CT
      │
      ▼
    Current MeasurementChannel
      │
      ▼
    Relay input
      │
      ▼
    Overcurrent / Directional / Differential function

and:

    PT / CVT
      │
      ▼
    Voltage MeasurementChannel
      │
      ▼
    Relay input
      │
      ▼
    Distance / Voltage / Directional function

The Relay must therefore not obtain its protection signal directly
from a raw CT/PT/CVT object.

Signal Domain
-------------

Measurement channels use explicit signal types rather than relying
on arbitrary field names.

Supported signal types include:

    CURRENT
    VOLTAGE
    POWER
    FREQUENCY
    PHASE_ANGLE
    IMPEDANCE
    DIGITAL
    CUSTOM

Phase identification supports:

    A
    B
    C
    N
    AB
    BC
    CA
    THREE_PHASE
    POSITIVE_SEQUENCE
    NEGATIVE_SEQUENCE
    ZERO_SEQUENCE
    NONE

Quality
-------

A channel may contain a valid numerical value while the signal is
not suitable for protection.

Therefore signal quality and availability are explicit.

The distinction is:

    available
        Whether a signal source is presently available.

    quality
        Whether the signal is considered valid/reliable.

Protection consumers must be able to reject invalid measurements
without inspecting the physical instrument model.

Time
----

The channel supports an optional timestamp.

The channel does not prescribe a particular simulation clock,
event scheduler, or time-domain engine.

Simulation layers may update the channel repeatedly.

GridForge V2 Status
-------------------

This module is part of the GridForge Model/Measurement foundation.

The contract is intentionally independent of:

    - protection algorithms
    - simulation engines
    - network topology
    - numerical solvers

Higher-level protection modules should depend on this contract
rather than directly depending on CT/PT/CVT implementation details.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from enum import Enum
from math import isfinite
from typing import Any, Optional


# =====================================================================
# SIGNAL TYPE
# =====================================================================


class MeasurementSignalType(Enum):
    """
    Canonical GridForge measurement signal types.
    """

    CURRENT = "CURRENT"
    VOLTAGE = "VOLTAGE"
    POWER = "POWER"
    FREQUENCY = "FREQUENCY"
    PHASE_ANGLE = "PHASE_ANGLE"
    IMPEDANCE = "IMPEDANCE"
    DIGITAL = "DIGITAL"
    CUSTOM = "CUSTOM"


# =====================================================================
# PHASE
# =====================================================================


class MeasurementPhase(Enum):
    """
    Phase or sequence designation for a measurement channel.
    """

    NONE = "NONE"

    A = "A"
    B = "B"
    C = "C"

    N = "N"

    AB = "AB"
    BC = "BC"
    CA = "CA"

    THREE_PHASE = "THREE_PHASE"

    POSITIVE_SEQUENCE = "POSITIVE_SEQUENCE"
    NEGATIVE_SEQUENCE = "NEGATIVE_SEQUENCE"
    ZERO_SEQUENCE = "ZERO_SEQUENCE"


# =====================================================================
# QUALITY
# =====================================================================


class MeasurementQuality(Enum):
    """
    Measurement signal quality state.

    GOOD
        Signal is valid and suitable for normal consumption.

    SUSPECT
        Signal exists but may not be reliable.

    INVALID
        Signal is not valid for engineering use.

    UNKNOWN
        Quality has not been established.
    """

    GOOD = "GOOD"
    SUSPECT = "SUSPECT"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


# =====================================================================
# MEASUREMENT CHANNEL
# =====================================================================


class MeasurementChannel:
    """
    Canonical GridForge V2 measurement signal channel.

    Parameters
    ----------
    id : str
        Unique channel identifier.

    signal_type : MeasurementSignalType
        Type of measurement represented by this channel.

    name : str, optional
        Human-readable channel name.

    source : object, optional
        Physical source equipment.

        Typical sources:

            CurrentTransformer
            PotentialTransformer
            CVT

        The source is referenced, not duplicated.

    source_terminal : object, optional
        Measurement-side terminal/interface from the source
        equipment.

    phase : MeasurementPhase, optional
        Phase or sequence associated with the signal.

    unit : str, optional
        Engineering unit.

        Examples:

            A
            kA
            V
            kV
            W
            MW
            Hz
            deg
            ohm

    nominal_value : float, optional
        Nominal/reference value associated with the channel.

    scale : float, optional
        Engineering scaling factor applied to the raw channel value.

    polarity : float, optional
        Measurement polarity.

        +1.0 means normal polarity.
        -1.0 means reversed polarity.

    available : bool, optional
        Whether the measurement source is currently available.

    quality : MeasurementQuality, optional
        Current signal quality.

    value : float or complex, optional
        Current engineering measurement.

    timestamp : float, optional
        Optional simulation/event timestamp.

    Notes
    -----
    The channel is deliberately lightweight.

    It represents a signal contract rather than a measurement
    simulation engine.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        id: str,
        signal_type: MeasurementSignalType,
        name: str = "",
        source: Any = None,
        source_terminal: Any = None,
        phase: MeasurementPhase = MeasurementPhase.NONE,
        unit: str = "",
        nominal_value: float = 0.0,
        scale: float = 1.0,
        polarity: float = 1.0,
        available: bool = True,
        quality: MeasurementQuality = MeasurementQuality.UNKNOWN,
        value: float | complex = 0.0,
        timestamp: Optional[float] = None,
    ) -> None:

        # ---------------------------------------------------------
        # Identity
        # ---------------------------------------------------------

        self._validate_id(id)

        self.id = id
        self.name = str(name)

        # ---------------------------------------------------------
        # Signal classification
        # ---------------------------------------------------------

        if not isinstance(
            signal_type,
            MeasurementSignalType,
        ):
            raise TypeError(
                "signal_type must be a MeasurementSignalType."
            )

        self.signal_type = signal_type

        if not isinstance(
            phase,
            MeasurementPhase,
        ):
            raise TypeError(
                "phase must be a MeasurementPhase."
            )

        self.phase = phase

        # ---------------------------------------------------------
        # Source association
        # ---------------------------------------------------------

        if source is not None:
            self._validate_reference(
                source,
                "source",
            )

        if source_terminal is not None:
            self._validate_reference(
                source_terminal,
                "source_terminal",
            )

        self.source = source
        self.source_terminal = source_terminal

        # ---------------------------------------------------------
        # Engineering metadata
        # ---------------------------------------------------------

        if not isinstance(unit, str):
            raise TypeError(
                "unit must be a string."
            )

        self.unit = unit

        self.nominal_value = float(
            nominal_value
        )

        self.scale = float(
            scale
        )

        self.polarity = float(
            polarity
        )

        self._validate_engineering_data()

        # ---------------------------------------------------------
        # Signal state
        # ---------------------------------------------------------

        self.available = bool(
            available
        )

        if not isinstance(
            quality,
            MeasurementQuality,
        ):
            raise TypeError(
                "quality must be a MeasurementQuality."
            )

        self.quality = quality

        # ---------------------------------------------------------
        # Current measurement
        # ---------------------------------------------------------

        self.value = self._validate_value(
            value
        )

        # ---------------------------------------------------------
        # Time information
        # ---------------------------------------------------------

        if timestamp is not None:
            timestamp = float(timestamp)

            if not isfinite(timestamp):
                raise ValueError(
                    "timestamp must be finite."
                )

        self.timestamp = timestamp

    # =============================================================
    # VALIDATION
    # =============================================================

    @staticmethod
    def _validate_id(
        value: str,
    ) -> None:
        """
        Validate channel identity.
        """

        if not isinstance(value, str):
            raise TypeError(
                "MeasurementChannel id must be a string."
            )

        if not value.strip():
            raise ValueError(
                "MeasurementChannel id cannot be empty."
            )

    # -------------------------------------------------------------

    @staticmethod
    def _validate_reference(
        value: Any,
        field_name: str,
    ) -> None:
        """
        Validate a referenced GridForge object.

        References require an identifiable object but the channel
        deliberately does not impose a concrete CT/PT/CVT class.
        """

        if not hasattr(value, "id"):
            raise TypeError(
                f"{field_name} must expose an 'id' attribute."
            )

        object_id = getattr(
            value,
            "id",
        )

        if not isinstance(object_id, str):
            raise TypeError(
                f"{field_name}.id must be a string."
            )

        if not object_id.strip():
            raise ValueError(
                f"{field_name}.id cannot be empty."
            )

    # -------------------------------------------------------------

    def _validate_engineering_data(self) -> None:
        """
        Validate engineering metadata.
        """

        if (
            not isfinite(self.nominal_value)
            or self.nominal_value < 0.0
        ):
            raise ValueError(
                "nominal_value must be finite and non-negative."
            )

        if (
            not isfinite(self.scale)
            or self.scale == 0.0
        ):
            raise ValueError(
                "scale must be finite and non-zero."
            )

        if (
            not isfinite(self.polarity)
            or self.polarity not in (-1.0, 1.0)
        ):
            raise ValueError(
                "polarity must be either +1.0 or -1.0."
            )

    # -------------------------------------------------------------

    @staticmethod
    def _validate_value(
        value: float | complex,
    ) -> float | complex:
        """
        Validate a channel measurement value.

        Real and complex values are both supported.

        Complex values are required for quantities such as:

            impedance
            phasors
        """

        if isinstance(value, bool):
            raise TypeError(
                "Measurement value cannot be bool."
            )

        if isinstance(value, complex):

            if (
                not isfinite(value.real)
                or not isfinite(value.imag)
            ):
                raise ValueError(
                    "Complex measurement value must be finite."
                )

            return value

        value = float(value)

        if not isfinite(value):
            raise ValueError(
                "Measurement value must be finite."
            )

        return value

    # =============================================================
    # SOURCE
    # =============================================================

    def set_source(
        self,
        source: Any,
    ) -> None:
        """
        Associate the channel with a measurement source.

        This does not modify the source equipment.
        """

        self._validate_reference(
            source,
            "source",
        )

        self.source = source

    # -------------------------------------------------------------

    def set_source_terminal(
        self,
        terminal: Any,
    ) -> None:
        """
        Associate the channel with a source measurement terminal.

        This stores only the local association.

        It does not create a network or protection connection.
        """

        self._validate_reference(
            terminal,
            "source_terminal",
        )

        self.source_terminal = terminal

    # =============================================================
    # MEASUREMENT UPDATE
    # =============================================================

    def update(
        self,
        value: float | complex,
        *,
        timestamp: Optional[float] = None,
        quality: Optional[MeasurementQuality] = None,
        available: Optional[bool] = None,
    ) -> None:
        """
        Update the channel measurement.

        Parameters
        ----------
        value:
            New engineering measurement.

        timestamp:
            Optional measurement timestamp.

        quality:
            Optional signal quality update.

        available:
            Optional availability update.

        Notes
        -----
        The supplied value is the channel engineering value.

        Scaling and instrument-specific transformation should be
        performed by the measurement-generation layer/plugin before
        the value is written here.
        """

        self.value = self._validate_value(
            value
        )

        if timestamp is not None:

            timestamp = float(
                timestamp
            )

            if not isfinite(timestamp):
                raise ValueError(
                    "timestamp must be finite."
                )

            self.timestamp = timestamp

        if quality is not None:

            if not isinstance(
                quality,
                MeasurementQuality,
            ):
                raise TypeError(
                    "quality must be a MeasurementQuality."
                )

            self.quality = quality

        if available is not None:
            self.available = bool(
                available
            )

    # =============================================================
    # ENGINEERING VALUE
    # =============================================================

    @property
    def engineering_value(
        self,
    ) -> float | complex:
        """
        Return the channel engineering value.

        The channel stores engineering-domain values.

        The source instrument's physical transformation is not
        recalculated here.
        """

        return (
            self.value
            * self.scale
            * self.polarity
        )

    # =============================================================
    # VALIDITY
    # =============================================================

    @property
    def is_valid(self) -> bool:
        """
        Return whether the signal is presently suitable for
        normal engineering consumption.
        """

        return (
            self.available
            and self.quality
            == MeasurementQuality.GOOD
        )

    # =============================================================

    @property
    def is_usable(self) -> bool:
        """
        Alias for the protection/consumer-facing validity check.

        A consumer should normally use this property rather than
        inspecting quality and availability independently.
        """

        return self.is_valid

    # =============================================================
    # SOURCE INFORMATION
    # =============================================================

    @property
    def source_id(self) -> str | None:
        """
        Return the source equipment identifier.
        """

        if self.source is None:
            return None

        return self.source.id

    # -------------------------------------------------------------

    @property
    def source_terminal_id(self) -> str | None:
        """
        Return the source measurement-terminal identifier.
        """

        if self.source_terminal is None:
            return None

        return self.source_terminal.id

    # =============================================================
    # SIGNAL INFORMATION
    # =============================================================

    @property
    def signal_name(self) -> str:
        """
        Return a canonical signal classification name.
        """

        return self.signal_type.value

    # =============================================================
    # SERVICE / AVAILABILITY
    # =============================================================

    def set_available(
        self,
        available: bool,
    ) -> None:
        """
        Set channel availability.

        Availability is a signal-domain state and does not modify
        the physical source equipment.
        """

        self.available = bool(
            available
        )

    # -------------------------------------------------------------

    def set_quality(
        self,
        quality: MeasurementQuality,
    ) -> None:
        """
        Set signal quality.
        """

        if not isinstance(
            quality,
            MeasurementQuality,
        ):
            raise TypeError(
                "quality must be a MeasurementQuality."
            )

        self.quality = quality

    # =============================================================
    # RESET
    # =============================================================

    def reset(
        self,
        value: float | complex = 0.0,
        *,
        quality: MeasurementQuality = (
            MeasurementQuality.UNKNOWN
        ),
        available: bool = True,
        timestamp: Optional[float] = None,
    ) -> None:
        """
        Reset channel signal state.

        Source association and engineering configuration remain
        unchanged.
        """

        self.value = self._validate_value(
            value
        )

        if not isinstance(
            quality,
            MeasurementQuality,
        ):
            raise TypeError(
                "quality must be a MeasurementQuality."
            )

        self.quality = quality
        self.available = bool(
            available
        )
        self.timestamp = timestamp

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured channel information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "signal_type": self.signal_type.value,
            "phase": self.phase.value,
            "unit": self.unit,
            "nominal_value": self.nominal_value,
            "scale": self.scale,
            "polarity": self.polarity,
            "value": self.value,
            "engineering_value": self.engineering_value,
            "available": self.available,
            "quality": self.quality.value,
            "usable": self.is_usable,
            "timestamp": self.timestamp,
            "source": self.source_id,
            "source_terminal": self.source_terminal_id,
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<MeasurementChannel "
            f"id={self.id}, "
            f"type={self.signal_type.value}, "
            f"phase={self.phase.value}, "
            f"value={self.value!r}, "
            f"quality={self.quality.value}, "
            f"available={self.available}>"
        )


__all__ = [
    "MeasurementSignalType",
    "MeasurementPhase",
    "MeasurementQuality",
    "MeasurementChannel",
]
