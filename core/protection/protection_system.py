"""
GridForge Protection System V2
==============================

File:
    core/protection/protection_system.py

Purpose
-------
Central orchestration layer for GridForge protection.

The ProtectionSystem coordinates:

    Relay
        |
        v
    RelayBase / Protection Function Plugin
        |
        v
    ProtectionDecision
        |
        v
    TripRequest
        |
        v
    BreakerManager

Architecture
------------

    Physical measurement system
            |
            v
    CT / PT / CVT
            |
            v
    MeasurementChannel
            |
            v
    RelayInput
            |
            v
    core/model/relay.py
            |
            v
    core/protection/relay_base.py
            |
            +--------------------------+
            |                          |
            v                          v
    Overcurrent Plugin         Distance Plugin
    Directional Plugin         Differential Plugin
            |                          |
            +------------+-------------+
                         |
                         v
                 ProtectionSystem
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
                    Breaker Model


V2 Responsibilities
--------------------
ProtectionSystem is responsible for:

- registering protection function instances;
- associating protection functions with authoritative Relay devices;
- associating protection functions with controlled breakers;
- verifying protection registration;
- verifying relay operational readiness;
- invoking protection-function evaluation;
- collecting protection decisions;
- generating trip requests;
- optionally dispatching trip requests to BreakerManager;
- recording protection events;
- resetting protection runtime state;
- providing diagnostics.

ProtectionSystem does NOT:

- acquire CT signals;
- acquire PT signals;
- acquire CVT signals;
- perform instrument-transformer conversion;
- create MeasurementChannels;
- calculate measurement values;
- calculate apparent impedance;
- calculate phase angles;
- calculate fault current;
- perform load flow;
- perform short-circuit analysis;
- build Ybus;
- implement overcurrent protection;
- implement IEC inverse curves;
- implement directional protection;
- implement distance protection;
- implement differential protection;
- coordinate relays;
- calculate relay settings;
- own Relay state;
- duplicate MeasurementChannel state;
- own Breaker state;
- modify Network topology;
- operate breakers directly.

Authoritative State
-------------------
The authoritative Relay device remains in:

    core/model/relay.py

Protection algorithms are responsible for interpreting Relay inputs.

ProtectionSystem only orchestrates those algorithms.

The Relay model remains the authoritative owner of:

- relay identity;
- relay type;
- input-channel bindings;
- relay settings;
- service state;
- enabled/blocked state;
- pickup state;
- trip state.

Measurement acquisition and signal transformation remain outside
this module.

Design Principle
----------------
ProtectionSystem is an orchestration boundary, not a protection
calculation engine.

A protection function must already know how to evaluate its
authoritative Relay inputs before it is registered here.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time as wall_clock_time
from typing import Any, Mapping


# =====================================================================
# PROTECTION DECISION
# =====================================================================


@dataclass(frozen=True, slots=True)
class ProtectionDecision:
    """
    Immutable result produced by a protection-function evaluation.

    Parameters
    ----------
    relay_id:
        Authoritative Relay identifier.

    operated:
        True when the protection function has issued an operating
        decision.

    picked_up:
        True when the protection element is in pickup condition.

    function:
        Protection-function identifier.

    reason:
        Optional human-readable operating explanation.

    metadata:
        Optional diagnostic information supplied by the protection
        function.

    Notes
    -----
    This object is a decision DTO.

    It is NOT authoritative relay state.

    The Relay model remains authoritative for persistent relay
    operating state.
    """

    relay_id: Any
    operated: bool
    picked_up: bool
    function: str
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
    Protection-issued request to operate a breaker.

    Parameters
    ----------
    relay_id:
        Relay that generated the protection decision.

    breaker_id:
        Controlled breaker identifier.

    function:
        Protection function that generated the request.

    time:
        Simulation/event time associated with the request.

    reason:
        Optional operating explanation.

    Notes
    -----
    TripRequest does not operate the breaker.

    BreakerManager remains responsible for actual breaker operation.
    """

    relay_id: Any
    breaker_id: Any
    function: str
    time: float
    reason: str = ""


# =====================================================================
# PROTECTION EVENT
# =====================================================================


