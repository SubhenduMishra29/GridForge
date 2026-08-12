```python
"""
GridForge Protection System
===========================

File:
    core/protection/protection_system.py

Purpose
-------
Central orchestration boundary for GridForge protection.

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
        Relay / RelayInput
            |
            v
    Protection Function Plugin
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


GridForge V2 Authority Boundary
--------------------------------

core/model/relay.py
    Authoritative Relay device state.

core/model/ct.py
core/model/pt.py
core/model/cvt.py
core/model/measurement_channel.py
    Measurement equipment and measurement-domain state.

core/protection/relay_base.py
    Protection-function plugin contract.

core/protection/<function>.py
    Protection-function implementations.

core/protection/protection_system.py
    Protection orchestration only.

core/protection/breaker_manager.py
    Breaker command boundary.

core/model/breaker.py
    Authoritative physical breaker state.

Responsibilities
----------------
ProtectionSystem:

- register protection-function plugins;
- associate plugins with authoritative Relay models;
- associate plugins with controlled breakers;
- validate protection registration;
- invoke protection-function evaluation;
- normalize protection decisions;
- generate TripRequest objects;
- dispatch TripRequest objects to BreakerManager;
- record protection/control orchestration events;
- reset protection runtime state;
- provide diagnostics.

ProtectionSystem does NOT:

- acquire CT signals;
- acquire PT signals;
- acquire CVT signals;
- transform instrument-transformer signals;
- create MeasurementChannel objects;
- calculate measurements;
- calculate impedance;
- calculate phase angles;
- calculate fault current;
- perform load flow;
- perform short-circuit analysis;
- build Y-bus;
- implement overcurrent protection;
- implement inverse-time curves;
- implement directional protection;
- implement distance protection;
- implement differential protection;
- coordinate protection functions;
- calculate relay settings;
- own Relay state;
- duplicate MeasurementChannel state;
- own Breaker state;
- directly call Breaker.open() or Breaker.close();
- modify Network topology;
- schedule simulation events.

Design Principle
----------------
ProtectionSystem is an orchestration boundary.

A protection function must already know how to interpret its
authoritative Relay inputs before it is registered here.

The system never becomes a second protection algorithm.

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
    Immutable result of a protection-function evaluation.

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
        Optional operating explanation.

    metadata:
        Optional diagnostic information supplied by the protection
        function.

    Notes
    -----
    This is a decision DTO.

    It is not authoritative Relay state.
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
    Immutable protection request to operate a breaker.

    Parameters
    ----------
    relay_id:
        Relay that generated the request.

    breaker_id:
        Controlled breaker identifier.

    function:
        Protection function that generated the request.

    time:
        Simulation/event time in seconds.

    reason:
        Optional operating explanation.

    Notes
    -----
    TripRequest does not operate the breaker.

    BreakerManager remains the sole protection-layer command
    boundary for physical breaker operation.
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
    Immutable protection/control orchestration event.

    This is history/diagnostic information.

    It is not authoritative device state.
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
    Internal protection registration.

    References are stored only.

    Relay and Breaker state are never duplicated here.
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

    The authoritative Relay model is supplied explicitly during
    registration.

    The protection plugin interprets Relay inputs.

    BreakerManager performs actual breaker commands.
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
            Any,
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
        relay: Any,
        breaker_id: Any = None,
    ) -> None:
        """
        Register a protection-function plugin against an
        authoritative Relay.

        Parameters
        ----------
        protection:
            RelayBase-derived protection function or compatible
            protection plugin.

        relay:
            Authoritative Relay model from core.model.relay.

        breaker_id:
            Optional controlled breaker identifier.

        Raises
        ------
        ValueError
            Invalid or duplicate registration.

        TypeError
            Protection plugin does not provide the required
            interface.

        Notes
        -----
        This method stores references only.

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

        # -------------------------------------------------------------
        # Relay identity
        # -------------------------------------------------------------

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

        if relay_id in self._registrations:
            raise ValueError(
                f"Relay '{relay_id}' is already registered."
            )

        # -------------------------------------------------------------
        # Protection-plugin identity
        # -------------------------------------------------------------

        protection_relay = getattr(
            protection,
            "relay",
            None,
        )

        if protection_relay is not None:
            if protection_relay is not relay:
                raise ValueError(
                    "Protection plugin is bound to a different "
                    "authoritative Relay model."
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
                "Protection plugin must provide evaluate()."
            )

        # -------------------------------------------------------------
        # Breaker reference
        # -------------------------------------------------------------

        if breaker_id is not None:

            if (
                self.breaker_manager is not None
                and hasattr(
                    self.breaker_manager,
                    "has_breaker",
                )
            ):

                if not self.breaker_manager.has_breaker(
                    breaker_id
                ):
                    raise KeyError(
                        f"Breaker '{breaker_id}' is not "
                        "registered with BreakerManager."
                    )

        self._registrations[
            relay_id
        ] = _ProtectionRegistration(
            protection=protection,
            relay=relay,
            breaker_id=breaker_id,
        )

    # =================================================================
    # COMPATIBILITY REGISTRATION
    # =================================================================

    def add_relay(
        self,
        protection: Any,
        breaker_id: Any = None,
    ) -> None:
        """
        Compatibility registration method.

        Preferred V2 form:

            register(
                protection=...,
                relay=...,
                breaker_id=...,
            )

        This method obtains the authoritative Relay from:

            protection.relay
        """

        relay = getattr(
            protection,
            "relay",
            None,
        )

        if relay is None:
            raise TypeError(
                "add_relay() requires a protection plugin "
                "exposing its authoritative Relay through "
                ".relay. Use register() for explicit V2 "
                "registration."
            )

        self.register(
            protection=protection,
            relay=relay,
            breaker_id=breaker_id,
        )

    # =================================================================
    # UNREGISTRATION
    # =================================================================

    def unregister(
        self,
        relay_id: Any,
    ) -> None:
        """
        Remove a protection registration.

        The authoritative Relay is not modified.
        """

        self._registrations.pop(
            relay_id,
            None,
        )

    # =================================================================
    # LOOKUP
    # =================================================================

    def get(
        self,
        relay_id: Any,
    ) -> Any | None:
        """
        Return the registered protection plugin.

        Returns None when the Relay is not registered.
        """

        registration = self._registrations.get(
            relay_id
        )

        if registration is None:
            return None

        return registration.protection

    # =================================================================
    # REGISTRATION INFORMATION
    # =================================================================

    @property
    def relay_ids(self) -> tuple[Any, ...]:
        """
        Return registered Relay identifiers.
        """

        return tuple(
            self._registrations.keys()
        )

    @property
    def events(self) -> tuple[ProtectionEvent, ...]:
        """
        Return protection events.

        The returned tuple cannot modify the internal event
        collection.
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
    # RELAY OPERATIONAL STATE
    # =================================================================

    @staticmethod
    def _relay_operational(
        relay: Any,
    ) -> bool:
        """
        Determine whether an authoritative Relay is operational.

        Preferred V2 interface:

            relay.operational

        The Relay model owns the meaning of this state.

        A limited compatibility fallback is retained for older
        Relay implementations.
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

        in_service = getattr(
            relay,
            "in_service",
            True,
        )

        if not bool(in_service):
            return False

        enabled = getattr(
            relay,
            "enabled",
            True,
        )

        if not bool(enabled):
            return False

        blocked = getattr(
            relay,
            "blocked",
            False,
        )

        if bool(blocked):
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

    # =================================================================
    # FUNCTION IDENTIFICATION
    # =================================================================

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
    ) -> ProtectionDecision:
        """
        Normalize a protection-function result.

        Preferred result:

            ProtectionDecision

        Compatibility forms:

            bool

        or:

            {
                "operated": bool,
                "picked_up": bool,
                "reason": str,
                "metadata": mapping,
            }

        The normalization layer does not create persistent Relay
        state.
        """

        relay = registration.relay
        protection = registration.protection

        relay_id = relay.id
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

            return result

        # -------------------------------------------------------------
        # Boolean compatibility result
        # -------------------------------------------------------------

        if isinstance(
            result,
            bool,
        ):

            return ProtectionDecision(
                relay_id=relay_id,
                operated=result,
                picked_up=result,
                function=function,
            )

        # -------------------------------------------------------------
        # Mapping compatibility result
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

    # =================================================================
    # SINGLE RELAY EVALUATION
    # =================================================================

    def evaluate_relay(
        self,
        relay_id: Any,
        time: float = 0.0,
    ) -> ProtectionDecision:
        """
        Evaluate one registered protection function.

        No raw measurement data is accepted.

        The protection plugin consumes authoritative Relay inputs.

        Parameters
        ----------
        relay_id:
            Registered Relay identifier.

        time:
            Simulation/event time used for protection events.

        Returns
        -------
        ProtectionDecision
        """

        simulation_time = self._validate_time(
            time
        )

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

        # -------------------------------------------------------------
        # Operational gate
        # -------------------------------------------------------------

        if not self._relay_operational(
            relay
        ):

            decision = ProtectionDecision(
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

            self._events.append(
                ProtectionEvent(
                    time=simulation_time,
                    event_type="PROTECTION_BLOCKED",
                    relay_id=relay.id,
                    breaker_id=registration.breaker_id,
                    function=function,
                    success=False,
                    reason=decision.reason,
                )
            )

            return decision

        # -------------------------------------------------------------
        # Protection plugin evaluation
        # -------------------------------------------------------------

        result = protection.evaluate()

        decision = self._make_decision(
            registration,
            result,
        )

        # -------------------------------------------------------------
        # Operating event
        # -------------------------------------------------------------

        if decision.operated:

            self._events.append(
                ProtectionEvent(
                    time=simulation_time,
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

    # =================================================================
    # ALL RELAYS
    # =================================================================

    def evaluate(
        self,
        time: float = 0.0,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Evaluate all registered protection functions.

        No measurement acquisition or calculation is performed.
        """

        simulation_time = self._validate_time(
            time
        )

        decisions: list[
            ProtectionDecision
        ] = []

        for relay_id in self._registrations:

            decisions.append(
                self.evaluate_relay(
                    relay_id,
                    time=simulation_time,
                )
            )

        return tuple(
            decisions
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
        Convert operated protection decisions into TripRequests.

        This method never operates breakers.

        Parameters
        ----------
        decisions:
            Protection decisions.

        time:
            Optional explicit command time.

            When omitted, the caller-supplied decision-cycle time
            is expected to have already been encoded by the caller.
            For deterministic operation, passing an explicit time
            is recommended.
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

                event_time = (
                    simulation_time
                    if simulation_time is not None
                    else 0.0
                )

                self._events.append(
                    ProtectionEvent(
                        time=event_time,
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

            request_time = (
                simulation_time
                if simulation_time is not None
                else 0.0
            )

            requests.append(
                TripRequest(
                    relay_id=decision.relay_id,
                    breaker_id=breaker_id,
                    function=decision.function,
                    time=request_time,
                    reason=decision.reason,
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

        BreakerManager remains the sole command boundary.
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
                        "error": (
                            "No BreakerManager is configured."
                        ),
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

            # ---------------------------------------------------------
            # Preserve command provenance.
            # ---------------------------------------------------------

            success = bool(
                trip(
                    request.breaker_id,
                    time=request.time,
                    source=request.relay_id,
                )
            )

            self._events.append(
                ProtectionEvent(
                    time=request.time,
                    event_type="BREAKER_TRIP",
                    relay_id=request.relay_id,
                    breaker_id=request.breaker_id,
                    function=request.function,
                    success=success,
                    reason=request.reason,
                )
            )

            results.append(
                {
                    "relay_id": request.relay_id,
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

            authoritative Relay inputs
                    |
                    v
            protection plugins
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

        This method performs no measurement acquisition and no
        protection calculation.
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
        Reset protection runtime state.

        Protection settings are not modified.

        Measurement state is not modified.

        Breaker state is not modified.
        """

        for registration in (
            self._registrations.values()
        ):

            protection = registration.protection

            reset = getattr(
                protection,
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
        Clear ProtectionSystem event history.

        Device state is unaffected.
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

        No Relay or Breaker state is copied into the manager.
        """

        registrations: dict[
            Any,
            dict[str, Any],
        ] = {}

        for (
            relay_id,
            registration,
        ) in self._registrations.items():

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
                "operational": self._relay_operational(
                    relay
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
        Return a concise developer-facing representation.
        """

        return (
            f"<ProtectionSystem "
            f"relays={len(self._registrations)}, "
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
