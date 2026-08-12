# core/model/fuse.py

"""
GridForge Fuse Model
====================

GridForge Model Layer V2

Defines the physical electrical fuse model.

Architecture
------------

A Fuse is a physical two-terminal series protection device.

    Equipment A
        │
     Terminal
        │
       Fuse
        │
     Terminal
        │
    Equipment B

Typical applications include:

    Bus ── Fuse ── Load
    Bus ── Fuse ── Transformer
    Bus ── Fuse ── Motor
    Bus ── Fuse ── Auxiliary circuit

The Fuse owns its two physical terminals.

The terminals identify local physical connection points. The
network/topology layer is responsible for assembling those terminals
into the global physical and electrical topology.

A Fuse differs from a Circuit Breaker:

    Fuse
        - passive protection device
        - normally conducts while intact
        - operates by melting/opening its fusible element
        - does not normally have a remote close command
        - replacement/reset is an equipment operation

    Circuit Breaker
        - actively operated switching device
        - can be opened and closed by a control/protection system
        - has specified interruption and operating characteristics

Responsibilities
----------------

The Fuse model provides:

- Physical two-terminal electrical equipment.
- Fuse identity.
- Local terminal ownership.
- Voltage rating.
- Continuous current rating.
- Interrupting rating.
- Fuse operating/current rating.
- Physical intact/blown state.
- Equipment service state.
- Basic local parameter validation.
- Diagnostic information.

The Fuse model does NOT:

- Detect faults.
- Calculate fault current.
- Determine fuse operating time from a fault.
- Implement time-current curves.
- Perform protection coordination.
- Build global topology.
- Register terminals with the network.
- Build Y-bus matrices.
- Perform load-flow calculations.
- Perform short-circuit calculations.
- Perform contingency analysis.
- Perform dynamic simulation.
- Store simulation event history.
- Store GUI geometry.

Those responsibilities belong to the appropriate GridForge layers.

State Ownership
---------------

The Fuse owns its authoritative physical state:

    INTACT
    BLOWN

It also stores whether the equipment is in service.

A blown fuse is electrically open.

The model does not store operation history.

A protection/simulation layer may separately record:

    time
    fuse
    initiating condition
    operation
    resulting state

without making that history part of the authoritative equipment model.

Topology
--------

The authoritative local connection points are:

    from_terminal
    to_terminal

The Electrical Topology layer determines whether the fuse contributes
a conductive branch.

Conceptually:

    INTACT + IN_SERVICE
        -> conductive

    BLOWN
        -> open

    OUT_OF_SERVICE
        -> excluded from active topology

The Fuse model itself does not modify the topology graph.

GridForge V2 Status
-------------------

This module is part of the GridForge Model Layer V2 baseline.

The Fuse is a fundamental physical electrical protection component
and therefore belongs in ``core/model``.

Detailed protection behavior, time-current characteristics,
coordination, topology derivation, and simulation events remain
outside this module.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from enum import Enum
from math import isfinite

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# FUSE STATE
# =====================================================================

class FuseState(Enum):
    """
    Authoritative physical fuse state.

    INTACT
        Fusible element is physically intact and electrically
        conductive.

    BLOWN
        Fusible element has operated and the electrical path is open.
    """

    INTACT = 1
    BLOWN = 2


# =====================================================================
# FUSE
# =====================================================================

class Fuse(ElectricalObject):
    """
    GridForge physical electrical fuse.

    A Fuse is a two-terminal passive series protection device.

    Parameters
    ----------
    id : str
        Unique GridForge fuse identifier.

    voltage_kv : float
        Rated operating voltage in kV.

    rated_current_a : float
        Continuous current rating in amperes.

    interrupting_capacity_ka : float
        Symmetrical interrupting-current capability in kA.

    fuse_current_a : float
        Nominal fuse operating/current rating in amperes.

    endpoint_from : optional
        Initial from-side electrical endpoint.

    endpoint_to : optional
        Initial to-side electrical endpoint.

    state : FuseState, optional
        Initial physical fuse state.

    in_service : bool, optional
        Equipment service state.

    name : str, optional
        Human-readable fuse name.

    Notes
    -----
    The Fuse owns its physical terminals.

    The Fuse does not own or manipulate global topology.

    A blown Fuse is physically open. The network layer determines the
    resulting electrical-topology consequence.
    """

    def __init__(
        self,
        id: str,
        voltage_kv: float,
        rated_current_a: float,
        interrupting_capacity_ka: float,
        fuse_current_a: float,
        endpoint_from=None,
        endpoint_to=None,
        state: FuseState = FuseState.INTACT,
        in_service: bool = True,
        name: str = "",
    ):
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
        # RATINGS
        # =============================================================

        self.voltage_kv = float(voltage_kv)

        self.rated_current_a = float(
            rated_current_a
        )

        self.interrupting_capacity_ka = float(
            interrupting_capacity_ka
        )

        self.fuse_current_a = float(
            fuse_current_a
        )

        # =============================================================
        # PHYSICAL STATE
        # =============================================================

        if not isinstance(state, FuseState):
            raise TypeError(
                "Fuse state must be a FuseState enum value."
            )

        self.state = state

        # =============================================================
        # SERVICE STATE
        # =============================================================

        self.in_service = bool(in_service)

        # =============================================================
        # VALIDATION
        # =============================================================

        self._validate_parameters()

    # =================================================================
    # ENDPOINT ACCESS
    # =================================================================

    @property
    def from_endpoint(self):
        """
        Return the local from-side endpoint.
        """

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self):
        """
        Return the local to-side endpoint.
        """

        return self.to_terminal.endpoint

    def endpoints(self):
        """
        Return the local endpoint pair.

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
    # TERMINAL CONNECTION
    # =================================================================

    def connect_from(self, endpoint) -> None:
        """
        Connect the from-side terminal to a local endpoint.

        Global topology remains the responsibility of
        ``core/network``.
        """

        self.from_terminal.connect(endpoint)

    def connect_to(self, endpoint) -> None:
        """
        Connect the to-side terminal to a local endpoint.

        Global topology remains the responsibility of
        ``core/network``.
        """

        self.to_terminal.connect(endpoint)

    def disconnect_from(self) -> None:
        """
        Disconnect the from-side terminal locally.
        """

        self.from_terminal.disconnect()

    def disconnect_to(self) -> None:
        """
        Disconnect the to-side terminal locally.
        """

        self.to_terminal.disconnect()

    # =================================================================
    # CONNECTION STATE
    # =================================================================

    @property
    def is_connected(self) -> bool:
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
        Validate local Fuse parameters.

        This performs only object-level validation.

        Network-level electrical compatibility and engineering rules
        belong to ``core/network`` and ``core/validation``.
        """

        if not isfinite(self.voltage_kv):
            raise ValueError(
                f"Fuse '{self.id}' voltage rating "
                "must be finite."
            )

        if self.voltage_kv <= 0.0:
            raise ValueError(
                f"Fuse '{self.id}' voltage rating "
                "must be greater than zero."
            )

        if not isfinite(self.rated_current_a):
            raise ValueError(
                f"Fuse '{self.id}' rated current "
                "must be finite."
            )

        if self.rated_current_a <= 0.0:
            raise ValueError(
                f"Fuse '{self.id}' rated current "
                "must be greater than zero."
            )

        if not isfinite(self.interrupting_capacity_ka):
            raise ValueError(
                f"Fuse '{self.id}' interrupting capacity "
                "must be finite."
            )

        if self.interrupting_capacity_ka <= 0.0:
            raise ValueError(
                f"Fuse '{self.id}' interrupting capacity "
                "must be greater than zero."
            )

        if not isfinite(self.fuse_current_a):
            raise ValueError(
                f"Fuse '{self.id}' fuse current "
                "must be finite."
            )

        if self.fuse_current_a <= 0.0:
            raise ValueError(
                f"Fuse '{self.id}' fuse current "
                "must be greater than zero."
            )

    # =================================================================
    # PHYSICAL STATE
    # =================================================================

    @property
    def is_intact(self) -> bool:
        """
        Return True when the fuse element is intact.
        """

        return self.state is FuseState.INTACT

    @property
    def is_blown(self) -> bool:
        """
        Return True when the fuse element has operated.
        """

        return self.state is FuseState.BLOWN

    @property
    def is_conductive(self) -> bool:
        """
        Return True when the Fuse is physically conductive.

        A Fuse contributes a conductive physical path only when it is
        intact and in service.

        This property is descriptive model state only. It does not
        modify or build network topology.
        """

        return (
            self.in_service
            and self.state is FuseState.INTACT
        )

    # =================================================================
    # FUSE OPERATION
    # =================================================================

    def blow(self) -> None:
        """
        Operate the fuse physically.

        This changes only the authoritative physical state.

        Fault detection, operating-time calculation and protection
        decisions belong to the protection/simulation layers.
        """

        self.state = FuseState.BLOWN

    # =================================================================
    # FUSE REPLACEMENT / RESET
    # =================================================================

    def reset(self) -> None:
        """
        Reset the fuse to the intact physical state.

        This represents replacement or restoration of the fuse element.

        It does not represent a protection calculation or simulation
        event.
        """

        self.state = FuseState.INTACT

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """
        Return True when the fuse is in service.
        """

        return self.in_service

    def put_in_service(self) -> None:
        """
        Mark the fuse as in service.
        """

        self.in_service = True

    def take_out_of_service(self) -> None:
        """
        Mark the fuse as out of service.

        The network layer is responsible for applying this state to
        the derived electrical topology.
        """

        self.in_service = False

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured Fuse information.
        """

        return {
            "id": self.id,
            "name": self.name,
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
            "fuse_current_a": self.fuse_current_a,
            "state": self.state.name,
            "conductive": self.is_conductive,
            "in_service": self.in_service,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        from_id = self.from_terminal.endpoint_id
        to_id = self.to_terminal.endpoint_id

        return (
            f"<Fuse "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"voltage={self.voltage_kv:.3f} kV, "
            f"rated={self.rated_current_a:.2f} A, "
            f"interrupting="
            f"{self.interrupting_capacity_ka:.2f} kA, "
            f"fuse_current="
            f"{self.fuse_current_a:.2f} A, "
            f"state={self.state.name}, "
            f"in_service={self.in_service}>"
        )
```
