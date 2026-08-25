# ============================================================
# File: core/application/commands/__init__.py
# GridForge V2 — Headless Application Commands
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Headless Application Commands.
 
This package contains immutable Application command contracts.

Commands represent requested intent only.

They do NOT:

* mutate Core;
* mutate Network;
* manipulate topology;
* manipulate terminals;
* execute Application Services;
* access Qt;
* access UI;
* access graphics objects.

Execution path
--------------

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


Current canonical model commands
--------------------------------

    model.create_bus
    model.delete_bus

    model.create_line
    model.delete_line

    model.create_transformer
    model.delete_transformer

    model.create_load
    model.delete_load


Endpoint rule
-------------

Line and Transformer creation commands carry EndpointReference
values, not Core endpoint objects.

An EndpointReference may identify:

* a Bus by its Bus ID; or
* a Terminal by equipment type, equipment ID, and terminal role.

Endpoint resolution is performed by EndpointResolver during
command-handler execution.

Load rule
---------

Load creation does not carry a Core Bus or Core Terminal.

A Load is initially created as a disconnected Core model object.

Topology attachment is handled separately by the appropriate
Application topology workflow.
"""

from __future__ import annotations

from .model_commands import (
    CREATE_BUS,
    DELETE_BUS,

    CREATE_LINE,
    DELETE_LINE,

    CREATE_TRANSFORMER,
    DELETE_TRANSFORMER,

    CREATE_LOAD,
    DELETE_LOAD,

    CreateBusCommand,
    DeleteBusCommand,

    CreateLineCommand,
    DeleteLineCommand,

    CreateTransformerCommand,
    DeleteTransformerCommand,

    CreateLoadCommand,
    DeleteLoadCommand,
)


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "CREATE_BUS",
    "DELETE_BUS",

    "CREATE_LINE",
    "DELETE_LINE",

    "CREATE_TRANSFORMER",
    "DELETE_TRANSFORMER",

    "CREATE_LOAD",
    "DELETE_LOAD",

    "CreateBusCommand",
    "DeleteBusCommand",

    "CreateLineCommand",
    "DeleteLineCommand",

    "CreateTransformerCommand",
    "DeleteTransformerCommand",

    "CreateLoadCommand",
    "DeleteLoadCommand",
]
