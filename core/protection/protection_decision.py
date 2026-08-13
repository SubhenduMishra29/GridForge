"""
GridForge V2 Protection Decision
================================

File
----
core/protection/protection_decision.py

Purpose
-------
Defines the canonical immutable decision contract produced by
GridForge V2 protection-function implementations.

Architecture
------------

    MeasurementChannel
            |
            v
       RelayInput
            |
            v
      ProtectionContext
            |
            v
       RelayBase
            |
            v
    ProtectionDecision
            |
            v
    ProtectionElement
            |
            v
    ProtectionSystem
            |
            v
     Protection Output
            |
            v
      BreakerManager

Design Principle
----------------
A protection function produces a protection decision.

The decision is an information-bearing result. It is not a breaker
command and does not directly operate physical equipment.

One physical Relay may contain multiple ProtectionElement instances,
and each element may independently produce a ProtectionDecision.

A ProtectionDecision therefore identifies:

    - authoritative relay;
    - protection-function instance;
    - protection function code;
    - pickup state;
    - operating state;
    - trip-request state;
    - blocking state;
    - validity;
    - operating time;
    - evaluation timestamp;
    - diagnostic reason;
    - extensible metadata.

Responsibilities
----------------
This module provides:

    - canonical protection decision representation;
    - immutable decision semantics;
    - validity semantics;
    - pickup / operate / trip-request state;
    - blocking state;
    - operating-time information;
    - evaluation timestamp;
    - diagnostic information;
    - safe decision constructors;
    - serialization/diagnostic representation.

This module does NOT:

    - calculate electrical quantities;
    - calculate protection characteristics;
    - access network topology;
    - operate breakers;
    - schedule simulation events;
    - coordinate protection functions;
    - modify Relay state;
    - modify ProtectionSystem state.

Trip semantics
--------------
The distinction between the following states is intentional:

    pickup
        The protection pickup criterion has been satisfied.

    operate
        The protection function has reached its operating criterion.

    trip_request
        The protection function requests a trip action.

A trip request is not physical breaker operation.

The downstream protection/output layer is responsible for converting
an actionable trip request into the appropriate system action.

Validity semantics
------------------
A decision with ``valid=False`` represents an unusable or invalid
evaluation result.

Invalid decisions must never request a trip.

Blocking semantics
------------------
A blocked decision represents a valid protection evaluation in which
the protection function was intentionally prevented from operating.

Blocked decisions must never request a trip.

Immutability
------------
ProtectionDecision is frozen and its metadata is defensively
immutable.

The object therefore represents a completed evaluation result rather
than mutable protection state.

Compatibility
-------------
``__bool__`` returns the value of ``actionable``.

This permits controlled migration from legacy boolean protection APIs
while retaining the complete ProtectionDecision contract.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping


# =====================================================================
# PROTECTION DECISION
# =====================================================================


@dataclass(frozen=True)
class ProtectionDecision:
    """
    Immutable result of one protection-function evaluation.

    Parameters
    ----------
    relay_id:
        Identifier of the authoritative physical Relay.

    function_code:
        Protection-function / ANSI device-function identifier.

    function_id:
        Identifier of the specific ProtectionElement/function
        instance.

        This is distinct from ``relay_id`` because one physical Relay
        may contain multiple protection functions.

    pickup:
        True when the pickup criterion is satisfied.

    operate:
        True when the protection function has reached its operating
        criterion.

    trip_request:
        True when the protection function requests a trip action.

        This does not operate a physical breaker.

    blocked:
        True when the protection function is prevented from operating
        by a blocking/interlocking condition.

    valid:
        True when the decision was produced from valid usable inputs.

    operating_time:
        Calculated or intentional operating time in seconds.

        ``None`` means that no operating time was determined.

        Positive infinity is permitted for numerical characteristics
        that represent a non-operating inverse-time condition.

    timestamp:
        Optional evaluation/simulation timestamp in seconds.

    reason:
        Human-readable diagnostic explanation.

    metadata:
        Extensible decision-specific metadata.
    """

    relay_id: Any
    function_code: str
    function_id: Any

    pickup: bool = False
    operate: bool = False
    trip_request: bool = False

    blocked: bool = False
    valid: bool = True

    operating_time: float | None = None
    timestamp: float | None = None

    reason: str = ""

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    # =================================================================
    # VALIDATION
    # =================================================================

    def __post_init__(self) -> None:
        """
        Validate and normalize the immutable decision contract.
        """

        # -------------------------------------------------------------
        # Function code
        # -------------------------------------------------------------

        if not isinstance(
            self.function_code,
            str,
        ):
            raise TypeError(
                "function_code must be a string."
            )

        function_code = (
            self.function_code
            .strip()
            .upper()
        )

        if not function_code:
            raise ValueError(
                "function_code cannot be empty."
            )

        object.__setattr__(
            self,
            "function_code",
            function_code,
        )

        # -------------------------------------------------------------
        # Identity
        # -------------------------------------------------------------

        if self.relay_id is None:
            raise ValueError(
                "relay_id cannot be None."
            )

        if self.function_id is None:
            raise ValueError(
                "function_id cannot be None."
            )

        # -------------------------------------------------------------
        # Boolean fields
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # Invalid / blocked decisions cannot request trips.
        # -------------------------------------------------------------

        if (
            not self.valid
            or self.blocked
        ) and self.trip_request:

            raise ValueError(
                "Invalid or blocked protection decisions "
                "cannot request a trip."
            )

        # -------------------------------------------------------------
        # Operating-time validation
        # -------------------------------------------------------------

        if self.operating_time is not None:

            try:
                operating_time = float(
                    self.operating_time
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "operating_time must be numeric."
                ) from exc

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

        # -------------------------------------------------------------
        # Timestamp validation
        # -------------------------------------------------------------

        if self.timestamp is not None:

            try:
                timestamp = float(
                    self.timestamp
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "timestamp must be numeric."
                ) from exc

            if not isfinite(timestamp):
                raise ValueError(
                    "timestamp must be finite."
                )

            object.__setattr__(
                self,
                "timestamp",
                timestamp,
            )

        # -------------------------------------------------------------
        # Reason
        # -------------------------------------------------------------

        object.__setattr__(
            self,
            "reason",
            str(self.reason),
        )

        # -------------------------------------------------------------
        # Metadata
        #
        # A frozen dataclass alone does not make a dictionary immutable.
        # Convert metadata to a MappingProxyType so the completed
        # decision cannot be modified through the metadata mapping.
        # -------------------------------------------------------------

        if self.metadata is None:

            metadata = {}

        else:

            if not isinstance(
                self.metadata,
                Mapping,
            ):
                raise TypeError(
                    "metadata must be a mapping."
                )

            metadata = dict(
                self.metadata
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                metadata
            ),
        )

    # =================================================================
    # DECISION SEMANTICS
    # =================================================================

    @property
    def active(self) -> bool:
        """
        Return True when the protection function has picked up or
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
        Return True when the decision represents an actionable
        trip request.

        Conditions:

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
        Alias for ``actionable``.

        Indicates that the protection decision is actively requesting
        a trip.
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
        timestamp: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionDecision":
        """
        Construct an invalid protection decision.

        Invalid decisions cannot request a trip.
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
        timestamp: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionDecision":
        """
        Construct a valid blocked protection decision.

        A blocked decision cannot request a trip.
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
        timestamp: float | None = None,
        operating_time: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionDecision":
        """
        Construct a valid non-operating protection decision.
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
    def pickup_decision(
        cls,
        *,
        relay_id: Any,
        function_code: str,
        function_id: Any,
        reason: str = "",
        timestamp: float | None = None,
        operating_time: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionDecision":
        """
        Construct a valid pickup-only decision.

        The protection element has picked up but has not yet reached
        its operating/trip criterion.
        """

        return cls(
            relay_id=relay_id,
            function_code=function_code,
            function_id=function_id,
            pickup=True,
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
    def operated(
        cls,
        *,
        relay_id: Any,
        function_code: str,
        function_id: Any,
        trip_request: bool = False,
        reason: str = "",
        timestamp: float | None = None,
        operating_time: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionDecision":
        """
        Construct a valid operated decision.

        ``trip_request`` is explicit because an operated protection
        function does not necessarily imply that the downstream
        system must immediately issue a breaker trip.
        """

        return cls(
            relay_id=relay_id,
            function_code=function_code,
            function_id=function_id,
            pickup=True,
            operate=True,
            trip_request=trip_request,
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
        timestamp: float | None = None,
        operating_time: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionDecision":
        """
        Construct a valid actionable trip-request decision.

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
        Return a dictionary representation of the decision.

        The returned metadata dictionary is independent from the
        decision's internal immutable metadata.
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
            "metadata": dict(
                self.metadata
            ),
        }

    # -----------------------------------------------------------------

    def as_dict(self) -> dict[str, Any]:
        """
        Compatibility alias for ``to_dict()``.
        """

        return self.to_dict()

    # -----------------------------------------------------------------

    def diagnostics(self) -> dict[str, Any]:
        """
        Return structured diagnostic information.

        This is intentionally equivalent to the serialization-safe
        representation and exists as a semantic diagnostics API for
        ProtectionElement and ProtectionSystem.
        """

        return self.to_dict()

    # =================================================================
    # BOOLEAN COMPATIBILITY
    # =================================================================

    def __bool__(self) -> bool:
        """
        Return whether this decision is actionable.

        This supports controlled migration from legacy boolean
        protection APIs without discarding the complete decision
        object.
        """

        return self.actionable


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ProtectionDecision",
]
