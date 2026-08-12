```python
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

- detect faults;
- calculate fault current;
- evaluate relays;
- calculate relay operating time;
- coordinate protection functions;
- process CT/PT/CVT signals;
- manage MeasurementChannel objects;
- modify electrical topology;
- build Y-bus;
- modify solver state;
- directly manipulate Breaker internal state;
- replace the authoritative Breaker model.

Authority Boundary
------------------

    core/model/breaker.py
        |
        +-- physical state
        +-- physical switching operation
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

The physical Breaker owns physical switching history when such
history is required by the physical equipment/simulation contract.

The BreakerManager owns protection/control-layer command events.

Therefore:

    Breaker
        = authoritative physical equipment state

    BreakerManager.events
        = protection/control command history


Important V2 Boundary
---------------------

BreakerManager does not create or infer physical breaker state.

An unknown breaker identifier is a configuration/reference error.

It is therefore invalid to interpret an unknown breaker as:

    closed
    open
    failed

All breaker lookup operations used for commands or status therefore
raise KeyError when the identifier is not registered.

The manager delegates physical switching exclusively to:

    Breaker.open()
    Breaker.close()

The manager does not pass simulation time into those methods.

Simulation/event scheduling belongs to the simulation/event layer.


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

    BreakerManager provides only the command and management
    boundary required by protection/control logic.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(self) -> None:
        """
        Create an empty BreakerManager.
        """

        self.breakers: Dict[str, Breaker] = {}

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

    # -------------------------------------------------------------

    register = add_breaker

    # =============================================================
    # REMOVAL
    # =============================================================

    def remove_breaker(
        self,
        breaker_id: str,
    ) -> Breaker:
        """
        Remove and return a registered breaker.

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
        breaker_id: str,
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
        breaker_id: str,
    ) -> bool:
        """
        Return True when a breaker is registered.
        """

        return breaker_id in self.breakers

    # =============================================================
    # REQUIRED LOOKUP
    # =============================================================

    def _require_breaker(
        self,
        breaker_id: str,
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
        Validate command/event time.

        Time is manager-level event metadata.

        It is NOT passed into the physical Breaker.open()
        or Breaker.close() methods.
        """

        try:
            value = float(time)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "Breaker operation time must be numeric."
            ) from exc

        if not isfinite(value):
            raise ValueError(
                "Breaker operation time must be finite."
            )

        return value

    # =============================================================
    # TRIP
    # =============================================================

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

        Parameters
        ----------
        breaker_id:
            Registered breaker identifier.

        time:
            Simulation/event time in seconds.

            This is command-event metadata only. It is not passed
            to the physical Breaker model.

        source:
            Optional command source identifier.

            Typical value:

                relay_id

            The manager records this value but does not interpret it.

        Returns
        -------
        bool
            True when the Breaker accepts the operation.

        Raises
        ------
        KeyError
            If the breaker is not registered.

        ValueError / TypeError
            If time is invalid.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        event_time = self._validate_time(
            time
        )

        result = breaker.open()

        success = bool(result)

        self._record_event(
            time=event_time,
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
        breaker_id: str,
        time: float = 0.0,
        source: Any = None,
    ) -> bool:
        """
        Execute a breaker close command.

        The physical operation is delegated exclusively to:

            Breaker.close()

        Parameters
        ----------
        breaker_id:
            Registered breaker identifier.

        time:
            Simulation/event time in seconds.

            This is command-event metadata only.

        source:
            Optional command source identifier.

        Returns
        -------
        bool
            True when the Breaker accepts the operation.

        Raises
        ------
        KeyError
            If the breaker is not registered.

        ValueError / TypeError
            If time is invalid.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        event_time = self._validate_time(
            time
        )

        result = breaker.close()

        success = bool(result)

        self._record_event(
            time=event_time,
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

    # -------------------------------------------------------------

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

    # -------------------------------------------------------------

    def is_failed(
        self,
        breaker_id: str,
    ) -> bool:
        """
        Return the authoritative breaker failure state.

        Unknown breaker identifiers raise KeyError.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        return bool(
            breaker.is_failed
        )

    # =============================================================
    # STATUS SNAPSHOT
    # =============================================================

    def get_status(
        self,
        breaker_id: str,
    ) -> Dict[str, Any]:
        """
        Return a structured status snapshot.

        The snapshot exposes only state owned by the authoritative
        Breaker model.
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

    # =============================================================
    # ALL BREAKER STATUS
    # =============================================================

    def get_all_status(
        self,
    ) -> Dict[str, Dict[str, Any]]:
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
        breaker_id: str,
        action: str,
        success: bool,
        source: Any = None,
    ) -> None:
        """
        Record a protection/control-layer command event.

        This event does not replace physical breaker state.

        The event answers:

            What command did the control/protection layer issue?

        The Breaker model answers:

            What is the physical state of the breaker?
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

        Event dictionaries are copied so callers cannot directly
        mutate the manager's internal event records.
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

        Physical breaker state is unaffected.
        """

        self.events.clear()

    # =============================================================
    # RESET
    # =============================================================

    def reset(
        self,
        reset_breakers: bool = False,
    ) -> None:
        """
        Reset manager-level state.

        Parameters
        ----------
        reset_breakers:
            If True, delegate reset to each Breaker that explicitly
            provides a reset() method.

        Notes
        -----
        Manager event history is always cleared.

        By default, physical breaker state is NOT changed.

        This is intentional: a protection/control manager reset
        must not silently alter physical equipment state.
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
```
