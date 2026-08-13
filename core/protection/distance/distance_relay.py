"""
GridForge Distance Protection Function
=======================================

File:
    core/protection/distance/distance_relay.py

Purpose
-------
Implements the baseline transmission-line distance protection
function for GridForge V2.

The baseline characteristic is an impedance-magnitude reach
characteristic:

    |Z_seen| <= |Z_zone|

Advanced distance characteristics are intentionally deferred.

Architectural Position
-----------------------

    PT / CVT + CT
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
    DistanceRelay
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
          |
          v
    Simulation Engine

Important V2 Principle
----------------------
This class represents ONE distance protection function / element.

It is not the physical Relay model.

A physical GridForge Relay may contain multiple protection
functions, for example:

    21       Distance protection
    50/51    Overcurrent
    67       Directional overcurrent
    50BF     Breaker failure

This implementation therefore owns only distance-protection
settings and algorithm-specific transient execution state.

Responsibilities
----------------
This module is responsible for:

    - consuming configured voltage/current RelayInputs;
    - validating measurement signals;
    - calculating apparent impedance;
    - determining the active protection zone;
    - determining pickup;
    - determining intentional operating time;
    - maintaining algorithm-specific timing state;
    - producing ProtectionDecision objects;
    - exposing diagnostic status.

It does NOT:

    - create CTs/PTs/CVTs;
    - create MeasurementChannels;
    - calculate system-wide fault currents;
    - access Network topology;
    - perform load flow;
    - perform short-circuit calculations;
    - coordinate multiple protection elements;
    - operate breakers;
    - modify the authoritative Relay model;
    - schedule simulation events;
    - own a simulation clock.

Baseline Characteristic
-----------------------
The baseline distance characteristic is intentionally simple:

    |Z_seen| <= |Z_zone|

The phase angle of impedance is retained for diagnostics, but the
baseline zone discriminator uses impedance magnitude only.

Zone timing semantics
---------------------
The protection function uses the following deterministic timing rule:

    No zone -> Zone X
        Start a new pickup interval.

    Zone X -> same Zone X
        Continue the existing pickup interval.

    Zone X -> Zone Y
        Restart the pickup interval for Zone Y.

    Zone X -> no zone
        Clear the pickup interval.

This prevents elapsed time accumulated in one zone from being
incorrectly transferred to another zone.

Future Extensions
-----------------
The architecture is intended to support:

    - Mho characteristic;
    - quadrilateral characteristic;
    - reactance characteristic;
    - load encroachment;
    - power swing blocking;
    - out-of-step protection;
    - memory polarization;
    - zero-sequence compensation;
    - phase/ground distance elements.

Timing Boundary
---------------
Zone operating times are protection-function characteristics.

The protection function does not own a simulation clock and does not
schedule events.

When ProtectionContext provides an evaluation timestamp, the function
maintains its pickup interval and determines whether the configured
zone operating time has elapsed.

The resulting ProtectionDecision is interpreted by the higher-level
protection/event/output architecture.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Any, Mapping

from core.protection.context import ProtectionContext
from core.protection.decision import ProtectionDecision
from core.protection.relay_base import RelayBase


# =====================================================================
# CONSTANTS
# =====================================================================

FUNCTION_CODE = "21"
FUNCTION_NAME = "DISTANCE PROTECTION"

VOLTAGE_INPUT = "voltage"
CURRENT_INPUT = "current"

ZERO_CURRENT_EPSILON = 1.0e-12


# =====================================================================
# DISTANCE SETTINGS
# =====================================================================


@dataclass(frozen=True, slots=True)
class DistanceProtectionSettings:
    """
    Immutable settings for one baseline distance-protection element.

    Parameters
    ----------
    zone1_reach:
        Zone-1 impedance reach.

    zone2_reach:
        Zone-2 impedance reach.

    zone3_reach:
        Zone-3 impedance reach.

    zone1_time:
        Zone-1 intentional operating time in seconds.

    zone2_time:
        Zone-2 intentional operating time in seconds.

    zone3_time:
        Zone-3 intentional operating time in seconds.

    Notes
    -----
    Zone reach is represented as a complex impedance because future
    directional/characteristic implementations may require the full
    impedance value.

    The current baseline discriminator uses only:

        abs(zone_reach)
    """

    zone1_reach: complex
    zone2_reach: complex
    zone3_reach: complex

    zone1_time: float = 0.0
    zone2_time: float = 0.3
    zone3_time: float = 1.0

    def __post_init__(self) -> None:
        try:
            zone1 = complex(self.zone1_reach)
            zone2 = complex(self.zone2_reach)
            zone3 = complex(self.zone3_reach)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Distance zone reaches must be valid numeric "
                "impedance values."
            ) from exc

        for name, reach in (
            ("zone1_reach", zone1),
            ("zone2_reach", zone2),
            ("zone3_reach", zone3),
        ):
            if not (
                math.isfinite(reach.real)
                and math.isfinite(reach.imag)
            ):
                raise ValueError(
                    f"{name} must contain finite real and "
                    "imaginary components."
                )

            if abs(reach) <= 0.0:
                raise ValueError(
                    f"{name} must be non-zero."
                )

        if not (
            abs(zone1)
            < abs(zone2)
            < abs(zone3)
        ):
            raise ValueError(
                "Distance zone reaches must satisfy "
                "|Z1| < |Z2| < |Z3|."
            )

        try:
            zone1_time = float(self.zone1_time)
            zone2_time = float(self.zone2_time)
            zone3_time = float(self.zone3_time)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Distance zone operating times must be numeric."
            ) from exc

        for name, operating_time in (
            ("zone1_time", zone1_time),
            ("zone2_time", zone2_time),
            ("zone3_time", zone3_time),
        ):
            if (
                not math.isfinite(operating_time)
                or operating_time < 0.0
            ):
                raise ValueError(
                    f"{name} must be finite and >= 0."
                )

        object.__setattr__(
            self,
            "zone1_reach",
            zone1,
        )

        object.__setattr__(
            self,
            "zone2_reach",
            zone2,
        )

        object.__setattr__(
            self,
            "zone3_reach",
            zone3,
        )

        object.__setattr__(
            self,
            "zone1_time",
            zone1_time,
        )

        object.__setattr__(
            self,
            "zone2_time",
            zone2_time,
        )

        object.__setattr__(
            self,
            "zone3_time",
            zone3_time,
        )

    @property
    def zone_times(self) -> Mapping[str, float]:
        """
        Return configured zone operating times.

        A read-only mapping is returned.
        """

        return MappingProxyType(
            {
                "ZONE1": self.zone1_time,
                "ZONE2": self.zone2_time,
                "ZONE3": self.zone3_time,
            }
        )


# =====================================================================
# DISTANCE PROTECTION FUNCTION
# =====================================================================


class DistanceRelay(RelayBase):
    """
    GridForge V2 baseline distance protection function.

    This class represents an ANSI 21 protection element, not the
    physical Relay device.

    Parameters
    ----------
    relay:
        Authoritative physical Relay model.

    relay_inputs:
        Mapping containing the required voltage and current RelayInput
        objects.

        Required names:

            "voltage"
            "current"

    settings:
        DistanceProtectionSettings instance.

    element_id:
        Stable identity of this protection-function instance.

        This is distinct from the physical relay identity because a
        physical relay may host multiple protection elements.

    enabled:
        Local function enable state.

    blocked:
        Static protection-function block state.
    """

    FUNCTION_CODE = FUNCTION_CODE
    FUNCTION_NAME = FUNCTION_NAME

    VOLTAGE_INPUT = VOLTAGE_INPUT
    CURRENT_INPUT = CURRENT_INPUT

    # ================================================================
    # INITIALIZATION
    # ================================================================

    def __init__(
        self,
        relay: Any,
        *,
        element_id: str,
        relay_inputs: Mapping[str, Any] | None = None,
        settings: DistanceProtectionSettings,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:

        if not isinstance(
            settings,
            DistanceProtectionSettings,
        ):
            raise TypeError(
                "settings must be a "
                "DistanceProtectionSettings instance."
            )

        super().__init__(
            relay=relay,
            element_id=element_id,
            function_code=self.FUNCTION_CODE,
            function_name=self.FUNCTION_NAME,
            relay_inputs=relay_inputs,
            settings={
                "zone1_reach": settings.zone1_reach,
                "zone2_reach": settings.zone2_reach,
                "zone3_reach": settings.zone3_reach,
                "zone1_time": settings.zone1_time,
                "zone2_time": settings.zone2_time,
                "zone3_time": settings.zone3_time,
            },
            enabled=enabled,
            blocked=blocked,
        )

        # Typed algorithm-specific configuration.
        #
        # Do NOT assign self.settings here because RelayBase.settings
        # is a read-only mapping property.
        self._distance_settings = settings

        # --------------------------------------------------------------
        # Algorithm-specific transient state.
        # --------------------------------------------------------------

        self._active_zone: str | None = None
        self._pickup_start_time: float | None = None
        self._last_timestamp: float | None = None

        self._last_voltage: complex | None = None
        self._last_current: complex | None = None
        self._last_impedance: complex | None = None

        self._last_operating_time: float | None = None
        self._last_decision: ProtectionDecision | None = None

        self.require_inputs(
            self.VOLTAGE_INPUT,
            self.CURRENT_INPUT,
        )

    # ================================================================
    # SETTINGS
    # ================================================================

    @property
    def distance_settings(
        self,
    ) -> DistanceProtectionSettings:
        """
        Return the immutable typed distance-protection settings.
        """

        return self._distance_settings

    # ----------------------------------------------------------------

    @property
    def zone1_reach(self) -> complex:
        """Return Zone-1 impedance reach."""

        return self._distance_settings.zone1_reach

    # ----------------------------------------------------------------

    @property
    def zone2_reach(self) -> complex:
        """Return Zone-2 impedance reach."""

        return self._distance_settings.zone2_reach

    # ----------------------------------------------------------------

    @property
    def zone3_reach(self) -> complex:
        """Return Zone-3 impedance reach."""

        return self._distance_settings.zone3_reach

    # ----------------------------------------------------------------

    @property
    def zone_times(self) -> Mapping[str, float]:
        """Return configured zone operating times."""

        return self._distance_settings.zone_times

    # ================================================================
    # MEASUREMENT ACCESS
    # ================================================================

    @staticmethod
    def _read_relay_input(
        relay_input: Any,
    ) -> Any:
        """
        Read a signal from a RelayInput.

        Supported RelayInput access forms, in preferred order:

            value
            signal
            read()

        The RelayInput remains the authoritative measurement boundary.
        """

        if relay_input is None:
            raise ValueError(
                "RelayInput cannot be None."
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

    # ----------------------------------------------------------------

    def voltage_signal(self) -> Any:
        """
        Return the voltage signal from the assigned RelayInput.
        """

        return self._read_relay_input(
            self.get_input(
                self.VOLTAGE_INPUT
            )
        )

    # ----------------------------------------------------------------

    def current_signal(self) -> Any:
        """
        Return the current signal from the assigned RelayInput.
        """

        return self._read_relay_input(
            self.get_input(
                self.CURRENT_INPUT
            )
        )

    # ----------------------------------------------------------------

    @staticmethod
    def _complex_measurement(
        value: Any,
        *,
        name: str,
    ) -> complex:
        """
        Convert and validate a measurement as a finite complex value.
        """

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} measurement cannot be bool."
            )

        try:
            value = complex(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{name} measurement must be numeric."
            ) from exc

        if not (
            math.isfinite(value.real)
            and math.isfinite(value.imag)
        ):
            raise ValueError(
                f"{name} measurement must be finite."
            )

        return value

    # ----------------------------------------------------------------

    def voltage_value(self) -> complex:
        """
        Return the validated voltage measurement.
        """

        return self._complex_measurement(
            self.voltage_signal(),
            name="Voltage",
        )

    # ----------------------------------------------------------------

    def current_value(self) -> complex:
        """
        Return the validated current measurement.
        """

        return self._complex_measurement(
            self.current_signal(),
            name="Current",
        )

    # ================================================================
    # IMPEDANCE
    # ================================================================

    @staticmethod
    def calculate_impedance(
        voltage: complex,
        current: complex,
    ) -> complex:
        """
        Calculate apparent impedance:

            Z = V / I

        Near-zero current is represented as infinite impedance.
        """

        voltage = DistanceRelay._complex_measurement(
            voltage,
            name="Voltage",
        )

        current = DistanceRelay._complex_measurement(
            current,
            name="Current",
        )

        if abs(current) < ZERO_CURRENT_EPSILON:
            return complex(
                float("inf"),
                0.0,
            )

        impedance = voltage / current

        if not (
            math.isfinite(impedance.real)
            and math.isfinite(impedance.imag)
        ):
            return complex(
                float("inf"),
                0.0,
            )

        return impedance

    # ----------------------------------------------------------------

    def apparent_impedance(
        self,
        *,
        voltage: complex | None = None,
        current: complex | None = None,
    ) -> complex:
        """
        Calculate apparent impedance from supplied or current
        RelayInput measurements.
        """

        if voltage is None:
            voltage = self.voltage_value()

        if current is None:
            current = self.current_value()

        return self.calculate_impedance(
            voltage,
            current,
        )

    # ================================================================
    # ZONE DETECTION
    # ================================================================

    def determine_zone(
        self,
        impedance: complex,
    ) -> str | None:
        """
        Determine the active distance-protection zone.

        Baseline characteristic:

            |Z_seen| <= |Z_zone|

        Returns
        -------
        str | None
            "ZONE1", "ZONE2", "ZONE3", or None.
        """

        impedance = self._complex_measurement(
            impedance,
            name="Impedance",
        )

        Z = abs(impedance)

        if Z <= abs(self.zone1_reach):
            return "ZONE1"

        if Z <= abs(self.zone2_reach):
            return "ZONE2"

        if Z <= abs(self.zone3_reach):
            return "ZONE3"

        return None

    # ----------------------------------------------------------------

    def check_zone(
        self,
        impedance: complex | None = None,
    ) -> str | None:
        """
        Determine the active zone from the current measurement.

        The calculated result is stored as local algorithm state.
        """

        if impedance is None:
            impedance = self.apparent_impedance()

        zone = self.determine_zone(
            impedance
        )

        self._active_zone = zone

        return zone

    # ================================================================
    # PICKUP
    # ================================================================

    def check_pickup(
        self,
        impedance: complex | None = None,
    ) -> bool:
        """
        Determine whether the distance element has picked up.
        """

        if not self.operational:
            self._active_zone = None
            return False

        return (
            self.check_zone(
                impedance
            )
            is not None
        )

    # ================================================================
    # OPERATING TIME
    # ================================================================

    def operating_time(
        self,
        zone: str | None = None,
    ) -> float:
        """
        Return the configured operating time for a zone.

        Returns
        -------
        float
            Operating time in seconds.

        math.inf
            When no protection zone is active.
        """

        if zone is None:
            zone = self._active_zone

        if zone is None:
            return math.inf

        try:
            return self.zone_times[zone]
        except KeyError as exc:
            raise ValueError(
                f"Unknown distance protection zone: {zone!r}."
            ) from exc

    # ================================================================
    # TIMESTAMP
    # ================================================================

    @staticmethod
    def _context_time(
        context: ProtectionContext | None,
    ) -> float | None:
        """
        Return the evaluation timestamp from ProtectionContext.

        ProtectionContext does not own a clock. The timestamp is
        supplied by the simulation/evaluation environment.
        """

        if context is None:
            return None

        try:
            timestamp = context.time
        except AttributeError as exc:
            raise TypeError(
                "context must provide a 'time' attribute."
            ) from exc

        return DistanceRelay._validate_timestamp(
            timestamp
        )

    # ----------------------------------------------------------------

    @staticmethod
    def _validate_timestamp(
        timestamp: float,
    ) -> float:
        """
        Validate a protection evaluation timestamp.
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

    # ----------------------------------------------------------------

    def _validate_timestamp_order(
        self,
        timestamp: float | None,
    ) -> None:
        """
        Ensure supplied evaluation timestamps do not move backwards.
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

    # ================================================================
    # TIMING STATE
    # ================================================================

    def _start_or_continue_pickup(
        self,
        *,
        zone: str,
        timestamp: float,
    ) -> None:
        """
        Start or continue the pickup interval.

        A zone transition starts a new timing interval.
        """

        if timestamp is None:
            raise ValueError(
                "A valid evaluation timestamp is required for "
                "stateful distance-protection timing."
            )

        if (
            self._active_zone != zone
            or self._pickup_start_time is None
        ):
            self._pickup_start_time = timestamp

        self._active_zone = zone

    # ----------------------------------------------------------------

    def _clear_runtime_state(self) -> None:
        """
        Clear transient distance-function timing state.

        Last measurement diagnostics are intentionally retained.
        """

        self._active_zone = None
        self._pickup_start_time = None
        self._last_operating_time = None

    # ================================================================
    # EVALUATION
    # ================================================================

    def evaluate(
        self,
        context: ProtectionContext | None = None,
    ) -> ProtectionDecision:
        """
        Evaluate one distance-protection cycle.

        Parameters
        ----------
        context:
            Protection execution context.

        Returns
        -------
        ProtectionDecision
            Canonical result of the distance protection evaluation.

        Timing
        ------
        A ProtectionContext timestamp is required when the function
        enters a timed pickup state.

        The function never creates or schedules simulation events.

        It only reports the protection decision.
        """

        timestamp = self._context_time(
            context
        )

        self._validate_timestamp_order(
            timestamp
        )

        self._last_timestamp = timestamp

        # --------------------------------------------------------------
        # Operational gate
        # --------------------------------------------------------------

        if not self.operational:

            self._clear_runtime_state()

            if self.blocked:
                decision = self.blocked_decision(
                    reason="Distance function is blocked.",
                    timestamp=timestamp,
                )

            else:
                decision = self.no_operation(
                    reason=self._inactive_reason(),
                    timestamp=timestamp,
                )

            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # Measurement acquisition
        # --------------------------------------------------------------

        try:
            voltage = self.voltage_value()

            current = self.current_value()

            impedance = self.calculate_impedance(
                voltage,
                current,
            )

        except (
            TypeError,
            ValueError,
            AttributeError,
        ) as exc:

            self._clear_runtime_state()

            decision = self.invalid_decision(
                reason=(
                    "Invalid distance-protection measurement: "
                    f"{exc}"
                ),
                timestamp=timestamp,
                metadata={
                    "voltage_input": self.VOLTAGE_INPUT,
                    "current_input": self.CURRENT_INPUT,
                },
            )

            self._last_decision = decision

            return decision

        self._last_voltage = voltage
        self._last_current = current
        self._last_impedance = impedance

        # --------------------------------------------------------------
        # Zone detection
        # --------------------------------------------------------------

        previous_zone = self._active_zone

        zone = self.determine_zone(
            impedance
        )

        # --------------------------------------------------------------
        # No pickup
        # --------------------------------------------------------------

        if zone is None:

            self._clear_runtime_state()

            decision = self.no_operation(
                reason=(
                    "Apparent impedance is outside all configured "
                    "distance-protection zones."
                ),
                timestamp=timestamp,
                metadata={
                    "voltage": voltage,
                    "current": current,
                    "impedance": impedance,
                    "impedance_magnitude": abs(impedance),
                    "active_zone": None,
                    "previous_zone": previous_zone,
                },
            )

            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # Stateful timing requires an execution timestamp
        # --------------------------------------------------------------

        if timestamp is None:

            self._clear_runtime_state()

            decision = self.invalid_decision(
                reason=(
                    "Distance protection requires "
                    "ProtectionContext.time for timed evaluation."
                ),
                timestamp=None,
                metadata={
                    "active_zone": zone,
                    "impedance": impedance,
                    "impedance_magnitude": abs(impedance),
                },
            )

            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # Start / continue pickup interval
        #
        # Zone transition restarts the timer.
        # --------------------------------------------------------------

        zone_changed = (
            previous_zone != zone
        )

        if (
            self._pickup_start_time is None
            or zone_changed
        ):
            self._pickup_start_time = timestamp

        self._active_zone = zone

        operating_time = self.operating_time(
            zone
        )

        self._last_operating_time = operating_time

        elapsed = (
            timestamp
            - self._pickup_start_time
        )

        operation_due = (
            elapsed >= operating_time
        )

        zone_reach = getattr(
            self,
            f"{zone.lower()}_reach",
        )

        metadata = {
            "voltage": voltage,
            "current": current,
            "impedance": impedance,
            "impedance_magnitude": abs(impedance),
            "active_zone": zone,
            "previous_zone": previous_zone,
            "zone_changed": zone_changed,
            "zone_reach": zone_reach,
            "pickup_start_time": self._pickup_start_time,
            "elapsed_time": elapsed,
            "operation_due": operation_due,
        }

        # --------------------------------------------------------------
        # Pickup but not yet operated
        # --------------------------------------------------------------

        if not operation_due:

            decision = self.make_decision(
                pickup=True,
                operate=False,
                trip_request=False,
                blocked=False,
                valid=True,
                operating_time=operating_time,
                timestamp=timestamp,
                reason=(
                    f"{zone} pickup active; "
                    "zone operating time not yet reached."
                ),
                metadata=metadata,
            )

            self._last_decision = decision

            return decision

        # --------------------------------------------------------------
        # Operation criterion reached
        # --------------------------------------------------------------

        decision = self.trip_decision(
            reason=(
                f"{zone} distance operating time reached."
            ),
            timestamp=timestamp,
            operating_time=operating_time,
            metadata=metadata,
        )

        self._last_decision = decision

        return decision

    # ================================================================
    # INACTIVE STATE
    # ================================================================

    def _inactive_reason(self) -> str:
        """
        Return a diagnostic explanation for inactive evaluation.
        """

        if not self.enabled:
            return "Distance function is disabled."

        if self.blocked:
            return "Distance function is blocked."

        if not bool(
            getattr(
                self.relay,
                "operational",
                True,
            )
        ):
            return "Authoritative relay is not operational."

        return "Distance function is not operational."

    # ================================================================
    # RESET
    # ================================================================

    def reset(self) -> None:
        """
        Reset transient distance-function state.

        Protection settings and authoritative physical Relay state
        remain unchanged.
        """

        super().reset()

        self._active_zone = None
        self._pickup_start_time = None
        self._last_timestamp = None

        self._last_voltage = None
        self._last_current = None
        self._last_impedance = None

        self._last_operating_time = None
        self._last_decision = None

    # ================================================================
    # DIAGNOSTICS
    # ================================================================

    @property
    def active_zone(self) -> str | None:
        """
        Return the locally determined active zone.
        """

        return self._active_zone

    # ----------------------------------------------------------------

    @property
    def pickup_start_time(self) -> float | None:
        """
        Return the beginning of the current pickup interval.
        """

        return self._pickup_start_time

    # ----------------------------------------------------------------

    @property
    def last_timestamp(self) -> float | None:
        """
        Return the last evaluation timestamp.
        """

        return self._last_timestamp

    # ----------------------------------------------------------------

    @property
    def last_voltage(self) -> complex | None:
        """
        Return the last sampled voltage.

        Diagnostic state only.
        """

        return self._last_voltage

    # ----------------------------------------------------------------

    @property
    def last_current(self) -> complex | None:
        """
        Return the last sampled current.

        Diagnostic state only.
        """

        return self._last_current

    # ----------------------------------------------------------------

    @property
    def last_impedance(self) -> complex | None:
        """
        Return the last calculated apparent impedance.

        Diagnostic state only.
        """

        return self._last_impedance

    # ----------------------------------------------------------------

    @property
    def last_operating_time(self) -> float | None:
        """
        Return the most recently calculated zone operating time.
        """

        return self._last_operating_time

    # ----------------------------------------------------------------

    @property
    def last_decision(
        self,
    ) -> ProtectionDecision | None:
        """
        Return the most recently generated protection decision.
        """

        return self._last_decision

    # ================================================================
    # STATUS
    # ================================================================

    def status(self) -> dict[str, Any]:
        """
        Return diagnostic information for this distance function.

        This is not the authoritative persistence representation.
        """

        result = super().status()

        result.update(
            {
                "function": "DISTANCE",
                "function_code": self.FUNCTION_CODE,

                "zone1_reach": self.zone1_reach,
                "zone2_reach": self.zone2_reach,
                "zone3_reach": self.zone3_reach,

                "zone1_time": self.zone_times["ZONE1"],
                "zone2_time": self.zone_times["ZONE2"],
                "zone3_time": self.zone_times["ZONE3"],

                "voltage": self._last_voltage,
                "current": self._last_current,

                "impedance": self._last_impedance,

                "impedance_magnitude": (
                    abs(self._last_impedance)
                    if self._last_impedance is not None
                    else None
                ),

                "active_zone": self._active_zone,

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

    # ================================================================
    # REPRESENTATION
    # ================================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        relay_id = getattr(
            self.relay,
            "id",
            self.relay_id,
        )

        return (
            f"<DistanceRelay "
            f"relay={relay_id!r}, "
            f"element={self.element_id!r}, "
            f"zone={self._active_zone!r}, "
            f"Z={self._last_impedance!r}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "DistanceProtectionSettings",
    "DistanceRelay",
]
