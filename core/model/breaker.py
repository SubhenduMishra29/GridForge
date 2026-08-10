```python
"""
GridForge Circuit Breaker Model
===============================

File:
    core/model/breaker.py

Defines the physical circuit-breaker model.

Responsibilities
----------------
- Maintain breaker electrical state.
- Open / close operation.
- Store equipment ratings.
- Store operating times.
- Model breaker failure.
- Record switching operations.

The Breaker model does NOT:
- Detect faults.
- Perform relay protection.
- Coordinate protection devices.
- Calculate fault currents.
- Decide when a breaker should trip.

Those responsibilities belong to:

    core/protection
    core/analysis
    core/simulation

The breaker is a physical switching element. Higher-level
protection and simulation systems issue commands to it.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from .base import ElectricalObject


class Breaker(ElectricalObject):
    """
    GridForge circuit breaker model.

    Parameters
    ----------
    id:
        Unique breaker identifier.

    connected_element:
        Electrical element controlled by the breaker.

        This may be a Line, Transformer, Branch, or another
        switchable network element.

    name:
        Human-readable breaker name.

    voltage_kv:
        Rated voltage in kV.

    rated_current:
        Rated continuous current.

    interrupting_capacity:
        Rated interrupting capacity.

    trip_time:
        Breaker opening time in seconds.

    close_time:
        Breaker closing time in seconds.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        id: str,
        connected_element=None,
        name: str = "",
        voltage_kv: float = 0.0,
        rated_current: float = 0.0,
        interrupting_capacity: float = 0.0,
        trip_time: float = 0.05,
        close_time: float = 0.10,
    ):
        """
        Initialize a GridForge circuit breaker.
        """

        super().__init__(
            id=id,
            name=name
        )

        # -----------------------------------------------------
        # Connection
        # -----------------------------------------------------

        self.connected_element = connected_element

        # -----------------------------------------------------
        # Equipment ratings
        # -----------------------------------------------------

        self.voltage_kv = float(
            voltage_kv
        )

        self.rated_current = float(
            rated_current
        )

        self.interrupting_capacity = float(
            interrupting_capacity
        )

        # -----------------------------------------------------
        # Operating times
        # -----------------------------------------------------

        self.trip_time = float(
            trip_time
        )

        self.close_time = float(
            close_time
        )

        # -----------------------------------------------------
        # Operational state
        # -----------------------------------------------------

        self.closed = True

        self.tripped = False

        self.failed = False

        # -----------------------------------------------------
        # Event tracking
        # -----------------------------------------------------

        self.last_operation_time = 0.0

        self.history: list[dict] = []

        self._validate()

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate(self) -> None:
        """
        Validate breaker configuration.
        """

        if self.voltage_kv < 0.0:
            raise ValueError(
                "Breaker voltage rating must be >= 0"
            )

        if self.rated_current < 0.0:
            raise ValueError(
                "Breaker rated current must be >= 0"
            )

        if self.interrupting_capacity < 0.0:
            raise ValueError(
                "Breaker interrupting capacity must be >= 0"
            )

        if self.trip_time < 0.0:
            raise ValueError(
                "Breaker trip time must be >= 0"
            )

        if self.close_time < 0.0:
            raise ValueError(
                "Breaker close time must be >= 0"
            )

    # =========================================================
    # OPEN OPERATION
    # =========================================================

    def open(
        self,
        time: float = 0.0
    ) -> bool:
        """
        Open the breaker.

        Parameters
        ----------
        time:
            Simulation/event time in seconds.

        Returns
        -------
        bool
            True if the operation was accepted.
            False if the breaker has failed.
        """

        if self.failed:
            return False

        time = float(time)

        self.closed = False

        self.tripped = True

        self.last_operation_time = time

        self._record_event(
            time=time,
            action="OPEN"
        )

        return True

    # =========================================================
    # CLOSE OPERATION
    # =========================================================

    def close(
        self,
        time: float = 0.0
    ) -> bool:
        """
        Close the breaker.

        Returns False when the breaker is failed.
        """

        if self.failed:
            return False

        time = float(time)

        self.closed = True

        self.tripped = False

        self.last_operation_time = time

        self._record_event(
            time=time,
            action="CLOSE"
        )

        return True

    # =========================================================
    # STATUS
    # =========================================================

    def is_closed(self) -> bool:
        """
        Return True when the breaker is closed.
        """

        return self.closed

    def is_open(self) -> bool:
        """
        Return True when the breaker is open.
        """

        return not self.closed

    def is_failed(self) -> bool:
        """
        Return True when the breaker is failed.
        """

        return self.failed

    # =========================================================
    # FAILURE MODEL
    # =========================================================

    def fail(self) -> None:
        """
        Put the breaker into failed state.

        Failure prevents subsequent open/close commands from
        being accepted.

        Existing physical state is not automatically changed.
        """

        self.failed = True

    def reset_failure(self) -> None:
        """
        Clear the breaker failure state.
        """

        self.failed = False

    # =========================================================
    # RESET
    # =========================================================

    def reset(self) -> None:
        """
        Restore the breaker to its initial state.
        """

        self.closed = True

        self.tripped = False

        self.failed = False

        self.last_operation_time = 0.0

        self.history.clear()

    # =========================================================
    # EVENT LOGGING
    # =========================================================

    def _record_event(
        self,
        time: float,
        action: str
    ) -> None:
        """
        Record a switching operation.
        """

        self.history.append(
            {
                "time": time,
                "action": action,
            }
        )

    # =========================================================
    # CONNECTION
    # =========================================================

    def connect(
        self,
        element
    ) -> None:
        """
        Connect the breaker to a switchable electrical element.
        """

        if element is None:
            raise ValueError(
                "Connected element cannot be None"
            )

        self.connected_element = element

    def disconnect(self) -> None:
        """
        Remove the currently connected electrical element.
        """

        self.connected_element = None

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(self) -> dict:
        """
        Return structured breaker information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "connected_element": (
                getattr(
                    self.connected_element,
                    "id",
                    None
                )
            ),
            "voltage_kv": self.voltage_kv,
            "rated_current": self.rated_current,
            "interrupting_capacity": (
                self.interrupting_capacity
            ),
            "trip_time": self.trip_time,
            "close_time": self.close_time,
            "closed": self.closed,
            "tripped": self.tripped,
            "failed": self.failed,
            "last_operation_time": (
                self.last_operation_time
            ),
            "operation_count": len(
                self.history
            ),
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        state = (
            "CLOSED"
            if self.closed
            else "OPEN"
        )

        if self.failed:
            state = f"{state}, FAILED"

        return (
            f"<Breaker "
            f"id={self.id}, "
            f"state={state}, "
            f"trip_time={self.trip_time:.4f}s>"
        )
```
