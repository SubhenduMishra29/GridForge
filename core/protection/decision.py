"""
GridForge V2 Protection Decision
================================

File
----
core/protection/decision.py

Purpose
-------
Defines the canonical immutable decision contract produced by
GridForge V2 protection-function plugins.

A ProtectionDecision represents the result of one protection-element
evaluation cycle.

Architecture
------------

    MeasurementChannel
            |
        RelayInput
            |
    RelayBase / ProtectionElement
            |
            v
    ProtectionDecision
            |
            v
    ProtectionSystem
            |
            v
       Protection Output
            |
            v
       BreakerManager

Identity Model
--------------
GridForge V2 deliberately distinguishes:

    relay_id
        Identity of the authoritative physical Relay.

    element_id
        Identity of the protection-function instance hosted by that
        Relay.

    function_code
        Protection function designation.

Example:

    Relay R1
        |
        +-- Element OC51
        |      function_code = "51"
        |
        +-- Element OC50
               function_code = "50"

Therefore:

    relay_id   = "R1"
    element_id = "OC51"
    function_code = "51"

The element identity is the canonical identity used by
ProtectionSystem to associate a decision with a ProtectionElement.

Responsibilities
----------------
ProtectionDecision provides:

    * canonical protection result representation;
    * protection-element identity;
    * physical Relay identity;
    * function-code identity;
    * pickup state;
    * operate state;
    * trip-request state;
    * blocking state;
    * validity state;
    * operating-time information;
    * evaluation timestamp;
    * diagnostic reason;
    * extensible metadata;
    * immutable decision semantics.

ProtectionDecision does NOT:

    * calculate electrical quantities;
    * calculate protection characteristics;
    * operate breakers;
    * modify Relay state;
    * modify MeasurementChannel state;
    * modify network topology;
    * schedule simulation events;
    * coordinate protection elements.

Decision Semantics
------------------
pickup
    Protection pickup criterion has been satisfied.

operate
    Protection element has reached its operating criterion.

trip_request
    Protection element requests a protection output/trip action.

blocked
    Protection operation was intentionally prevented.

valid
    Decision was produced from valid usable evaluation conditions.

actionable
    True only when:

        valid
        AND not blocked
        AND trip_request

The decision is a request/result object only. Physical breaker
operation belongs to a higher protection-output layer.

Compatibility
-------------
The canonical V2 API is:

    core.protection.decision.ProtectionDecision

A legacy compatibility module may re-export this class, but must not
maintain a second ProtectionDecision implementation.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any, Mapping


# =====================================================================
# PROTECTION DECISION
# =====================================================================


@dataclass(frozen=True, slots=True)
class ProtectionDecision:
    """
    Immutable result of one protection-element evaluation.

    Parameters
    ----------
    relay_id:
        Identity of the authoritative physical Relay.

    element_id:
        Stable identity of the ProtectionElement instance.

        This is the canonical decision identity and is intentionally
        distinct from ``relay_id``.

    function_code:
        Canonical protection function designation.

        Examples:

            21
            27
            32
            46
            50
            51
            59
            67
            81
            87T
            50BF

    pickup:
        True when the protection pickup criterion is satisfied.

    operate:
        True when the protection function has reached its operating
        criterion.

    trip_request:
        True when the protection function requests a trip/output
        action.

        This does NOT operate a physical breaker.

    blocked:
        True when operation was prevented by a blocking condition.

    valid:
        True when the decision was produced from valid evaluation
        inputs and is suitable for downstream processing.

    operating_time:
        Optional calculated or intentional protection operating time
        in seconds.

        ``None`` means no operating time was determined.

        Positive infinity may represent a mathematical non-operating
        inverse-time condition.

    timestamp:
        Optional evaluation/simulation/event timestamp.

    reason:
        Human-readable diagnostic explanation.

    metadata:
        Extensible decision metadata.

    Notes
    -----
    The object is frozen and therefore cannot be mutated after
    construction.

    Metadata is copied during construction so that the decision does
    not retain ownership of the caller's mutable mapping.
    """

    # =================================================================
    # IDENTITY
    # =================================================================

    relay_id: Any
    element_id: Any
    function_code: str

    # =================================================================
    # PROTECTION STATE
    # =================================================================

    pickup: bool = False
    operate: bool = False
    trip_request: bool = False
    blocked: bool = False
    valid: bool = True

    # =================================================================
    # EXECUTION INFORMATION
    # =================================================================

    operating_time: float | None = None
    timestamp: float | None = None

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    reason: str = ""

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    # =================================================================
    # VALIDATION
    # =================================================================

    def __post_init__(self) -> None:
        """
        Validate and normalize the immutable decision.
        """

        # -------------------------------------------------------------
        # Function code
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # Relay identity
        # -------------------------------------------------------------

        if self.relay_id is None:
            raise ValueError(
                "relay_id cannot be None."
            )

        # -------------------------------------------------------------
        # Protection-element identity
        # -------------------------------------------------------------

        if self.element_id is None:
            raise ValueError(
                "element_id cannot be None."
            )

        # -------------------------------------------------------------
        # Boolean normalization
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
        # Operating time
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
        # Timestamp
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
            str(self.reason).strip(),
        )

        # -------------------------------------------------------------
        # Metadata
        # -------------------------------------------------------------

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata or {}),
        )

    # =================================================================
    # SEMANTIC STATE
    # =================================================================

    @property
    def active(self) -> bool:
        """
        Return True when the protection element has picked up or
        operated.

        This does not imply a trip request.
        """

        return (
            self.pickup
            or self.operate
        )

    # -----------------------------------------------------------------

    @property
    def actionable(self) -> bool:
        """
        Return True when this decision represents a valid actionable
        trip request.

        Definition
        ----------

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
        Return whether the protection decision is actionable.

        ``asserted`` is retained as a semantic convenience alias.
        """

        return self.actionable

    # =================================================================
    # FACTORY METHODS
    # =================================================================

    @classmethod
    def invalid(
        cls,
        *,
        relay_id: Any,
        element_id: Any,
        function_code: str,
        reason: str,
        timestamp: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionDecision":
        """
        Construct an invalid protection decision.

        Invalid decisions can never request a trip.
        """

        return cls(
            relay_id=relay_id,
            element_id=element_id,
            function_code=function_code,
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
        element_id: Any,
        function_code: str,
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
            element_id=element_id,
            function_code=function_code,
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
        element_id: Any,
        function_code: str,
        reason: str = "",
        timestamp: float | None = None,
        operating_time: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionDecision":
        """
        Construct a valid non-operating decision.
        """

        return cls(
            relay_id=relay_id,
            element_id=element_id,
            function_code=function_code,
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
        element_id: Any,
        function_code: str,
        reason: str = "",
        timestamp: float | None = None,
        operating_time: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionDecision":
        """
        Construct a valid pickup-only decision.

        The element has picked up but has not yet reached its operating
        or trip criterion.
        """

        return cls(
            relay_id=relay_id,
            element_id=element_id,
            function_code=function_code,
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
    def trip(
        cls,
        *,
        relay_id: Any,
        element_id: Any,
        function_code: str,
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
            element_id=element_id,
            function_code=function_code,
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
    # DIAGNOSTICS / SERIALIZATION
    # =================================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Return a detached dictionary representation of the decision.

        The returned mapping is not authoritative decision state and
        may safely be modified by diagnostic consumers.
        """

        return {
            "relay_id": self.relay_id,
            "element_id": self.element_id,
            "function_code": self.function_code,
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

    def diagnostics(self) -> dict[str, Any]:
        """
        Return diagnostic information.

        This is intentionally equivalent to ``to_dict()`` while
        providing an explicit diagnostics-oriented API used by
        ProtectionElement.status().
        """

        return self.to_dict()

    # =================================================================
    # COMPATIBILITY
    # =================================================================

    def as_dict(self) -> dict[str, Any]:
        """
        Compatibility alias for legacy callers.

        New V2 code should prefer ``to_dict()``.
        """

        return self.to_dict()

    # -----------------------------------------------------------------

    @property
    def function_id(self) -> Any:
        """
        Compatibility alias for legacy code.

        In GridForge V2 the canonical identity is ``element_id``.

        ``function_id`` is retained only as a read-only compatibility
        view and must not be used as a second independent identity.
        """

        return self.element_id

    # -----------------------------------------------------------------

    @property
    def tripped(self) -> bool:
        """
        Compatibility semantic alias.

        A decision is considered tripped when it contains an
        actionable trip request.
        """

        return self.actionable

    # -----------------------------------------------------------------

    @property
    def operated(self) -> bool:
        """
        Compatibility semantic alias for ``operate``.
        """

        return self.operate

    # -----------------------------------------------------------------

    def __bool__(self) -> bool:
        """
        Boolean compatibility.

        A ProtectionDecision evaluates to True only when it represents
        an actionable protection trip request.

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
