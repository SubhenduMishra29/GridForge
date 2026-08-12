```python
# core/model/disconnector.py

"""
GridForge Disconnector Model
============================

GridForge Model Layer V2

Defines the physical electrical disconnector / isolator model.

Architecture
------------

A Disconnector is a physical two-terminal switching device used for
electrical isolation.

    Equipment A
        │
     Terminal
        │
   Disconnector
        │
     Terminal
        │
    Equipment B

Typical applications include:

    Bus ── Disconnector ── Breaker
    Bus ── Disconnector ── Line
    Bus ── Disconnector ── Transformer
    Bus ── Disconnector ── Bus

The Disconnector owns its two physical terminals.

The terminals identify local physical connection points. The network
layer is responsible for assembling those terminals into the global
physical and electrical topology.

A Disconnector differs fundamentally from a Circuit Breaker:

    Disconnector
        - provides electrical isolation
        - normally operates without interrupting fault current
        - does not provide protection interruption capability

    Circuit Breaker
        - provides switching
        - can interrupt load/fault current within its ratings
        - participates in protection clearing

The Disconnector model therefore stores physical switching state but
does not implement protection or topology logic.

Responsibilities
----------------

The Disconnector model provides:

- Physical two-terminal electrical equipment.
- Disconnector identity.
- Local terminal ownership.
- Voltage rating.
- Continuous current rating.
- Mechanical operating time.
- Open/closed physical state.
- Equipment service state.
- Basic local parameter validation.
- Diagnostic information.

The Disconnector model does NOT:

- Build global topology.
- Register terminals with the network.
- Determine electrical connectivity.
- Build Y-bus matrices.
- Perform load-flow calculations.
- Perform short-circuit calculations.
- Detect faults.
- Perform protection calculations.
- Issue breaker/disconnector control commands.
- Perform dynamic simulation.
- Store simulation event history.
- Store GUI geometry.

Those responsibilities belong to the appropriate GridForge layers.

State Ownership
---------------

The Disconnector owns its authoritative physical state:

    OPEN
    CLOSED

It also stores whether the physical equipment is in service.

The model does not store operation history.

A simulation/event layer may separately record:

    time
    disconnector
    command
    resulting state

without making that history part of the authoritative equipment model.

Topology
--------

The authoritative local connection points are:

    from_terminal
    to_terminal

Their actual network connectivity is assembled by the network/topology
layer.

Changing the Disconnector state changes only the physical equipment
state. The network layer derives the corresponding electrical topology.

GridForge V2 Status
-------------------

This module is part of the GridForge Model Layer V2 baseline.

The Disconnector is a fundamental switchgear model and therefore
belongs in ``core/model``.

Detailed topology, protection, control and simulation behavior remains
outside this module.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# DISCONNECTOR
# =====================================================================

class Disconnector(ElectricalObject):
    """
    GridForge physical electrical disconnector / isolator.

    A Disconnector is a two-terminal physical switching device used
    primarily for electrical isolation.

    Parameters
    ----------
    id : str
        Unique GridForge disconnector identifier.

    voltage_kv : float
        Rated operating voltage in kV.

    rated_current_a : float
        Continuous current rating in amperes.

    endpoint_from : optional
        Initial from-side electrical endpoint.

        Normally this should remain ``None`` until the network/topology
        assembly establishes the physical connection.

    endpoint_to : optional
        Initial to-side electrical endpoint.

    operating_time : float, optional
        Mechanical operating time in seconds.

    closed : bool, optional
        Initial physical state.

        ``True`` means the disconnector is physically closed.
        ``False`` means the disconnector is physically open.

    in_service : bool, optional
        Equipment service state.

    name : str, optional
        Human-readable disconnector name.

    Notes
    -----
    The Disconnector owns its physical terminals.

    It does not own or manipulate the global network topology.

    In particular, ``open()`` and ``close()`` modify only the local
    physical state. The network/topology layer is responsible for
    deriving the resulting electrical connectivity.
    """

    def __init__(
        self,
        id: str,
        voltage_kv: float,
        rated_current_a: float,
        endpoint_from=None,
        endpoint_to=None,
        operating_time: float = 1.0,
        closed: bool = True,
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
        # EQUIPMENT RATINGS
        # =============================================================

        self.voltage_kv = float(voltage_kv)

        self.rated_current_a = float(
            rated_current_a
        )

        # =============================================================
        # OPERATING CHARACTERISTICS
        # =============================================================

        self.operating_time = float(
            operating_time
        )

        # =============================================================
        # PHYSICAL STATE
        # =============================================================

        self.closed = bool(closed)

        # =============================================================
        # SERVICE STATE
        # =============================================================

        self.in_service = bool(in_service)

        # =============================================================
        # LOCAL VALIDATION
        # =============================================================

        self._validate_parameters()

    # =================================================================
    # ENDPOINT ACCESS
    # =================================================================

    @property
    def from_endpoint(self):
        """
        Return the local from-side endpoint.

        Returns
        -------
        object or None
            Endpoint currently referenced by ``from_terminal``.
        """

        return self.from_terminal.endpoint

    @property
    def to_endpoint(self):
        """
        Return the local to-side endpoint.

        Returns
        -------
        object or None
            Endpoint currently referenced by ``to_terminal``.
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

        This changes only the terminal's local endpoint reference.

        Global topology remains the responsibility of
        ``core/network``.
        """

        self.from_terminal.connect(endpoint)

    def connect_to(self, endpoint) -> None:
        """
        Connect the to-side terminal to a local endpoint.

        This changes only the terminal's local endpoint reference.

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
    # LOCAL CONNECTION STATE
    # =================================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both physical terminals have local endpoints.
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
        Validate local disconnector parameters.

        This performs only object-level validation.

        Network-level electrical compatibility and topology rules
        belong to ``core/network`` and ``core/validation``.
        """

        if not isfinite(self.voltage_kv):
            raise ValueError(
                f"Disconnector '{self.id}' voltage rating "
                "must be finite."
            )

        if self.voltage_kv <= 0.0:
            raise ValueError(
                f"Disconnector '{self.id}' voltage rating "
                "must be greater than zero."
            )

        if not isfinite(self.rated_current_a):
            raise ValueError(
                f"Disconnector '{self.id}' rated current "
                "must be finite."
            )

        if self.rated_current_a <= 0.0:
            raise ValueError(
                f"Disconnector '{self.id}' rated current "
                "must be greater than zero."
            )

        if not isfinite(self.operating_time):
            raise ValueError(
                f"Disconnector '{self.id}' operating time "
                "must be finite."
            )

        if self.operating_time < 0.0:
            raise ValueError(
                f"Disconnector '{self.id}' operating time "
                "cannot be negative."
            )

    # =================================================================
    # OPERATING STATE
    # =================================================================

    def open(self) -> None:
        """
        Open the disconnector.

        This changes only the authoritative local physical state.

        The network layer must derive the corresponding electrical
        topology from this state.
        """

        self.closed = False

    def close(self) -> None:
        """
        Close the disconnector.

        This changes only the authoritative local physical state.

        The network layer must derive the corresponding electrical
        topology from this state.
        """

        self.closed = True

    # =================================================================
    # STATUS
    # =================================================================

    @property
    def is_closed(self) -> bool:
        """
        Return True when the disconnector is physically closed.
        """

        return self.closed

    @property
    def is_open(self) -> bool:
        """
        Return True when the disconnector is physically open.
        """

        return not self.closed

    @property
    def is_in_service(self) -> bool:
        """
        Return True when the disconnector is in service.
        """

        return self.in_service

    # =================================================================
    # SERVICE STATE
    # =================================================================

    def put_in_service(self) -> None:
        """
        Mark the physical disconnector as in service.

        This changes only local equipment state.
        """

        self.in_service = True

    def take_out_of_service(self) -> None:
        """
        Mark the physical disconnector as out of service.

        This changes only local equipment state.

        The network layer is responsible for applying the resulting
        state to the derived topology.
        """

        self.in_service = False

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured disconnector information.
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
            "operating_time": self.operating_time,
            "closed": self.closed,
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
            f"<Disconnector "
            f"id={self.id}, "
            f"{from_id} -> {to_id}, "
            f"voltage={self.voltage_kv:.3f} kV, "
            f"rated={self.rated_current_a:.2f} A, "
            f"closed={self.closed}, "
            f"in_service={self.in_service}>"
        )
```
