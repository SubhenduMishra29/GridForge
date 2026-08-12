```python
"""
GridForge Protection System
===========================

File:
    core/protection/protection_system.py

Purpose
-------
Central orchestration boundary for GridForge V2 protection.

Architectural Principle
-----------------------

A physical/numerical Relay may contain multiple protection
functions.

Therefore:

    Relay != ProtectionFunction

Example:

    Relay R1
        |
        +-- OvercurrentFunction
        +-- EarthFaultFunction
        +-- DirectionalFunction
        +-- DistanceFunction
        +-- VoltageFunction
        +-- FrequencyFunction

ProtectionSystem orchestrates those function instances.

It does not become a protection algorithm.

Authority Boundary
-------------------

core/model/relay.py
    Authoritative Relay device identity, configuration and state.

core/model/ct.py
core/model/pt.py
core/model/cvt.py
core/model/measurement_channel.py
    Authoritative measurement-domain objects.

core/protection/relay_base.py
    Protection-function execution contract.

core/protection/<function>.py
    Concrete protection algorithms/elements.

core/protection/protection_system.py
    Protection-function orchestration and decision aggregation.

core/protection/breaker_manager.py
    Breaker command boundary.

core/model/breaker.py
    Authoritative physical breaker state.

Responsibilities
----------------
ProtectionSystem:

- register multiple protection functions;
- allow multiple functions on one Relay;
- associate functions with authoritative Relay models;
- associate functions with controlled breakers;
- validate protection registration;
- evaluate protection functions;
- normalize protection results;
- aggregate decisions;
- generate TripRequest objects;
- dispatch TripRequests through BreakerManager;
- preserve provenance;
- record orchestration events;
- reset protection-function runtime state;
- expose diagnostics.

ProtectionSystem does NOT:

- acquire measurements;
- create measurement channels;
- calculate electrical quantities;
- implement protection algorithms;
- calculate impedance;
- calculate fault current;
- perform load flow;
- perform short-circuit analysis;
- build Y-bus;
- coordinate relay settings;
- directly operate breakers;
- modify network topology;
- schedule simulation events.

Multifunction Relay Model
-------------------------

The internal registration structure is function-centric:

    function_id
        |
        +-- protection function
        +-- authoritative relay
        +-- breaker association
        +-- optional metadata

This permits:

    Relay R1
        |
        +-- OC1
        +-- EF1
        +-- DIST1
        +-- UV1

without duplicating Relay state.

Trip Ownership
--------------

ProtectionSystem creates TripRequest objects.

BreakerManager remains the sole protection-layer command boundary
for physical breaker operation.

    ProtectionFunction
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
            |
            v
          Breaker

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
    Immutable result of one protection-function evaluation.

    Parameters
    ----------
    relay_id:
        Authoritative physical Relay identifier.

    function_id:
        Protection-function instance identifier.

    operated:
        True when the protection element has reached its operating
        criterion.

    picked_up:
        True when the protection element is in pickup condition.

    trip:
        True when the function requests a protection trip.

        This is deliberately separate from pickup and operation.

    function:
        Protection-function type/name.

    time:
        Evaluation time.

    reason:
        Operating explanation.

    metadata:
        Function-specific diagnostic information.

    Notes
    -----
    This is a decision DTO.

    It is not authoritative Relay state.
    """

    relay_id: Any
    function_id: Any
    operated: bool
    picked_up: bool
    trip: bool
    function: str
    time: float = 0.0
    reason: str = ""
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )


# =====================================================================
# TRIP REQUEST
# =====================================================================


@dataclass(frozen=True, slots=True)
class TripRequest:
    """
    Immutable request to operate a controlled breaker.

    TripRequest does not operate the breaker.
    """

    relay_id: Any
    function_id: Any
    breaker_id: Any
    function: str
    time: float
    reason: str = ""
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )


# =====================================================================
# PROTECTION EVENT
# =====================================================================


@dataclass(frozen=True, slots=True)
class ProtectionEvent:
    """
    Immutable protection/control orchestration event.

    This represents history and diagnostics.

    It is not authoritative device state.
    """

    time: float
    event_type: str
    relay_id: Any
    function_id: Any = None
    breaker_id: Any = None
    function: str = ""
    success: bool | None = None
    reason: str = ""
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )


# =====================================================================
# INTERNAL REGISTRATION
# =====================================================================


@dataclass(slots=True)
class _ProtectionRegistration:
    """
    Internal protection-function registration.

    References are stored only.

    Relay and Breaker state are never duplicated.
    """

    protection: Any
    relay: Any
    breaker_id: Any = None


# =====================================================================
# PROTECTION SYSTEM
# =====================================================================


class ProtectionSystem:
    """
    Central GridForge V2 protection orchestrator.

    The primary registration identity is function_id rather than
    relay_id.

    This permits multiple protection functions to operate on one
    authoritative Relay.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        breaker_manager: Any = None,
    ) -> None:
        """
        Create an empty ProtectionSystem.
        """

        self.breaker_manager = breaker_manager

        self._registrations: dict[
            str,
            _ProtectionRegistration,
        ] = {}

        self._events: list[
            ProtectionEvent
        ] = []

    # =================================================================
    # REGISTRATION
    # =================================================================

    def register(
        self,
        protection: Any,
        relay: Any | None = None,
        breaker_id: Any = None,
        *,
        function_id: str | None = None,
    ) -> str:
        """
        Register one protection-function instance.

        Parameters
        ----------
        protection:
            RelayBase-derived protection function.

        relay:
            Authoritative Relay model.

            When omitted, protection.relay is used.

        breaker_id:
            Optional controlled breaker.

        function_id:
            Optional explicit protection-function identifier.

            When omitted, protection.function_id or protection.id
            is used.

        Returns
        -------
        str
            Registered function identifier.

        Notes
        -----
        Multiple protection functions may reference the same Relay.
        """

        if protection is None:
            raise ValueError(
                "protection cannot be None."
            )

        # -------------------------------------------------------------
        # Resolve authoritative Relay
        # -------------------------------------------------------------

        if relay is None:
            relay = getattr(
                protection,
                "relay",
                None,
            )

        if relay is None:
            raise ValueError(
                "An authoritative Relay must be supplied either "
                "through register(..., relay=...) or "
                "protection.relay."
            )

        relay_id = getattr(
            relay,
            "id",
            None,
        )

        if not isinstance(
            relay_id,
            str,
        ) or not relay_id.strip():
            raise ValueError(
                "relay must provide a non-empty string id."
            )

        # -------------------------------------------------------------
        # Verify plugin Relay binding
        # -------------------------------------------------------------

        protection_relay = getattr(
            protection,
            "relay",
            None,
        )

        if (
            protection_relay is not None
            and protection_relay is not relay
        ):
            raise ValueError(
                "Protection function is bound to a different "
                "authoritative Relay model."
            )

        # -------------------------------------------------------------
        # Function identity
        # -------------------------------------------------------------

        if function_id is None:

            function_id = getattr(
                protection,
                "function_id",
                None,
            )

        if function_id is None:

            function_id = getattr(
                protection,
                "id",
                None,
            )

        if not isinstance(
            function_id,
            str,
        ) or not function_id.strip():
            raise ValueError(
                "Protection function must provide a non-empty "
                "function_id or id."
            )

        function_id = function_id.strip()

        if function_id in self._registrations:
            raise ValueError(
                f"Protection function '{function_id}' "
                "is already registered."
            )

        # -------------------------------------------------------------
        # Verify function identity consistency
        # -------------------------------------------------------------

        protection_function_id = getattr(
            protection,
            "function_id",
            None,
        )

        if (
            protection_function_id is not None
            and protection_function_id != function_id
        ):
            raise ValueError(
                "function_id does not match the protection "
                "function's authoritative function_id."
            )

        # -------------------------------------------------------------
        # Evaluation interface
        # -------------------------------------------------------------

        evaluate = getattr(
            protection,
            "evaluate",
            None,
        )

        if not callable(evaluate):
            raise TypeError(
                "Protection function must provide evaluate()."
            )

        # -------------------------------------------------------------
        # Breaker validation
        # -------------------------------------------------------------

        if breaker_id is not None:

            has_breaker = getattr(
                self.breaker_manager,
                "has_breaker",
                None,
            )

            if (
                self.breaker_manager is not None
                and callable(has_breaker)
                and not has_breaker(breaker_id)
            ):
                raise KeyError(
                    f"Breaker '{breaker_id}' is not "
                    "registered with BreakerManager."
                )

        self._registrations[
            function_id
        ] = _ProtectionRegistration(
            protection=protection,
            relay=relay,
            breaker_id=breaker_id,
        )

        return function_id

    # =================================================================
    # COMPATIBILITY REGISTRATION
    # =================================================================

    def add_relay(
        self,
        protection: Any,
        breaker_id: Any = None,
    ) -> str:
        """
        Compatibility registration method.

        Despite its historical name, this registers one protection
        function.

        Preferred V2 form:

            register(
                protection=...,
                relay=...,
                breaker_id=...,
            )
        """

        return self.register(
            protection=protection,
            relay=getattr(
                protection,
                "relay",
                None,
            ),
            breaker_id=breaker_id,
        )

    # =================================================================
    # UNREGISTRATION
    # =================================================================

    def unregister(
        self,
        function_id: str,
    ) -> None:
        """
        Remove one protection-function registration.

        The authoritative Relay is not modified.
        """

        self._registrations.pop(
            function_id,
            None,
        )

    # =================================================================
    # LOOKUP
    # =================================================================

    def get(
        self,
        function_id: str,
    ) -> Any | None:
        """
        Return a registered protection function.
        """

        registration = self._registrations.get(
            function_id
        )

        if registration is None:
            return None

        return registration.protection

    # -----------------------------------------------------------------

    def get_relay_functions(
        self,
        relay_id: Any,
    ) -> tuple[Any, ...]:
        """
        Return all protection functions associated with one Relay.
        """

        return tuple(
            registration.protection
            for registration in self._registrations.values()
            if registration.relay.id == relay_id
        )

    # -----------------------------------------------------------------

    def function_ids_for_relay(
        self,
        relay_id: Any,
    ) -> tuple[str, ...]:
        """
        Return all protection-function IDs belonging to a Relay.
        """

        return tuple(
            function_id
            for function_id, registration
            in self._registrations.items()
            if registration.relay.id == relay_id
        )

    # =================================================================
    # REGISTRATION INFORMATION
    # =================================================================

    @property
    def function_ids(self) -> tuple[str, ...]:
        """
        Return registered protection-function identifiers.
        """

        return tuple(
            self._registrations.keys()
        )

    # -----------------------------------------------------------------

    @property
    def relay_ids(self) -> tuple[Any, ...]:
        """
        Return unique authoritative Relay identifiers.

        Multiple functions belonging to the same Relay appear only
        once.
        """

        seen: list[Any] = []

        for registration in (
            self._registrations.values()
        ):

            relay_id = registration.relay.id

            if relay_id not in seen:
                seen.append(relay_id)

        return tuple(seen)

    # -----------------------------------------------------------------

    @property
    def events(
        self,
    ) -> tuple[ProtectionEvent, ...]:
        """
        Return immutable event history.
        """

        return tuple(
            self._events
        )

    # =================================================================
    # TIME VALIDATION
    # =================================================================

    @staticmethod
    def _validate_time(
        value: float,
    ) -> float:
        """
        Validate simulation/event time.
        """

        value = float(value)

        if not isfinite(value):
            raise ValueError(
                "Protection event time must be finite."
            )

        return value

    # =================================================================
    # FUNCTION IDENTIFICATION
    # =================================================================

    @staticmethod
    def _function_name(
        protection: Any,
    ) -> str:
        """
        Return the protection-function name.
        """

        for attribute in (
            "function_name",
            "protection_function",
            "relay_type",
            "name",
        ):

            value = getattr(
                protection,
                attribute,
                None,
            )

            if (
                isinstance(value, str)
                and value.strip()
            ):
                return value

        return protection.__class__.__name__

    # =================================================================
    # DECISION NORMALIZATION
    # =================================================================

    @classmethod
    def _make_decision(
        cls,
        registration: _ProtectionRegistration,
        result: Any,
        *,
        time: float,
    ) -> ProtectionDecision:
        """
        Normalize a protection-function result.

        Supported result forms:

            ProtectionDecision

            bool

            mapping

        Mapping keys:

            operated
            picked_up
            trip
            reason
            metadata

        Compatibility aliases:

            tripped -> trip
        """

        relay = registration.relay
        protection = registration.protection

        relay_id = relay.id

        function_id = getattr(
            protection,
            "function_id",
            getattr(
                protection,
                "id",
                None,
            ),
        )

        if function_id is None:
            raise RuntimeError(
                "Protection function does not expose a "
                "function identifier."
            )

        function = cls._function_name(
            protection
        )

        # -------------------------------------------------------------
        # Native decision
        # -------------------------------------------------------------

        if isinstance(
            result,
            ProtectionDecision,
        ):

            if result.relay_id != relay_id:
                raise ValueError(
                    "ProtectionDecision relay_id does not match "
                    "the registered authoritative Relay."
                )

            if result.function_id != function_id:
                raise ValueError(
                    "ProtectionDecision function_id does not "
                    "match the registered protection function."
                )

            return result

        # -------------------------------------------------------------
        # Boolean compatibility
        # -------------------------------------------------------------

        if isinstance(
            result,
            bool,
        ):

            return ProtectionDecision(
                relay_id=relay_id,
                function_id=function_id,
                operated=result,
                picked_up=result,
                trip=result,
                function=function,
                time=time,
            )

        # -------------------------------------------------------------
        # Mapping compatibility
        # -------------------------------------------------------------

        if isinstance(
            result,
            Mapping,
        ):

            operated = bool(
                result.get(
                    "operated",
                    result.get(
                        "tripped",
                        False,
                    ),
                )
            )

            picked_up = bool(
                result.get(
                    "picked_up",
                    operated,
                )
            )

            trip = bool(
                result.get(
                    "trip",
                    result.get(
                        "tripped",
                        operated,
                    ),
                )
            )

            reason = str(
                result.get(
                    "reason",
                    "",
                )
            )

            metadata = result.get(
                "metadata",
                {},
            )

            if not isinstance(
                metadata,
                Mapping,
            ):
                raise TypeError(
                    "Protection decision metadata must be "
                    "a mapping."
                )

            return ProtectionDecision(
                relay_id=relay_id,
                function_id=function_id,
                operated=operated,
                picked_up=picked_up,
                trip=trip,
                function=function,
                time=time,
                reason=reason,
                metadata=dict(metadata),
            )

        raise TypeError(
            "Protection function evaluate() must return "
            "ProtectionDecision, bool, or a mapping."
        )

    # =================================================================
    # SINGLE FUNCTION EVALUATION
    # =================================================================

    def evaluate_function(
        self,
        function_id: str,
        time: float = 0.0,
    ) -> ProtectionDecision:
        """
        Evaluate one protection-function instance.
        """

        simulation_time = self._validate_time(
            time
        )

        registration = self._registrations.get(
            function_id
        )

        if registration is None:
            raise KeyError(
                f"Protection function '{function_id}' "
                "is not registered."
            )

        protection = registration.protection
        relay = registration.relay

        function = self._function_name(
            protection
        )

        # -------------------------------------------------------------
        # Function availability
        # -------------------------------------------------------------

        is_available = getattr(
            protection,
            "is_available",
            None,
        )

        if callable(is_available):

            if not bool(
                is_available()
            ):

                decision = ProtectionDecision(
                    relay_id=relay.id,
                    function_id=function_id,
                    operated=False,
                    picked_up=False,
                    trip=False,
                    function=function,
                    time=simulation_time,
                    reason=(
                        "Protection function is not available."
                    ),
                )

                self._events.append(
                    ProtectionEvent(
                        time=simulation_time,
                        event_type="PROTECTION_BLOCKED",
                        relay_id=relay.id,
                        function_id=function_id,
                        breaker_id=registration.breaker_id,
                        function=function,
                        success=False,
                        reason=decision.reason,
                    )
                )

                return decision

        # -------------------------------------------------------------
        # Evaluate function
        # -------------------------------------------------------------

        result = protection.evaluate()

        decision = self._make_decision(
            registration,
            result,
            time=simulation_time,
        )

        if decision.operated:

            self._events.append(
                ProtectionEvent(
                    time=simulation_time,
                    event_type="PROTECTION_OPERATE",
                    relay_id=relay.id,
                    function_id=function_id,
                    breaker_id=registration.breaker_id,
                    function=function,
                    success=None,
                    reason=decision.reason,
                    metadata=dict(
                        decision.metadata
                    ),
                )
            )

        elif decision.picked_up:

            self._events.append(
                ProtectionEvent(
                    time=simulation_time,
                    event_type="PROTECTION_PICKUP",
                    relay_id=relay.id,
                    function_id=function_id,
                    breaker_id=registration.breaker_id,
                    function=function,
                    success=None,
                    reason=decision.reason,
                    metadata=dict(
                        decision.metadata
                    ),
                )
            )

        return decision

    # =================================================================
    # SINGLE RELAY EVALUATION
    # =================================================================

    def evaluate_relay(
        self,
        relay_id: Any,
        time: float = 0.0,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Evaluate every protection function belonging to one Relay.

        Multiple functions may therefore produce independent
        decisions during the same evaluation cycle.
        """

        simulation_time = self._validate_time(
            time
        )

        function_ids = self.function_ids_for_relay(
            relay_id
        )

        if not function_ids:
            raise KeyError(
                f"Relay '{relay_id}' has no registered "
                "protection functions."
            )

        return tuple(
            self.evaluate_function(
                function_id,
                time=simulation_time,
            )
            for function_id in function_ids
        )

    # =================================================================
    # ALL FUNCTIONS
    # =================================================================

    def evaluate(
        self,
        time: float = 0.0,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Evaluate all registered protection functions.
        """

        simulation_time = self._validate_time(
            time
        )

        return tuple(
            self.evaluate_function(
                function_id,
                time=simulation_time,
            )
            for function_id in self._registrations
        )

    # =================================================================
    # DECISION AGGREGATION
    # =================================================================

    @staticmethod
    def trip_decisions(
        decisions: tuple[
            ProtectionDecision,
            ...
        ] | list[
            ProtectionDecision
        ],
    ) -> tuple[ProtectionDecision, ...]:
        """
        Return only decisions that explicitly request a trip.

        Pickup and operation are not automatically converted into a
        breaker trip.
        """

        return tuple(
            decision
            for decision in decisions
            if isinstance(
                decision,
                ProtectionDecision,
            )
            and decision.trip
        )

    # =================================================================
    # TRIP REQUEST GENERATION
    # =================================================================

    def trip_requests(
        self,
        decisions: tuple[
            ProtectionDecision,
            ...
        ] | list[
            ProtectionDecision
        ],
        time: float | None = None,
    ) -> tuple[TripRequest, ...]:
        """
        Convert protection trip decisions into TripRequests.

        No breaker operation occurs here.

        The function-specific decision remains the provenance of the
        request.
        """

        if decisions is None:
            raise ValueError(
                "decisions cannot be None."
            )

        simulation_time = (
            None
            if time is None
            else self._validate_time(time)
        )

        requests: list[
            TripRequest
        ] = []

        for decision in decisions:

            if not isinstance(
                decision,
                ProtectionDecision,
            ):
                raise TypeError(
                    "decisions must contain only "
                    "ProtectionDecision objects."
                )

            if not decision.trip:
                continue

            registration = self._registrations.get(
                decision.function_id
            )

            if registration is None:
                raise RuntimeError(
                    "Protection decision references an "
                    "unregistered protection function."
                )

            breaker_id = registration.breaker_id

            request_time = (
                simulation_time
                if simulation_time is not None
                else decision.time
            )

            if breaker_id is None:

                self._events.append(
                    ProtectionEvent(
                        time=request_time,
                        event_type="TRIP_REQUEST_REJECTED",
                        relay_id=decision.relay_id,
                        function_id=decision.function_id,
                        breaker_id=None,
                        function=decision.function,
                        success=False,
                        reason=(
                            "No breaker is associated with "
                            "the protection function."
                        ),
                    )
                )

                continue

            requests.append(
                TripRequest(
                    relay_id=decision.relay_id,
                    function_id=decision.function_id,
                    breaker_id=breaker_id,
                    function=decision.function,
                    time=request_time,
                    reason=decision.reason,
                    metadata=dict(
                        decision.metadata
                    ),
                )
            )

        return tuple(
            requests
        )

    # =================================================================
    # BREAKER DISPATCH
    # =================================================================

    def operate(
        self,
        requests: tuple[
            TripRequest,
            ...
        ] | list[
            TripRequest
        ],
    ) -> tuple[
        dict[str, Any],
        ...
    ]:
        """
        Dispatch TripRequests to BreakerManager.

        ProtectionSystem never calls Breaker.open() directly.
        """

        if requests is None:
            raise ValueError(
                "requests cannot be None."
            )

        results: list[
            dict[str, Any]
        ] = []

        if self.breaker_manager is None:

            for request in requests:

                reason = (
                    "No BreakerManager is configured."
                )

                self._events.append(
                    ProtectionEvent(
                        time=request.time,
                        event_type="TRIP_REQUEST_UNDISPATCHED",
                        relay_id=request.relay_id,
                        function_id=request.function_id,
                        breaker_id=request.breaker_id,
                        function=request.function,
                        success=False,
                        reason=reason,
                    )
                )

                results.append(
                    {
                        "relay_id": request.relay_id,
                        "function_id": request.function_id,
                        "breaker_id": request.breaker_id,
                        "function": request.function,
                        "success": False,
                        "error": reason,
                    }
                )

            return tuple(
                results
            )

        trip = getattr(
            self.breaker_manager,
            "trip",
            None,
        )

        if not callable(trip):
            raise TypeError(
                "BreakerManager must provide trip()."
            )

        for request in requests:

            success = bool(
                trip(
                    request.breaker_id,
                    time=request.time,
                    source=request.relay_id,
                    function_id=request.function_id,
                )
            )

            self._events.append(
                ProtectionEvent(
                    time=request.time,
                    event_type="BREAKER_TRIP",
                    relay_id=request.relay_id,
                    function_id=request.function_id,
                    breaker_id=request.breaker_id,
                    function=request.function,
                    success=success,
                    reason=request.reason,
                    metadata=dict(
                        request.metadata
                    ),
                )
            )

            results.append(
                {
                    "relay_id": request.relay_id,
                    "function_id": request.function_id,
                    "breaker_id": request.breaker_id,
                    "function": request.function,
                    "success": success,
                    "error": "",
                }
            )

        return tuple(
            results
        )

    # =================================================================
    # COMPLETE PROTECTION CYCLE
    # =================================================================

    def process(
        self,
        time: float = 0.0,
    ) -> tuple[
        dict[str, Any],
        ...
    ]:
        """
        Execute one protection orchestration cycle.

        Sequence
        --------

        Measurement architecture
                |
                v
        Protection functions
                |
                v
        ProtectionDecision
                |
                v
        TripRequest
                |
                v
        BreakerManager
                |
                v
              Breaker

        ProtectionSystem performs orchestration only.
        """

        simulation_time = self._validate_time(
            time
        )

        decisions = self.evaluate(
            time=simulation_time
        )

        requests = self.trip_requests(
            decisions,
            time=simulation_time,
        )

        return self.operate(
            requests
        )

    # =================================================================
    # RESET
    # =================================================================

    def reset(
        self,
    ) -> None:
        """
        Reset every registered protection-function instance.

        Relay configuration/settings are not modified.

        Measurement state is not modified.

        Breaker state is not modified.
        """

        for registration in (
            self._registrations.values()
        ):

            reset = getattr(
                registration.protection,
                "reset",
                None,
            )

            if callable(reset):
                reset()

        self._events.clear()

    # =================================================================
    # EVENT ACCESS
    # =================================================================

    def clear_events(
        self,
    ) -> None:
        """
        Clear orchestration event history.
        """

        self._events.clear()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def status(
        self,
    ) -> dict[str, Any]:
        """
        Return structured ProtectionSystem diagnostics.

        No Relay or Breaker state is copied into this manager.
        """

        functions: dict[
            str,
            dict[str, Any],
        ] = {}

        relays: dict[
            Any,
            dict[str, Any],
        ] = {}

        for (
            function_id,
            registration,
        ) in self._registrations.items():

            relay = registration.relay
            protection = registration.protection

            status_method = getattr(
                protection,
                "status",
                None,
            )

            if callable(status_method):
                function_status = status_method()
            else:
                function_status = {
                    "function_id": function_id,
                    "relay_id": relay.id,
                }

            functions[
                function_id
            ] = function_status

            relay_entry = relays.setdefault(
                relay.id,
                {
                    "relay_id": relay.id,
                    "relay_type": getattr(
                        relay,
                        "type",
                        None,
                    ),
                    "function_ids": [],
                },
            )

            relay_entry[
                "function_ids"
            ].append(
                function_id
            )

        return {
            "relay_count": len(relays),
            "function_count": len(
                self._registrations
            ),
            "relays": relays,
            "functions": functions,
            "event_count": len(
                self._events
            ),
            "breaker_manager_available": (
                self.breaker_manager is not None
            ),
        }

    # =================================================================
    # SUMMARY
    # =================================================================

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Return the ProtectionSystem diagnostic summary.
        """

        return self.status()

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
        """

        return (
            f"<ProtectionSystem "
            f"relays={len(self.relay_ids)}, "
            f"functions={len(self._registrations)}, "
            f"events={len(self._events)}, "
            f"breaker_manager="
            f"{self.breaker_manager is not None}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ProtectionDecision",
    "TripRequest",
    "ProtectionEvent",
    "ProtectionSystem",
]
```