@dataclass(frozen=True, slots=True)
class ProtectionEvent:
    """
    Immutable protection event record.

    This is an event/history object, not authoritative device state.
    """

    time: float
    event_type: str
    relay_id: Any
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
    Internal registration record.

    This contains references only.

    It does not duplicate Relay state.
    """

    protection: Any
    relay: Any
    breaker_id: Any


# =====================================================================
# PROTECTION SYSTEM
# =====================================================================


class ProtectionSystem:
    """
    Central GridForge V2 protection orchestrator.

    Parameters
    ----------
    breaker_manager:
        Optional BreakerManager responsible for actual breaker
        operation.

    Notes
    -----
    A protection function must be registered against an authoritative
    Relay model.

    The protection function is expected to be a RelayBase-derived
    implementation or a compatible protection plugin.
    """

    # ==============================================================
    # INITIALIZATION
    # ==============================================================

    def __init__(
        self,
        breaker_manager: Any = None,
    ) -> None:

        self.breaker_manager = breaker_manager

        self._registrations: dict[
            Any,
            _ProtectionRegistration,
        ] = {}

        self._events: list[
            ProtectionEvent
        ] = []

    # ==============================================================
    # REGISTRATION
    # ==============================================================

    def register(
        self,
        protection: Any,
        relay: Any,
        breaker_id: Any = None,
    ) -> None:
        """
        Register a protection-function plugin.

        Parameters
        ----------
        protection:
            RelayBase-derived protection implementation.

        relay:
            Authoritative Relay model from core.model.relay.

        breaker_id:
            Optional controlled breaker identifier.

        Raises
        ------
        ValueError
            If registration is invalid or duplicated.

        TypeError
            If the protection plugin does not expose the required
            interface.

        Notes
        -----
        ProtectionSystem stores references only.

        It does not copy Relay state.
        """

        if protection is None:
            raise ValueError(
                "protection cannot be None."
            )

        if relay is None:
            raise ValueError(
                "relay cannot be None."
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

        protection_relay = getattr(
            protection,
            "relay",
            None,
        )

        if protection_relay is not None:
            if protection_relay is not relay:
                raise ValueError(
                    "Protection plugin is bound to a different "
                    "Relay model."
                )

        protection_id = getattr(
            protection,
            "id",
            None,
        )

        if protection_id is not None:
            if protection_id != relay_id:
                raise ValueError(
                    "Protection plugin id does not match "
                    "the authoritative Relay id."
                )

        evaluate = getattr(
            protection,
            "evaluate",
            None,
        )

        if not callable(evaluate):
            raise TypeError(
                "Protection plugin must provide evaluate()."
            )

        if relay_id in self._registrations:
            raise ValueError(
                f"Relay '{relay_id}' is already registered."
            )

        self._registrations[
            relay_id
        ] = _ProtectionRegistration(
            protection=protection,
            relay=relay,
            breaker_id=breaker_id,
        )

    # ==============================================================
    # COMPATIBILITY ALIAS
    # ==============================================================

    def add_relay(
        self,
        protection: Any,
        breaker_id: Any = None,
    ) -> None:
        """
        Compatibility registration method.

        Preferred V2 usage is:

            register(
                protection=...,
                relay=...,
                breaker_id=...,
            )

        This method accepts a RelayBase-derived protection object
        whose authoritative Relay is available through:

            protection.relay
        """

        relay = getattr(
            protection,
            "relay",
            None,
        )

        if relay is None:
            raise TypeError(
                "add_relay() requires a protection plugin exposing "
                "its authoritative Relay through .relay. "
                "Use register() for explicit V2 registration."
            )

        self.register(
            protection=protection,
            relay=relay,
            breaker_id=breaker_id,
        )

    # ==============================================================
    # UNREGISTRATION
    # ==============================================================

    def unregister(
        self,
        relay_id: Any,
    ) -> None:
        """
        Remove a protection registration.

        This does not modify the Relay model.
        """

        self._registrations.pop(
            relay_id,
            None,
        )

    # ==============================================================
    # LOOKUP
    # ==============================================================

    def get(
        self,
        relay_id: Any,
    ) -> Any | None:
        """
        Return the registered protection plugin for a Relay.
        """

        registration = self._registrations.get(
            relay_id
        )

        if registration is None:
            return None

        return registration.protection

    # ==============================================================
    # REGISTRATION INFORMATION
    # ==============================================================

    @property
    def relay_ids(self) -> tuple[Any, ...]:
        """
        Return registered authoritative Relay identifiers.
        """

        return tuple(
            self._registrations.keys()
        )

    @property
    def events(self) -> tuple[ProtectionEvent, ...]:
        """
        Return recorded protection events.

        The returned collection is immutable from the caller's
        perspective.
        """

        return tuple(
            self._events
        )

    # ==============================================================
    # RELAY READINESS
    # ==============================================================

    @staticmethod
    def _relay_operational(
        relay: Any,
    ) -> bool:
        """
        Determine whether an authoritative Relay is operational.

        The Relay owns the operational-state semantics.

        Preferred V2 interface:

            relay.operational

        Fallback compatibility logic is intentionally limited to
        the basic model state and does not create new state.
        """

        operational = getattr(
            relay,
            "operational",
            None,
        )

        if operational is not None:
            return bool(
                operational
            )

        if not bool(
            getattr(
                relay,
                "in_service",
                False,
            )
        ):
            return False

        if not bool(
            getattr(
                relay,
                "enabled",
                True,
            )
        ):
            return False

        if bool(
            getattr(
                relay,
                "blocked",
                False,
            )
        ):
            return False

        required_inputs_available = getattr(
            relay,
            "required_inputs_available",
            None,
        )

        if callable(
            required_inputs_available
        ):
            return bool(
                required_inputs_available()
            )

        return True

    # ==============================================================
    # PROTECTION FUNCTION NAME
    # ==============================================================

    @staticmethod
    def _function_name(
        protection: Any,
    ) -> str:
        """
        Return the protection-function identifier.
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

            if isinstance(
                value,
                str,
            ) and value.strip():

                return value

        return protection.__class__.__name__

    # ==============================================================
    # DECISION NORMALIZATION
    # ==============================================================

    @classmethod
    def _make_decision(
        cls,
        registration: _ProtectionRegistration,
        result: Any,
    ) -> ProtectionDecision:
        """
        Normalize a protection-plugin evaluation result.

        Supported plugin result forms:

            bool

        or:

            ProtectionDecision

        or a mapping containing:

            {
                "operated": bool,
                "picked_up": bool,
                "reason": str,
                "metadata": dict,
            }

        The preferred V2 form is ProtectionDecision.
        """

        relay = registration.relay
        protection = registration.protection

        relay_id = relay.id
        function = cls._function_name(
            protection
        )

        if isinstance(
            result,
            ProtectionDecision,
        ):
            if result.relay_id != relay_id:
                raise ValueError(
                    "ProtectionDecision relay_id does not match "
                    "the registered Relay."
                )

            return result

        if isinstance(
            result,
            bool,
        ):

            picked_up = bool(
                getattr(
                    relay,
                    "picked_up",
                    result,
                )
            )

            operated = bool(
                getattr(
                    relay,
                    "tripped",
                    result,
                )
            )

            return ProtectionDecision(
                relay_id=relay_id,
                operated=operated,
                picked_up=picked_up,
                function=function,
            )

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
                    getattr(
                        relay,
                        "picked_up",
                        False,
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
                    "Protection decision metadata must be a mapping."
                )

            return ProtectionDecision(
                relay_id=relay_id,
                operated=operated,
                picked_up=picked_up,
                function=function,
                reason=reason,
                metadata=dict(metadata),
            )

        raise TypeError(
            "Protection plugin evaluate() must return "
            "ProtectionDecision, bool, or a mapping."
        )

    # ==============================================================
    # SINGLE RELAY EVALUATION
    # ==============================================================

    def evaluate_relay(
        self,
        relay_id: Any,
    ) -> ProtectionDecision:
        """
        Evaluate one registered protection function.

        No raw measurement data is accepted here.

        Measurements must already have passed through:

            CT / PT / CVT
                    |
                    v
            MeasurementChannel
                    |
                    v
                RelayInput
                    |
                    v
                  Relay

        The protection plugin consumes that authoritative input
        state.
        """

        registration = self._registrations.get(
            relay_id
        )

        if registration is None:
            raise KeyError(
                f"Relay '{relay_id}' is not registered."
            )

        relay = registration.relay
        protection = registration.protection

        function = self._function_name(
            protection
        )

        # ----------------------------------------------------------
        # Operational gate
        # ----------------------------------------------------------

        if not self._relay_operational(
            relay
        ):

            clear_trip = getattr(
                relay,
                "set_trip",
                None,
            )

            if callable(clear_trip):
                clear_trip(False)

            return ProtectionDecision(
                relay_id=relay.id,
                operated=False,
                picked_up=bool(
                    getattr(
                        relay,
                        "picked_up",
                        False,
                    )
                ),
                function=function,
                reason="Relay is not operational.",
            )

        # ----------------------------------------------------------
        # Evaluate protection plugin
        # ----------------------------------------------------------

        result = protection.evaluate()

        decision = self._make_decision(
            registration,
            result,
        )

        # ----------------------------------------------------------
        # Protection event
        # ----------------------------------------------------------

        if decision.operated:

            self._events.append(
                ProtectionEvent(
                    time=0.0,
                    event_type="PROTECTION_OPERATE",
                    relay_id=relay.id,
                    breaker_id=registration.breaker_id,
                    function=decision.function,
                    success=None,
                    reason=decision.reason,
                    metadata=dict(
                        decision.metadata
                    ),
                )
            )

        return decision

    # ==============================================================
    # ALL RELAYS
    # ==============================================================

    def evaluate(
        self,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Evaluate all registered protection functions.

        Returns
        -------
        tuple[ProtectionDecision, ...]
            One decision for every registered Relay.

        Notes
        -----
        This method does not:

        - acquire measurements;
        - update measurement channels;
        - calculate protection quantities;
        - operate breakers.
        """

        decisions: list[
            ProtectionDecision
        ] = []

        for relay_id in self._registrations:

            decision = self.evaluate_relay(
                relay_id
            )

            decisions.append(
                decision
            )

        return tuple(
            decisions
        )

    # ==============================================================
    # TRIP REQUEST GENERATION
    # ==============================================================

    def trip_requests(
        self,
        decisions: tuple[
            ProtectionDecision,
            ...
        ] | list[
            ProtectionDecision
        ],
        time: float = 0.0,
    ) -> tuple[TripRequest, ...]:
        """
        Convert protection decisions into breaker trip requests.

        This method does NOT operate breakers.

        Only operated decisions with a registered breaker target
        produce TripRequest objects.
        """

        requests: list[
            TripRequest
        ] = []

        simulation_time = float(
            time
        )

        for decision in decisions:

            if not decision.operated:
                continue

            registration = self._registrations.get(
                decision.relay_id
            )

            if registration is None:
                raise RuntimeError(
                    "Protection decision references an "
                    "unregistered Relay."
                )

            breaker_id = registration.breaker_id

            if breaker_id is None:
                self._events.append(
                    ProtectionEvent(
                        time=simulation_time,
                        event_type="TRIP_REQUEST_REJECTED",
                        relay_id=decision.relay_id,
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
                    breaker_id=breaker_id,
                    function=decision.function,
                    time=simulation_time,
                    reason=decision.reason,
                )
            )

        return tuple(
            requests
        )

    # ==============================================================
    # BREAKER OPERATION
    # ==============================================================

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
        Dispatch TripRequest objects to BreakerManager.

        BreakerManager remains the sole authority for breaker
        operation.

        ProtectionSystem never calls Breaker.open() directly.
        """

        results: list[
            dict[str, Any]
        ] = []

        if requests is None:
            raise ValueError(
                "requests cannot be None."
            )

        if self.breaker_manager is None:

            for request in requests:

                self._events.append(
                    ProtectionEvent(
                        time=request.time,
                        event_type="TRIP_REQUEST_UNDISPATCHED",
                        relay_id=request.relay_id,
                        breaker_id=request.breaker_id,
                        function=request.function,
                        success=False,
                        reason=(
                            "No BreakerManager is configured."
                        ),
                    )
                )

                results.append(
                    {
                        "relay_id": request.relay_id,
                        "breaker_id": request.breaker_id,
                        "function": request.function,
                        "success": False,
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

            try:

                result = trip(
                    request.breaker_id,
                    request.time,
                )

                success = bool(
                    result
                )

                error = ""

            except Exception as exc:

                success = False
                error = str(
                    exc
                )

            self._events.append(
                ProtectionEvent(
                    time=request.time,
                    event_type="BREAKER_TRIP",
                    relay_id=request.relay_id,
                    breaker_id=request.breaker_id,
                    function=request.function,
                    success=success,
                    reason=(
                        error
                        if error
                        else request.reason
                    ),
                )
            )

            results.append(
                {
                    "relay_id": request.relay_id,
                    "breaker_id": request.breaker_id,
                    "function": request.function,
                    "success": success,
                    "error": error,
                }
            )

        return tuple(
            results
        )

    # ==============================================================
    # COMPLETE PROTECTION CYCLE
    # ==============================================================

    def process(
        self,
        time: float = 0.0,
    ) -> tuple[
        dict[str, Any],
        ...
    ]:
        """
        Execute one complete protection orchestration cycle.

        Sequence
        --------
        1. Relay inputs already exist.
        2. Protection plugins evaluate those inputs.
        3. Protection decisions are produced.
        4. Trip requests are generated.
        5. BreakerManager receives trip requests.

        This method deliberately does not acquire measurements.
        """

        decisions = self.evaluate()

        requests = self.trip_requests(
            decisions,
            time=time,
        )

        return self.operate(
            requests
        )

    # ==============================================================
    # RESET
    # ==============================================================

    def reset(
        self,
    ) -> None:
        """
        Reset protection runtime state.

        Relay settings are preserved.

        Measurement acquisition state is not owned by this class.
        """

        for registration in (
            self._registrations.values()
        ):

            protection = registration.protection
            relay = registration.relay

            protection_reset = getattr(
                protection,
                "reset",
                None,
            )

            if callable(
                protection_reset
            ):
                protection_reset()

            elif protection is not relay:

                relay_reset = getattr(
                    relay,
                    "reset",
                    None,
                )

                if callable(
                    relay_reset
                ):
                    relay_reset()

        self._events.clear()

    # ==============================================================
    # DIAGNOSTICS
    # ==============================================================

    def status(
        self,
    ) -> dict[str, Any]:
        """
        Return structured protection-system diagnostics.

        No authoritative device state is copied into the system.
        """

        registrations: dict[
            Any,
            dict[str, Any]
        ] = {}

        for relay_id, registration in (
            self._registrations.items()
        ):

            relay = registration.relay
            protection = registration.protection

            registrations[
                relay_id
            ] = {
                "relay_id": relay_id,
                "relay_type": getattr(
                    relay,
                    "type",
                    None,
                ),
                "function": self._function_name(
                    protection
                ),
                "breaker_id": registration.breaker_id,
                "in_service": bool(
                    getattr(
                        relay,
                        "in_service",
                        False,
                    )
                ),
                "enabled": bool(
                    getattr(
                        relay,
                        "enabled",
                        True,
                    )
                ),
                "blocked": bool(
                    getattr(
                        relay,
                        "blocked",
                        False,
                    )
                ),
                "operational": self._relay_operational(
                    relay
                ),
                "picked_up": bool(
                    getattr(
                        relay,
                        "picked_up",
                        False,
                    )
                ),
                "tripped": bool(
                    getattr(
                        relay,
                        "tripped",
                        False,
                    )
                ),
            }

        return {
            "relay_count": len(
                self._registrations
            ),
            "relays": registrations,
            "event_count": len(
                self._events
            ),
            "breaker_manager_available": (
                self.breaker_manager is not None
            ),
        }

    # ==============================================================
    # SUMMARY
    # ==============================================================

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Return the protection-system summary.

        Alias for status().
        """

        return self.status()


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
