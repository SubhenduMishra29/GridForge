# ============================================================
# File: core/application/command.py
# GridForge V2 — Headless Application Command Contract
# Author: Subhendu Mishra
# ============================================================

"""
Immutable Application command contract.

A Command represents application intent.

Commands:
    * do not mutate Core state;
    * do not execute services;
    * do not access UI or Qt;
    * do not contain Core model objects;
    * carry only immutable command data.

Execution is performed by CommandManager through registered
command handlers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4


# ============================================================
# IMMUTABILITY
# ============================================================

def _freeze_value(value: Any) -> Any:
    """
    Recursively freeze common mutable container values.
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
    Base immutable Application command.

    ``payload`` contains only command data.

    It must never contain:
        * Core model instances;
        * services;
        * handlers;
        * UI objects;
        * Qt objects;
        * mutable application state.
    """

    command_type: str

    payload: Mapping[str, Any] = field(
        default_factory=dict
    )

    command_id: UUID = field(
        default_factory=uuid4
    )

    correlation_id: UUID | None = None

    causation_id: UUID | None = None

    # ========================================================
    # VALIDATION / FREEZING
    # ========================================================

    def __post_init__(self) -> None:
        """
        Validate and freeze command state.
        """

        if not isinstance(
            self.command_type,
            str,
        ):
            raise TypeError(
                "command_type must be a string."
            )

        command_type = self.command_type.strip()

        if not command_type:
            raise ValueError(
                "command_type must not be empty."
            )

        object.__setattr__(
            self,
            "command_type",
            command_type,
        )

        if not isinstance(
            self.payload,
            Mapping,
        ):
            raise TypeError(
                "payload must be a mapping."
            )

        frozen_payload = _freeze_value(
            self.payload
        )

        if not isinstance(
            frozen_payload,
            Mapping,
        ):
            raise TypeError(
                "Failed to freeze command payload."
            )

        object.__setattr__(
            self,
            "payload",
            MappingProxyType(
                dict(frozen_payload)
            ),
        )

        if not isinstance(
            self.command_id,
            UUID,
        ):
            raise TypeError(
                "command_id must be a UUID."
            )

        if (
            self.correlation_id is not None
            and not isinstance(
                self.correlation_id,
                UUID,
            )
        ):
            raise TypeError(
                "correlation_id must be a UUID or None."
            )

        if (
            self.causation_id is not None
            and not isinstance(
                self.causation_id,
                UUID,
            )
        ):
            raise TypeError(
                "causation_id must be a UUID or None."
            )

    # ========================================================
    # CAUSATION
    # ========================================================

    def with_causation(
        self,
        causation_id: UUID,
    ) -> Command:
        """
        Return a new command with the supplied causation ID.

        The original command remains unchanged.
        """

        if not isinstance(
            causation_id,
            UUID,
        ):
            raise TypeError(
                "causation_id must be a UUID."
            )

        return type(self)(
            command_type=self.command_type,
            payload=dict(self.payload),
            command_id=self.command_id,
            correlation_id=self.correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "Command",
]
