# ============================================================
# File: core/application/commands/__init__.py
# GridForge V2 — Headless Application Commands
# ============================================================
"""
GridForge V2
============

Package:
    core.application.commands

Purpose
-------
Public Application command boundary.

Concrete commands represent explicit Application intent.

Commands:

    CreateBusCommand
    DeleteBusCommand
    CreateLineCommand
    DeleteLineCommand

Architectural flow
------------------

    UI / Plugin / Automation
              |
              v
       Application Command
              |
              v
       CommandManager
              |
              v
       Application Handler
              |
              v
       Application Service
              |
              v
             Core

Commands do NOT:

    * mutate Core;
    * mutate Network;
    * manipulate topology;
    * access Qt;
    * access graphics objects;
    * execute services.

The command package is therefore a transportable Application
intent boundary.

Current model commands
----------------------

    model.create_bus
    model.delete_bus
    model.create_line
    model.delete_line

The corresponding handlers are registered through the
Application composition boundary.
"""

from __future__ import annotations

from .model_commands import (
    CREATE_BUS,
    CREATE_LINE,
    DELETE_BUS,
    DELETE_LINE,
    CreateBusCommand,
    CreateLineCommand,
    DeleteBusCommand,
    DeleteLineCommand,
)


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "CREATE_BUS",
    "DELETE_BUS",
    "CREATE_LINE",
    "DELETE_LINE",
    "CreateBusCommand",
    "DeleteBusCommand",
    "CreateLineCommand",
    "DeleteLineCommand",
]
