# core/model/terminal.py

"""
GridForge Terminal Model
========================

GridForge Model Layer V2

Defines the physical electrical Terminal abstraction used by GridForge
equipment models.

Architecture
------------
A Terminal represents a physical electrical connection point belonging
to an electrical equipment model.

The Terminal is deliberately NOT the network topology.

A terminal identifies the local connection point of equipment. The
network layer is responsible for determining how terminals and buses
are connected within the global electrical topology.

Examples
--------

A load:

    Load
      │
    Terminal
      │
      └──── Network topology ──── Bus

A breaker:

    Breaker
    ├── from_terminal
    └── to_terminal

    Bus ── Breaker ── Load

A line:

    Line
    ├── from_terminal
    └── to_terminal

    Bus ── Line ── Bus

A transformer:

    Transformer
    ├── from_terminal
    └── to_terminal

    Bus ── Transformer ── Bus

A breaker inserted into an equipment connection:

    Bus
      │
    Breaker.from_terminal
      │
    Breaker
      │
    Breaker.to_terminal
      │
    Load.terminal
      │
    Load

Responsibilities
----------------
The Terminal:

- Represents a physical electrical connection point.
- Stores its owning equipment object.
- Stores its locally connected endpoint when applicable.
- Provides connection state.
- Provides local connection validation.
- Provides connection diagnostics.
- Provides compatibility access to a Bus when the endpoint is a Bus.

The Terminal does NOT:

- Build global network topology.
- Register itself with the network.
- Modify the network graph.
- Determine electrical connectivity globally.
- Build Y-bus matrices.
- Calculate electrical quantities.
- Perform load-flow calculations.
- Perform short-circuit calculations.
- Perform protection calculations.
- Perform dynamic simulation.
- Manage GUI objects.

Those responsibilities belong to the appropriate GridForge layers.

Ownership
---------
The Terminal belongs to an equipment model.

For example:

    Load
      └── Terminal

    Breaker
      ├── from_terminal
      └── to_terminal

    Line
      ├── from_terminal
      └── to_terminal

The Terminal does not own or register the connected endpoint.

Connection Model
---------------
The local Terminal connection is represented as:

    Terminal
        │
        ▼
    endpoint

The endpoint must satisfy the GridForge electrical-object contract
required by the model layer.

The network layer determines whether that endpoint represents a
currently valid network connection.

Bus Compatibility
-----------------
Historically GridForge terminals were Bus-specific.

For compatibility with the existing frozen Model/Network interfaces,
the Terminal provides:

    terminal.bus

when its endpoint is a Bus-like object.

This property is a derived compatibility interface.

The authoritative local reference is:

    terminal.endpoint

New equipment models should use ``endpoint`` internally when a
general physical connection point is required.

The Terminal does not import the concrete Bus class. This preserves
the existing dependency direction and avoids unnecessary circular
dependencies.

Validation
----------
The Terminal validates only the local endpoint contract.

It requires:

- endpoint is not None when connected;
- endpoint exposes a non-empty string ``id``.

It does not determine whether the endpoint is legally connectable to
another object.

Connection compatibility and topology rules belong to
``core/network/``.

Disconnection
-------------
A Terminal may be locally disconnected:

    terminal.disconnect()

A disconnected terminal has:

    endpoint = None

This does not modify global network topology.

The network layer must perform any required topology update.

GridForge V2 Status
-------------------
This module is part of the GridForge Model Layer V2 baseline.

This revision is a fundamental correction to the original Bus-only
Terminal abstraction.

The change is required to support physical switching equipment and
general equipment connection points while preserving the separation
between:

    core/model
        physical equipment state

    core/network
        global electrical topology

    core/solver
        numerical computation

    core/analysis
        study interfaces

    core/protection
        protection logic

    core/simulation
        time-domain/event execution

Future changes require evidence of a genuinely fundamental
architectural requirement.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


# =====================================================================
# TERMINAL
# =====================================================================

class Terminal:
    """
    GridForge physical electrical connection point.

    Parameters
    ----------
    endpoint :
        Electrical endpoint to which this terminal is locally connected.

        The endpoint must expose a non-empty string ``id`` attribute.

    Notes
    -----
    The Terminal deliberately does not import concrete GridForge model
    classes such as Bus, Load, Generator, or Breaker.

    This keeps the model dependency graph lightweight and prevents
    unnecessary circular dependencies.

    The network layer remains responsible for determining whether the
    endpoint relationship is valid within the global network.
    """

    def __init__(self, endpoint):
        """
        Create a Terminal.

        Parameters
        ----------
        endpoint :
            Initial electrical endpoint.

        Notes
        -----
        ``endpoint`` may be ``None`` only after explicit
        disconnection.

        Construction requires a valid connected endpoint.
        """

        self._validate_endpoint(endpoint)

        self.endpoint = endpoint

    # =================================================================
    # VALIDATION
    # =================================================================

    @staticmethod
    def _validate_endpoint(endpoint) -> None:
        """
        Validate the minimum electrical-endpoint contract.

        The Terminal intentionally does not import concrete model
        classes.

        The endpoint must expose:

            id : str

        with a non-empty identifier.

        This is local model validation only.

        Network-wide compatibility rules belong to ``core/network``.
        """

        if endpoint is None:
            raise ValueError(
                "Terminal must be connected to a valid electrical endpoint."
            )

        if not hasattr(endpoint, "id"):
            raise TypeError(
                "Terminal requires an electrical endpoint with "
                "an 'id' attribute."
            )

        endpoint_id = getattr(endpoint, "id")

        if not isinstance(endpoint_id, str):
            raise TypeError(
                "Terminal endpoint ID must be a string."
            )

        if not endpoint_id.strip():
            raise ValueError(
                "Terminal cannot connect to an endpoint with "
                "an empty ID."
            )

    # =================================================================
    # CONNECTION
    # =================================================================

    def connect(self, endpoint) -> None:
        """
        Connect this Terminal to an electrical endpoint.

        Parameters
        ----------
        endpoint :
            New electrical endpoint.

        Notes
        -----
        This changes only the local endpoint reference.

        It does NOT:

        - modify global topology;
        - register the terminal;
        - update the network graph;
        - rebuild Y-bus;
        - update solver structures.

        Those operations belong to the appropriate network layer.
        """

        self._validate_endpoint(endpoint)

        self.endpoint = endpoint

    # =================================================================
    # DISCONNECTION
    # =================================================================

    def disconnect(self) -> None:
        """
        Disconnect this Terminal from its local endpoint.

        Notes
        -----
        A disconnected Terminal has:

            endpoint = None

        This changes only the local model reference.

        It does not modify global network topology.
        """

        self.endpoint = None

    # =================================================================
    # CONNECTION STATE
    # =================================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when the Terminal has a connected endpoint.
        """

        return self.endpoint is not None

    # =================================================================
    # BUS COMPATIBILITY
    # =================================================================

    @property
    def bus(self):
        """
        Return the connected Bus when the endpoint is Bus-like.

        This property preserves compatibility with the existing
        GridForge Model/Network interfaces that use:

            terminal.bus

        The property is derived from ``endpoint``.

        Returns
        -------
        object or None
            The endpoint when it exposes the Bus contract, otherwise
            ``None``.

        Notes
        -----
        The Terminal deliberately does not import ``Bus``.

        A Bus-like endpoint is identified structurally by its
        ``id`` attribute.

        Network-layer validation remains responsible for determining
        whether the endpoint is actually a registered GridForge Bus.
        """

        if self.endpoint is None:
            return None

        return self.endpoint

    # =================================================================
    # ENDPOINT ID
    # =================================================================

    @property
    def endpoint_id(self) -> str | None:
        """
        Return the connected endpoint identifier.

        Returns
        -------
        str or None
            Endpoint ID when connected, otherwise ``None``.
        """

        if self.endpoint is None:
            return None

        return self.endpoint.id

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return Terminal connection information.

        Returns
        -------
        dict
            Structured local terminal information.
        """

        return {
            "endpoint": self.endpoint_id,
            "connected": self.is_connected,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        if self.endpoint is None:
            return "<Terminal endpoint=None>"

        return (
            f"<Terminal "
            f"endpoint={self.endpoint.id}>"
        )
