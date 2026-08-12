"""
GridForge Breaker Model
=======================

GridForge Model Layer V2

Defines the GridForge physical circuit-breaker model.

Architecture
------------

A Breaker is a physical two-terminal switching device.

The breaker is installed in series between two electrical endpoints:

    Equipment A
         |
      Terminal
         |
       Breaker
         |
      Terminal
         |
    Equipment B

Examples include:

    Bus ── Breaker ── Bus
    Bus ── Breaker ── Load
    Bus ── Breaker ── Generator
    Bus ── Breaker ── Line
    Bus ── Breaker ── Transformer

The Breaker owns its two physical terminals.

The network/topology layer determines what those terminals are
connected to and maintains the global electrical topology.

Responsibilities
----------------

The Breaker model provides:

- Physical two-terminal switching equipment.
- Breaker identity.
- Two local physical terminals.
- Voltage rating.
- Continuous current rating.
- Interrupting-current capability.
- Trip operating time.
- Close operating time.
- Open/closed physical state.
- Equipment failure state.
- Basic local parameter validation.
- Diagnostic information.

The Breaker model does NOT:

- Determine whether a fault exists.
- Detect faults.
- Issue protection decisions.
- Perform relay calculations.
- Perform breaker coordination.
- Determine breaker-failure conditions.
- Modify global network topology.
- Rebuild Y-bus.
- Perform load flow.
- Perform short-circuit calculations.
- Perform contingency analysis.
- Perform dynamic simulation.
- Store simulation event history.
- Store GUI geometry.

Protection commands belong to the protection layer.

Operation scheduling and event history belong to the simulation/event
layer.

Global connectivity belongs to the network/topology layer.

State Ownership
---------------

The Breaker owns only its authoritative physical equipment state:

    closed
    failed

These states are intentionally independent.

Therefore the following combinations are valid:

    OPEN
    CLOSED
    OPEN + FAILED
    CLOSED + FAILED

A failed breaker is not necessarily open. For example, a breaker may
fail to trip and therefore remain physically closed.

The model does not store historical operation events.

A simulation may record:

    time
    breaker
    command
    resulting state

without making that history part of the authoritative equipment model.

Topology
--------

The Breaker's terminals are the authoritative local connection points:

    from_terminal
    to_terminal

A terminal may initially be disconnected.

The network layer is responsible for:

- registering the equipment;
- validating complete connections;
- constructing physical connections;
- constructing the physical graph;
- deriving electrical topology;
- applying the Breaker's state to that topology.

The Breaker does not directly modify the Network object.

Terminal Architecture
---------------------

The Breaker uses the current GridForge Terminal abstraction.

The Terminal owns the local endpoint reference:

    terminal.endpoint

The Breaker does not assume that the endpoint is necessarily a Bus.

An endpoint may be:

- a Bus;
- another Terminal;
- another network-supported endpoint.

The authoritative local connection is therefore:

    from_terminal.endpoint
    to_terminal.endpoint

Bus-specific compatibility is provided by Terminal.bus and must not
be used as the Breaker's primary topology representation.

GridForge V2 Status
-------------------

This module is part of the GridForge Model Layer V2 baseline.

The Breaker is a fundamental switchgear model and therefore remains
inside core/model.

Detailed protection, control, measurement, topology, and simulation
capabilities remain outside this module.

Future changes require evidence of a genuinely fundamental
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

    trip_time : float, optional
        Mechanical/equipment trip operating time in seconds.

    close_time : float, optional
        Mechanical/equipment close operating time in seconds.

    endpoint_from : object, optional
        Initial from-side electrical endpoint.

        May be None when the breaker is created before network
        assembly.

    endpoint_to : object, optional
        Initial to-side electrical endpoint.

        May be None when the breaker is created before network
        assembly.

    name : str, optional
        Human-readable breaker name.

    Notes
    -----
    The Breaker owns two Terminal objects.

    The Terminal objects belong to this Breaker and contain the
    local endpoint references.

    The Breaker does not own global topology.
    """

    def __init__(
        self,
        id: str,
        voltage_kv: float,
        rated_current_a: float,
        interrupting_capacity_ka: float,
        trip_time: float = 0.05,
        close_time: float = 0.10,
        endpoint_from: Any = None,
        endpoint_to: Any = None,
        name: str = "",
    ) -> None:

        super().__init__(
            id=id,
            name=name,
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
        # EQUIPMENT RATINGS
        # =============================================================

        self.voltage_kv = float(voltage_kv)

        self.rated_current_a = float(
            rated_current_a
        )

        self.interrupting_capacity_ka = float(
            interrupting_capacity_ka
        )

        # =============================================================
        # OPERATING CHARACTERISTICS
        # =============================================================

        self.trip_time = float(trip_time)
        self.close_time = float(close_time)

        # =============================================================
        # PHYSICAL STATE
        # =============================================================

        # A newly created breaker is physically closed unless
        # explicitly opened by the model user or simulation.
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
        tuple
            ``(from_terminal, to_terminal)``
        """

        return (
            self.from_terminal,
            self.to_terminal,
        )

    # =================================================================
    # ENDPOINT ACCESS
    # =================================================================

    @property
    def from_endpoint(self):
        """
        Return the authoritative from-side local endpoint.

        This is equivalent to:

            self.from_terminal.endpoint

        The returned object is not assumed to be a Bus.
        """

        return self.from_terminal.endpoint

    # -----------------------------------------------------------------

    @property
    def to_endpoint(self):
        """
        Return the authoritative to-side local endpoint.

        This is equivalent to:

            self.to_terminal.endpoint

        The returned object is not assumed to be a Bus.
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
        This method exposes local model state only.

        It does not resolve global network topology.
        """

        return (
            self.from_terminal.endpoint,
            self.to_terminal.endpoint,
        )

    # =================================================================
    # TERMINAL CONNECTION
    # =================================================================

    def connect_from(self, endpoint: Any) -> None:
        """
        Connect the from-side terminal to a local endpoint.

        This changes only the Breaker's local terminal state.

        It does not modify Network or global topology.
        """

        self.from_terminal.connect(endpoint)

    # -----------------------------------------------------------------

    def connect_to(self, endpoint: Any) -> None:
        """
        Connect the to-side terminal to a local endpoint.

        This changes only the Breaker's local terminal state.

        It does not modify Network or global topology.
        """

        self.to_terminal.connect(endpoint)

    # -----------------------------------------------------------------

    def disconnect_from(self) -> None:
        """
        Disconnect the Breaker's from-side terminal locally.
        """

        self.from_terminal.disconnect()

    # -----------------------------------------------------------------

    def disconnect_to(self) -> None:
        """
        Disconnect the Breaker's to-side terminal locally.
        """

        self.to_terminal.disconnect()

    # =================================================================
    # LOCAL CONNECTION STATE
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
    # VALIDATION
    # =================================================================

    def _validate_parameters(self) -> None:
        """
        Validate local breaker engineering parameters.

        System-level topology and equipment compatibility rules
        belong to core/network and core/validation.
        """

        # -------------------------------------------------------------
        # Voltage rating
        # -------------------------------------------------------------

        if not isfinite(self.voltage_kv):
            raise ValueError(
                f"Breaker '{self.id}' voltage rating "
                "must be finite."
            )

        if self.voltage_kv <= 0.0:
            raise ValueError(
                f"Breaker '{self.id}' voltage rating "
                "must be greater than zero."
            )

        # -------------------------------------------------------------
        # Continuous current rating
        # -------------------------------------------------------------

        if not isfinite(self.rated_current_a):
            raise ValueError(
                f"Breaker '{self.id}' rated current "
                "must be finite."
            )

        if self.rated_current_a <= 0.0:
            raise ValueError(
                f"Breaker '{self.id}' rated current "
                "must be greater than zero."
            )

        # -------------------------------------------------------------
        # Interrupting capability
        # -------------------------------------------------------------

        if not isfinite(
            self.interrupting_capacity_ka
        ):
            raise ValueError(
                f"Breaker '{self.id}' interrupting capacity "
                "must be finite."
            )

        if self.interrupting_capacity_ka <= 0.0:
            raise ValueError(
                f"Breaker '{self.id}' interrupting capacity "
                "must be greater than zero."
            )

        # -------------------------------------------------------------
        # Trip time
        # -------------------------------------------------------------

        if not isfinite(self.trip_time):
            raise ValueError(
                f"Breaker '{self.id}' trip time "
                "must be finite."
            )

        if self.trip_time < 0.0:
            raise ValueError(
                f"Breaker '{self.id}' trip time "
                "cannot be negative."
            )

        # -------------------------------------------------------------
        # Close time
        # -------------------------------------------------------------

        if not isfinite(self.close_time):
            raise ValueError(
                f"Breaker '{self.id}' close time "
                "must be finite."
            )

        if self.close_time < 0.0:
            raise ValueError(
                f"Breaker '{self.id}' close time "
                "cannot be negative."
            )

    # =================================================================
    # OPERATING STATE
    # =================================================================

    def open(self) -> None:
        """
        Open the circuit breaker.

        This changes only the local physical state.

        The network/topology layer observes the resulting state when
        rebuilding the active electrical topology.
        """

        self.closed = False

    # -----------------------------------------------------------------

    def close(self) -> None:
        """
        Close the circuit breaker.

        This changes only the local physical state.

        The network/topology layer observes the resulting state when
        rebuilding the active electrical topology.
        """

        self.closed = True

    # =================================================================
    # STATUS
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
    def is_failed(self) -> bool:
        """
        Return True when the breaker is marked as failed.
        """

        return self.failed

    # =================================================================
    # FAILURE STATE
    # =================================================================

    def mark_failed(self) -> None:
        """
        Mark the breaker as failed.

        This records equipment condition only.

        Breaker-failure detection and protection logic belong to
        core/protection and/or core/simulation.
        """

        self.failed = True

    # -----------------------------------------------------------------

    def clear_failure(self) -> None:
        """
        Clear the Breaker's equipment-failure state.
        """

        self.failed = False

    # =================================================================
    # SERVICE / TOPOLOGY SEMANTICS
    # =================================================================

    @property
    def conducts(self) -> bool:
        """
        Return whether the Breaker is physically closed.

        Notes
        -----
        This is a local equipment-state interpretation.

        The network/topology layer decides how this state affects
        the derived electrical topology.

        A failed breaker may still be physically closed and therefore
        ``conducts`` remains True until the physical state changes.
        """

        return self.closed

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured Breaker information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "Breaker",
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
            f"closed={self.closed}, "
            f"failed={self.failed}>"
        )
