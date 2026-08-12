"""
GridForge Circuit Breaker Model
===============================

GridForge Model Layer V2

Defines the GridForge physical circuit-breaker model.

Architecture
------------
A Breaker is a physical two-terminal switching device.

The breaker is installed in series between two electrical endpoints:

    Equipment A
        │
    Terminal
        │
     Breaker
        │
    Terminal
        │
    Equipment B

Examples include:

    Bus ── Breaker ── Bus
    Bus ── Breaker ── Load
    Bus ── Breaker ── Generator
    Bus ── Breaker ── Line
    Bus ── Breaker ── Transformer

The Breaker therefore owns its own two physical terminals.

The network/topology layer is responsible for determining what those
terminals are connected to and for maintaining the global electrical
topology.

Responsibilities
----------------
The Breaker model provides:

- Physical two-terminal switching equipment.
- Breaker identity.
- Terminal endpoints.
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
The Breaker owns only its authoritative physical state:

    OPEN
    CLOSED
    FAILED

The model does not store historical operation events.

A simulation may record:

    time
    breaker
    command
    resulting state

without making that history part of the authoritative equipment model.

Topology
--------
The Breaker is a physical series element.

Its terminals are the authoritative local connection points:

    from_terminal
    to_terminal

The Terminal objects reference the connected electrical endpoints.

The network layer remains responsible for registration, validation,
topology construction, and network-wide connection rules.

GridForge V2 Status
-------------------
This module is part of the GridForge Model Layer V2 baseline.

The Breaker is a fundamental switchgear model and therefore remains
inside ``core/model``.

Detailed protection, control, measurement, and simulation capabilities
must remain outside this module.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

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

    endpoint_from :
        From-side electrical endpoint.

    endpoint_to :
        To-side electrical endpoint.

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

    name : str, optional
        Human-readable breaker name.

    Notes
    -----
    The breaker terminals reference electrical endpoints.

    The breaker does not own the global topology.

    The network layer determines the actual network connectivity and
    electrical consequences of the breaker state.
    """

    def __init__(
        self,
        id: str,
        endpoint_from,
        endpoint_to,
        voltage_kv: float,
        rated_current_a: float,
        interrupting_capacity_ka: float,
        trip_time: float = 0.05,
        close_time: float = 0.10,
        name: str = "",
    ):
        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # CONNECTIVITY
        # =============================================================

        if endpoint_from is None:
            raise ValueError(
                "Breaker from-endpoint cannot be None."
            )

        if endpoint_to is None:
            raise ValueError(
                "Breaker to-endpoint cannot be None."
            )

        if endpoint_from is endpoint_to:
            raise ValueError(
                "Breaker cannot connect an endpoint to itself."
            )

        self.from_terminal = Terminal(endpoint_from)
        self.to_terminal = Terminal(endpoint_to)

        # =============================================================
        # EQUIPMENT RATINGS
        # =============================================================

        self.voltage_kv = float(voltage_kv)
        self.rated_current_a = float(rated_current_a)
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

        self.closed = True

        # =============================================================
        # EQUIPMENT CONDITION
        # =============================================================

        self.failed = False

        # =============================================================
        # VALIDATION
        # =============================================================

        self._validate_parameters()

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def from_endpoint(self):
        """
        Return the from-side electrical endpoint.
        """

        return self.from_terminal.bus

    @property
    def to_endpoint(self):
        """
        Return the to-side electrical endpoint.
        """

        return self.to_terminal.bus

    def endpoints(self):
        """
        Return the breaker endpoint pair.

        Returns
        -------
        tuple
            ``(from_endpoint, to_endpoint)``
        """

        return (
            self.from_endpoint,
            self.to_endpoint,
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_parameters(self) -> None:
        """
        Validate local breaker parameters.

        System-level topology and equipment compatibility rules belong
        to the network layer.
        """

        if not isfinite(self.voltage_kv):
            raise ValueError(
                f"Breaker '{self.id}' voltage rating must be finite."
            )

        if self.voltage_kv <= 0.0:
            raise ValueError(
                f"Breaker '{self.id}' voltage rating must be "
                "greater than zero."
            )

        if not isfinite(self.rated_current_a):
            raise ValueError(
                f"Breaker '{self.id}' rated current must be finite."
            )

        if self.rated_current_a <= 0.0:
            raise ValueError(
                f"Breaker '{self.id}' rated current must be "
                "greater than zero."
            )

        if not isfinite(self.interrupting_capacity_ka):
            raise ValueError(
                f"Breaker '{self.id}' interrupting capacity "
                "must be finite."
            )

        if self.interrupting_capacity_ka <= 0.0:
            raise ValueError(
                f"Breaker '{self.id}' interrupting capacity "
                "must be greater than zero."
            )

        if not isfinite(self.trip_time):
            raise ValueError(
                f"Breaker '{self.id}' trip time must be finite."
            )

        if self.trip_time < 0.0:
            raise ValueError(
                f"Breaker '{self.id}' trip time cannot be negative."
            )

        if not isfinite(self.close_time):
            raise ValueError(
                f"Breaker '{self.id}' close time must be finite."
            )

        if self.close_time < 0.0:
            raise ValueError(
                f"Breaker '{self.id}' close time cannot be negative."
            )

    # =================================================================
    # OPERATING STATE
    # =================================================================

    def open(self) -> None:
        """
        Open the circuit breaker.

        This changes only the local physical state.

        The network layer is responsible for applying the resulting
        topology change to the active network representation.
        """

        self.closed = False

    def close(self) -> None:
        """
        Close the circuit breaker.

        This changes only the local physical state.

        The network layer is responsible for applying the resulting
        topology change to the active network representation.
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

    @property
    def is_open(self) -> bool:
        """
        Return True when the breaker is physically open.
        """

        return not self.closed

    @property
    def is_failed(self) -> bool:
        """
        Return True when the breaker is marked failed.
        """

        return self.failed

    # =================================================================
    # FAILURE STATE
    # =================================================================

    def mark_failed(self) -> None:
        """
        Mark the breaker as failed.

        This records equipment condition only.

        Breaker-failure detection logic belongs to protection/simulation
        layers.
        """

        self.failed = True

    def clear_failure(self) -> None:
        """
        Clear the breaker equipment-failure state.
        """

        self.failed = False

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured breaker information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "from_endpoint": self.from_endpoint.id,
            "to_endpoint": self.to_endpoint.id,
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

        return (
            f"<Breaker "
            f"id={self.id}, "
            f"{self.from_endpoint.id} -> "
            f"{self.to_endpoint.id}, "
            f"voltage={self.voltage_kv:.3f} kV, "
            f"rated={self.rated_current_a:.2f} A, "
            f"interrupting="
            f"{self.interrupting_capacity_ka:.2f} kA, "
            f"closed={self.closed}, "
            f"failed={self.failed}>"
        )
