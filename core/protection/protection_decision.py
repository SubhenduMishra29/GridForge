```python
"""
GridForge V2 Protection Decision
================================

File:
    core/protection/protection_decision.py

Purpose
-------
Defines the canonical decision contract produced by GridForge V2
protection-function plugins.

A ProtectionDecision represents the result of one protection-element
evaluation cycle.

Architecture
------------

    MeasurementChannel
            |
        RelayInput
            |
    Protection Element
            |
            v
    ProtectionDecision
            |
            v
    ProtectionSystem
            |
            v
       TripRequest
            |
            v
      BreakerManager

Design Principle
----------------
Protection elements make protection decisions.

They do not directly operate circuit breakers.

This module therefore provides the boundary between:

    protection-function execution

and:

    protection-system orchestration / breaker operation.

A ProtectionDecision is an immutable result object. It does not
modify the Relay model, Network, Breaker, MeasurementChannel, or
ProtectionSystem.

The decision object is deliberately generic enough to support:

    - overcurrent
    - directional overcurrent
    - distance
    - differential
    - voltage
    - frequency
    - negative sequence
    - thermal
    - breaker failure
    - generator protection
    - transformer protection
    - busbar protection
    - motor protection
    - custom/vendor-specific protection functions

The object also supports future time-domain and event-driven
protection execution without coupling this layer to a particular
simulation engine.

Responsibilities
----------------
This module provides:

    - canonical protection decision representation;
    - decision validity;
    - pickup/operate/trip-request state;
    - intentional operating time;
    - evaluation timestamp;
    - function and relay identity;
    - blocking information;
    - reason/diagnostic information;
    - extensible metadata;
    - safe decision construction.

This module does NOT:

    - calculate fault current;
    - calculate relay characteristics;
    - operate breakers;
    - modify relay state;
    - modify network topology;
    - schedule simulation events;
    - coordinate multiple protection elements.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any, Mapping, Optional


# =====================================================================
# PROTECTION DECISION
# =====================================================================


@dataclass(frozen=True)
class ProtectionDecision:
    """
    Immutable result of one protection-element evaluation.

    Parameters
    ----------
    relay_id:
        Identifier of the authoritative physical relay device.

    function_code:
        Protection function / ANSI device-function identifier.

        Examples:

            21
            50
            51
            67
            87T
            50BF

    function_id:
        Identifier of the specific protection element instance.

        This is distinct from ``relay_id`` because one physical relay
        may host many protection elements.

    pickup:
        True when the protection element's pickup criterion is met.

    operate:
        True when the element has reached its operating criterion.

        For instantaneous functions this may be equivalent to pickup.

        For time-dependent functions pickup may occur before operation.

    trip_request:
        True when the protection element requests a trip action.

        This is a request only. It does not operate a breaker.

    blocked:
        True when the element was prevented from operating by a
        protection blocking/interlocking condition.

    valid:
        True when the decision was produced from valid usable inputs
        and is suitable for downstream protection processing.

    operating_time:
        Optional intentional/calculated operating time in seconds.

        ``None`` means that no operating time was determined.

        ``math.inf`` may be used by numerical protection functions
        to represent an inverse-time condition that has not reached
        pickup, although such a decision would normally have
        ``pickup=False``.

    timestamp:
        Optional simulation/event/evaluation timestamp.

    reason:
        Human-readable diagnostic reason.

    metadata:
        Extensible immutable decision metadata.

    Notes
    -----
    The decision object contains no direct reference to a Breaker.

    A protection system may convert a valid trip request into a
    breaker command according to its own coordination and topology
    rules.
    """

    relay_id: Any

    function_code: str

    function_id: Any

    pickup: bool = False

    operate: bool = False

    trip_request: bool = False

    blocked: bool = False

    valid: bool = True

    operating_time: Optional[float] = None

    timestamp: Optional[float] = None

    reason: str = ""

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    # =================================================================
    # VALIDATION
    # =================================================================

    def __post_init__(self) -> None:
        """
        Validate the immutable decision contract.
        """

        function_code = str(
            self.function_code
        ).strip().upper()

        if not function_code:
            raise ValueError(
                "function_code cannot be empty."
            )

        object.__setattr__(
            self,
            "function_code",
            function_code,
        )

        if self.relay_id is None:
            raise ValueError(
                "relay_id cannot be None."
            )

        if self.function_id is None:
            raise ValueError(
                "function_id cannot be None."
            )

        if (
            self.operating_time is not None
        ):

            operating_time = float(
                self.operating_time
            )

            if (
                not isfinite(operating_time)
                and operating_time != float("inf")
            ):
                raise ValueError(
                    "operating_time must be finite "
                    "or positive infinity."
                )

            if operating_time < 0.0:
                raise ValueError(
                    "operating_time cannot be negative."
                )

            object.__setattr__(
                self,
                "operating_time",
                operating_time,
            )

        if self.timestamp is not None:

            timestamp = float(
                self.timestamp
            )

            if not isfinite(timestamp):
                raise ValueError(
                    "timestamp must be finite."
                )

            object.__setattr__(
                self,
                "timestamp",
                timestamp,
            )

        object.__setattr__(
            self,
            "pickup",
            bool(self.pickup),
        )

        object.__setattr__(
            self,
            "operate",
            bool(self.operate),
        )

        object.__setattr__(
            self,
            "trip_request",
            bool(self.trip_request),
        )

        object.__setattr__(
            self,
            "blocked",
            bool(self.blocked),
        )

        object.__setattr__(
            self,
            "valid",
            bool(self.valid),
        )

        object.__setattr__(
            self,
            "reason",
            str(self.reason),
        )

        if self.metadata is None:
            object.__setattr__(
                self,
                "metadata",
                {},
            )
        else:
            object.__setattr__(
                self,
                "metadata",
                dict(self.metadata),
            )

    # =================================================================
    # DECISION SEMANTICS
    # =================================================================

    @property
    def active(self) -> bool:
        """
        Return True when the protection element has picked up or
        operated.
        """

        return (
            self.pickup
            or self.operate
        )

    # -----------------------------------------------------------------

    @property
    def actionable(self) -> bool:
        """
        Return whether the decision represents a valid actionable
        protection trip request.

        A decision is actionable only when:

            valid
            AND
            not blocked
            AND
            trip_request
        """

        return (
            self.valid
            and not self.blocked
            and self.trip_request
        )

    # -----------------------------------------------------------------

    @property
    def asserted(self) -> bool:
        """
        Alias indicating that the protection element is actively
        requesting operation.
        """

        return self.actionable

    # =================================================================
    # DIAGNOSTIC CONSTRUCTORS
    # =================================================================

    @classmethod
    def invalid(
        cls,
        *,
        relay_id: Any,
        function_code: str,
        function_id: Any,
        reason: str,
        timestamp: Optional[float] = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> "ProtectionDecision":
        """
        Construct a decision indicating invalid protection inputs
        or an invalid evaluation condition.

        Invalid decisions must never request a trip.
        """

        return cls(
            relay_id=relay_id,
            function_code=function_code,
            function_id=function_id,
            pickup=False,
            operate=False,
            trip_request=False,
            blocked=False,
            valid=False,
            operating_time=None,
            timestamp=timestamp,
            reason=reason,
            metadata=metadata or {},
        )

    # -----------------------------------------------------------------

    @classmethod
    def blocked_decision(
        cls,
        *,
        relay_id: Any,
        function_code: str,
        function_id: Any,
        reason: str = "Protection element blocked.",
        timestamp: Optional[float] = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> "ProtectionDecision":
        """
        Construct a blocked protection decision.

        A blocked element cannot request a trip.
        """

        return cls(
            relay_id=relay_id,
            function_code=function_code,
            function_id=function_id,
            pickup=False,
            operate=False,
            trip_request=False,
            blocked=True,
            valid=True,
            operating_time=None,
            timestamp=timestamp,
            reason=reason,
            metadata=metadata or {},
        )

    # -----------------------------------------------------------------

    @classmethod
    def no_operation(
        cls,
        *,
        relay_id: Any,
        function_code: str,
        function_id: Any,
        reason: str = "",
        timestamp: Optional[float] = None,
        operating_time: Optional[float] = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> "ProtectionDecision":
        """
        Construct a valid non-operating decision.
        """

        return cls(
            relay_id=relay_id,
            function_code=function_code,
            function_id=function_id,
            pickup=False,
            operate=False,
            trip_request=False,
            blocked=False,
            valid=True,
            operating_time=operating_time,
            timestamp=timestamp,
            reason=reason,
            metadata=metadata or {},
        )

    # -----------------------------------------------------------------

    @classmethod
    def trip(
        cls,
        *,
        relay_id: Any,
        function_code: str,
        function_id: Any,
        reason: str = "",
        timestamp: Optional[float] = None,
        operating_time: Optional[float] = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> "ProtectionDecision":
        """
        Construct a valid trip-request decision.

        This does not operate a physical breaker.
        """

        return cls(
            relay_id=relay_id,
            function_code=function_code,
            function_id=function_id,
            pickup=True,
            operate=True,
            trip_request=True,
            blocked=False,
            valid=True,
            operating_time=operating_time,
            timestamp=timestamp,
            reason=reason,
            metadata=metadata or {},
        )

    # =================================================================
    # SERIALIZATION / DIAGNOSTICS
    # =================================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Return a serialization-safe decision representation.

        Metadata is copied so callers cannot mutate the decision's
        stored metadata through the returned dictionary.
        """

        return {
            "relay_id": self.relay_id,
            "function_code": self.function_code,
            "function_id": self.function_id,
            "pickup": self.pickup,
            "operate": self.operate,
            "trip_request": self.trip_request,
            "blocked": self.blocked,
            "valid": self.valid,
            "operating_time": self.operating_time,
            "timestamp": self.timestamp,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }

    # -----------------------------------------------------------------

    def __bool__(self) -> bool:
        """
        Boolean compatibility.

        A ProtectionDecision evaluates to True only when it represents
        an actionable protection trip request.

        This permits controlled migration from legacy boolean
        protection APIs without changing the decision semantics.
        """

        return self.actionable


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ProtectionDecision",
]
```
