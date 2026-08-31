# ============================================================
# File: core/model/terminal.py
# GridForge V2 — Terminal Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Terminal
=======================

Authoritative electrical connection point owned by an
electrical equipment model.

Architecture
------------

    Equipment
        │
        ├── owns Terminal
        │
        └── Terminal
              │
              └── endpoint
                       │
                       ▼
                    Network
                       │
                       ▼
                    Topology

Terminal is a local domain object.

It does NOT:
    - own Network topology
    - resolve Network membership
    - traverse terminal chains
    - construct Y-bus matrices
    - assign solver indices
    - perform numerical calculations
    - execute protection logic
    - manage SLD/UI state
    - mutate global Network state

Canonical contract
------------------

    Terminal
    ├── owner
    ├── role
    ├── endpoint
    ├── attach(endpoint)
    ├── detach()
    ├── is_connected
    └── validate()

Important invariants
--------------------

1. Every authoritative Terminal has an owning Equipment object.
2. Every authoritative Terminal has a semantic role.
3. Endpoint is optional until the Terminal is connected.
4. Terminal owns the endpoint reference.
5. Equipment must not maintain a duplicate endpoint reference.
6. attach() and detach() are the canonical endpoint mutation APIs.
7. is_connected is derived from endpoint.
8. Terminal never interprets global topology.
9. Terminal never imports Network, Solver, UI, SLD, or Analysis.
10. Legacy compatibility aliases are intentionally not provided.

The Network layer is responsible for interpreting Terminal
endpoints into authoritative electrical topology.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .base import ElectricalObject


class Terminal:
    """
    Authoritative electrical connection point.

    A Terminal belongs to exactly one Equipment object and may
    reference one endpoint.

    Parameters
    ----------
    owner:
        Authoritative owning Equipment object.

    role:
        Semantic role of the terminal within its owner.

    endpoint:
        Optional endpoint object. The endpoint is intentionally
        not resolved into Network topology by Terminal.

    Notes
    -----
    Terminal is deliberately small. Global connectivity belongs
    to the Network layer.
    """

    __slots__ = (
        "_owner",
        "_role",
        "_endpoint",
    )

    def __init__(
        self,
        *,
        owner: "ElectricalObject",
        role: str,
        endpoint: Any | None = None,
    ) -> None:
        """
        Create an authoritative Terminal.

        Parameters
        ----------
        owner:
            Equipment object that owns this Terminal.

        role:
            Semantic role of the Terminal.

        endpoint:
            Optional initial endpoint.

        Raises
        ------
        TypeError
            If owner or role has an invalid type.

        ValueError
            If role is empty or endpoint is invalid.
        """
        if owner is None:
            raise TypeError("Terminal owner must not be None.")

        if not isinstance(role, str):
            raise TypeError("Terminal role must be a string.")

        normalized_role = role.strip()

        if not normalized_role:
            raise ValueError("Terminal role must not be empty.")

        self._owner = owner
        self._role = normalized_role
        self._endpoint: Any | None = None

        if endpoint is not None:
            self.attach(endpoint)

        self.validate()

    # --------------------------------------------------------
    # Authoritative properties
    # --------------------------------------------------------

    @property
    def owner(self) -> "ElectricalObject":
        """
        Return the authoritative equipment owner.
        """
        return self._owner

    @property
    def role(self) -> str:
        """
        Return the semantic terminal role.
        """
        return self._role

    @property
    def endpoint(self) -> Any | None:
        """
        Return the currently attached endpoint.

        None means that the Terminal is currently disconnected.
        """
        return self._endpoint

    # --------------------------------------------------------
    # Connection state
    # --------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """
        Return True when an endpoint is attached.
        """
        return self._endpoint is not None

    # --------------------------------------------------------
    # Endpoint mutation
    # --------------------------------------------------------

    def attach(self, endpoint: Any) -> None:
        """
        Attach this Terminal to an endpoint.

        This operation changes only the local Terminal state.
        It does not modify Network topology.

        Parameters
        ----------
        endpoint:
            Endpoint object to associate with this Terminal.

        Raises
        ------
        ValueError
            If the endpoint is invalid.

        Notes
        -----
        Re-attaching replaces the current endpoint. Network-level
        topology invalidation/rebuild is outside Terminal's
        responsibility.
        """
        self._validate_endpoint(endpoint)

        self._endpoint = endpoint

        self.validate()

    def detach(self) -> None:
        """
        Detach the current endpoint.

        This operation changes only the local Terminal state.
        It does not modify Network topology.
        """
        self._endpoint = None

        self.validate()

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def validate(self) -> None:
        """
        Validate Terminal-local invariants.

        Validation is intentionally limited to this Terminal's
        own state. Network-wide validation belongs to Network.
        """
        if self._owner is None:
            raise ValueError("Terminal owner must not be None.")

        if not isinstance(self._role, str):
            raise TypeError("Terminal role must be a string.")

        if not self._role.strip():
            raise ValueError("Terminal role must not be empty.")

        if self._endpoint is not None:
            self._validate_endpoint(self._endpoint)

    # --------------------------------------------------------
    # Internal validation helpers
    # --------------------------------------------------------

    @staticmethod
    def _validate_endpoint(endpoint: Any) -> None:
        """
        Validate the minimal endpoint contract.

        Terminal intentionally does not require the endpoint to be
        a specific equipment type. Endpoint interpretation belongs
        to the Network layer.

        The endpoint must expose a non-empty string ``id`` so that
        it participates in GridForge's canonical identity model.
        """
        if endpoint is None:
            raise ValueError("Terminal endpoint must not be None.")

        endpoint_id = getattr(endpoint, "id", None)

        if not isinstance(endpoint_id, str):
            raise TypeError(
                "Terminal endpoint must expose a string 'id' attribute."
            )

        if not endpoint_id.strip():
            raise ValueError(
                "Terminal endpoint id must not be empty."
            )

    # --------------------------------------------------------
    # Representation
    # --------------------------------------------------------

    def __repr__(self) -> str:
        """
        Return a concise debugging representation.
        """
        endpoint_id = None

        if self._endpoint is not None:
            endpoint_id = getattr(self._endpoint, "id", None)

        return (
            f"{type(self).__name__}("
            f"owner={self._owner!r}, "
            f"role={self._role!r}, "
            f"endpoint={endpoint_id!r}"
            f")"
        )
