# ============================================================

# File: core/model/terminal.py

# GridForge V2 — Terminal Model

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Terminal Model.

Defines the local electrical terminal abstraction used by GridForge
equipment models.

## Architecture

A Terminal represents one physical or logical electrical connection
point owned by an equipment model.

```
Equipment
    |
    +-- Terminal
          |
          +-- endpoint
```

A Terminal owns only its local endpoint reference.

The Terminal does not own, construct, or interpret global electrical
topology.

## Architecture boundaries

Model layer

```

Terminal owns:

    - its equipment owner;
    - its local role;
    - its local endpoint reference;
    - local connection state;
    - local contract validation.

Terminal does not own:

    - Network membership;
    - global connectivity;
    - connectivity graphs;
    - electrical islands;
    - topology traversal;
    - numerical indexing;
    - Y-bus construction;
    - solver state;
    - protection execution;
    - simulation execution;
    - application command resolution;
    - UI or SLD state.

Application layer
```

Application-layer EndpointReference and EndpointResolver abstractions
resolve external references into canonical Core objects.

Terminal must not import or depend upon those abstractions.

Network layer

```

The Network layer interprets terminal endpoint relationships and derives
electrical topology.

The canonical conceptual relationship is:

    Equipment
        |
        +-- Terminal
              |
              +-- endpoint
                     |
                     +-- Bus

A Terminal does not traverse chains of other Terminal instances to
discover a Bus.

Ownership
---------

A Terminal belongs to one equipment owner.

Terminal ownership is established during construction and must not be
silently transferred to another equipment object.

A Terminal is therefore not an independently registered engineering
object and does not introduce a second global identity.

Its contextual identity is defined by:

    owner + role

Endpoint semantics
------------------

The endpoint is intentionally treated as a local reference by this
class.

Terminal validates only the minimum local contract required to store
and report the endpoint.

Interpretation of the endpoint as a Bus, validation of Network
membership, and construction of electrical topology belong to the
Network layer.

GridForge V2
"""

from __future__ import annotations

from typing import Any


# ============================================================
# TERMINAL
# ============================================================


class Terminal:
    """
    Local electrical connection point owned by an equipment model.

    Parameters
    ----------
    endpoint:
        Optional local endpoint reference.

    owner:
        Equipment object that owns this Terminal.

    role:
        Optional terminal role, for example:

            - "BUS"
            - "FROM"
            - "TO"
            - "HV"
            - "LV"
            - "P1"
            - "P2"

    Notes
    -----
    A Terminal stores only local connection information.

    It does not determine global topology or resolve chains of
    Terminal objects.
    """

    def __init__(
        self,
        endpoint: Any = None,
        owner: Any = None,
        role: str | None = None,
    ) -> None:
        """
        Create a Terminal.

        Parameters
        ----------
        endpoint:
            Optional local endpoint reference.

        owner:
            Optional equipment owner.

        role:
            Optional terminal role.
        """

        if owner is not None:
            self._validate_owner(owner)

        normalized_role = self._normalize_role(role)

        if endpoint is not None:
            self._validate_endpoint(endpoint)

        self._owner = owner
        self._role = normalized_role
        self._endpoint = endpoint

        self.validate()

    # ========================================================
    # OWNER
    # ========================================================

    @property
    def owner(self) -> Any:
        """
        Return the equipment that owns this Terminal.
        """

        return self._owner

    @property
    def owner_id(self) -> str | None:
        """
        Return the owning equipment identifier.

        Returns
        -------
        str | None
            The owner ID when an owner exists, otherwise ``None``.
        """

        if self._owner is None:
            return None

        return self._owner.id

    # ========================================================
    # ROLE
    # ========================================================

    @property
    def role(self) -> str | None:
        """
        Return the local terminal role.
        """

        return self._role

    @property
    def terminal_role(self) -> str | None:
        """
        Compatibility alias for :attr:`role`.
        """

        return self._role

    @staticmethod
    def _normalize_role(
        role: str | None,
    ) -> str | None:
        """
        Normalize an optional terminal role.

        Empty or whitespace-only roles are rejected.

        Parameters
        ----------
        role:
            Optional role string.

        Returns
        -------
        str | None
            Normalized role or ``None``.
        """

        if role is None:
            return None

        if not isinstance(role, str):
            raise TypeError(
                "Terminal role must be a string or None."
            )

        normalized = role.strip()

        if not normalized:
            raise ValueError(
                "Terminal role cannot be empty."
            )

        return normalized

    # ========================================================
    # ENDPOINT
    # ========================================================

    @property
    def endpoint(self) -> Any:
        """
        Return the locally attached endpoint.

        The returned object is not interpreted by Terminal as global
        electrical topology.
        """

        return self._endpoint

    @property
    def endpoint_id(self) -> str | None:
        """
        Return the local endpoint identifier.

        Returns
        -------
        str | None
            The endpoint ID when attached, otherwise ``None``.
        """

        if self._endpoint is None:
            return None

        return self._endpoint.id

    @property
    def is_connected(self) -> bool:
        """
        Return whether a local endpoint is attached.

        This indicates only local attachment state.

        It does not imply that the endpoint belongs to a Network or
        that the Terminal participates in valid electrical topology.
        """

        return self._endpoint is not None

    # ========================================================
    # LOCAL ATTACHMENT
    # ========================================================

    def attach(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach a local endpoint.

        This operation changes only this Terminal's local endpoint
        reference.

        It does not:

            - register objects with a Network;
            - validate Network membership;
            - build a connectivity graph;
            - determine electrical topology;
            - rebuild numerical structures;
            - assign indices;
            - resolve application EndpointReference objects.

        Parameters
        ----------
        endpoint:
            Local endpoint object.
        """

        self._validate_endpoint(endpoint)

        self._endpoint = endpoint

        self.validate()

    def detach(
        self,
    ) -> None:
        """
        Remove the local endpoint reference.

        This operation changes only:

            terminal.endpoint
        """

        self._endpoint = None

    # ========================================================
    # COMPATIBILITY API
    # ========================================================

    def connect(
        self,
        endpoint: Any,
    ) -> None:
        """
        Compatibility alias for :meth:`attach`.

        New Core code should prefer ``attach()`` because the operation
        is explicitly local and does not imply ownership of global
        Network topology.
        """

        self.attach(endpoint)

    def disconnect(
        self,
    ) -> None:
        """
        Compatibility alias for :meth:`detach`.

        New Core code should prefer ``detach()``.
        """

        self.detach()

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_owner(
        owner: Any,
    ) -> None:
        """
        Validate the minimum equipment owner contract.

        The owner must expose a non-empty string ``id``.
        """

        if not hasattr(owner, "id"):
            raise TypeError(
                "Terminal owner must expose an 'id' attribute."
            )

        owner_id = getattr(owner, "id")

        if not isinstance(owner_id, str):
            raise TypeError(
                "Terminal owner ID must be a string."
            )

        if not owner_id.strip():
            raise ValueError(
                "Terminal owner ID cannot be empty."
            )

    @staticmethod
    def _validate_endpoint(
        endpoint: Any,
    ) -> None:
        """
        Validate the minimum local endpoint contract.

        An endpoint must expose a non-empty string ``id``.

        Terminal deliberately does not determine endpoint category,
        Network membership, or electrical compatibility.

        Those responsibilities belong to the appropriate Network and
        validation contracts.
        """

        if endpoint is None:
            raise ValueError(
                "Terminal endpoint cannot be None."
            )

        if not hasattr(endpoint, "id"):
            raise TypeError(
                "Terminal endpoint must expose an 'id' attribute."
            )

        endpoint_id = getattr(endpoint, "id")

        if not isinstance(endpoint_id, str):
            raise TypeError(
                "Terminal endpoint ID must be a string."
            )

        if not endpoint_id.strip():
            raise ValueError(
                "Terminal endpoint ID cannot be empty."
            )

    def validate_parameters(
        self,
    ) -> bool:
        """
        Validate the local Terminal contract.

        Validation covers only:

            - owner identity;
            - role validity;
            - endpoint identity.

        Validation does not cover:

            - electrical compatibility;
            - Network membership;
            - global topology;
            - electrical islands;
            - branch connectivity.
        """

        if self._owner is not None:
            self._validate_owner(
                self._owner,
            )

        if self._role is not None:
            self._normalize_role(
                self._role,
            )

        if self._endpoint is not None:
            self._validate_endpoint(
                self._endpoint,
            )

        return True

    def validate(
        self,
    ) -> bool:
        """
        Validate this Terminal.

        Returns
        -------
        bool
            ``True`` when the local Terminal contract is valid.
        """

        return self.validate_parameters()

    # ========================================================
    # COMPATIBILITY BUS ACCESS
    # ========================================================

    @property
    def bus(self) -> Any:
        """
        Return a directly attached Bus-like endpoint.

        This property is retained only as a compatibility accessor for
        existing model code.

        No Terminal-to-Terminal traversal is performed.

        If the endpoint is another Terminal, ``None`` is returned.
        Bus resolution beyond the directly attached endpoint belongs
        to the Network endpoint resolver.

        New Core code should use the canonical Network endpoint
        resolution contract rather than relying on this compatibility
        accessor.
        """

        endpoint = self._endpoint

        if endpoint is None:
            return None

        if isinstance(endpoint, Terminal):
            return None

        return endpoint

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Return structured Terminal-local diagnostics.

        The returned data describes only this Terminal's local state.
        It is not a topology query.
        """

        return {
            "owner": self.owner_id,
            "role": self.role,
            "endpoint": self.endpoint_id,
            "connected": self.is_connected,
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<Terminal "
            f"owner={self.owner_id!r}, "
            f"role={self.role!r}, "
            f"endpoint={self.endpoint_id!r}>"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "Terminal",
]
