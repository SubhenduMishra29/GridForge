# core/model/terminal.py

"""
GridForge Terminal Model
========================

GridForge Model Layer V2

Defines the physical electrical Terminal abstraction used by
GridForge equipment models.

Architecture
------------
A Terminal represents a physical electrical connection point belonging
to an electrical equipment model.

The Terminal is NOT the global network topology.

A Terminal identifies a local connection point of equipment. The
network layer remains responsible for determining and maintaining
global electrical topology.

Examples
--------
Load:

    Load
      |
    Terminal
      |
      +---- Network topology ---- Bus

Breaker:

    Breaker
    |      |
    from   to
    terminal terminal

    Bus -- Breaker -- Load

Line:

    Line
    |    |
    from to

    Bus -- Line -- Bus

Transformer:

    Transformer
    |          |
    from       to

    Bus -- Transformer -- Bus

Responsibilities
----------------
The Terminal:

- Represents a physical electrical connection point.
- Stores its owning equipment object when provided.
- Stores its local connection endpoint.
- Provides connection state.
- Provides local connection validation.
- Provides connection diagnostics.
- Provides compatibility access to a connected Bus.

The Terminal does NOT:

- Build global network topology.
- Register itself with the network.
- Modify the network graph.
- Determine global electrical connectivity.
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
A Terminal belongs to an equipment model.

Examples:

    Load
      |
    terminal

    Breaker
    |      |
    from   to
    terminal terminal

    Line
    |    |
    from to
    terminal terminal

The owner is local model information.

The Terminal does not register itself with the owner or network.

Connection Model
----------------
A Terminal contains a local connection endpoint.

The endpoint may represent:

- a Bus-like object;
- another Terminal.

This allows physical equipment connections such as:

    Bus -- Breaker -- Load

without making the Breaker directly own or manipulate global
network topology.

The network layer remains responsible for validating complete
network connections and constructing the global topology.

Bus Compatibility
-----------------
Historically GridForge terminals were Bus-specific.

For compatibility with existing Model/Network interfaces, the
Terminal provides:

    terminal.bus

This property returns the connected Bus when the endpoint is
Bus-like.

If the endpoint is another Terminal, ``terminal.bus`` follows the
terminal connection when possible.

The authoritative local connection reference remains:

    terminal.endpoint

The Terminal deliberately does not import the concrete Bus class.

Validation
----------
The Terminal validates only the local endpoint contract.

An endpoint must expose a non-empty string ``id`` attribute.

A Terminal may connect directly to another Terminal.

The Terminal does not determine whether a connection is electrically
legal. That belongs to ``core/network``.

Disconnection
-------------
A Terminal may be locally disconnected:

    terminal.disconnect()

A disconnected Terminal has:

    endpoint = None

This modifies only the local model reference.

GridForge V2 Status
-------------------
This module is part of the GridForge Model Layer V2 baseline.

This revision replaces the original Bus-only Terminal abstraction.

The generalized terminal architecture supports physical switching
equipment and general equipment connection points while preserving
the separation between:

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
        Local electrical connection endpoint.

        The endpoint may be a Bus-like object or another Terminal.

    owner :
        Optional owning equipment object.

        The owner is local model information and is not registered
        automatically with the network.
    """

    def __init__(
        self,
        endpoint=None,
        owner=None,
    ) -> None:
        """
        Create a GridForge Terminal.

        Parameters
        ----------
        endpoint :
            Initial local connection endpoint.

        owner :
            Equipment object owning this Terminal.

        Notes
        -----
        ``endpoint`` may be None when creating a disconnected
        Terminal.
        """

        if owner is not None:
            self._validate_owner(owner)

        if endpoint is not None:
            self._validate_endpoint(endpoint)

        self.owner = owner
        self.endpoint = endpoint

    # =================================================================
    # VALIDATION
    # =================================================================

    @staticmethod
    def _validate_owner(owner) -> None:
        """
        Validate the minimum owner contract.

        The owner must expose a non-empty string ``id`` attribute.
        """

        if not hasattr(owner, "id"):
            raise TypeError(
                "Terminal owner requires an object with an "
                "'id' attribute."
            )

        owner_id = getattr(owner, "id")

        if not isinstance(owner_id, str):
            raise TypeError(
                "Terminal owner ID must be a string."
            )

        if not owner_id.strip():
            raise ValueError(
                "Terminal owner cannot have an empty ID."
            )

    @staticmethod
    def _validate_endpoint(endpoint) -> None:
        """
        Validate the minimum local endpoint contract.

        An endpoint must expose a non-empty string ``id`` attribute.

        Concrete endpoint compatibility is deliberately not validated
        here because that is a network/topology responsibility.
        """

        if endpoint is None:
            raise ValueError(
                "Terminal endpoint cannot be None during connection."
            )

        if not hasattr(endpoint, "id"):
            raise TypeError(
                "Terminal endpoint requires an object with an "
                "'id' attribute."
            )

        endpoint_id = getattr(endpoint, "id")

        if not isinstance(endpoint_id, str):
            raise TypeError(
                "Terminal endpoint ID must be a string."
            )

        if not endpoint_id.strip():
            raise ValueError(
                "Terminal endpoint cannot have an empty ID."
            )

    # =================================================================
    # CONNECTION
    # =================================================================

    def connect(self, endpoint) -> None:
        """
        Connect this Terminal to an electrical endpoint.

        This changes only the local endpoint reference.

        It does NOT:

        - modify global topology;
        - register the terminal;
        - update the network graph;
        - rebuild Y-bus;
        - update solver structures.
        """

        self._validate_endpoint(endpoint)

        self.endpoint = endpoint

    # =================================================================
    # DISCONNECTION
    # =================================================================

    def disconnect(self) -> None:
        """
        Disconnect this Terminal from its local endpoint.

        This changes only the local model reference.
        """

        self.endpoint = None

    # =================================================================
    # CONNECTION STATE
    # =================================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when this Terminal has a local endpoint.
        """

        return self.endpoint is not None

    # =================================================================
    # BUS COMPATIBILITY
    # =================================================================

    @property
    def bus(self):
        """
        Return the Bus associated with this Terminal when available.

        Returns
        -------
        object or None
            Connected Bus-like object, or None.

        Notes
        -----
        This is a compatibility accessor for existing GridForge code.

        It is derived from ``endpoint``.

        If the endpoint is another Terminal, the terminal chain is
        followed until a non-Terminal endpoint is reached.

        A cyclic Terminal connection returns None rather than entering
        infinite recursion.
        """

        endpoint = self.endpoint

        if endpoint is None:
            return None

        visited: set[int] = set()

        while isinstance(endpoint, Terminal):
            object_id = id(endpoint)

            if object_id in visited:
                return None

            visited.add(object_id)

            if endpoint.endpoint is None:
                return None

            endpoint = endpoint.endpoint

        return endpoint

    # =================================================================
    # ENDPOINT INFORMATION
    # =================================================================

    @property
    def endpoint_id(self) -> str | None:
        """
        Return the connected endpoint identifier.
        """

        if self.endpoint is None:
            return None

        return self.endpoint.id

    # =================================================================
    # OWNER INFORMATION
    # =================================================================

    @property
    def owner_id(self) -> str | None:
        """
        Return the owning equipment identifier.
        """

        if self.owner is None:
            return None

        return self.owner.id

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured Terminal information.
        """

        bus = self.bus

        return {
            "owner": self.owner_id,
            "endpoint": self.endpoint_id,
            "connected": self.is_connected,
            "bus": (
                bus.id
                if bus is not None
                else None
            ),
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<Terminal "
            f"owner={self.owner_id}, "
            f"endpoint={self.endpoint_id}>"
        )
