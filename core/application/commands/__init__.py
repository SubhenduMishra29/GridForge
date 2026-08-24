# ============================================================

# File: core/application/commands/**init**.py

# GridForge V2 — Headless Application Commands

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Headless Application Commands.

This package contains immutable Application command contracts.

Commands represent requested intent only.

They do NOT:

```
* mutate Core;
* mutate Network;
* manipulate topology;
* manipulate terminals;
* execute Application Services;
* access Qt;
* access UI;
* access graphics objects.
```

## Execution path

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
  Core Public API
```

## Current canonical model commands

```
model.create_bus
model.delete_bus

model.create_line
model.delete_line

model.create_transformer
model.delete_transformer
```

## Endpoint rule

Line and Transformer creation commands carry endpoint identifiers,
not Core endpoint objects.

The current Application boundary resolves these identifiers against
canonical Network Bus IDs inside the command handler.
"""

from __future__ import annotations

from .model_commands import (
CREATE_BUS,
DELETE_BUS,
CREATE_LINE,
DELETE_LINE,
CREATE_TRANSFORMER,
DELETE_TRANSFORMER,
CreateBusCommand,
DeleteBusCommand,
CreateLineCommand,
DeleteLineCommand,
CreateTransformerCommand,
DeleteTransformerCommand,
)

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"CREATE_BUS",
"DELETE_BUS",
"CREATE_LINE",
"DELETE_LINE",
"CREATE_TRANSFORMER",
"DELETE_TRANSFORMER",
"CreateBusCommand",
"DeleteBusCommand",
"CreateLineCommand",
"DeleteLineCommand",
"CreateTransformerCommand",
"DeleteTransformerCommand",
]
