# ============================================================

# File: core/application/bootstrap.py

# GridForge V2 — Headless Application Composition Root

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Application Composition Root.

This module constructs the complete headless Application runtime.

## Composition

```
Core Network
     |
     v
ApplicationContext
     |
     v
CommandManager
     |
     +----------------------+
     |                      |
     v                      v
Model Handlers          CommandHistory
     |
     v
ModelService
     |
     v
    Core
```

## Responsibilities

The Composition Root owns wiring only.

It does NOT:

```
* construct domain models;
* mutate Network;
* execute commands;
* implement business logic;
* manipulate topology;
* build Y-bus;
* access Qt;
* access UI;
* manage plugins.
```

## Application ownership

The Application façade owns the configured CommandManager.

The Core Network remains externally supplied.

Therefore:

```
Application
    owns
        CommandManager
            owns
                ApplicationContext reference
                CommandHistory
                command registrations

Core Network
    remains canonical Core state
```

"""

from **future** import annotations

from typing import Any

from .application import Application
from .command_handlers import register_model_handlers
from .command_manager import CommandManager
from .context import ApplicationContext

# ============================================================

# APPLICATION FACTORY

# ============================================================

def create_application(
network: Any,
) -> Application:
"""
Construct the canonical headless GridForge Application.

```
Parameters
----------
network:
    Already-created canonical Core Network.

Returns
-------
Application
    Fully composed headless Application façade.

Composition order
-----------------

1. Validate the supplied Network.
2. Construct ApplicationContext.
3. Construct CommandManager.
4. Register all canonical model handlers.
5. Construct Application façade.

The Application façade receives only CommandManager because
CommandManager already owns the Application execution context.
"""

if network is None:
    raise ValueError(
        "network must not be None."
    )

# --------------------------------------------------------
# Application Context
# --------------------------------------------------------

context = ApplicationContext(
    network=network,
)

# --------------------------------------------------------
# Command Manager
# --------------------------------------------------------

command_manager = CommandManager(
    context=context,
)

# --------------------------------------------------------
# Canonical model handlers
# --------------------------------------------------------

register_model_handlers(
    command_manager,
)

# --------------------------------------------------------
# Public Application façade
# --------------------------------------------------------

return Application(
    command_manager=command_manager,
)
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"create_application",
]
