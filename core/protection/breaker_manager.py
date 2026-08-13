"""
GridForge V2 Protection System
==============================

File
----
core/protection/breaker_manager.py

Purpose
-------
Protection/control-layer manager for circuit breakers.

The BreakerManager provides the command boundary between the
protection/control system and the authoritative physical Breaker
model.

Architecture
------------

    ProtectionSystem
           |
           | trip / close command
           v
    BreakerManager
           |
           | Breaker.open()
           | Breaker.close()
           v
    core/model/breaker.py
           |
           v
    Authoritative physical breaker state


Authority Boundary
------------------

    core/model/breaker.py
        |
        +-- physical breaker identity
        +-- physical breaker state
        +-- physical switching operation
        |
        v
    BreakerManager
        |
        +-- command validation
        +-- command dispatch
        +-- protection/control event history
        +-- state queries
        |
        v
    ProtectionSystem


Important V2 Rules
------------------

BreakerManager:

* references authoritative Breaker objects;
* delegates physical switching exclusively to Breaker.open()
  and Breaker.close();
* derives physical state from the authoritative Breaker;
* records protection/control-layer command events;
* does not own physical breaker state;
* does not maintain a simulation clock;
* does not schedule simulation events;
* does not evaluate protection functions;
* does not calculate fault quantities;
* does not manipulate MeasurementChannel objects;
* does not modify network topology;
* does not directly manipulate Breaker internal state.

An unknown breaker identifier is a configuration/reference error.

It is therefore never interpreted as:

    closed
    open
    failed


Physical Breaker Contract
-------------------------

The authoritative V2 Breaker model provides:

    breaker.id
    breaker.is_closed
    breaker.is_open
    breaker.is_failed

and:

    breaker.open()
    breaker.close()

The physical open()/close() methods take no arguments and return
None.

Therefore command success is determined from the authoritative
post-operation physical state rather than from the return value of
open()/close().

BreakerManager does not pass simulation time to the physical
Breaker.

Simulation time belongs to the simulation/event layer.


Event Boundary
--------------

The physical Breaker owns physical equipment state.

BreakerManager owns protection/control command history.

Therefore:

    Breaker
        = authoritative physical equipment state

    BreakerManager.events
        = protection/control command history


Event semantics
---------------

A successful TRIP event means:

    the manager issued Breaker.open()
    and the authoritative breaker state is open afterward.

A successful CLOSE event means:

    the manager issued Breaker.close()
    and the authoritative breaker state is closed afterward.

An exception raised by the physical Breaker operation is propagated
to the caller and is not converted into a successful command event.

Event history is manager-owned diagnostic/control history and is not
the authoritative physical equipment history.


Reset
-----

BreakerManager.reset() clears manager-owned command history only.

It does not reset physical Breaker state.

The authoritative V2 Breaker model does not expose reset(), and the
manager therefore does not invent or emulate a physical reset
operation.


Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from copy import deepcopy
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping

from core.model.breaker import Breaker


class BreakerManager:
    """
    GridForge V2 protection/control-layer breaker manager.

    The authoritative physical breaker remains the
    ``core.model.breaker.Breaker`` instance.

    BreakerManager owns only:

    * breaker registration;
    * command dispatch;
    * command-event history;
    * authoritative state queries;
    * manager diagnostics.

    Physical breaker state is never duplicated here.
    """

    # =================================================================
    # EVENT CONTRACT
    # =================================================================

    _TRIP_ACTION = "TRIP"
    _CLOSE_ACTION = "CLOSE"

    _VALID_ACTIONS = frozenset(
        {
            _TRIP_ACTION,
            _CLOSE_ACTION,
        }
    )

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(self) -> None:
        """
        Create an empty BreakerManager.
        """

        self._breakers: dict[str, Breaker] = {}
        self._events: list[dict[str, Any]] = {}

        # Correct the intentionally explicit internal type below.
        self._events = []

    # =================================================================
    # REGISTRATION
    # =================================================================

    def add_breaker(
        self,
        breaker: Breaker,
    ) -> None:
        """
        Register an authoritative physical Breaker.

        The Breaker object itself remains externally owned.

        Raises
        ------
        TypeError
            If ``breaker`` is not a Breaker.

        ValueError
            If the breaker identifier is invalid or already registered.
        """

        if not isinstance(
            breaker,
            Breaker,
        ):
            raise TypeError(
                "breaker must be an instance of "
                "core.model.breaker.Breaker."
            )

        breaker_id = self._normalize_id(
            breaker.id,
            argument="breaker.id",
        )

        if breaker_id in self._breakers:
            raise ValueError(
                f"Breaker already exists: {breaker_id}"
            )

        self._breakers[breaker_id] = breaker

    # -----------------------------------------------------------------

    register = add_breaker

    # =================================================================
    # REMOVAL
    # =================================================================

    def remove_breaker(
        self,
        breaker_id: str,
    ) -> Breaker:
        """
        Remove and return a registered Breaker.

        Removing a breaker does not modify the physical Breaker.

        Raises
        ------
        KeyError
            If the breaker is not registered.
        """

        normalized_id = self._normalize_id(
            breaker_id,
            argument="breaker_id",
        )

        breaker = self._require_breaker(
            normalized_id
        )

        del self._breakers[normalized_id]

        return breaker

    # =================================================================
    # LOOKUP
    # =================================================================

    def get_breaker(
        self,
        breaker_id: str,
    ) -> Breaker | None:
        """
        Return a registered authoritative Breaker.

        Returns None when the identifier is not registered.

        Raises
        ------
        TypeError
            If ``breaker_id`` is not a string.

        ValueError
            If ``breaker_id`` is empty or whitespace.
        """

        normalized_id = self._normalize_id(
            breaker_id,
            argument="breaker_id",
        )

        return self._breakers.get(
            normalized_id
        )

    # -----------------------------------------------------------------

    def has_breaker(
        self,
        breaker_id: str,
    ) -> bool:
        """
        Return True when a breaker is registered.
        """

        normalized_id = self._normalize_id(
            breaker_id,
            argument="breaker_id",
        )

        return normalized_id in self._breakers

    # =================================================================
    # REQUIRED LOOKUP
    # =================================================================

    def _require_breaker(
        self,
        breaker_id: str,
    ) -> Breaker:
        """
        Return a registered Breaker.

        Raises
        ------
        KeyError
            If the breaker is not registered.
        """

        normalized_id = self._normalize_id(
            breaker_id,
            argument="breaker_id",
        )

        breaker = self._breakers.get(
            normalized_id
        )

        if breaker is None:
            raise KeyError(
                f"Breaker not found: {normalized_id}"
            )

        return breaker

    # =================================================================
    # IDENTIFIER VALIDATION
    # =================================================================

    @staticmethod
    def _normalize_id(
        value: Any,
        *,
        argument: str,
    ) -> str:
        """
        Validate and normalize a breaker identifier.

        BreakerManager uses the same semantic identity represented by
        the authoritative Breaker model.

        No identifier is silently converted from another type.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{argument} must be a string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{argument} cannot be empty."
            )

        return normalized

    # =================================================================
    # TIME VALIDATION
    # =================================================================

    @staticmethod
    def _validate_time(
        time: float,
    ) -> float:
        """
        Validate manager-level command/event time.

        Time is event metadata only.

        It is never passed to Breaker.open() or Breaker.close().
        """

        if isinstance(
            time,
            bool,
        ):
            raise TypeError(
                "Breaker operation time must be numeric."
            )

        try:
            value = float(
                time
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise TypeError(
                "Breaker operation time must be numeric."
            ) from exc

        if not isfinite(value):
            raise ValueError(
                "Breaker operation time must be finite."
            )

        return value

    # =================================================================
    # SOURCE NORMALIZATION
    # =================================================================

    @staticmethod
    def _normalize_source(
        source: Any,
    ) -> Any:
        """
        Normalize a command source for event history.

        Objects exposing an ``id`` are represented by that identifier.
        Primitive diagnostic values are retained.

        The manager does not create a second authoritative identity.
        """

        if source is None:
            return None

        if isinstance(
            source,
            (str, int, float, bool),
        ):
            return source

        source_id = getattr(
            source,
            "id",
            None,
        )

        if source_id is not None:
            return source_id

        return str(
            source
        )

    # =================================================================
    # PHYSICAL RESULT VERIFICATION
    # =================================================================

    @staticmethod
    def _verify_trip(
        breaker: Breaker,
    ) -> bool:
        """
        Determine trip success from authoritative Breaker state.
        """

        return bool(
            breaker.is_open
        )

    # -----------------------------------------------------------------

    @staticmethod
    def _verify_close(
        breaker: Breaker,
    ) -> bool:
        """
        Determine close success from authoritative Breaker state.
        """

        return bool(
            breaker.is_closed
        )

    # =================================================================
    # TRIP
    # =================================================================

    def trip(
        self,
        breaker_id: str,
        time: float = 0.0,
        source: Any = None,
    ) -> bool:
        """
        Execute a breaker trip command.

        The physical operation is delegated exclusively to:

            Breaker.open()

        The return value is derived from the authoritative
        post-operation Breaker state.

        Raises
        ------
        KeyError
            If the breaker is not registered.

        TypeError / ValueError
            If the identifier or event time is invalid.

        Exception
            Any exception raised by Breaker.open() is propagated.
        """

        normalized_id = self._normalize_id(
            breaker_id,
            argument="breaker_id",
        )

        event_time = self._validate_time(
            time
        )

        breaker = self._require_breaker(
            normalized_id
        )

        # -------------------------------------------------------------
        # Physical operation
        # -------------------------------------------------------------

        breaker.open()

        # -------------------------------------------------------------
        # Authoritative post-operation state
        # -------------------------------------------------------------

        success = self._verify_trip(
            breaker
        )

        # -------------------------------------------------------------
        # Protection/control event
        # -------------------------------------------------------------

        self._record_event(
            time=event_time,
            breaker_id=normalized_id,
            action=self._TRIP_ACTION,
            success=success,
            source=source,
        )

        return success

    # =================================================================
    # CLOSE
    # =================================================================

    def close(
        self,
        breaker_id: str,
        time: float = 0.0,
        source: Any = None,
    ) -> bool:
        """
        Execute a breaker close command.

        The physical operation is delegated exclusively to:

            Breaker.close()

        The return value is derived from the authoritative
        post-operation Breaker state.

        Raises
        ------
        KeyError
            If the breaker is not registered.

        TypeError / ValueError
            If the identifier or event time is invalid.

        Exception
            Any exception raised by Breaker.close() is propagated.
        """

        normalized_id = self._normalize_id(
            breaker_id,
            argument="breaker_id",
        )

        event_time = self._validate_time(
            time
        )

        breaker = self._require_breaker(
            normalized_id
        )

        # -------------------------------------------------------------
        # Physical operation
        # -------------------------------------------------------------

        breaker.close()

        # -------------------------------------------------------------
        # Authoritative post-operation state
        # -------------------------------------------------------------

        success = self._verify_close(
            breaker
        )

        # -------------------------------------------------------------
        # Protection/control event
        # -------------------------------------------------------------

        self._record_event(
            time=event_time,
            breaker_id=normalized_id,
            action=self._CLOSE_ACTION,
            success=success,
            source=source,
        )

        return success

    # =================================================================
    # AUTHORITATIVE STATE
    # =================================================================

    def is_closed(
        self,
        breaker_id: str,
    ) -> bool:
        """
        Return the authoritative physical closed state.

        Unknown breaker identifiers raise KeyError.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        return bool(
            breaker.is_closed
        )

    # -----------------------------------------------------------------

    def is_open(
        self,
        breaker_id: str,
    ) -> bool:
        """
        Return the authoritative physical open state.

        Unknown breaker identifiers raise KeyError.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        return bool(
            breaker.is_open
        )

    # -----------------------------------------------------------------

    def is_failed(
        self,
        breaker_id: str,
    ) -> bool:
        """
        Return the authoritative physical failure state.

        Unknown breaker identifiers raise KeyError.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        return bool(
            breaker.is_failed
        )

    # =================================================================
    # STATUS
    # =================================================================

    def get_status(
        self,
        breaker_id: str,
    ) -> dict[str, Any]:
        """
        Return a structured authoritative Breaker status snapshot.

        This method does not expose manager-owned mutable state.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        return {
            "id": breaker.id,
            "closed": bool(
                breaker.is_closed
            ),
            "open": bool(
                breaker.is_open
            ),
            "failed": bool(
                breaker.is_failed
            ),
        }

    # =================================================================
    # ALL STATUS
    # =================================================================

    def get_all_status(
        self,
    ) -> dict[str, dict[str, Any]]:
        """
        Return status snapshots for all registered breakers.

        Returned structures are detached from manager-owned state.
        """

        return {
            breaker_id: {
                "id": breaker.id,
                "closed": bool(
                    breaker.is_closed
                ),
                "open": bool(
                    breaker.is_open
                ),
                "failed": bool(
                    breaker.is_failed
                ),
            }
            for breaker_id, breaker
            in self._breakers.items()
        }

    # =================================================================
    # EVENT LOGGING
    # =================================================================

    def _record_event(
        self,
        *,
        time: float,
        breaker_id: str,
        action: str,
        success: bool,
        source: Any = None,
    ) -> None:
        """
        Record one protection/control command event.

        This is manager-owned event history and is not physical
        Breaker state.
        """

        normalized_id = self._normalize_id(
            breaker_id,
            argument="breaker_id",
        )

        if action not in self._VALID_ACTIONS:
            raise ValueError(
                f"Unsupported breaker command action: {action!r}"
            )

        event_time = self._validate_time(
            time
        )

        event: dict[str, Any] = {
            "time": event_time,
            "breaker": normalized_id,
            "action": action,
            "success": bool(
                success
            ),
        }

        normalized_source = self._normalize_source(
            source
        )

        if normalized_source is not None:
            event["source"] = normalized_source

        self._events.append(
            event
        )

    # =================================================================
    # EVENT ACCESS
    # =================================================================

    def get_events(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return a detached copy of manager event history.

        The returned data cannot mutate the internal event records.

        Deep copying also protects nested mutable event values.
        """

        return deepcopy(
            self._events
        )

    # -----------------------------------------------------------------

    @property
    def events(
        self,
    ) -> tuple[Mapping[str, Any], ...]:
        """
        Return a read-only diagnostic view of command events.

        Event history remains manager-owned.
        """

        return tuple(
            MappingProxyType(
                deepcopy(event)
            )
            for event in self._events
        )

    # =================================================================
    # BREAKER REGISTRY ACCESS
    # =================================================================

    @property
    def breakers(
        self,
    ) -> Mapping[str, Breaker]:
        """
        Return a read-only view of the registered Breaker registry.

        The Breaker objects themselves remain authoritative physical
        objects; this property prevents external replacement or
        deletion of registry entries.
        """

        return MappingProxyType(
            self._breakers
        )

    # =================================================================
    # EVENT CLEAR
    # =================================================================

    def clear_events(self) -> None:
        """
        Clear protection/control command history.

        Physical Breaker state is unaffected.
        """

        self._events.clear()

    # =================================================================
    # RESET
    # =================================================================

    def reset(self) -> None:
        """
        Reset manager-owned runtime history.

        Physical Breaker state is deliberately unchanged.

        The authoritative V2 Breaker model does not provide a reset()
        operation, so BreakerManager does not invent one.
        """

        self._events.clear()

    # =================================================================
    # SUMMARY
    # =================================================================

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Return structured BreakerManager diagnostics.

        The returned structure is detached from manager-owned state.
        """

        return {
            "breaker_count": len(
                self._breakers
            ),
            "breakers": self.get_all_status(),
            "event_count": len(
                self._events
            ),
            "events": self.get_events(),
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<BreakerManager "
            f"breakers={len(self._breakers)}, "
            f"events={len(self._events)}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "BreakerManager",
]
