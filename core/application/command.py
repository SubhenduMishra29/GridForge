# ============================================================

# File: core/application/command.py

# GridForge V2 — Headless Application Command Contract

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Headless Application Command Contract.

A Command represents an explicit Application-level intent.

The command is:

```
* headless;
* immutable;
* serializable at the Application boundary;
* independent of Core implementation details;
* independent of UI implementation details.
```

## Execution boundary

```
External Consumer
      |
      v
   Command
      |
      v
CommandManager
      |
      v
   Handler
      |
      v
Application Service
      |
      v
    Core
```

A Command does not:

```
* mutate Core;
* mutate Network;
* execute services;
* maintain history;
* perform undo/redo;
* manipulate topology;
* build Y-bus;
* access Qt;
* access UI;
* contain graphics objects.
```

## Payload boundary

The payload contains Application-level input values only.

Valid:

```
{
    "bus_id": "BUS-001",
    "voltage": 132.0,
}
```

Invalid:

```
{
    "graphics_item": QGraphicsItem(...),
}
```

Core objects should not be embedded in command payloads.

For example, endpoint references are represented by stable
Application-level identifiers and resolved by handlers.

## Immutability

Commands are immutable after construction.

The payload is converted to a MappingProxyType at construction
time. Therefore the command's top-level payload mapping cannot
be modified after creation.

Nested values should also be immutable Application values.

## Python compatibility

GridForge V2 targets Python 3.10/3.11.

This module therefore avoids Python 3.12-only syntax.
"""

from **future** import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4

# ============================================================

# COMMAND

# ============================================================

@dataclass(frozen=True)
class Command:
"""
Base immutable Application command.

```
Parameters
----------
command_type:
    Stable semantic identifier for the command.

payload:
    Application-level input values.

    The supplied mapping is defensively copied and exposed
    as a read-only MappingProxyType.

command_id:
    Unique identifier for this command instance.

correlation_id:
    Optional identifier associating this command with a
    larger Application operation.

causation_id:
    Optional identifier identifying the command/event that
    caused this command.
"""

command_type: str

payload: Mapping[str, Any] = field(
    default_factory=dict,
)

command_id: UUID = field(
    default_factory=uuid4,
)

correlation_id: UUID | None = None

causation_id: UUID | None = None

def __post_init__(self) -> None:
    """
    Validate and freeze the structural command contract.
    """

    # ----------------------------------------------------
    # Command type
    # ----------------------------------------------------

    if not isinstance(
        self.command_type,
        str,
    ):
        raise TypeError(
            "Command command_type must be a string."
        )

    normalized_type = self.command_type.strip()

    if not normalized_type:
        raise ValueError(
            "Command command_type must not be empty."
        )

    object.__setattr__(
        self,
        "command_type",
        normalized_type,
    )

    # ----------------------------------------------------
    # Payload
    # ----------------------------------------------------

    if not isinstance(
        self.payload,
        Mapping,
    ):
        raise TypeError(
            "Command payload must be a mapping."
        )

    # Defensive copy + read-only wrapper.
    #
    # This prevents callers from mutating the command
    # through the original dictionary after construction.
    frozen_payload = MappingProxyType(
        dict(self.payload)
    )

    object.__setattr__(
        self,
        "payload",
        frozen_payload,
    )

    # ----------------------------------------------------
    # Command identity
    # ----------------------------------------------------

    if not isinstance(
        self.command_id,
        UUID,
    ):
        raise TypeError(
            "Command command_id must be a UUID."
        )

    # ----------------------------------------------------
    # Correlation identity
    # ----------------------------------------------------

    if (
        self.correlation_id is not None
        and not isinstance(
            self.correlation_id,
            UUID,
        )
    ):
        raise TypeError(
            "Command correlation_id must be a UUID or None."
        )

    # ----------------------------------------------------
    # Causation identity
    # ----------------------------------------------------

    if (
        self.causation_id is not None
        and not isinstance(
            self.causation_id,
            UUID,
        )
    ):
        raise TypeError(
            "Command causation_id must be a UUID or None."
        )
```

# ============================================================

# COMMAND METADATA

# ============================================================

@dataclass(frozen=True)
class CommandMetadata:
"""
Optional descriptive metadata for Application infrastructure.

```
Metadata is intentionally separate from command payload.

Payload answers:

    What input does this command require?

Metadata answers:

    How should Application infrastructure describe
    or identify this command?

Appropriate metadata includes:

    * display_name;
    * category;
    * origin;
    * plugin_id.

Metadata must remain headless and must not contain UI
runtime objects.
"""

display_name: str | None = None

category: str | None = None

origin: str | None = None

plugin_id: str | None = None

def __post_init__(self) -> None:
    """Validate metadata values."""

    fields = {
        "display_name": self.display_name,
        "category": self.category,
        "origin": self.origin,
        "plugin_id": self.plugin_id,
    }

    for name, value in fields.items():

        if (
            value is not None
            and not isinstance(
                value,
                str,
            )
        ):
            raise TypeError(
                f"CommandMetadata {name} "
                "must be a string or None."
            )
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"Command",
"CommandMetadata",
]
