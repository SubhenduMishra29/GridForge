"""
GridForge V2 Protection Decision.

File
----
core/protection/decision.py

Purpose
-------
Defines the authoritative result contract produced by a protection
function evaluation.

A ProtectionDecision describes what a protection function concluded
during one evaluation step.

It does NOT operate physical equipment.

Architectural Boundary
----------------------
Protection function
        |
        v
ProtectionDecision
        |
        v
Protection Scheme / Output Logic
        |
        v
Trip Command
        |
        v
Physical Breaker / Switch

A ProtectionDecision therefore represents protection logic state,
not an equipment command.

Important distinction
---------------------
The following states are intentionally separate:

    pickup
        The measured quantity has crossed the function pickup
        criterion.

    operate
        The protection function has satisfied its operating criterion.

    trip_request
        The protection function requests a downstream protection
        scheme/output layer to issue a trip.

    blocked
        The function was prevented from operating.

    valid
        The evaluation itself produced a valid result.

A function may be picked up without operating, and may operate
without directly changing equipment state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ProtectionDecision:
    """
    Immutable result of one protection-function evaluation.

    Parameters
    ----------
    element_id:
        Stable identity of the protection-function instance that
        produced this decision.

    relay_id:
        Identity of the authoritative physical Relay hosting the
        protection function.

    function_code:
        Protection function designation, for example ``50``, ``51``,
        ``21`` or ``87T``.

    timestamp:
        Evaluation time.

        The exact type is intentionally not prescribed here because
        the final ProtectionContext/time contract may use a simulation
        time type rather than Python datetime.

    pickup:
        True when the function pickup criterion is satisfied.

    operate:
        True when the function has satisfied its operating criterion.

    trip_request:
        True when the function requests the downstream protection
        scheme/output layer to issue a trip.

    blocked:
        True when the function was blocked or inhibited during this
        evaluation.

    valid:
        True when the evaluation produced a valid protection result.

    reason:
        Optional machine-readable or human-readable explanation of
        the decision.

    measured:
        Optional measured/evaluated quantities relevant to diagnostics.

    values:
        Additional function-specific diagnostic values.

    metadata:
        Additional non-authoritative diagnostic/context information.
    """

    element_id: str
    relay_id: Any
    function_code: str

    timestamp: Any = None

    pickup: bool = False
    operate: bool = False
    trip_request: bool = False

    blocked: bool = False
    valid: bool = True

    reason: str = ""

    measured: Mapping[str, Any] = field(
        default_factory=dict,
    )

    values: Mapping[str, Any] = field(
        default_factory=dict,
    )

    metadata: Mapping[str, Any] = field(
        default_factory=dict,
    )

    def __post_init__(self) -> None:
        """
        Normalize immutable/public values and validate the decision.

        ProtectionDecision is frozen, but mappings supplied by callers
        could otherwise remain mutable. They are therefore copied into
        immutable mapping views.
        """

        element_id = str(self.element_id).strip()

        if not element_id:
            raise ValueError(
                "ProtectionDecision.element_id cannot be empty."
            )

        function_code = str(self.function_code).strip().upper()

        if not function_code:
            raise ValueError(
                "ProtectionDecision.function_code cannot be empty."
            )

        if self.relay_id is None:
            raise ValueError(
                "ProtectionDecision.relay_id cannot be None."
            )

        object.__setattr__(
            self,
            "element_id",
            element_id,
        )

        object.__setattr__(
            self,
            "function_code",
            function_code,
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
            str(self.reason).strip(),
        )

        object.__setattr__(
            self,
            "measured",
            MappingProxyType(dict(self.measured)),
        )

        object.__setattr__(
            self,
            "values",
            MappingProxyType(dict(self.values)),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

        self._validate_state()

    # ==================================================================
    # Validation
    # ==================================================================

    def _validate_state(self) -> None:
        """
        Validate logical relationships between decision states.
        """

        # A blocked function cannot issue an effective trip request.
        if self.blocked and self.trip_request:
            raise ValueError(
                "A blocked protection function cannot issue "
                "trip_request=True."
            )

        # A trip request represents an operating protection function.
        if self.trip_request and not self.operate:
            raise ValueError(
                "trip_request=True requires operate=True."
            )

        # An operating function must have reached pickup.
        if self.operate and not self.pickup:
            raise ValueError(
                "operate=True requires pickup=True."
            )

        # An invalid evaluation cannot produce an effective operation.
        if not self.valid and (
            self.pickup
            or self.operate
            or self.trip_request
        ):
            raise ValueError(
                "An invalid protection decision cannot assert "
                "pickup, operate, or trip_request."
            )

    # ==================================================================
    # State helpers
    # ==================================================================

    @property
    def asserted(self) -> bool:
        """
        Return True when the protection function has asserted pickup.
        """
        return self.pickup

    @property
    def operating(self) -> bool:
        """
        Return True when the protection function is operating.
        """
        return self.operate

    @property
    def requires_trip(self) -> bool:
        """
        Return True when downstream protection logic has been
        requested to issue a trip.
        """
        return self.trip_request

    @property
    def actionable(self) -> bool:
        """
        Return True when the decision contains a valid effective
        trip request.

        This does NOT mean that equipment has been operated.
        """
        return (
            self.valid
            and not self.blocked
            and self.trip_request
        )

    # ==================================================================
    # Derived state
    # ==================================================================

    @property
    def inactive(self) -> bool:
        """
        Return True when the protection function is neither picked up
        nor operating nor requesting a trip.
        """
        return not (
            self.pickup
            or self.operate
            or self.trip_request
        )

    # ==================================================================
    # Diagnostics
    # ==================================================================

    def as_dict(self) -> dict[str, Any]:
        """
        Return a diagnostic representation.

        This is intended for diagnostics and testing, not as the
        authoritative persistence schema.
        """
        return {
            "element_id": self.element_id,
            "relay_id": self.relay_id,
            "function_code": self.function_code,
            "timestamp": self.timestamp,
            "pickup": self.pickup,
            "operate": self.operate,
            "trip_request": self.trip_request,
            "blocked": self.blocked,
            "valid": self.valid,
            "reason": self.reason,
            "measured": dict(self.measured),
            "values": dict(self.values),
            "metadata": dict(self.metadata),
        }


__all__ = [
    "ProtectionDecision",
]
