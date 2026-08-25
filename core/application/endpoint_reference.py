# ============================================================
# File: core/application/endpoint_reference.py
# GridForge V2 — Application Endpoint Reference
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2
============

Module:
    core.application.endpoint_reference

Purpose
-------
Defines the immutable Application-layer reference used by
commands to identify an electrical endpoint without embedding
Core model objects inside Application commands.

Architectural Boundary
----------------------

    UI / Plugin
         |
         | EndpointReference
         v
    Application Command
         |
         v
    Command Handler
         |
         | resolve
         v
    Canonical Core Endpoint
         |
         v
    Application Service
         |
         v
    Core Network / Model

EndpointReference is an Application value object.

It is NOT:

    * a Core model;
    * a Terminal;
    * a Bus;
    * an electrical topology object;
    * a UI object;
    * a persistent Core entity.

The Core remains authoritative for actual endpoint objects.

Supported Endpoint Kinds
-------------------------

BUS
    Identifies a Bus directly.

TERMINAL
    Identifies a terminal belonging to a Core equipment object.

Terminal identity is represented by:

    equipment_id
    terminal_role

This deliberately does not introduce a globally unique
Terminal.id into Core.

Why terminal_role?
------------------
Core Terminal currently derives its identity from its owning
equipment and role. Terminal roles include values such as:

    from
    to
    P1
    P2
    H1
    H2
    ...

The Application reference therefore mirrors the existing Core
identity model instead of inventing another identity system.

Immutability
------------
EndpointReference is immutable.

Commands may safely contain EndpointReference instances without
acquiring mutable Core state.

Core Resolution
---------------
EndpointReference does not resolve itself.

Resolution belongs to the Application handler/service boundary,
because resolving the reference requires access to canonical
Core Network state.

Validation
----------
This module validates reference structure.

It does not perform engineering/domain validation.

Examples
--------

Bus:

    EndpointReference.bus(
        "BUS-001"
    )

Terminal:

    EndpointReference.terminal(
        equipment_id="TR-001",
        terminal_role="HV",
    )

No Core object is stored in either reference.

Author:
    Subhendu Mishra

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


# ============================================================
# ENDPOINT KIND
# ============================================================

class EndpointReferenceKind(str, Enum):
    """
    Identifies the type of endpoint represented by an
    EndpointReference.
    """

    BUS = "bus"
    TERMINAL = "terminal"


# ============================================================
# ENDPOINT REFERENCE
# ============================================================

@dataclass(frozen=True, slots=True)
class EndpointReference:
    """
    Immutable Application-layer reference to a Core electrical
    endpoint.

    Parameters
    ----------
    kind:
        EndpointReferenceKind.BUS or
        EndpointReferenceKind.TERMINAL.

    object_id:
        Canonical Core object identifier.

        For BUS:
            this is the Bus id.

        For TERMINAL:
            this is the owning equipment id.

    terminal_role:
        Terminal role when kind is TERMINAL.

        Must be None for BUS.

    Notes
    -----
    No Core object is stored here.

    This class therefore remains safe to use inside immutable
    Application Commands.
    """

    kind: EndpointReferenceKind
    object_id: str
    terminal_role: str | None = None

    # ========================================================
    # VALIDATION
    # ========================================================

    def __post_init__(self) -> None:
        """
        Validate the structural integrity of the reference.
        """

        if not isinstance(
            self.kind,
            EndpointReferenceKind,
        ):
            raise TypeError(
                "kind must be an EndpointReferenceKind."
            )

        if (
            not isinstance(self.object_id, str)
            or not self.object_id.strip()
        ):
            raise ValueError(
                "object_id must be a non-empty string."
            )

        object_id = self.object_id.strip()

        object.__setattr__(
            self,
            "object_id",
            object_id,
        )

        if self.kind is EndpointReferenceKind.BUS:
            if self.terminal_role is not None:
                raise ValueError(
                    "terminal_role must be None for "
                    "a bus endpoint reference."
                )

            return

        if self.kind is EndpointReferenceKind.TERMINAL:
            if (
                not isinstance(
                    self.terminal_role,
                    str,
                )
                or not self.terminal_role.strip()
            ):
                raise ValueError(
                    "terminal_role must be a non-empty "
                    "string for a terminal endpoint reference."
                )

            object.__setattr__(
                self,
                "terminal_role",
                self.terminal_role.strip(),
            )

            return

        raise ValueError(
            f"Unsupported endpoint reference kind: "
            f"{self.kind!r}."
        )

    # ========================================================
    # FACTORIES
    # ========================================================

    @classmethod
    def bus(
        cls,
        bus_id: str,
    ) -> "EndpointReference":
        """
        Create a Bus endpoint reference.
        """

        return cls(
            kind=EndpointReferenceKind.BUS,
            object_id=bus_id,
        )

    @classmethod
    def terminal(
        cls,
        *,
        equipment_id: str,
        terminal_role: str,
    ) -> "EndpointReference":
        """
        Create a Terminal endpoint reference.

        Parameters
        ----------
        equipment_id:
            Canonical Core id of the owning equipment.

        terminal_role:
            Role identifying the terminal on that equipment.
        """

        return cls(
            kind=EndpointReferenceKind.TERMINAL,
            object_id=equipment_id,
            terminal_role=terminal_role,
        )

    # ========================================================
    # KIND HELPERS
    # ========================================================

    @property
    def is_bus(self) -> bool:
        """
        Return True when this reference identifies a Bus.
        """

        return self.kind is EndpointReferenceKind.BUS

    @property
    def is_terminal(self) -> bool:
        """
        Return True when this reference identifies a Terminal.
        """

        return self.kind is EndpointReferenceKind.TERMINAL

    @property
    def bus_id(self) -> str | None:
        """
        Return the Bus id when this is a Bus reference.
        """

        if not self.is_bus:
            return None

        return self.object_id

    @property
    def equipment_id(self) -> str | None:
        """
        Return the owning equipment id when this is a Terminal
        reference.
        """

        if not self.is_terminal:
            return None

        return self.object_id

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_mapping(self) -> Mapping[str, Any]:
        """
        Return a plain immutable mapping suitable for inclusion
        in Application command payloads.
        """

        if self.is_bus:
            return {
                "kind": self.kind.value,
                "object_id": self.object_id,
            }

        return {
            "kind": self.kind.value,
            "object_id": self.object_id,
            "terminal_role": self.terminal_role,
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __str__(self) -> str:
        """
        Return a stable human-readable representation.
        """

        if self.is_bus:
            return (
                f"EndpointReference("
                f"bus={self.object_id})"
            )

        return (
            "EndpointReference("
            f"terminal={self.object_id}:"
            f"{self.terminal_role})"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "EndpointReference",
    "EndpointReferenceKind",
]
