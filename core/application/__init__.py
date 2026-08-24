# ============================================================

# File: core/application/**init**.py

# GridForge V2 — Headless Application Layer

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Headless Application Layer.

The Application layer is the controlled boundary between external
consumers and the Core engineering/domain layers.

External consumers include:

```
* UI;
* plugins;
* automation;
* command-line clients;
* future headless integrations.
```

Canonical mutation path:

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
Command Handler
      |
      v
Application Service
      |
      v
  Core Public API
```

The Application layer does not own:

```
* electrical domain state;
* Network membership;
* topology;
* Y-bus state;
* engineering invariants;
* analysis algorithms;
* solver algorithms;
* numerical infrastructure.
```

## Headless boundary

The package must not depend on:

```
* PySide6;
* PyQt5;
* PyQt6;
* Qt;
* QWidget;
* QGraphicsScene;
* QGraphicsItem;
* SLD/canvas implementation;
* renderers;
* UI controllers.
```

## Package export policy

Only stable, intentionally public Application contracts are
exported from this package root.

Implementation and composition infrastructure must be imported
from its concrete module.

The following remain intentionally internal at package-root level:

```
CommandManager
    core.application.command_manager

Transaction
    core.application.transaction

CommandHistory
    core.application.history

ModelService
    core.application.services.model_service

ApplicationContext
    core.application.context

Command handlers
    core.application.command_handlers

Model commands
    core.application.commands.model_commands

Bootstrap
    core.application.bootstrap
```

This prevents the package root from becoming an implementation
namespace and keeps the public Application contract stable.
"""

from __future__ import annotations

from .application import Application
from .command import Command
from .errors import (
ApplicationError,
ValidationError,
DomainError,
ResourceError,
ExecutionError,
)
from .results import ApplicationResult

__all__ = [
"Application",
"Command",
"ApplicationResult",
"ApplicationError",
"ValidationError",
"DomainError",
"ResourceError",
"ExecutionError",
]
