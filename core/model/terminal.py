# core/model/terminal.py

"""
GridForge V2 Terminal Model
===========================

Author:
Subhendu Mishra

Defines the local electrical Terminal abstraction used by
GridForge equipment models.

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

A Terminal owns only its local connection reference.

The Network layer interprets canonical model relationships and builds
derived electrical topology.

The Application layer resolves external endpoint references and
coordinates controlled mutations.

## Responsibilities

A Terminal:

```
- belongs to one equipment owner;
- has an optional local role;
- stores one local endpoint reference;
- exposes local connection state;
- validates only its own local contract;
- provides diagnostics.
```

A Terminal does NOT:

```
- own global network topology;
- build or maintain a connectivity graph;
- traverse terminal chains;
- determine electrical islands;
- register itself with a Network;
- resolve application EndpointReference values;
- assign numerical indices;
- build Y-bus matrices;
- perform electrical calculations;
- perform protection calculations;
- perform simulation;
- own UI or SLD state.
```

## Identity

A Terminal is not an independent ElectricalObject.

Its identity is contextual:

```
owning equipment + terminal role
```

The Terminal therefore does not introduce a second globally unique
identifier.

## Connection Contract

The authoritative local attachment is:

```
terminal.endpoint
```

The endpoint representation is intentionally opaque to this model
class. Terminal validates only the minimum identity contract required
for diagnostics.

Interpretation of an endpoint as an electrical Bus belongs outside
this class.

The Network layer is responsible for consuming canonical terminal
relationships when constructing derived topology.

## Application Endpoint References

EndpointReference and EndpointResolver belong to core/application.

Terminal must not import either abstraction.

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
GridForge local electrical connection point.

```
Parameters
----------
endpoint:
    Optional local endpoint object.

owner:
    Optional equipment object that owns this Terminal.

role:
    Optional terminal role such as ``P1``, ``P2``, ``H1``,
    ``H2``, ``from`` or ``to``.

Notes
-----
A Terminal stores only its own local attachment reference.
It does not interpret that reference as global topology.
"""

def __init__(
    self,
    endpoint: Any = None,
    owner: Any = None,
    role: str | None = None,
) -> None:
    """
    Create a GridForge Terminal.
    """

    if owner is not None:
        self._validate_owner(owner)

    normalized_role = self._normalize_role(role)

    if endpoint is not None:
        self._validate_endpoint(endpoint)

    self.owner = owner
    self.role = normalized_role
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

    normalized = role.strip()

    if not normalized:
        return None

    return normalized

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
    Validate the minimum Terminal owner contract.

    The owner must expose a non-empty string ``id``.
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

    An endpoint must expose a non-empty string ``id``.

    Terminal deliberately does not determine the concrete
    endpoint category or electrical compatibility. Those
    responsibilities belong to the appropriate higher-level
    Core contracts.
    """

    if endpoint is None:
        raise ValueError(
            "Terminal endpoint cannot be None during "
            "attachment."
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
    Validate Terminal-local state.

    This validates only:

        - owner identity contract;
        - terminal role;
        - endpoint identity contract.

    It does not validate:

        - electrical compatibility;
        - Network membership;
        - global topology;
        - connectivity legality.
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
    Validate this Terminal's local contract.
    """

    return self.validate_parameters()

# =================================================================
# LOCAL ATTACHMENT
# =================================================================

def attach(
    self,
    endpoint: Any,
) -> None:
    """
    Attach this Terminal to a local endpoint.

    This method mutates only this Terminal's local endpoint
    reference.

    It does NOT:

        - register the endpoint with a Network;
        - validate Network membership;
        - modify global topology;
        - build connectivity graphs;
        - update numerical structures;
        - rebuild Y-bus;
        - resolve application endpoint references.
    """

    self._validate_endpoint(
        endpoint,
    )

    self.endpoint = endpoint

    self.validate()

def detach(self) -> None:
    """
    Remove this Terminal's local endpoint reference.

    This method changes only:

        terminal.endpoint
    """

    self.endpoint = None

# -----------------------------------------------------------------
# COMPATIBILITY ALIASES
# -----------------------------------------------------------------

def connect(
    self,
    endpoint: Any,
) -> None:
    """
    Compatibility alias for ``attach()``.

    New Core code should prefer ``attach()`` because the method
    describes a local terminal operation without implying that
    this object manages global Network topology.
    """

    self.attach(
        endpoint,
    )

def disconnect(self) -> None:
    """
    Compatibility alias for ``detach()``.

    New Core code should prefer ``detach()``.
    """

    self.detach()

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
# COMPATIBILITY ACCESS
# =================================================================

@property
def bus(self) -> Any:
    """
    Return the directly attached Bus-like endpoint when available.

    This is a compatibility accessor only.

    No Terminal-to-Terminal traversal is performed. The Terminal
    does not resolve chains, detect cycles, or determine global
    electrical connectivity.

    Endpoint interpretation beyond the direct local reference
    belongs to the Network layer.
    """

    endpoint = self.endpoint

    if endpoint is None:
        return None

    if isinstance(
        endpoint,
        Terminal,
    ):
        return None

    return endpoint

# =================================================================
# ENDPOINT INFORMATION
# =================================================================

@property
def endpoint_id(self) -> str | None:
    """
    Return the directly attached endpoint identifier.
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
    Return structured Terminal-local diagnostics.

    The returned information describes only this Terminal's local
    state. It is not a topology query.
    """

    return {
        "owner": self.owner_id,
        "role": self.role,
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

    return (
        f"<Terminal "
        f"owner={self.owner_id}, "
        f"role={self.role!r}, "
        f"endpoint={self.endpoint_id}>"
    )
```

# =====================================================================

# PUBLIC API

# =====================================================================

__all__ = [
"Terminal",
]
