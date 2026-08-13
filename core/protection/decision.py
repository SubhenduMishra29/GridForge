"""
GridForge V2 Protection Decision
=================================

File
----
core/protection/decision.py

Purpose
-------
Defines the canonical immutable decision contract produced by
GridForge V2 protection-function implementations.

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

    This does NOT operate a physical breaker.

blocked
    Protection operation was intentionally prevented.

valid
    Decision was produced from valid usable evaluation conditions.

active
    True when pickup or operate is asserted.

actionable
    True only when:

        valid
        AND not blocked
        AND trip_request

Canonical invariants
--------------------
The decision contract enforces the following relationships:

    trip_request -> operate
    operate      -> pickup

and:

    blocked      -> not operate
    blocked      -> not trip_request

and:

    not valid    -> not pickup
    not valid    -> not operate
    not valid    -> not trip_request

Therefore an actionable decision is necessarily:

    valid
    pickup
    operate
    trip_request
    not blocked

Immutability
------------
The ProtectionDecision dataclass is frozen.

The metadata container is additionally wrapped in
``MappingProxyType`` so callers cannot mutate the decision through
``decision.metadata``.

Metadata values themselves are intentionally treated as opaque
application-owned objects. GridForge does not perform arbitrary deep
copying of metadata values.

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
from math import isfinite, isinf, isnan
from types import MappingProxyType
from typing import Any, Mapping


# =====================================================================
# VALIDATION HELPERS
# =====================================================================


def _require_non_empty_string(
    value: Any,
    name: str,
) -> str:
    """
    Require a non-empty string and return its normalized form.
    """

    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be a string."
        )

    result = value.strip()

    if not result:
        raise ValueError(
            f"{name} cannot be empty."
        )

    return result


def _require_bool(
    value: Any,
    name: str,
) -> bool:
    """
    Require an actual bool.

    Boolean coercion is intentionally not performed.

    For example:

        bool("false") == True

    is unsafe for a protection-state contract.
    """

    if not isinstance(value, bool):
        raise TypeError(
            f"{name} must be a boolean."
        )

    return value


def _normalize_optional_time(
    value: Any,
    name: str,
) -> float | None:
    """
    Validate an optional protection time.

    Accepted:

        None
        finite value >= 0
        positive infinity

    Rejected:

        NaN
        negative values
        negative infinity
    """

    if value is None:
        return None

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be numeric or None."
        ) from exc

    if isnan(result):
        raise ValueError(
            f"{name} cannot be NaN."
        )

    if result == float("-inf"):
        raise ValueError(
            f"{name} cannot be negative infinity."
        )

    if result < 0.0:
        raise ValueError(
            f"{name} cannot be negative."
        )

    if not isfinite(result) and not isinf(result):
        raise ValueError(
            f"{name} must be finite or positive infinity."
        )

    return result


def _normalize_timestamp(
    value: Any,
) -> float | None:
    """
    Validate an optional finite evaluation timestamp.
    """

    if value is None:
        return None

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "timestamp must be numeric or None."
        ) from exc

    if not isfinite(result):
        raise ValueError(
            "timestamp must be finite."
        )

    return result


def _normalize_metadata(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """
    Copy and freeze the metadata mapping.

    The mapping container becomes read-only through
    MappingProxyType.
    """

    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise TypeError(
            "metadata must be a mapping or None."
        )

    return MappingProxyType(
        dict(value)
    )


# =====================================================================
# PROTECTION DECISION
# =====================================================================


@dataclass(
    frozen=True,
    slots=True,
)
class ProtectionDecision:
    """
    Immutable result of one protection-element evaluation.

    Parameters
    ----------
    relay_id:
        Identity of the authoritative physical Relay.

    element_id:
        Stable identity of the ProtectionElement instance.

    function_code:
        Canonical protection function designation.

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
        Optional protection operating time in seconds.

        ``None`` means no operating time was determined.

        Positive infinity may represent a mathematical non-operating
        inverse-time condition.

    timestamp:
        Optional finite evaluation/simulation/event timestamp.

    reason:
        Human-readable diagnostic explanation.

    metadata:
        Extensible decision metadata.

    Notes
    -----
    The object is frozen after construction.

    The metadata mapping itself is also read-only. The metadata values
    are opaque caller-owned objects and are not deep-copied.
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
        default_factory=dict,
        compare=True,
        hash=False,
    )

    # =================================================================
    # VALIDATION
    # =================================================================

    def __post_init__(self) -> None:
        """
        Validate and normalize the decision contract.

        This method enforces the semantic invariants of a protection
        decision rather than merely validating individual fields.
        """

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
        # Function code
        # -------------------------------------------------------------

        function_code = _require_non_empty_string(
            self.function_code,
            "function_code",
        )

        object.__setattr__(
            self,
            "function_code",
            function_code.upper(),
        )

        # -------------------------------------------------------------
        # Boolean state
        # -------------------------------------------------------------

        pickup = _require_bool(
            self.pickup,
            "pickup",
        )

        operate = _require_bool(
            self.operate,
            "operate",
        )

        trip_request = _require_bool(
            self.trip_request,
            "trip_request",
        )

        blocked = _require_bool(
            self.blocked,
            "blocked",
        )

        valid = _require_bool(
            self.valid,
            "valid",
        )

        # -------------------------------------------------------------
        # State invariants
        # -------------------------------------------------------------
        #
        # Protection progression:
        #
        #     pickup -> operate -> trip_request
        #
        # More precisely:
        #
        #     operate requires pickup
        #     trip_request requires operate
        #
        # Blocking and invalidity suppress operation.
        # -------------------------------------------------------------

        if operate and not pickup:
            raise ValueError(
                "operate cannot be True when pickup is False."
            )

        if trip_request and not operate:
            raise ValueError(
                "trip_request cannot be True when operate is False."
            )

        if blocked and operate:
            raise ValueError(
                "blocked decisions cannot have operate=True."
            )

        if blocked and trip_request:
            raise ValueError(
                "blocked decisions cannot have trip_request=True."
            )

        if not valid:
            if pickup or operate or trip_request:
                raise ValueError(
                    "Invalid decisions cannot assert pickup, "
                    "operate, or trip_request."
                )

        # -------------------------------------------------------------
        # Store normalized boolean state
        # -------------------------------------------------------------

        object.__setattr__(
            self,
            "pickup",
            pickup,
        )

        object.__setattr__(
            self,
            "operate",
            operate,
        )

        object.__setattr__(
            self,
            "trip_request",
            trip_request,
        )

        object.__setattr__(
            self,
            "blocked",
            blocked,
        )

        object.__setattr__(
            self,
            "valid",
            valid,
        )

        # -------------------------------------------------------------
        # Operating time
        # -------------------------------------------------------------

        object.__setattr__(
            self,
            "operating_time",
            _normalize_optional_time(
                self.operating_time,
                "operating_time",
            ),
        )

        # -------------------------------------------------------------
        # Timestamp
        # -------------------------------------------------------------

        object.__setattr__(
            self,
            "timestamp",
            _normalize_timestamp(
                self.timestamp,
            ),
        )

        # -------------------------------------------------------------
        # Reason
        # -------------------------------------------------------------

        if self.reason is None:
            normalized_reason = ""
        else:
            if not isinstance(
                self.reason,
                str,
            ):
                raise TypeError(
                    "reason must be a string."
                )

            normalized_reason = (
                self.reason.strip()
            )

        object.__setattr__(
            self,
            "reason",
            normalized_reason,
        )

        # -------------------------------------------------------------
        # Metadata
        # -------------------------------------------------------------

        object.__setattr__(
            self,
            "metadata",
            _normalize_metadata(
                self.metadata,
            ),
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
        Semantic alias for ``actionable``.
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

        Invalid decisions cannot request a trip.
        """

        if not isinstance(
            reason,
            str,
        ):
            raise TypeError(
                "Invalid protection decision reason "
                "must be a string."
            )

        if not reason.strip():
            raise ValueError(
                "Invalid protection decisions require a reason."
            )

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
            metadata=metadata,
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

        if not isinstance(
            reason,
            str,
        ):
            raise TypeError(
                "Blocked protection decision reason "
                "must be a string."
            )

        normalized_reason = reason.strip()

        if not normalized_reason:
            raise ValueError(
                "Blocked protection decisions require a reason."
            )

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
            reason=normalized_reason,
            metadata=metadata,
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
            metadata=metadata,
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
            metadata=metadata,
        )

    # -----------------------------------------------------------------

    @classmethod
    def operate_decision(
        cls,
        *,
        relay_id: Any,
        element_id: Any,
        function_code: str,
        trip_request: bool = False,
        reason: str = "",
        timestamp: float | None = None,
        operating_time: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ProtectionDecision":
        """
        Construct a valid operating decision.

        ``trip_request`` may be False when the protection function has
        operated internally but the function does not itself request
        a protection output.

        This is useful for protection functions whose operating state
        is consumed by a higher-level scheme.
        """

        if not isinstance(
            trip_request,
            bool,
        ):
            raise TypeError(
                "trip_request must be a boolean."
            )

        return cls(
            relay_id=relay_id,
            element_id=element_id,
            function_code=function_code,
            pickup=True,
            operate=True,
            trip_request=trip_request,
            blocked=False,
            valid=True,
            operating_time=operating_time,
            timestamp=timestamp,
            reason=reason,
            metadata=metadata,
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
            metadata=metadata,
        )

    # =================================================================
    # DIAGNOSTICS / SERIALIZATION
    # =================================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Return a detached dictionary representation of the decision.

        The returned mapping is mutable and is not authoritative
        decision state.
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

        Equivalent to ``to_dict()``.
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
        """

        return self.actionable

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<ProtectionDecision "
            f"relay_id={self.relay_id!r}, "
            f"element_id={self.element_id!r}, "
            f"function_code={self.function_code!r}, "
            f"pickup={self.pickup}, "
            f"operate={self.operate}, "
            f"trip_request={self.trip_request}, "
            f"blocked={self.blocked}, "
            f"valid={self.valid}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ProtectionDecision",
]
