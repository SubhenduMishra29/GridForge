# ============================================================
# File: core/application/endpoint_reference.py
# GridForge V2 — Application Endpoint References
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Application Endpoint References
================================================

Defines immutable references used by Application Commands to
identify canonical Core electrical endpoints.

This module contains references only.

It does NOT contain:

    * Core model objects
    * topology state
    * electrical calculations
    * UI state
    * SLD state
    * endpoint mutation
    * network membership

Architecture
------------

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
    Canonical Core Bus / Terminal
        |
        v
    ModelService
        |
        v
    Core Model / Network

Endpoint identity
-----------------

A Bus endpoint is identified by:

    bus_id

A Terminal endpoint is identified by:

    equipment_type
    equipment_id
    terminal_role

This is required because the current NetworkRegistry guarantees
identifier uniqueness within an equipment family, not globally
across all equipment families.

A Terminal does not receive a globally unique Terminal ID.

Its identity remains:

    owning equipment + terminal role

The reference therefore mirrors the existing Core identity
contract rather than introducing a second identity system.

Author:
    Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


# ============================================================
# ENDPOINT REFERENCE KIND
# ============================================================

class EndpointReferenceKind(str, Enum):
    """
    Type of electrical endpoint referenced by an Application
    command.
    """

    BUS = "bus"
    TERMINAL = "terminal"


# ============================================================
# EQUIPMENT TYPE
# ============================================================

class EquipmentType(str, Enum):
    """
    Canonical Network equipment families that may own terminals.

    These values correspond to NetworkRegistry collections.

    The enum is intentionally Application-facing. It does not
    replace the Core model classes.
    """

    LINE = "line"
    TRANSFORMER = "transformer"
    GENERATOR = "generator"
    LOAD = "load"
    SHUNT = "shunt"


# ============================================================
# ENDPOINT REFERENCE
# ============================================================

@dataclass(frozen=True, slots=True)
class EndpointReference:
    """
    Immutable Application reference to a canonical electrical
    endpoint.

    BUS
    ---
    For a Bus:

        kind = BUS
        object_id = Bus.id
        equipment_type = None
        terminal_role = None

    TERMINAL
    --------
    For a Terminal:

        kind = TERMINAL
        object_id = owning equipment.id
        equipment_type = owning equipment family
        terminal_role = terminal.role

    No Core object is stored.
    """

    kind: EndpointReferenceKind
    object_id: str
    equipment_type: EquipmentType | None = None
    terminal_role: str | None = None

    # ========================================================
    # VALIDATION
    # ========================================================

    def __post_init__(self) -> None:
        """
        Validate and normalize the immutable reference.
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

        object.__setattr__(
            self,
            "object_id",
            self.object_id.strip(),
        )

        # ----------------------------------------------------
        # BUS
        # ----------------------------------------------------

        if self.kind is EndpointReferenceKind.BUS:

            if self.equipment_type is not None:
                raise ValueError(
                    "equipment_type must be None "
                    "for a Bus endpoint."
                )

            if self.terminal_role is not None:
                raise ValueError(
                    "terminal_role must be None "
                    "for a Bus endpoint."
                )

            return

        # ----------------------------------------------------
        # TERMINAL
        # ----------------------------------------------------

        if self.kind is EndpointReferenceKind.TERMINAL:

            if not isinstance(
                self.equipment_type,
                EquipmentType,
            ):
                raise TypeError(
                    "equipment_type must be an "
                    "EquipmentType for a terminal "
                    "endpoint."
                )

            if (
                not isinstance(
                    self.terminal_role,
                    str,
                )
                or not self.terminal_role.strip()
            ):
                raise ValueError(
                    "terminal_role must be a "
                    "non-empty string for a terminal "
                    "endpoint."
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
        equipment_type: EquipmentType,
        equipment_id: str,
        terminal_role: str,
    ) -> "EndpointReference":
        """
        Create a Terminal endpoint reference.

        Parameters
        ----------
        equipment_type:
            Canonical Network equipment family.

        equipment_id:
            Canonical identifier within that family.

        terminal_role:
            Role of the terminal on the equipment.
        """

        return cls(
            kind=EndpointReferenceKind.TERMINAL,
            object_id=equipment_id,
            equipment_type=equipment_type,
            terminal_role=terminal_role,
        )

    # ========================================================
    # TYPE HELPERS
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

    # ========================================================
    # ID HELPERS
    # ========================================================

    @property
    def bus_id(self) -> str | None:
        """
        Return the Bus ID when this is a Bus reference.
        """

        if not self.is_bus:
            return None

        return self.object_id

    @property
    def equipment_id(self) -> str | None:
        """
        Return the owning equipment ID when this is a Terminal
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
        Return an immutable mapping suitable for diagnostics,
        command transport, or persistence adapters.
        """

        if self.is_bus:
            return MappingProxyType(
                {
                    "kind": self.kind.value,
                    "object_id": self.object_id,
                }
            )

        return MappingProxyType(
            {
                "kind": self.kind.value,
                "object_id": self.object_id,
                "equipment_type": (
                    self.equipment_type.value
                    if self.equipment_type is not None
                    else None
                ),
                "terminal_role": self.terminal_role,
            }
        )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __str__(self) -> str:
        """
        Return a stable human-readable representation.
        """

        if self.is_bus:
            return (
                "EndpointReference("
                f"bus={self.object_id})"
            )

        return (
            "EndpointReference("
            f"{self.equipment_type.value}:"
            f"{self.object_id}:"
            f"{self.terminal_role})"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "EndpointReference",
    "EndpointReferenceKind",
    "EquipmentType",
]
