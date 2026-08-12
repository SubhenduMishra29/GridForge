"""
GridForge Model Layer V2
========================

File:
    core/model/breaker.py

Purpose
-------
Defines the canonical GridForge physical circuit-breaker model.

Architecture
------------

A Breaker is a physical two-terminal switching device installed
in series between two electrical endpoints.

Examples:

    Bus ── Breaker ── Bus
    Bus ── Breaker ── Load
    Bus ── Breaker ── Generator
    Bus ── Breaker ── Line
    Bus ── Breaker ── Transformer

The Breaker owns its two physical terminals.

The Terminal owns the local endpoint reference.

The Network/topology layer determines the global electrical
connectivity and interprets the Breaker's physical state.

Responsibilities
----------------
The Breaker model provides:

- physical two-terminal switchgear representation;
- breaker identity;
- two physical terminals;
- rated voltage;
- continuous current rating;
- symmetrical interrupting-current capability;
- short-time withstand-current capability;
- short-circuit making/closing-current capability;
- opening/trip operating time;
- closing operating time;
- service state;
- physical open/closed state;
- equipment failure state;
- local terminal connection operations;
- local engineering-parameter validation;
- diagnostic information.

The Breaker does NOT:

- detect faults;
- calculate fault current;
- make protection decisions;
- implement relay logic;
- determine breaker-failure conditions;
- coordinate protection;
- schedule operations;
- store operation history;
- store simulation events;
- modify Network topology;
- rebuild Y-bus;
- perform load flow;
- perform short-circuit studies;
- perform contingency analysis;
- perform dynamic simulation;
- manage GUI state.

Those responsibilities belong to the appropriate GridForge layers.

State Ownership
---------------

The Breaker owns only authoritative physical equipment state:

    in_service
    closed
    failed

These states are independent.

Valid combinations therefore include:

    in_service=True,  closed=True,  failed=False
    in_service=True,  closed=False, failed=False
    in_service=True,  closed=False, failed=True
    in_service=True,  closed=True,  failed=True
    in_service=False, closed=True,  failed=False

A failed breaker is not necessarily open.

For example, a breaker may fail to operate and remain physically
closed.

The model therefore deliberately does not contain a ``tripped``
state.

A protection command to trip a breaker results in the physical
operation:

    breaker.open()

Whether that command is delayed, rejected, fails mechanically,
or is recorded as an event belongs to the protection/simulation
layers.

Terminal Architecture
---------------------

The Breaker owns:

    from_terminal
    to_terminal

Each Terminal contains its local endpoint:

    terminal.endpoint

The endpoint may be:

- a Bus;
- another Terminal;
- another network-supported endpoint.

The Breaker does not assume that either endpoint is a Bus.

Global topology remains owned by:

    core/network

Protection remains owned by:

    core/protection

Event scheduling/history remains owned by:

    core/simulation

The Breaker therefore remains a physical equipment model rather
than becoming a topology or protection controller.

Engineering Parameters
----------------------

The following are physical breaker nameplate/operational
characteristics:

    voltage_kv
    rated_current_a
    interrupting_capacity_ka
    short_time_withstand_ka
    making_capacity_ka
    trip_time
    close_time

The detailed interpretation of these quantities in a particular
study belongs to the relevant solver/protection/simulation layer.

GridForge V2 Status
-------------------

Canonical GridForge Model Layer V2 breaker model.

Future modifications require evidence of a genuinely fundamental
architectural requirement.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# CIRCUIT BREAKER
# =====================================================================

class Breaker(ElectricalObject):
    """
    GridForge physical circuit breaker.

    A Breaker is a two-terminal series switching device.

    Parameters
    ----------
    id : str
        Unique GridForge breaker identifier.

    voltage_kv : float
        Rated operating voltage in kV.

    rated_current_a : float
        Continuous current rating in amperes.

    interrupting_capacity_ka : float
        Symmetrical interrupting-current capability in kA.

    short_time_withstand_ka : float
        Short-time withstand current capability in kA.

    making_capacity_ka : float
        Short-circuit making/closing current capability in kA.

    trip_time : float, optional
        Breaker opening/trip operating time in seconds.

    close_time : float, optional
        Breaker closing operating time in seconds.

    endpoint_from : object, optional
        Initial from-side local endpoint.

    endpoint_to : object, optional
        Initial to-side local endpoint.

    name : str, optional
        Human-readable breaker name.

    in_service : bool, optional
        Equipment service state.

    Notes
    -----
    ``from_terminal`` and ``to_terminal`` are the authoritative
    local physical interfaces.

    The Breaker does not own global network topology.
    """

    def __init__(
        self,
        id: str,
        voltage_kv: float,
        rated_current_a: float,
        interrupting_capacity_ka: float,
        short_time_withstand_ka: float,
        making_capacity_ka: float,
        trip_time: float = 0.05,
        close_time: float = 0.10,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        name: str = "",
        in_service: bool = True,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # EQUIPMENT RATINGS
        # =============================================================

        self.voltage_kv = float(
            voltage_kv
        )

        self.rated_current_a = float(
            rated_current_a
        )

        self.interrupting_capacity_ka = float(
            interrupting_capacity_ka
        )

        self.short_time_withstand_ka = float(
            short_time_withstand_ka
        )

        self.making_capacity_ka = float(
            making_capacity_ka
        )

        # =============================================================
        # OPERATING CHARACTERISTICS
        # =============================================================

        self.trip_time = float(
            trip_time
        )

        self.close_time = float(
            close_time
        )

        # =============================================================
        # SERVICE STATE
        # =============================================================

        self.in_service = bool(
            in_service
        )

        # =============================================================
        # PHYSICAL TERMINALS
        # =============================================================

        self.from_terminal = Terminal(
            endpoint=endpoint_from,
            owner=self,
        )

        self.to_terminal = Terminal(
            endpoint=endpoint_to,
            owner=self,
        )

        # =============================================================
        # PHYSICAL SWITCHING STATE
        # =============================================================

        # A newly created breaker is physically closed.
        #
        # This is equipment state only. Network/topology decides
        # how the state is interpreted in the global electrical graph.
        self.closed = True

        # Equipment condition is independent of switching state.
        self.failed = False

        # =============================================================
        # LOCAL VALIDATION
        # =============================================================

        self._validate_parameters()

    # =================================================================
    # TERMINALS
    # =================================================================

    @property
    def terminals(self) -> tuple[Terminal, Terminal]:
        """
        Return the Breaker's two physical terminals.

        Returns
        -------
        tuple[Terminal, Terminal]
            ``(from_terminal, to_terminal)``
        """

        return (
            self.from_terminal,
            self.to_terminal,
        )

    # -----------------------------------------------------------------

    @property
    def primary_terminal(self) -> Terminal:
        """
        Compatibility alias for the from-side terminal.

        The canonical Breaker terminology remains
        ``from_terminal`` / ``to_terminal``.
        """

        return self.from_terminal

    # -----------------------------------------------------------------

    @property
    def secondary_terminal(self) -> Terminal:
        """
        Compatibility alias for the to-side terminal.

        The canonical Breaker terminology remains
        ``from_terminal`` / ``to_terminal``.
        """

        return self.to_terminal

    # =================================================================
    # ENDPOINT ACCESS
    # =================================================================

    @property
    def from_endpoint(self):
        """
        Return the authoritative from-side local endpoint.

        Equivalent to:

            self.from_terminal.endpoint
        """

        return self.from_terminal.endpoint

    # -----------------------------------------------------------------

    @property
    def to_endpoint(self):
        """
        Return the authoritative to-side local endpoint.

        Equivalent to:

            self.to_terminal.endpoint
        """

        return self.to_terminal.endpoint

    # -----------------------------------------------------------------

    def endpoints(self) -> tuple[Any, Any]:
        """
        Return the Breaker's local endpoint pair.

        Returns
        -------
        tuple
            ``(from_endpoint, to_endpoint)``

        Notes
        -----
        This exposes local model state only.

        It does not resolve or modify global network topology.
        """

        return (
            self.from_terminal.endpoint,
            self.to_terminal.endpoint,
        )

    # =================================================================
    # TERMINAL CONNECTION
    # =================================================================

    def connect_from(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the from-side terminal locally.

        This modifies only the local Terminal reference.

        It does not modify Network or global topology.
        """

        self.from_terminal.connect(
            endpoint
        )

    # -----------------------------------------------------------------

    def connect_to(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the to-side terminal locally.

        This modifies only the local Terminal reference.

        It does not modify Network or global topology.
        """

        self.to_terminal.connect(
            endpoint
        )

    # -----------------------------------------------------------------

    def disconnect_from(self) -> None:
        """
        Disconnect the from-side terminal locally.
        """

        self.from_terminal.disconnect()

    # -----------------------------------------------------------------

    def disconnect_to(self) -> None:
        """
        Disconnect the to-side terminal locally.
        """

        self.to_terminal.disconnect()

    # =================================================================
    # CONNECTION STATE
    # =================================================================

    @property
    def is_fully_connected(self) -> bool:
        """
        Return True when both physical terminals have endpoints.
        """

        return (
            self.from_terminal.is_connected
            and self.to_terminal.is_connected
        )

    # =================================================================
    # PARAMETER VALIDATION
    # =================================================================

    def _validate_parameters(self) -> None:
        """
        Validate local breaker engineering parameters.

        System-level electrical compatibility and topology rules
        belong to core/network and core/validation.
        """

        self._validate_positive(
            self.voltage_kv,
            "voltage_kv",
        )

        self._validate_positive(
            self.rated_current_a,
            "rated_current_a",
        )

        self._validate_positive(
            self.interrupting_capacity_ka,
            "interrupting_capacity_ka",
        )

        self._validate_positive(
            self.short_time_withstand_ka,
            "short_time_withstand_ka",
        )

        self._validate_positive(
            self.making_capacity_ka,
            "making_capacity_ka",
        )

        self._validate_non_negative(
            self.trip_time,
            "trip_time",
        )

        self._validate_non_negative(
            self.close_time,
            "close_time",
        )

    # -----------------------------------------------------------------

    @staticmethod
    def _validate_positive(
        value: float,
        field_name: str,
    ) -> None:
        """
        Validate a strictly positive engineering quantity.
        """

        if not isfinite(value):
            raise ValueError(
                f"{field_name} must be finite."
            )

        if value <= 0.0:
            raise ValueError(
                f"{field_name} must be greater than zero."
            )

    # -----------------------------------------------------------------

    @staticmethod
    def _validate_non_negative(
        value: float,
        field_name: str,
    ) -> None:
        """
        Validate a non-negative engineering quantity.
        """

        if not isfinite(value):
            raise ValueError(
                f"{field_name} must be finite."
            )

        if value < 0.0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

    # =================================================================
    # SWITCHING OPERATIONS
    # =================================================================

    def open(self) -> None:
        """
        Open the physical breaker.

        This changes only the authoritative local physical
        switching state.

        It does not:

        - modify Network;
        - rebuild topology;
        - schedule an event;
        - record history;
        - perform protection logic.

        Notes
        -----
        Opening a failed breaker is still a physical-state
        operation at the model level.

        Whether a real-world failed breaker should reject the
        operation belongs to the protection/simulation model,
        not this basic equipment state transition.
        """

        self.closed = False

    # -----------------------------------------------------------------

    def close(self) -> None:
        """
        Close the physical breaker.

        This changes only the authoritative local physical
        switching state.

        It does not:

        - modify Network;
        - rebuild topology;
        - schedule an event;
        - record history;
        - perform synchronization checks;
        - perform protection logic.
        """

        self.closed = True

    # =================================================================
    # SERVICE STATE
    # =================================================================

    def set_in_service(
        self,
        in_service: bool,
    ) -> None:
        """
        Set the local equipment service state.

        Network/topology interpretation of service state belongs
        outside the Breaker model.
        """

        self.in_service = bool(
            in_service
        )

    # =================================================================
    # SWITCHING STATE
    # =================================================================

    @property
    def is_closed(self) -> bool:
        """
        Return True when the breaker is physically closed.
        """

        return self.closed

    # -----------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        """
        Return True when the breaker is physically open.
        """

        return not self.closed

    # -----------------------------------------------------------------

    @property
    def conducts(self) -> bool:
        """
        Return the local physical conduction state.

        This is equivalent to the physical closed state.

        The Network layer decides how this state affects the
        derived electrical topology.
        """

        return self.closed

    # =================================================================
    # FAILURE STATE
    # =================================================================

    @property
    def is_failed(self) -> bool:
        """
        Return True when the breaker is marked failed.
        """

        return self.failed

    # -----------------------------------------------------------------

    def mark_failed(self) -> None:
        """
        Mark the breaker as failed.

        This records equipment condition only.

        Breaker-failure detection belongs to the protection/
        simulation layers.
        """

        self.failed = True

    # -----------------------------------------------------------------

    def clear_failure(self) -> None:
        """
        Clear the breaker equipment-failure state.
        """

        self.failed = False

    # =================================================================
    # RESET
    # =================================================================

    def reset(self) -> None:
        """
        Reset the Breaker to its model initialization state.

        Resetting the physical equipment model is deliberately
        limited to local state.

        Terminal topology is not modified.
        """

        self.closed = True
        self.failed = False

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured Breaker engineering and state information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "Breaker",

            "in_service": self.in_service,

            "from_endpoint": (
                self.from_terminal.endpoint_id
            ),
            "to_endpoint": (
                self.to_terminal.endpoint_id
            ),

            "from_connected": (
                self.from_terminal.is_connected
            ),
            "to_connected": (
                self.to_terminal.is_connected
            ),

            "voltage_kv": self.voltage_kv,
            "rated_current_a": self.rated_current_a,
            "interrupting_capacity_ka": (
                self.interrupting_capacity_ka
            ),
            "short_time_withstand_ka": (
                self.short_time_withstand_ka
            ),
            "making_capacity_ka": (
                self.making_capacity_ka
            ),

            "trip_time": self.trip_time,
            "close_time": self.close_time,

            "closed": self.closed,
            "failed": self.failed,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        from_id = (
            self.from_terminal.endpoint_id
            if self.from_terminal.is_connected
            else None
        )

        to_id = (
            self.to_terminal.endpoint_id
            if self.to_terminal.is_connected
            else None
        )

        return (
            f"<Breaker "
            f"id={self.id}, "
            f"from={from_id}, "
            f"to={to_id}, "
            f"voltage={self.voltage_kv:.3f} kV, "
            f"rated={self.rated_current_a:.2f} A, "
            f"interrupting="
            f"{self.interrupting_capacity_ka:.2f} kA, "
            f"short_time="
            f"{self.short_time_withstand_ka:.2f} kA, "
            f"making="
            f"{self.making_capacity_ka:.2f} kA, "
            f"closed={self.closed}, "
            f"failed={self.failed}>"
        )


__all__ = [
    "Breaker",
]
```
