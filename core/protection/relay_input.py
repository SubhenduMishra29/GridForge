```python
"""
GridForge V2 Relay Input
========================

File:
    core/protection/relay_input.py

Purpose
-------
Defines the canonical GridForge V2 RelayInput abstraction.

RelayInput is the logical interface between the protection
measurement architecture and protection functions.

Architectural position
-----------------------

    CT / PT / CVT
          |
          v
    MeasurementChannel
          |
          v
       RelayInput
          |
          +-------------------------------+
          |               |               |
          v               v               v
      50/51/67         21/27/59          87
    Overcurrent         Voltage       Differential

RelayInput is NOT a physical measurement device.

It is a logical consumer-facing binding to an existing
MeasurementChannel.

Design principles
-----------------
1. MeasurementChannel owns the measurement signal.
2. RelayInput references the channel; it does not duplicate it.
3. Multiple protection functions may consume the same input.
4. One multifunction relay may contain many RelayInputs.
5. Protection functions must consume signals through this
   abstraction rather than directly accessing CT/PT/CVT objects.
6. Invalid or unavailable measurements must be detectable before
   protection algorithms consume them.

Responsibilities
----------------
RelayInput provides:

- input identity;
- logical name;
- functional role;
- MeasurementChannel association;
- expected signal type;
- expected phase;
- enable/disable state;
- signal access;
- quality access;
- availability access;
- validity checking;
- diagnostic status.

RelayInput does NOT:

- create MeasurementChannel objects;
- create CT/PT/CVT objects;
- simulate instruments;
- calculate protection quantities;
- perform relay logic;
- coordinate relays;
- operate breakers;
- modify network topology;
- own global protection state.

Multifunction relay support
---------------------------

A single relay may contain:

    Ia
    Ib
    Ic
    In
    Va
    Vb
    Vc
    Vn
    V1
    I1
    I2
    I0
    V0

These logical inputs may then be shared by multiple protection
functions.

Example:

    Ia/Ib/Ic
        |
        +----> 50/51
        |
        +----> 67
        |
        +----> 87
        |
        +----> fault recording

Likewise:

    Va/Vb/Vc + Ia/Ib/Ic
        |
        +----> 21 Distance
        |
        +----> 67 Directional
        |
        +----> 27/59 Voltage
        |
        +----> 81 Frequency

No protection function should create another copy of the
measurement.

Future architecture
--------------------
This contract is intentionally suitable for future support of:

- instantaneous signals;
- RMS signals;
- phasors;
- sequence components;
- frequency;
- power;
- impedance;
- digital/binary signals;
- sampled values;
- simulation-time measurements;
- event timestamps;
- signal-quality states;
- redundant measurement channels;
- measurement selection logic.

The RelayInput itself remains a logical binding and should not
become a measurement-processing engine.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from typing import Any, Optional

from .measurement_channel import (
    MeasurementChannel,
    MeasurementPhase,
    MeasurementQuality,
    MeasurementSignalType,
)


# =====================================================================
# RELAY INPUT
# =====================================================================


class RelayInput:
    """
    Canonical GridForge V2 logical protection input.

    Parameters
    ----------
    id:
        Unique RelayInput identifier.

    channel:
        Existing MeasurementChannel consumed by this input.

    name:
        Human-readable input name.

    role:
        Functional role of the input.

        Examples:

            PHASE_A_CURRENT
            PHASE_B_CURRENT
            PHASE_C_CURRENT
            RESIDUAL_CURRENT
            PHASE_A_VOLTAGE
            POSITIVE_SEQUENCE_CURRENT
            POSITIVE_SEQUENCE_VOLTAGE
            ZERO_SEQUENCE_CURRENT
            ZERO_SEQUENCE_VOLTAGE

    expected_signal_type:
        Optional expected signal classification.

    expected_phase:
        Optional expected phase/sequence classification.

    enabled:
        Whether this logical input is enabled.

    Notes
    -----
    RelayInput stores only a reference to the authoritative
    MeasurementChannel.

    It does not maintain a second measurement value.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        id: str,
        channel: MeasurementChannel,
        *,
        name: str = "",
        role: str = "",
        expected_signal_type: Optional[
            MeasurementSignalType
        ] = None,
        expected_phase: Optional[
            MeasurementPhase
        ] = None,
        enabled: bool = True,
    ) -> None:

        self._validate_id(id)

        if not isinstance(
            channel,
            MeasurementChannel,
        ):
            raise TypeError(
                "channel must be a MeasurementChannel."
            )

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "name must be a string."
            )

        if not isinstance(
            role,
            str,
        ):
            raise TypeError(
                "role must be a string."
            )

        if (
            expected_signal_type is not None
            and not isinstance(
                expected_signal_type,
                MeasurementSignalType,
            )
        ):
            raise TypeError(
                "expected_signal_type must be a "
                "MeasurementSignalType or None."
            )

        if (
            expected_phase is not None
            and not isinstance(
                expected_phase,
                MeasurementPhase,
            )
        ):
            raise TypeError(
                "expected_phase must be a "
                "MeasurementPhase or None."
            )

        self.id = id
        self.name = name
        self.role = role

        # -------------------------------------------------------------
        # Authoritative measurement reference
        # -------------------------------------------------------------

        self.channel = channel

        self.expected_signal_type = (
            expected_signal_type
        )

        self.expected_phase = (
            expected_phase
        )

        self.enabled = bool(
            enabled
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    @staticmethod
    def _validate_id(
        value: str,
    ) -> None:
        """
        Validate RelayInput identity.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "RelayInput id must be a string."
            )

        if not value.strip():
            raise ValueError(
                "RelayInput id cannot be empty."
            )

    # =================================================================
    # CHANNEL
    # =================================================================

    @property
    def measurement_channel(
        self,
    ) -> MeasurementChannel:
        """
        Return the authoritative MeasurementChannel.
        """

        return self.channel

    # -----------------------------------------------------------------

    @property
    def channel_id(
        self,
    ) -> str:
        """
        Return the associated measurement-channel ID.
        """

        return self.channel.id

    # =================================================================
    # SIGNAL CLASSIFICATION
    # =================================================================

    @property
    def signal_type(
        self,
    ) -> MeasurementSignalType:
        """
        Return the actual signal type supplied by the channel.
        """

        return self.channel.signal_type

    # -----------------------------------------------------------------

    @property
    def phase(
        self,
    ) -> MeasurementPhase:
        """
        Return the actual phase or sequence designation.
        """

        return self.channel.phase

    # -----------------------------------------------------------------

    @property
    def unit(
        self,
    ) -> str:
        """
        Return the engineering unit.
        """

        return self.channel.unit

    # =================================================================
    # SIGNAL VALUE
    # =================================================================

    @property
    def value(
        self,
    ) -> float | complex:
        """
        Return the channel's stored value.

        This is a direct view of MeasurementChannel state.
        """

        return self.channel.value

    # -----------------------------------------------------------------

    @property
    def engineering_value(
        self,
    ) -> float | complex:
        """
        Return the engineering-domain channel value.

        Scaling and polarity are resolved by MeasurementChannel.
        """

        return self.channel.engineering_value

    # -----------------------------------------------------------------

    def read(
        self,
        *,
        require_valid: bool = True,
    ) -> float | complex:
        """
        Read the current engineering signal.

        Parameters
        ----------
        require_valid:
            If True, the input must be enabled and the associated
            channel must be available with GOOD quality.

        Returns
        -------
        float | complex
            Current engineering value.
        """

        if require_valid:
            self.require_valid()
        else:
            self.validate_contract()

        return self.engineering_value

    # =================================================================
    # QUALITY / AVAILABILITY
    # =================================================================

    @property
    def available(
        self,
    ) -> bool:
        """
        Return channel availability.
        """

        return bool(
            self.channel.available
        )

    # -----------------------------------------------------------------

    @property
    def quality(
        self,
    ) -> MeasurementQuality:
        """
        Return channel signal quality.
        """

        return self.channel.quality

    # -----------------------------------------------------------------

    @property
    def is_valid(
        self,
    ) -> bool:
        """
        Return whether this input currently provides a valid signal.
        """

        return (
            self.enabled
            and self.channel.available
            and self.channel.quality
            == MeasurementQuality.GOOD
        )

    # -----------------------------------------------------------------

    @property
    def is_usable(
        self,
    ) -> bool:
        """
        Protection-consumer-facing validity alias.
        """

        return self.is_valid

    # =================================================================
    # TIME
    # =================================================================

    @property
    def timestamp(
        self,
    ) -> Optional[float]:
        """
        Return the source measurement timestamp.
        """

        return self.channel.timestamp

    # =================================================================
    # SOURCE
    # =================================================================

    @property
    def source(
        self,
    ) -> Any:
        """
        Return the associated physical measurement source.
        """

        return self.channel.source

    # -----------------------------------------------------------------

    @property
    def source_id(
        self,
    ) -> Optional[str]:
        """
        Return source equipment ID.
        """

        return self.channel.source_id

    # -----------------------------------------------------------------

    @property
    def source_terminal(
        self,
    ) -> Any:
        """
        Return the associated source terminal.
        """

        return self.channel.source_terminal

    # -----------------------------------------------------------------

    @property
    def source_terminal_id(
        self,
    ) -> Optional[str]:
        """
        Return source-terminal ID.
        """

        return self.channel.source_terminal_id

    # =================================================================
    # CONTRACT VALIDATION
    # =================================================================

    def validate_contract(
        self,
    ) -> None:
        """
        Validate the configured RelayInput contract.

        This checks configuration compatibility only.

        It does not require the signal to currently be available.
        """

        if (
            self.expected_signal_type is not None
            and self.signal_type
            != self.expected_signal_type
        ):
            raise ValueError(
                f"RelayInput '{self.id}' expects signal type "
                f"'{self.expected_signal_type.value}', but channel "
                f"'{self.channel_id}' provides "
                f"'{self.signal_type.value}'."
            )

        if (
            self.expected_phase is not None
            and self.phase
            != self.expected_phase
        ):
            raise ValueError(
                f"RelayInput '{self.id}' expects phase "
                f"'{self.expected_phase.value}', but channel "
                f"'{self.channel_id}' provides "
                f"'{self.phase.value}'."
            )

    # -----------------------------------------------------------------

    def require_valid(
        self,
    ) -> None:
        """
        Require this input to be usable by a protection function.
        """

        self.validate_contract()

        if not self.enabled:
            raise RuntimeError(
                f"RelayInput '{self.id}' is disabled."
            )

        if not self.channel.available:
            raise RuntimeError(
                f"MeasurementChannel '{self.channel_id}' "
                "is unavailable."
            )

        if (
            self.channel.quality
            != MeasurementQuality.GOOD
        ):
            raise RuntimeError(
                f"MeasurementChannel '{self.channel_id}' "
                f"has quality "
                f"'{self.channel.quality.value}'."
            )

    # =================================================================
    # CONFIGURATION
    # =================================================================

    def set_enabled(
        self,
        enabled: bool,
    ) -> None:
        """
        Enable or disable this logical input.

        The associated MeasurementChannel is not modified.
        """

        self.enabled = bool(
            enabled
        )

    # -----------------------------------------------------------------

    def set_channel(
        self,
        channel: MeasurementChannel,
    ) -> None:
        """
        Replace the associated MeasurementChannel.

        The replacement must satisfy the configured contract.
        """

        if not isinstance(
            channel,
            MeasurementChannel,
        ):
            raise TypeError(
                "channel must be a MeasurementChannel."
            )

        old_channel = self.channel

        self.channel = channel

        try:
            self.validate_contract()
        except Exception:
            self.channel = old_channel
            raise

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def status(
        self,
    ) -> dict[str, Any]:
        """
        Return structured RelayInput diagnostic information.

        Measurement state is obtained from the authoritative
        MeasurementChannel at call time.
        """

        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "enabled": self.enabled,

            "channel_id": self.channel_id,

            "signal_type": (
                self.signal_type.value
            ),

            "phase": (
                self.phase.value
            ),

            "expected_signal_type": (
                self.expected_signal_type.value
                if self.expected_signal_type is not None
                else None
            ),

            "expected_phase": (
                self.expected_phase.value
                if self.expected_phase is not None
                else None
            ),

            "unit": self.unit,

            "value": self.value,

            "engineering_value": (
                self.engineering_value
            ),

            "available": self.available,

            "quality": (
                self.quality.value
            ),

            "usable": self.is_usable,

            "timestamp": self.timestamp,

            "source": self.source_id,

            "source_terminal": (
                self.source_terminal_id
            ),
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return concise developer-facing representation.
        """

        return (
            f"<RelayInput "
            f"id={self.id}, "
            f"role={self.role!r}, "
            f"channel={self.channel_id}, "
            f"type={self.signal_type.value}, "
            f"phase={self.phase.value}, "
            f"enabled={self.enabled}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "RelayInput",
]
```
