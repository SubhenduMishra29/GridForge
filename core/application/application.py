# ============================================================

# File: core/application/application.py

# GridForge V2 — Headless Application Facade

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Headless Application Facade.

The Application façade is the stable public entry point between
external consumers and the internal Application infrastructure.

## Architecture

```
External Consumer
      |
      v
  Application
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

The façade owns no Core state.

The façade does not expose:

```
* CommandManager;
* ApplicationContext;
* Transaction;
* CommandHistory;
* handlers;
* Application services;
* Core internals.
```

The canonical mutation path is:

```
Application.execute(command)
```

## Headless boundary

This module must remain independent of:

```
* PySide6;
* PyQt;
* Qt;
* QGraphicsScene;
* QGraphicsItem;
* UI;
* SLD;
* canvas;
* renderers;
* plugin implementation details.
```

## Composition

The Application object receives a fully configured CommandManager
from the Composition Root.

The Application does not construct:

```
* Network;
* ApplicationContext;
* CommandManager;
* services;
* handlers.
```

This keeps construction outside the public façade.

## Capability discovery

Consumers may query whether a command is supported without
executing it.

Command execution remains the only mutation entry point.
"""

from **future** import annotations

from .command import Command
from .command_manager import CommandManager
from .results import ApplicationResult

class Application:
"""
Public headless GridForge Application façade.

```
Parameters
----------
command_manager:
    Fully configured internal Application command manager.

The command manager is intentionally private.

External consumers interact through the semantic façade methods.
"""

def __init__(
    self,
    command_manager: CommandManager,
) -> None:

    if not isinstance(
        command_manager,
        CommandManager,
    ):
        raise TypeError(
            "Application command_manager must be "
            "a CommandManager."
        )

    self._command_manager = command_manager

# ========================================================
# EXECUTION
# ========================================================

def execute(
    self,
    command: Command,
) -> ApplicationResult:
    """
    Execute an Application command.

    This is the canonical mutation entry point.

    External consumers provide immutable Application commands.
    The internal CommandManager performs dispatch,
    transaction management, and history management.
    """

    if not isinstance(
        command,
        Command,
    ):
        raise TypeError(
            "Application.execute requires a Command."
        )

    return self._command_manager.execute(
        command,
    )

# ========================================================
# CAPABILITY DISCOVERY
# ========================================================

def supports(
    self,
    command_type: str,
) -> bool:
    """
    Return whether a command type is currently supported.

    This performs capability discovery only.

    It does not execute or mutate anything.
    """

    if not isinstance(
        command_type,
        str,
    ):
        return False

    return self._command_manager.is_registered(
        command_type,
    )

def command_types(
    self,
) -> tuple[str, ...]:
    """
    Return the currently registered command types.

    The returned tuple is immutable.

    This is a capability-discovery API, not an infrastructure
    access API.
    """

    return self._command_manager.registered_commands()
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"Application",
]
