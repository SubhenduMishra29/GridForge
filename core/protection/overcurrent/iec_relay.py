"""
GridForge V2 IEC Overcurrent Protection Function
================================================

File
----
core/protection/overcurrent/iec_relay.py

Purpose
-------
Implements an IEC 60255 inverse-time overcurrent protection function
for GridForge V2.

This class represents ONE protection function / element (IEC 51)
hosted by an authoritative physical Relay.

Architectural Position
----------------------

    CT / PT / CVT
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
    IECOvercurrentRelay
          |
          v
    ProtectionDecision
          |
          v
    ProtectionSystem
          |
          v
    Protection Output Layer
          |
          v
      BreakerManager

Architectural Rules
-------------------
This class:

    * owns IEC 51 function configuration;
    * references RelayInput;
    * owns transient IEC timing state;
    * evaluates the protection characteristic;
    * produces ProtectionDecision.

This class does NOT:

    * represent the physical Relay;
    * own CT/PT/MeasurementChannel state;
    * calculate electrical quantities;
    * access network topology;
    * execute power-system solvers;
    * operate breakers;
    * schedule simulation events;
    * modify network topology;
    * coordinate other protection functions;
    * own a simulation clock;
    * perform persistence or file I/O.

Timing Boundary
---------------
IEC inverse-time mathematics is provided by:

    core.protection.relay_functions

Evaluation time is supplied by:

    ProtectionContext.time

The protection function does not own a clock.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from core.protection.context import ProtectionContext
from core.protection.decision import ProtectionDecision
from core.protection.relay_base import RelayBase
from core.protection.relay_functions import (
    current_multiplier,
    iec_pickup,
    iec_time,
    normalize_iec_curve,
)


# =====================================================================
# DEFAULTS
# =====================================================================

DEFAULT_CURVE = "SI"
DEFAULT_TMS = 1.0

FUNCTION_CODE = "51"
FUNCTION_NAME = "IEC INVERSE-TIME OVERCURRENT"

CURRENT_INPUT = "current"


# =====================================================================
# SETTINGS
# =====================================================================


@dataclass(frozen=True, slots=True)
class IECOvercurrentSettings:
    """
    Immutable configuration for one IEC 51 overcurrent function.

    Parameters
    ----------
    pickup:
        Pickup current in the engineering convention of the assigned
        RelayInput / MeasurementChannel.

    curve:
        IEC inverse-time characteristic.

    TMS:
        IEC Time Multiplier Setting.

    Notes
    -----
    These settings belong exclusively to this protection function.
    They do not replace or duplicate physical Relay configuration.
    """

    pickup: float
    curve: str = DEFAULT_CURVE
    TMS: float = DEFAULT_TMS

    def __post_init__(self) -> None:
        try:
            pickup = float(self.pickup)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "pickup must be numeric."
            ) from exc

        if not math.isfinite(pickup) or pickup <= 0.0:
            raise ValueError(
                "pickup must be finite and positive."
            )

        curve = normalize_iec_curve(
            self.curve
        )

        try:
            TMS = float(self.TMS)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "TMS must be numeric."
            ) from exc

        # relay_functions.iec_time() requires TMS > 0.
        if not math.isfinite(TMS) or TMS <= 0.0:
            raise ValueError(
                "TMS must be finite and positive."
            )

        object.__setattr__(
            self,
            "pickup",
            pickup,
        )

        object.__setattr__(
            self,
            "curve",
            curve,
        )

        object.__setattr__(
            self,
            "TMS",
            TMS,
        )


# =====================================================================
# IEC OVERCURRENT RELAY
# =====================================================================


class IECOvercurrentRelay(RelayBase):
    """
    IEC 51 inverse-time overcurrent protection function.

    This class is a protection-function implementation, not a physical
    relay model.

    A physical Relay may host multiple protection functions, for
    example:

        Relay R1
            |
            +-- 50
            +-- 51
            +-- 46
            +-- 50BF

    The function reads current exclusively through its assigned
    RelayInput.
    """

    CURRENT_INPUT = CURRENT_INPUT
    FUNCTION_CODE = FUNCTION_CODE
    FUNCTION_NAME = FUNCTION_NAME

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        relay: Any,
        *,
        element_id: str,
        relay_inputs: Mapping[str, Any] | None = None,
        settings: IECOvercurrentSettings,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:
        """
        Initialize one IEC 51 protection function.
        """

        if not isinstance(
            settings,
            IECOvercurrentSettings,
        ):
            raise TypeError(
                "settings must be an "
                "IECOvercurrentSettings instance."
            )

        super().__init__(
            relay=relay,
            element_id=element_id,
            function_code=self.FUNCTION_CODE,
            function_name=self.FUNCTION_NAME,
            relay_inputs=relay_inputs,
            settings={
                "pickup": settings.pickup,
                "curve": settings.curve,
                "TMS": settings.TMS,
            },
            enabled=enabled,
            blocked=blocked,
        )

        # Typed immutable configuration.
        #
        # RelayBase.settings remains the canonical read-only mapping
        # exposed by the base class.
        self._iec_settings = settings

        # --------------------------------------------------------------
        # Transient execution state
        # --------------------------------------------------------------

        self._pickup_start_time: float | None = None
        self._last_timestamp: float | None = None
        self._last_current: float | None = None
        self._last_operating_time: float | None = None
        self._last_decision: ProtectionDecision | None = None
        self._operated: bool = False

        self.require_inputs(
            self.CURRENT_INPUT
        )

    # =================================================================
    # SETTINGS
    # =================================================================

    @property
    def iec_settings(
        self,
    ) -> IECOvercurrentSettings:
        """
        Return the immutable typed IEC settings.
        """

        return self._iec_settings

    # -----------------------------------------------------------------

    @property
    def pickup(self) -> float:
        """Return configured pickup current."""

        return self._iec_settings.pickup

    # -----------------------------------------------------------------

    @property
    def curve(self) -> str:
        """Return canonical IEC curve identifier."""

        return self._iec_settings.curve

    # -----------------------------------------------------------------

    @property
    def TMS(self) -> float:
        """Return configured IEC Time Multiplier Setting."""

        return self._iec_settings.TMS

    # =================================================================
    # MEASUREMENT
    # =================================================================

    def current_signal(self) -> Any:
        """
        Read the current signal from the assigned RelayInput.

        RelayInput remains the measurement boundary.

        Supported RelayInput access patterns are:

            value
            signal
            read()
        """

        relay_input = self.get_input(
            self.CURRENT_INPUT
        )

        if hasattr(
            relay_input,
            "value",
        ):
            value = getattr(
                relay_input,
                "value",
            )

            if callable(value):
                return value()

            return value

        if hasattr(
            relay_input,
            "signal",
        ):
            signal = getattr(
                relay_input,
                "signal",
            )

            if callable(signal):
                return signal()

            return signal

        if hasattr(
            relay_input,
            "read",
        ):
            return relay_input.read()

        raise AttributeError(
            "RelayInput does not expose a supported measurement "
            "accessor. Expected 'value', 'signal', or 'read'."
        )

    # -----------------------------------------------------------------

    def current_value(self) -> float:
        """
        Return the validated current magnitude.

        Scalar and complex phasor values are accepted.

        The IEC characteristic operates on:

            |I|
        """

        value = self.current_signal()

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                "Current measurement cannot be bool."
            )

        try:
            value = complex(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Current measurement must be numeric."
            ) from exc

        if not (
            math.isfinite(value.real)
            and math.isfinite(value.imag)
        ):
            raise ValueError(
                "Current measurement must be finite."
            )

        return abs(value)

    # =================================================================
    # PICKUP
    # =================================================================

    def check_pickup(self) -> bool:
        """
        Evaluate the IEC overcurrent pickup criterion.

        Criterion:

            |I| > Pickup
        """

        return iec_pickup(
            current=self.current_value(),
            pickup=self.pickup,
        )

    # =================================================================
    # CURRENT MULTIPLE
    # =================================================================

    def current_multiple(
        self,
        current: float | None = None,
    ) -> float:
        """
        Return current multiple:

            M = |I| / Pickup
        """

        if current is None:
            current = self.current_value()

        return current_multiplier(
            current=current,
            pickup=self.pickup,
        )

    # =================================================================
    # OPERATING TIME
    # =================================================================

    def operating_time(
        self,
        current: float | None = None,
    ) -> float:
        """
        Calculate IEC inverse-time operating time.

        Returns math.inf when the current does not exceed pickup.

        This method evaluates only the numerical characteristic.
        """

        if current is None:
            current = self.current_value()

        return iec_time(
            current=current,
            pickup=self.pickup,
            curve=self.curve,
            TMS=self.TMS,
        )

    # =================================================================
    # EVALUATION
    # =================================================================

    def evaluate(
        self,
        context: ProtectionContext | None = None,
    ) -> ProtectionDecision:
        """
        Evaluate the IEC 51 protection function.

        A timed IEC 51 element requires an authoritative evaluation
        timestamp. Therefore context=None is permitted only while the
        function is not required to maintain a timed pickup interval.

        In normal simulation execution, ProtectionContext.time must be
        supplied by the simulation/protection execution layer.

        The method never operates equipment or schedules events.
        """

        timestamp = self._context_time(
            context
        )

        self._validate_timestamp_order(
            timestamp
        )

        # --------------------------------------------------------------
        # Disabled / blocked / non-operational
        # --------------------------------------------------------------

        if not self.operational:
            self._clear_pickup_timing()

            decision = self.no_operation(
                reason=self._inactive_reason(),
                timestamp=timestamp,
                operating_time=None,
            )

            self._last_timestamp = timestamp
            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # A previously operated element remains operated until reset.
        # --------------------------------------------------------------

        if self._operated:
            decision = self.trip_decision(
                reason=(
                    "IEC overcurrent element remains operated "
                    "until reset."
                ),
                timestamp=timestamp,
                operating_time=self._last_operating_time,
                metadata={
                    "current": self._last_current,
                    "pickup": self.pickup,
                    "curve": self.curve,
                    "TMS": self.TMS,
                    "latched": True,
                },
            )

            self._last_timestamp = timestamp
            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # Measurement acquisition
        # --------------------------------------------------------------

        try:
            current = self.current_value()

        except (
            TypeError,
            ValueError,
            AttributeError,
        ) as exc:

            self._clear_pickup_timing()
            self._last_current = None
            self._last_operating_time = None

            decision = self.invalid_decision(
                reason=(
                    "Invalid current measurement: "
                    f"{exc}"
                ),
                timestamp=timestamp,
                metadata={
                    "input": self.CURRENT_INPUT,
                },
            )

            self._last_timestamp = timestamp
            self._last_decision = decision

            return decision

        self._last_current = current

        # --------------------------------------------------------------
        # Pickup
        # --------------------------------------------------------------

        picked_up = iec_pickup(
            current=current,
            pickup=self.pickup,
        )

        if not picked_up:
            self._clear_pickup_timing()
            self._last_operating_time = None

            decision = self.no_operation(
                reason=(
                    "Current below IEC overcurrent pickup."
                ),
                timestamp=timestamp,
                operating_time=None,
                metadata={
                    "current": current,
                    "pickup": self.pickup,
                    "current_multiple": self.current_multiple(
                        current
                    ),
                    "curve": self.curve,
                    "TMS": self.TMS,
                },
            )

            self._last_timestamp = timestamp
            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # Timed IEC operation requires a simulation/evaluation time.
        # --------------------------------------------------------------

        if timestamp is None:
            self._clear_pickup_timing()
            self._last_operating_time = self.operating_time(
                current
            )

            decision = self.invalid_decision(
                reason=(
                    "IEC inverse-time evaluation requires "
                    "ProtectionContext.time."
                ),
                timestamp=None,
                metadata={
                    "current": current,
                    "pickup": self.pickup,
                    "current_multiple": self.current_multiple(
                        current
                    ),
                    "curve": self.curve,
                    "TMS": self.TMS,
                },
            )

            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # Start / continue pickup timing
        # --------------------------------------------------------------

        if self._pickup_start_time is None:
            self._pickup_start_time = timestamp

        operating_time = self.operating_time(
            current
        )

        self._last_operating_time = operating_time

        elapsed = (
            timestamp
            - self._pickup_start_time
        )

        operation_due = (
            math.isfinite(operating_time)
            and elapsed >= operating_time
        )

        metadata = {
            "current": current,
            "pickup": self.pickup,
            "current_multiple": self.current_multiple(
                current
            ),
            "curve": self.curve,
            "TMS": self.TMS,
            "pickup_start_time": self._pickup_start_time,
            "elapsed_time": elapsed,
            "operation_due": operation_due,
            "latched": False,
        }

        # --------------------------------------------------------------
        # Pickup but operating time not yet reached
        # --------------------------------------------------------------

        if not operation_due:
            decision = self.pickup_decision(
                reason=(
                    "IEC overcurrent pickup active; "
                    "operating time not yet reached."
                ),
                timestamp=timestamp,
                operating_time=operating_time,
                metadata=metadata,
            )

            self._last_timestamp = timestamp
            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # IEC operation reached
        # --------------------------------------------------------------

        self._operated = True

        metadata["latched"] = True

        decision = self.trip_decision(
            reason=(
                "IEC overcurrent operating time reached."
            ),
            timestamp=timestamp,
            operating_time=operating_time,
            metadata=metadata,
        )

        self._last_timestamp = timestamp
        self._last_decision = decision

        return decision

    # =================================================================
    # TIMESTAMP
    # =================================================================

    @staticmethod
    def _context_time(
        context: ProtectionContext | None,
    ) -> float | None:
        """
        Extract the authoritative evaluation timestamp.

        ProtectionContext supplies time; it does not own a clock.
        """

        if context is None:
            return None

        try:
            timestamp = context.time
        except AttributeError as exc:
            raise TypeError(
                "context must provide a 'time' attribute."
            ) from exc

        return IECOvercurrentRelay._validate_timestamp(
            timestamp
        )

    # -----------------------------------------------------------------

    def _validate_timestamp_order(
        self,
        timestamp: float | None,
    ) -> None:
        """
        Reject backwards evaluation time.

        Timestamp-less evaluation is permitted only for static
        non-timed evaluation paths.
        """

        if timestamp is None:
            return

        previous = self._last_timestamp

        if (
            previous is not None
            and timestamp < previous
        ):
            raise ValueError(
                "Protection evaluation timestamp cannot move "
                "backwards."
            )

    # -----------------------------------------------------------------

    @staticmethod
    def _validate_timestamp(
        timestamp: float,
    ) -> float:
        """
        Validate one evaluation timestamp.
        """

        try:
            timestamp = float(timestamp)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "timestamp must be numeric."
            ) from exc

        if not math.isfinite(timestamp):
            raise ValueError(
                "timestamp must be finite."
            )

        return timestamp

    # =================================================================
    # STATE
    # =================================================================

    def _clear_pickup_timing(self) -> None:
        """
        Clear the current pickup interval.
        """

        self._pickup_start_time = None

    # -----------------------------------------------------------------

    def _inactive_reason(self) -> str:
        """
        Return the reason why the function is not operational.
        """

        if not self.enabled:
            return (
                "IEC overcurrent function is disabled."
            )

        if self.blocked:
            return (
                "IEC overcurrent function is statically blocked."
            )

        if not bool(
            getattr(
                self.relay,
                "operational",
                True,
            )
        ):
            return (
                "Authoritative relay is not operational."
            )

        return (
            "IEC overcurrent function is not operational."
        )

    # =================================================================
    # RESET
    # =================================================================

    def reset(self) -> None:
        """
        Reset all transient IEC 51 execution state.

        Does not modify:

            * physical Relay;
            * RelayInput;
            * MeasurementChannel;
            * breaker;
            * network;
            * ProtectionSystem.
        """

        super().reset()

        self._pickup_start_time = None
        self._last_timestamp = None
        self._last_current = None
        self._last_operating_time = None
        self._last_decision = None
        self._operated = False

    # =================================================================
    # TIMING STATE
    # =================================================================

    @property
    def pickup_start_time(
        self,
    ) -> float | None:
        """
        Return the beginning of the current pickup interval.
        """

        return self._pickup_start_time

    # -----------------------------------------------------------------

    @property
    def last_timestamp(
        self,
    ) -> float | None:
        """
        Return the last evaluation timestamp.
        """

        return self._last_timestamp

    # -----------------------------------------------------------------

    @property
    def last_current(
        self,
    ) -> float | None:
        """
        Return the last sampled current magnitude.
        """

        return self._last_current

    # -----------------------------------------------------------------

    @property
    def last_operating_time(
        self,
    ) -> float | None:
        """
        Return the most recently calculated operating time.
        """

        return self._last_operating_time

    # -----------------------------------------------------------------

    @property
    def last_decision(
        self,
    ) -> ProtectionDecision | None:
        """
        Return the most recently produced decision.
        """

        return self._last_decision

    # -----------------------------------------------------------------

    @property
    def operated(
        self,
    ) -> bool:
        """
        Return whether the function has reached its operating criterion.

        The operated state is transient execution state and is cleared
        by reset().
        """

        return self._operated

    # =================================================================
    # STATUS
    # =================================================================

    def status(self) -> dict[str, Any]:
        """
        Return diagnostic protection-function status.

        This is not the persistence representation.
        """

        result = super().status()

        current = self._last_current

        result.update(
            {
                "function": "IEC_OVERCURRENT",
                "function_code": self.FUNCTION_CODE,
                "pickup": self.pickup,
                "curve": self.curve,
                "TMS": self.TMS,
                "current": current,
                "current_multiple": (
                    self.current_multiple(current)
                    if current is not None
                    else None
                ),
                "operating_time": (
                    self._last_operating_time
                ),
                "pickup_start_time": (
                    self._pickup_start_time
                ),
                "last_timestamp": (
                    self._last_timestamp
                ),
                "operated": self._operated,
                "last_decision": (
                    self._last_decision.to_dict()
                    if self._last_decision is not None
                    else None
                ),
            }
        )

        return result

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
        """

        return (
            f"<{self.__class__.__name__} "
            f"id={self.element_id!r}, "
            f"relay_id={self.relay_id!r}, "
            f"code={self.FUNCTION_CODE!r}, "
            f"pickup={self.pickup!r}, "
            f"curve={self.curve!r}, "
            f"TMS={self.TMS!r}, "
            f"enabled={self.enabled}, "
            f"blocked={self.blocked}, "
            f"operated={self._operated}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "IECOvercurrentSettings",
    "IECOvercurrentRelay",
]
