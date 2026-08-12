"""
GridForge Protection System
===========================

File:
    core/protection/breaker_manager.py

Purpose
-------
Protection/control-layer manager for circuit breakers.

The BreakerManager provides the command boundary between the
protection system and the authoritative physical Breaker model.

Architecture
------------

    ProtectionSystem
           |
           | Trip / Close command
           v
    BreakerManager
           |
           | breaker.open()
           | breaker.close()
           v
    core/model/breaker.py
           |
           v
    Physical breaker state


Responsibilities
----------------
- Register authoritative Breaker models.
- Remove registered breakers.
- Retrieve registered breakers.
- Validate breaker command references.
- Execute trip commands.
- Execute close commands.
- Query breaker state.
- Record protection/control-layer events.
- Provide manager status.
- Delegate physical operations to Breaker.

The BreakerManager does NOT:
- Detect faults.
- Calculate fault current.
- Evaluate relays.
- Calculate relay operating time.
- Coordinate protection functions.
- Process CT/PT/CVT signals.
- Manage MeasurementChannel objects.
- Modify electrical topology.
- Build Y-bus.
- Modify solver state.
- Directly manipulate Breaker internal state.
- Replace the authoritative Breaker model.

Authority Boundary
------------------

    core/model/breaker.py
        |
        +-- physical state
        +-- physical switching operation
        +-- breaker history
        |
        v
    core/protection/breaker_manager.py
        |
        +-- command dispatch
        +-- protection/control event recording
        |
        v
    core/protection/protection_system.py


Event Boundary
--------------

The physical Breaker owns physical switching history.

The BreakerManager owns protection/control-layer command events.

Therefore:

    Breaker.history
        = physical equipment history

    BreakerManager.events
        = protection/control command history


GridForge V2 Contract
---------------------

Unknown breaker identifiers are configuration/reference errors.

They must NOT be interpreted as:

    closed
    open
    failed

A missing breaker raises KeyError.

The manager never silently creates breakers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from math import isfinite
from typing import Any, Dict, List, Optional

from core.model.breaker import Breaker


class BreakerManager:
    """
    GridForge V2 protection/control-layer breaker manager.

    The authoritative physical breaker object remains the
    ``core.model.breaker.Breaker`` instance.

    BreakerManager only provides the command and management
    boundary required by the protection/control layer.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(self) -> None:
        """
        Create an empty BreakerManager.
        """

        self.breakers: Dict[Any, Breaker] = {}

        self.events: List[Dict[str, Any]] = []

    # =============================================================
    # REGISTRATION
    # =============================================================

    def add_breaker(
        self,
        breaker: Breaker,
    ) -> None:
        """
        Register an authoritative Breaker model.

        Parameters
        ----------
        breaker:
            Instance of ``core.model.breaker.Breaker``.

        Raises
        ------
        TypeError
            If ``breaker`` is not a Breaker.

        ValueError
            If a breaker with the same identifier is already
            registered.
        """

        if not isinstance(breaker, Breaker):
            raise TypeError(
                "breaker must be an instance of "
                "core.model.breaker.Breaker."
            )

        breaker_id = breaker.id

        if breaker_id in self.breakers:
            raise ValueError(
                f"Breaker already exists: {breaker_id}"
            )

        self.breakers[breaker_id] = breaker

    # =============================================================
    # REGISTRATION ALIAS
    # =============================================================

    register = add_breaker

    # =============================================================
    # REMOVAL
    # =============================================================

    def remove_breaker(
        self,
        breaker_id: Any,
    ) -> Breaker:
        """
        Remove and return a registered breaker.

        Parameters
        ----------
        breaker_id:
            Breaker identifier.

        Returns
        -------
        Breaker
            Removed authoritative Breaker.

        Raises
        ------
        KeyError
            If the breaker is not registered.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        del self.breakers[breaker_id]

        return breaker

    # =============================================================
    # LOOKUP
    # =============================================================

    def get_breaker(
        self,
        breaker_id: Any,
    ) -> Optional[Breaker]:
        """
        Return a registered Breaker.

        Returns
        -------
        Breaker or None
            The authoritative Breaker when registered.
        """

        return self.breakers.get(
            breaker_id
        )

    # -------------------------------------------------------------

    def has_breaker(
        self,
        breaker_id: Any,
    ) -> bool:
        """
        Return True when a breaker is registered.
        """

        return breaker_id in self.breakers

    # =============================================================
    # INTERNAL LOOKUP
    # =============================================================

    def _require_breaker(
        self,
        breaker_id: Any,
    ) -> Breaker:
        """
        Return a registered Breaker.

        Raises
        ------
        KeyError
            If the breaker does not exist.
        """

        breaker = self.get_breaker(
            breaker_id
        )

        if breaker is None:
            raise KeyError(
                f"Breaker not found: {breaker_id}"
            )

        return breaker

    # =============================================================
    # TIME VALIDATION
    # =============================================================

    @staticmethod
    def _validate_time(
        time: float,
    ) -> float:
        """
        Validate and normalize event/simulation time.
        """

        time = float(time)

        if not isfinite(time):
            raise ValueError(
                "Breaker operation time must be finite."
            )

        return time

    # =============================================================
    # TRIP
    # =============================================================

    def trip(
        self,
        breaker_id: Any,
        time: float = 0.0,
        source: Any = None,
    ) -> bool:
        """
        Execute a breaker trip command.

        The physical operation is delegated exclusively to:

            Breaker.open(time)

        Parameters
        ----------
        breaker_id:
            Registered breaker identifier.

        time:
            Event/simulation time in seconds.

        source:
            Optional source identifier for the command.

            Typical value:

                relay_id

            This is event metadata only. The manager does not
            interpret the source.

        Returns
        -------
        bool
            Result returned by ``Breaker.open()``.

        Raises
        ------
        KeyError
            If the breaker is not registered.

        ValueError
            If time is invalid.

        Notes
        -----
        BreakerManager never directly changes physical breaker
        state.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        time = self._validate_time(
            time
        )

        result = breaker.open(
            time=time
        )

        success = bool(
            result
        )

        self._record_event(
            time=time,
            breaker_id=breaker_id,
            action="TRIP",
            success=success,
            source=source,
        )

        return success

    # =============================================================
    # CLOSE
    # =============================================================

    def close(
        self,
        breaker_id: Any,
        time: float = 0.0,
        source: Any = None,
    ) -> bool:
        """
        Execute a breaker close command.

        The physical operation is delegated exclusively to:

            Breaker.close(time)

        Parameters
        ----------
        breaker_id:
            Registered breaker identifier.

        time:
            Event/simulation time in seconds.

        source:
            Optional command source identifier.

        Returns
        -------
        bool
            Result returned by ``Breaker.close()``.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        time = self._validate_time(
            time
        )

        result = breaker.close(
            time=time
        )

        success = bool(
            result
        )

        self._record_event(
            time=time,
            breaker_id=breaker_id,
            action="CLOSE",
            success=success,
            source=source,
        )

        return success

    # =============================================================
    # STATUS
    # =============================================================

    def is_closed(
        self,
        breaker_id: Any,
    ) -> bool:
        """
        Return the authoritative physical breaker state.

        Raises
        ------
        KeyError
            If the breaker is not registered.

        Notes
        -----
        Unknown breakers are never treated as closed.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        return bool(
            breaker.is_closed()
        )

    # -------------------------------------------------------------

    def is_open(
        self,
        breaker_id: Any,
    ) -> bool:
        """
        Return the authoritative physical open state.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        return bool(
            breaker.is_open()
        )

    # -------------------------------------------------------------

    def is_failed(
        self,
        breaker_id: Any,
    ) -> bool:
        """
        Return the authoritative breaker failure state.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        return bool(
            breaker.is_failed()
        )

    # =============================================================
    # STATE SNAPSHOT
    # =============================================================

    def get_status(
        self,
        breaker_id: Any,
    ) -> Dict[str, Any]:
        """
        Return a structured status snapshot for one breaker.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        return {
            "id": breaker.id,
            "closed": bool(
                breaker.is_closed()
            ),
            "open": bool(
                breaker.is_open()
            ),
            "tripped": bool(
                getattr(
                    breaker,
                    "tripped",
                    False,
                )
            ),
            "failed": bool(
                breaker.is_failed()
            ),
        }

    # =============================================================
    # ALL BREAKER STATUS
    # =============================================================

    def get_all_status(
        self,
    ) -> Dict[Any, Dict[str, Any]]:
        """
        Return status snapshots for all registered breakers.
        """

        return {
            breaker_id: self.get_status(
                breaker_id
            )
            for breaker_id in self.breakers
        }

    # =============================================================
    # EVENT LOGGING
    # =============================================================

    def _record_event(
        self,
        time: float,
        breaker_id: Any,
        action: str,
        success: bool,
        source: Any = None,
    ) -> None:
        """
        Record a protection/control-layer breaker event.

        The event records the command issued by this manager.

        Physical switching history remains owned by Breaker.
        """

        event: Dict[str, Any] = {
            "time": float(time),
            "breaker": breaker_id,
            "action": str(action),
            "success": bool(success),
        }

        if source is not None:
            event["source"] = source

        self.events.append(
            event
        )

    # =============================================================
    # EVENT ACCESS
    # =============================================================

    def get_events(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Return a copy of the manager event history.

        The returned list can be inspected without modifying the
        manager's internal event collection.
        """

        return [
            dict(event)
            for event in self.events
        ]

    # =============================================================
    # EVENT CLEAR
    # =============================================================

    def clear_events(self) -> None:
        """
        Clear protection/control-layer events.

        This does not modify physical breaker state.
        """

        self.events.clear()

    # =============================================================
    # RESET
    # =============================================================

    def reset(
        self,
        reset_breakers: bool = True,
    ) -> None:
        """
        Reset manager state.

        Parameters
        ----------
        reset_breakers:
            When True, delegate reset to each authoritative
            Breaker.

        Notes
        -----
        The manager never implements physical reset logic itself.

        Setting ``reset_breakers=False`` clears only manager-level
        event state.
        """

        if reset_breakers:

            for breaker in self.breakers.values():

                reset = getattr(
                    breaker,
                    "reset",
                    None,
                )

                if not callable(reset):
                    raise AttributeError(
                        f"Breaker '{breaker.id}' does not "
                        "provide reset()."
                    )

                reset()

        self.events.clear()

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(
        self,
    ) -> Dict[str, Any]:
        """
        Return structured BreakerManager information.
        """

        return {
            "breaker_count": len(
                self.breakers
            ),
            "breakers": self.get_all_status(),
            "event_count": len(
                self.events
            ),
            "events": self.get_events(),
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<BreakerManager "
            f"breakers={len(self.breakers)}, "
            f"events={len(self.events)}>"
        )


__all__ = [
    "BreakerManager",
]
