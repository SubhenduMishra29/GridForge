# ============================================================
# File: core/application/command.py
# GridForge V2 — Application Command
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Application Command
===================================

Immutable application command envelope.

Architectural responsibilities
-------------------------------

A Command represents application intent.

A Command:

    * is immutable;
    * identifies the requested application operation;
    * carries immutable value data;
    * carries command identity metadata;
    * carries optional correlation metadata;
    * carries optional causation metadata.

A Command does NOT:

    * mutate Core;
    * resolve domain objects;
    * perform topology operations;
    * perform engineering calculations;
    * access UI state;
    * execute handlers.

Command execution belongs to CommandManager and the
registered command handler.

Metadata
--------

command_id
    Unique identity of this command instance.

correlation_id
    Identifies the larger application workflow/correlation.

causation_id
    Identifies the command/event that caused this command,
    when applicable.

Lifecycle
---------

CommandManager does not clone or rewrite commands during
normal execution or redo.

Correlation and causation metadata are supplied when the
command is constructed.

There is intentionally no generic command-cloning or
``with_causation()`` API.

A generic reconstruction mechanism is incompatible with
GridForge's typed command constructors unless a separate,
explicit typed command factory/cloning contract is introduced.

Author:
    Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID


# ============================================================
# IMMUTABILITY HELPERS
# ============================================================

def _freeze_value(value: Any) -> Any:
    """
    Recursively convert supported mutable container values
    into immutable equivalents.

    Supported conversions:

        Mapping
            -> MappingProxyType

        list
            -> tuple

        tuple
            -> tuple with recursively frozen members

        set
            -> frozenset

        frozenset
            -> frozenset with recursively frozen members

    Other values are retained as-is.
    """

    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _freeze_value(item)
                for key, item in value.items()
            }
        )

    if isinstance(value, list):
        return tuple(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, tuple):
        return tuple(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, set):
        return frozenset(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, frozenset):
        return frozenset(
            _freeze_value(item)
            for item in value
        )

    return value


# ============================================================
# COMMAND
# ============================================================

@dataclass(frozen=True, slots=True)
class Command:
    """
    Immutable application command envelope.

    Specialized application commands inherit from this class
    and provide their own typed constructors.

    The base Command contains only the common command envelope.
    Domain meaning remains in the specialized command and Core
    application handler/service layers.
    """

    command_type: str
    payload: Mapping[str, Any]

    command_id: UUID
    correlation_id: UUID | None = None
    causation_id: UUID | None = None

    # ========================================================
    # POST INITIALIZATION
    # ========================================================

    def __post_init__(self) -> None:
        """
        Validate and freeze command data.

        The payload is recursively converted into immutable
        container structures so callers cannot mutate the
        command through mutable nested containers.
        """

        if not isinstance(self.command_type, str):
            raise TypeError(
                "command_type must be a string."
            )

        if not self.command_type:
            raise ValueError(
                "command_type must not be empty."
            )

        if not isinstance(self.command_id, UUID):
            raise TypeError(
                "command_id must be a UUID."
            )

        if (
            self.correlation_id is not None
            and not isinstance(self.correlation_id, UUID)
        ):
            raise TypeError(
                "correlation_id must be a UUID or None."
            )

        if (
            self.causation_id is not None
            and not isinstance(self.causation_id, UUID)
        ):
            raise TypeError(
                "causation_id must be a UUID or None."
            )

        if not isinstance(self.payload, Mapping):
            raise TypeError(
                "payload must be a mapping."
            )

        object.__setattr__(
            self,
            "payload",
            _freeze_value(self.payload),
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "Command",
]
