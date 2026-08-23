# core/model/terminal.py
"""
GridForge V2 Terminal Model
===========================

Author:
    Subhendu Mishra

Defines the physical electrical Terminal abstraction used by
GridForge equipment models.

Architecture
------------

A Terminal represents a local physical connection point belonging
to an equipment model.

    Equipment
        |
     Terminal
        |
     endpoint
        |
        +---- Bus
        |
        +---- Terminal

The Terminal is NOT the global network topology.

Responsibilities
----------------

The Terminal:

    - represents one local equipment connection point;
    - stores its owning equipment;
    - stores its local connection endpoint;
    - stores an optional local terminal role;
    - provides connection state;
    - provides local endpoint validation;
    - provides connection diagnostics;
    - provides compatibility access to a connected Bus-like object.

The Terminal does NOT:

    - build global network topology;
    - register itself with the network;
    - modify the network graph;
    - determine global electrical connectivity;
    - build Y-bus matrices;
    - perform load-flow calculations;
    - perform short-circuit calculations;
    - perform protection calculations;
    - perform dynamic simulation;
    - manage GUI objects.

Those responsibilities belong to the appropriate GridForge layers.

Identity
--------

A Terminal is not an independent equipment object.

It therefore does NOT inherit from ElectricalObject.

A Terminal may optionally have a local role such as:

    P1
    P2
    S1
    S2
    H1
    H2
    X1
    X2
    from
    to

The equipment remains the owner of the Terminal.

The optional role is descriptive interface information and is not
a globally unique model identifier.

Connection Model
----------------

The authoritative local connection reference is:

    terminal.endpoint

The endpoint may be:

    - a Bus-like object;
    - another Terminal.

Terminal.connect() modifies only this local reference.

The network layer remains responsible for determining whether the
connection is electrically legal and for maintaining global
topology.

Bus Compatibility
-----------------

For compatibility with existing GridForge interfaces:

    terminal.bus

returns the Bus-like endpoint when available.

If the endpoint is another Terminal, the terminal chain is followed
when possible.

Cycle detection prevents recursive terminal connections from
causing infinite traversal.

Validation
----------

Terminal validation is local only.

The owner, when present, must expose:

    owner.id

The endpoint, when present, must expose:

    endpoint.id

The Terminal does not validate electrical compatibility. That is
the responsibility of core/network.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any


# =====================================================================
# TERMINAL
# =====================================================================


class Terminal:
    """
    GridForge physical electrical connection point.

    Parameters
    ----------
    endpoint:
        Initial local connection endpoint.

    owner:
        Optional owning equipment object.

    role:
        Optional local terminal role, for example ``P1``, ``H1``,
        ``from``, or ``to``.
    """

    def __init__(
        self,
        endpoint: Any = None,
        owner: Any = None,
        role: str | None = None,
    ) -> None:
        """
        Create a GridForge Terminal.

        ``endpoint`` may be None when creating a disconnected
        terminal.
        """

        if owner is not None:
            self._validate_owner(owner)

        role = self._normalize_role(role)

        if endpoint is not None:
            self._validate_endpoint(endpoint)

        self.owner = owner
        self.role = role
        self.endpoint = endpoint

        self.validate()

    # =================================================================
    # ROLE
    # =================================================================

    @staticmethod
    def _normalize_role(
        role: str | None,
    ) -> str | None:
        """
        Normalize an optional terminal role.
        """

        if role is None:
            return None

        if not isinstance(role, str):
            raise TypeError(
                "Terminal role must be a string or None."
            )

        role = role.strip()

        if not role:
            return None

        return role

    @property
    def terminal_role(self) -> str | None:
        """
        Return the local terminal role.

        This is an alias for ``role``.
        """

        return self.role

    # =================================================================
    # VALIDATION
    # =================================================================

    @staticmethod
    def _validate_owner(
        owner: Any,
    ) -> None:
        """
        Validate the minimum owner contract.

        The owner must expose a non-empty string ``id`` attribute.
        """

        if not hasattr(owner, "id"):
            raise TypeError(
                "Terminal owner requires an object with "
                "an 'id' attribute."
            )

        owner_id = getattr(
            owner,
            "id",
        )

        if not isinstance(owner_id, str):
            raise TypeError(
                "Terminal owner ID must be a string."
            )

        if not owner_id.strip():
            raise ValueError(
                "Terminal owner cannot have an empty ID."
            )

    @staticmethod
    def _validate_endpoint(
        endpoint: Any,
    ) -> None:
        """
        Validate the minimum local endpoint contract.

        An endpoint must expose a non-empty string ``id`` attribute.

        Concrete electrical compatibility is deliberately not
        validated here because that belongs to core/network.
        """

        if endpoint is None:
            raise ValueError(
                "Terminal endpoint cannot be None during "
                "connection."
            )

        if not hasattr(endpoint, "id"):
            raise TypeError(
                "Terminal endpoint requires an object with "
                "an 'id' attribute."
            )

        endpoint_id = getattr(
            endpoint,
            "id",
        )

        if not isinstance(endpoint_id, str):
            raise TypeError(
                "Terminal endpoint ID must be a string."
            )

        if not endpoint_id.strip():
            raise ValueError(
                "Terminal endpoint cannot have an empty ID."
            )

    def validate_parameters(self) -> bool:
        """
        Validate Terminal-local parameters.

        This validates only:

            - owner contract;
            - role;
            - endpoint contract.

        It does not validate electrical topology.
        """

        if self.owner is not None:
            self._validate_owner(
                self.owner,
            )

        if self.role is not None:
            if not isinstance(
                self.role,
                str,
            ):
                raise TypeError(
                    "Terminal role must be a string or None."
                )

            if not self.role.strip():
                raise ValueError(
                    "Terminal role cannot be empty."
                )

        if self.endpoint is not None:
            self._validate_endpoint(
                self.endpoint,
            )

        return True

    def validate(self) -> bool:
        """
        Public Terminal validation entry point.
        """

        return self.validate_parameters()

    # =================================================================
    # CONNECTION
    # =================================================================

    def connect(
        self,
        endpoint: Any,
    ) -> None:
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

        self._validate_endpoint(
            endpoint,
        )

        self.endpoint = endpoint

        self.validate()

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
    def bus(self) -> Any:
        """
        Return the Bus-like object associated with this Terminal.

        If the endpoint is another Terminal, follow the local terminal
        chain until a non-Terminal endpoint is reached.

        Cyclic terminal connections return None.

        This is a compatibility accessor only.

        The authoritative local connection remains:

            terminal.endpoint
        """

        endpoint = self.endpoint

        if endpoint is None:
            return None

        visited: set[int] = set()

        while isinstance(
            endpoint,
            Terminal,
        ):
            object_identity = id(endpoint)

            if object_identity in visited:
                return None

            visited.add(
                object_identity,
            )

            endpoint = endpoint.endpoint

            if endpoint is None:
                return None

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

    def summary(self) -> dict[str, Any]:
        """
        Return structured Terminal information.
        """

        bus = self.bus

        return {
            "owner": self.owner_id,
            "role": self.role,
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
            f"role={self.role!r}, "
            f"endpoint={self.endpoint_id}>"
        )


__all__ = [
    "Terminal",
]
