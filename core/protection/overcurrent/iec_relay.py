# Final `core/protection/overcurrent/iec_relay.py`

"""
GridForge IEC Overcurrent Protection Function
==============================================

File:
    core/protection/overcurrent/iec_relay.py

Purpose
-------
Implements an IEC 60255 inverse-time overcurrent protection
function for GridForge V2.

Architectural Position
-----------------------

    CurrentTransformer
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

Important V2 Principle
----------------------
This class represents ONE protection function / element.

It is not a second physical relay model.

A physical GridForge Relay may contain multiple protection
functions, for example:

    50       Instantaneous phase overcurrent
    51       IEC inverse-time overcurrent
    50N/50G  Instantaneous earth fault
    51N/51G  Earth-fault inverse time
    67       Directional overcurrent

This implementation therefore owns only the algorithm-specific
configuration and transient execution state associated with the
IEC 51 function.

Responsibilities
----------------
This module is responsible for:

    - consuming a configured current RelayInput;
    - validating the measurement signal;
    - evaluating pickup;
    - evaluating the IEC inverse-time characteristic;
    - maintaining algorithm-specific timing state;
    - producing ProtectionDecision objects;
    - exposing protection-function diagnostic state.

It does NOT:

    - create CTs;
    - create MeasurementChannels;
    - calculate fault current;
    - access Network topology;
    - perform load flow;
    - perform short-circuit calculations;
    - coordinate multiple relays;
    - operate breakers;
    - schedule simulation events;
    - modify the authoritative Relay model;
    - own a simulation clock.

Timing Boundary
---------------
IEC inverse-time mathematics is provided by:

    core.protection.relay_functions

Simulation/evaluation time is supplied by the caller through
ProtectionContext.

The protection function records pickup timing state and determines
whether the IEC operating criterion has been reached.

It does not own a global clock or schedule simulation events.

The resulting ProtectionDecision is consumed by the higher-level
protection/event/output architecture.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Optional

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
# ELEMENT SETTINGS
# =====================================================================


@dataclass(frozen=True)
class IECOvercurrentSettings:
    """
    Immutable settings for one IEC inverse-time overcurrent element.

    Parameters
    ----------
    pickup:
        Pickup current in the engineering convention of the assigned
        measurement channel.

    curve:
        IEC inverse-time characteristic.

    TMS:
        Time Multiplier Setting.

    Notes
    -----
    This object contains function-specific algorithm settings.

    It does not replace or duplicate the authoritative Relay model.
    """

    pickup: float
    curve: str = DEFAULT_CURVE
    TMS: float = DEFAULT_TMS

    def __post_init__(self) -> None:
        pickup = float(self.pickup)

        if not math.isfinite(pickup) or pickup <= 0.0:
            raise ValueError(
                "pickup must be finite and positive."
            )

        curve = normalize_iec_curve(self.curve)

        TMS = float(self.TMS)

        if not math.isfinite(TMS) or TMS < 0.0:
            raise ValueError(
                "TMS must be finite and >= 0."
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
    GridForge V2 IEC inverse-time overcurrent protection function.

    This implementation represents an IEC 51 protection element,
    not a physical Relay.

    Parameters
    ----------
    relay:
        Authoritative GridForge Relay model.

    relay_inputs:
        Mapping containing the assigned current RelayInput.

    settings:
        IEC overcurrent element settings.

    element_id:
        Stable identity of this protection-function instance.

        This must be distinct from the physical relay identity because
        one physical relay may host multiple protection functions.

    Notes
    -----
    The protection function reads current exclusively through its
    assigned RelayInput.

    It does not read:

        relay.current

    and does not calculate electrical current itself.
    """

    CURRENT_INPUT = CURRENT_INPUT
    FUNCTION_CODE = FUNCTION_CODE
    FUNCTION_NAME = FUNCTION_NAME

    # ================================================================
    # INITIALIZATION
    # ================================================================

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

        self.settings = settings

        # --------------------------------------------------------------
        # Algorithm-specific transient state.
        #
        # This is local execution state only.
        # It does not duplicate Relay or MeasurementChannel state.
        # --------------------------------------------------------------

        self._pickup_start_time: float | None = None
        self._last_timestamp: float | None = None
        self._last_current: float | None = None
        self._last_operating_time: float | None = None
        self._last_decision: ProtectionDecision | None = None

        self.require_inputs(
            self.CURRENT_INPUT
        )

    # ================================================================
    # SETTINGS
    # ================================================================

    @property
    def pickup(self) -> float:
        """Return configured element pickup current."""

        return self.settings.pickup

    @property
    def curve(self) -> str:
        """Return canonical IEC curve identifier."""

        return self.settings.curve

    @property
    def TMS(self) -> float:
        """Return configured Time Multiplier Setting."""

        return self.settings.TMS

    # ================================================================
    # MEASUREMENT
    # ================================================================

    def current_signal(self) -> Any:
        """
        Obtain the current signal from the configured RelayInput.

        The RelayInput remains authoritative for the measurement.
        """

        relay_input = self.get_input(
            self.CURRENT_INPUT
        )

        # RelayInput is the measurement boundary. The preferred API is
        # a signal/value accessor exposed by RelayInput.
        #
        # Supporting both common access forms keeps this function
        # independent of the concrete measurement implementation while
        # preserving RelayInput ownership of the signal.
        if hasattr(relay_input, "value"):
            value = getattr(
                relay_input,
                "value",
            )

            if callable(value):
                return value()

            return value

        if hasattr(relay_input, "signal"):
            signal = getattr(
                relay_input,
                "signal",
            )

            if callable(signal):
                return signal()

            return signal

        if hasattr(relay_input, "read"):
            return relay_input.read()

        raise AttributeError(
            "RelayInput does not expose a supported measurement "
            "accessor. Expected 'value', 'signal', or 'read'."
        )

    # ----------------------------------------------------------------

    def current_value(self) -> float:
        """
        Return a validated scalar current magnitude.

        Complex current values are accepted because protection
        measurement chains may expose phasors.

        The IEC magnitude characteristic uses abs(I).
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

    # ================================================================
    # PICKUP
    # ================================================================

    def check_pickup(self) -> bool:
        """
        Evaluate the IEC overcurrent pickup criterion.

        Returns
        -------
        bool
            True when measured current is strictly above pickup.
        """

        return iec_pickup(
            current=self.current_value(),
            pickup=self.pickup,
        )

    # ================================================================
    # CURRENT MULTIPLE
    # ================================================================

    def current_multiple(
        self,
        current: float | None = None,
    ) -> float:
        """
        Return current multiple M.

        Parameters
        ----------
        current:
            Optional already-sampled current magnitude.

            When omitted, the current is read from RelayInput.
        """

        if current is None:
            current = self.current_value()

        return current_multiplier(
            current=current,
            pickup=self.pickup,
        )

    # ================================================================
    # OPERATING TIME
    # ================================================================

    def operating_time(
        self,
        current: float | None = None,
    ) -> float:
        """
        Calculate the IEC characteristic operating time.

        Returns
        -------
        float
            Operating time in seconds.

            math.inf is returned when the element is not picked up.

        Notes
        -----
        This method evaluates the mathematical characteristic only.

        It does not operate the protection function or request a trip.
        """

        if current is None:
            current = self.current_value()

        return iec_time(
            current=current,
            pickup=self.pickup,
            curve=self.curve,
            TMS=self.TMS,
        )

    # ================================================================
    # EVALUATION
    # ================================================================

    def evaluate(
        self,
        context: ProtectionContext | None = None,
    ) -> ProtectionDecision:
        """
        Evaluate one IEC overcurrent protection cycle.

        Parameters
        ----------
        context:
            Protection execution context.

            When supplied, ``context.time`` is the authoritative
            evaluation timestamp.

        Returns
        -------
        ProtectionDecision
            Canonical immutable result of this protection-function
            evaluation.

        Behaviour
        ---------
        The method:

            1. validates execution state;
            2. obtains the evaluation timestamp;
            3. reads current through RelayInput;
            4. evaluates pickup;
            5. calculates IEC operating time;
            6. maintains pickup timing state;
            7. determines whether the operating criterion is due;
            8. returns a ProtectionDecision.

        Important
        ---------
        This method does NOT:

            - operate a breaker;
            - call breaker.open();
            - call breaker.trip();
            - schedule an event;
            - modify the authoritative Relay model.

        A trip request is represented only in the returned
        ProtectionDecision.

        The higher-level protection/event/output layer owns event
        scheduling and physical breaker operation.
        """

        timestamp = self._context_time(
            context
        )

        self._validate_timestamp_order(
            timestamp
        )

        self._last_timestamp = timestamp

        # --------------------------------------------------------------
        # Disabled / blocked / non-operational state
        # --------------------------------------------------------------

        if not self.operational:
            self._clear_pickup_timing()

            decision = ProtectionDecision.no_operation(
                relay_id=self.relay_id,
                function_code=self.FUNCTION_CODE,
                function_id=self.element_id,
                reason=self._inactive_reason(),
                timestamp=timestamp,
                operating_time=None,
            )

            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # Measurement acquisition
        # --------------------------------------------------------------

        try:
            current = self.current_value()
        except (TypeError, ValueError, AttributeError) as exc:

            self._clear_pickup_timing()

            decision = ProtectionDecision.invalid(
                relay_id=self.relay_id,
                function_code=self.FUNCTION_CODE,
                function_id=self.element_id,
                reason=(
                    "Invalid current measurement: "
                    f"{exc}"
                ),
                timestamp=timestamp,
                metadata={
                    "input": self.CURRENT_INPUT,
                },
            )

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

            decision = ProtectionDecision.no_operation(
                relay_id=self.relay_id,
                function_code=self.FUNCTION_CODE,
                function_id=self.element_id,
                reason="Current below IEC overcurrent pickup.",
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

            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # Start / continue pickup interval
        # --------------------------------------------------------------

        if self._pickup_start_time is None:
            self._pickup_start_time = timestamp

        operating_time = self.operating_time(
            current
        )

        self._last_operating_time = operating_time

        # --------------------------------------------------------------
        # Determine whether operation is due
        # --------------------------------------------------------------

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
        }

        # --------------------------------------------------------------
        # Pickup but not yet operated
        # --------------------------------------------------------------

        if not operation_due:

            decision = ProtectionDecision(
                relay_id=self.relay_id,
                function_code=self.FUNCTION_CODE,
                function_id=self.element_id,
                pickup=True,
                operate=False,
                trip_request=False,
                blocked=False,
                valid=True,
                operating_time=operating_time,
                timestamp=timestamp,
                reason=(
                    "IEC overcurrent pickup active; "
                    "operating time not yet reached."
                ),
                metadata=metadata,
            )

            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # Operation criterion reached
        # --------------------------------------------------------------

        decision = ProtectionDecision.trip(
            relay_id=self.relay_id,
            function_code=self.FUNCTION_CODE,
            function_id=self.element_id,
            reason=(
                "IEC overcurrent operating time reached."
            ),
            timestamp=timestamp,
            operating_time=operating_time,
            metadata=metadata,
        )

        self._last_decision = decision

        return decision

    # ================================================================
    # TIMESTAMP
    # ================================================================

    @staticmethod
    def _context_time(
        context: ProtectionContext | None,
    ) -> float | None:
        """
        Extract the caller-supplied evaluation time.

        ProtectionContext does not own a clock. Its ``time`` value is
        supplied by the execution environment.
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

    # ----------------------------------------------------------------

    def _validate_timestamp_order(
        self,
        timestamp: float | None,
    ) -> None:
        """
        Validate monotonic evaluation time.

        A timestamp-less evaluation is permitted for compatibility
        with instantaneous/static evaluation.

        Once a stateful timed sequence has started, supplied timestamps
        must not move backwards.
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

    # ----------------------------------------------------------------

    @staticmethod
    def _validate_timestamp(
        timestamp: float,
    ) -> float:
        """
        Validate an evaluation timestamp.
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

    # ================================================================
    # STATE
    # ================================================================

    def _clear_pickup_timing(self) -> None:
        """
        Clear the transient pickup timing interval.

        This does not modify the authoritative Relay state.
        """

        self._pickup_start_time = None

    # ----------------------------------------------------------------

    def _inactive_reason(self) -> str:
        """
        Return a diagnostic explanation for inactive evaluation.
        """

        if not self.enabled:
            return "IEC overcurrent function is disabled."

        if self.blocked:
            return "IEC overcurrent function is statically blocked."

        if not bool(
            getattr(
                self.relay,
                "operational",
                True,
            )
        ):
            return "Authoritative relay is not operational."

        return "IEC overcurrent function is not operational."

    # ================================================================
    # RESET
    # ================================================================

    def reset(self) -> None:
        """
        Reset transient IEC protection-function state.

        This method does not modify:

            - the physical Relay;
            - RelayInput;
            - MeasurementChannel;
            - breaker state;
            - network topology;
            - protection-system state.
        """

        super().reset()

        self._pickup_start_time = None
        self._last_timestamp = None
        self._last_current = None
        self._last_operating_time = None
        self._last_decision = None

    # ================================================================
    # TIMING STATE
    # ================================================================

    @property
    def pickup_start_time(self) -> float | None:
        """
        Return the timestamp at which pickup was first observed during
        the current pickup interval.
        """

        return self._pickup_start_time

    @property
    def last_timestamp(self) -> float | None:
        """
        Return the last supplied evaluation timestamp.
        """

        return self._last_timestamp

    @property
    def last_current(self) -> float | None:
        """
        Return the last sampled current magnitude.

        This is diagnostic state only.
        """

        return self._last_current

    @property
    def last_operating_time(self) -> float | None:
        """
        Return the most recently calculated IEC operating time.

        None means that the latest evaluation did not determine an
        operating time.
        """

        return self._last_operating_time

    @property
    def last_decision(self) -> ProtectionDecision | None:
        """
        Return the most recently produced ProtectionDecision.
        """

        return self._last_decision

    # ================================================================
    # STATUS
    # ================================================================

    def status(self) -> dict[str, Any]:
        """
        Return protection-function diagnostic status.

        The status is diagnostic information only. It is not the
        authoritative persistence representation.
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
                "last_decision": (
                    self._last_decision.to_dict()
                    if self._last_decision is not None
                    else None
                ),
            }
        )

        return result


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "IECOvercurrentSettings",
    "IECOvercurrentRelay",
]
```
