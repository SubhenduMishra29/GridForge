"""
GridForge Breaker Manager
==========================

File:
    core/protection/breaker_manager.py

Purpose
-------
Protection control-layer manager for circuit breakers.

Responsibilities
----------------
- Register physical Breaker models.
- Execute relay-generated trip commands.
- Execute close commands.
- Query breaker state.
- Maintain protection/switching events.
- Provide access to registered breakers.

The authoritative physical breaker model is:

    core/model/breaker.py

This manager does NOT:
- Detect faults.
- Calculate fault currents.
- Perform protection calculations.
- Coordinate relays.
- Directly manipulate breaker internal state.

All physical breaker state changes are performed through:

    Breaker.open()
    Breaker.close()

Architecture
------------

    ProtectionSystem
           |
           | trip(command)
           v
    BreakerManager
           |
           | breaker.open(time)
           v
    core/model/breaker.py
           |
           v
    Physical breaker state

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.model.breaker import Breaker


class BreakerManager:
    """
    Protection-layer manager for GridForge circuit breakers.

    The Breaker object remains the authoritative owner of physical
    breaker state.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(self) -> None:

        self.breakers: Dict[
            Any,
            Breaker,
        ] = {}

        self.events: List[
            Dict[str, Any]
        ] = []

    # =============================================================
    # REGISTER BREAKER
    # =============================================================

    def add_breaker(
        self,
        breaker: Breaker,
    ) -> None:
        """
        Register a physical Breaker model.

        Parameters
        ----------
        breaker:
            Breaker instance from core.model.breaker.
        """

        if not isinstance(
            breaker,
            Breaker,
        ):
            raise TypeError(
                "breaker must be an instance "
                "of core.model.breaker.Breaker."
            )

        if breaker.id in self.breakers:
            raise ValueError(
                f"Breaker already exists: "
                f"{breaker.id}"
            )

        self.breakers[
            breaker.id
        ] = breaker

    # =============================================================
    # REMOVE BREAKER
    # =============================================================

    def remove_breaker(
        self,
        breaker_id: Any,
    ) -> None:
        """
        Remove a registered breaker.
        """

        self.breakers.pop(
            breaker_id,
            None,
        )

    # =============================================================
    # TRIP COMMAND
    # =============================================================

    def trip(
        self,
        breaker_id: Any,
        time: float = 0.0,
    ) -> bool:
        """
        Execute a breaker trip command.

        Parameters
        ----------
        breaker_id:
            Registered breaker identifier.

        time:
            Event/simulation time in seconds.

        Returns
        -------
        bool
            True when the breaker accepted the open command.

        Notes
        -----
        The physical operation is delegated to:

            Breaker.open(time)

        BreakerManager never directly changes:

            breaker.closed
            breaker.tripped
            breaker.failed
        """

        breaker = self._require_breaker(
            breaker_id
        )

        time = float(
            time
        )

        result = breaker.open(
            time=time
        )

        self._record_event(
            time=time,
            breaker_id=breaker_id,
            action="TRIP",
            success=result,
        )

        return bool(
            result
        )

    # =============================================================
    # CLOSE COMMAND
    # =============================================================

    def close(
        self,
        breaker_id: Any,
        time: float = 0.0,
    ) -> bool:
        """
        Execute a breaker close command.

        The physical operation is delegated to:

            Breaker.close(time)
        """

        breaker = self._require_breaker(
            breaker_id
        )

        time = float(
            time
        )

        result = breaker.close(
            time=time
        )

        self._record_event(
            time=time,
            breaker_id=breaker_id,
            action="CLOSE",
            success=result,
        )

        return bool(
            result
        )

    # =============================================================
    # STATUS
    # =============================================================

    def is_closed(
        self,
        breaker_id: Any,
    ) -> bool:
        """
        Return breaker closed state.

        Parameters
        ----------
        breaker_id:
            Breaker identifier.

        Returns
        -------
        bool
            True when the breaker is closed.

        Notes
        -----
        An unknown breaker is treated as closed for compatibility
        with the original GridForge protection behavior.

        This behavior should be used carefully because it represents
        an implicit connected state rather than an actual breaker.
        """

        breaker = self.get_breaker(
            breaker_id
        )

        if breaker is None:
            return True

        return breaker.is_closed()

    # =============================================================
    # OPEN STATUS
    # =============================================================

    def is_open(
        self,
        breaker_id: Any,
    ) -> bool:
        """
        Return breaker open state.

        Unknown breakers are treated as not open, consistent with
        the implicit-connected behavior of is_closed().
        """

        breaker = self.get_breaker(
            breaker_id
        )

        if breaker is None:
            return False

        return breaker.is_open()

    # =============================================================
    # FAILURE STATUS
    # =============================================================

    def is_failed(
        self,
        breaker_id: Any,
    ) -> bool:
        """
        Return breaker failure state.

        Raises
        ------
        KeyError
            If the breaker is not registered.
        """

        breaker = self._require_breaker(
            breaker_id
        )

        return breaker.is_failed()

    # =============================================================
    # GET BREAKER
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
            Registered breaker or None when not found.
        """

        return self.breakers.get(
            breaker_id
        )

    # =============================================================
    # INTERNAL BREAKER VALIDATION
    # =============================================================

    def _require_breaker(
        self,
        breaker_id: Any,
    ) -> Breaker:
        """
        Return a registered breaker or raise KeyError.
        """

        breaker = self.get_breaker(
            breaker_id
        )

        if breaker is None:
            raise KeyError(
                f"Breaker not found: "
                f"{breaker_id}"
            )

        return breaker

    # =============================================================
    # EVENT LOGGING
    # =============================================================

    def _record_event(
        self,
        time: float,
        breaker_id: Any,
        action: str,
        success: bool,
    ) -> None:
        """
        Record a breaker-manager operation.

        The physical Breaker also maintains its own history.

        Therefore:

            Breaker.history
                = physical switching history

            BreakerManager.events
                = protection/control-layer events
        """

        self.events.append(
            {
                "time": time,
                "breaker": breaker_id,
                "action": action,
                "success": bool(success),
            }
        )

    # =============================================================
    # RESET
    # =============================================================

    def reset(
        self,
    ) -> None:
        """
        Reset all registered breakers and clear manager events.

        Physical reset is delegated to Breaker.reset().
        """

        for breaker in self.breakers.values():
            breaker.reset()

        self.events.clear()

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(
        self,
    ) -> Dict[str, Any]:
        """
        Return structured breaker-manager information.
        """

        return {
            "breakers": {
                breaker_id: {
                    "closed": breaker.is_closed(),
                    "tripped": breaker.tripped,
                    "failed": breaker.failed,
                }
                for breaker_id, breaker
                in self.breakers.items()
            },
            "events": list(
                self.events
            ),
        }


__all__ = [
    "BreakerManager",
]
```
