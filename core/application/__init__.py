# ============================================================
# File: core/application/commands/__init__.py
# GridForge V2 — Application Command Definitions
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Application Commands
====================================

Public command definitions for the headless Application layer.

Commands represent immutable application intent.

They do not:
    * mutate Core state;
    * execute services;
    * resolve endpoints;
    * access UI or Qt;
    * contain Core model objects.

Endpoint-bearing commands use ``EndpointReference`` values.

An endpoint reference may identify either:

    * a Bus directly by its Bus ID; or
    * a Terminal by equipment type, equipment ID,
      and terminal role.

Endpoint resolution is performed by ``EndpointResolver`` at
command-handler execution time.
"""

from .model_commands import (
    CreateBusCommand,
    CreateLineCommand,
    CreateTransformerCommand,
    DeleteBusCommand,
    DeleteLineCommand,
    DeleteTransformerCommand,
)


__all__ = [
    "CreateBusCommand",
    "CreateLineCommand",
    "CreateTransformerCommand",
    "DeleteBusCommand",
    "DeleteLineCommand",
    "DeleteTransformerCommand",
]
