# ============================================================
# File: core/application/commands/__init__.py
# GridForge V2 — Headless Application Commands
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Headless Application Commands
=============================================

Public package API for immutable Application command contracts.

This module is intentionally a thin re-export layer.

Canonical command definitions live in:

    core.application.commands.model_commands

Commands represent Application intent only.

They:

    * do not mutate Core;
    * do not mutate Network;
    * do not resolve endpoints;
    * do not manipulate topology;
    * do not access UI state;
    * do not access Qt;
    * do not contain Core model objects;
    * do not contain solver indices;
    * do not contain Y-bus indices;
    * do not contain numerical matrix data.

Endpoint-bearing commands carry EndpointReference value objects.
Endpoint resolution belongs to the Application handler boundary.

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
    ModelService
          |
          v
    Core / Network

The command package is deliberately independent of the numerical
analysis layer. Y-bus construction and numerical index reconciliation
are outside this Application command contract and are audited separately.
"""

from __future__ import annotations

from .model_commands import (
    # ========================================================
    # BUS
    # ========================================================
    CREATE_BUS,
    DELETE_BUS,
    CreateBusCommand,
    DeleteBusCommand,

    # ========================================================
    # LINE
    # ========================================================
    CREATE_LINE,
    DELETE_LINE,
    CreateLineCommand,
    DeleteLineCommand,

    # ========================================================
    # TRANSFORMER
    # ========================================================
    CREATE_TRANSFORMER,
    DELETE_TRANSFORMER,
    CreateTransformerCommand,
    DeleteTransformerCommand,

    # ========================================================
    # LOAD
    # ========================================================
    CREATE_LOAD,
    DELETE_LOAD,
    UPDATE_LOAD,
    CreateLoadCommand,
    DeleteLoadCommand,
    UpdateLoadCommand,

    # ========================================================
    # GRID
    # ========================================================
    CREATE_GRID,
    DELETE_GRID,
    UPDATE_GRID,
    CreateGridCommand,
    DeleteGridCommand,
    UpdateGridCommand,

    # ========================================================
    # BRANCH
    # ========================================================
    CREATE_BRANCH,
    UPDATE_BRANCH,
    DELETE_BRANCH,
    CreateBranchCommand,
    UpdateBranchCommand,
    DeleteBranchCommand,

    # ========================================================
    # CABLE
    # ========================================================
    CREATE_CABLE,
    UPDATE_CABLE,
    DELETE_CABLE,
    CreateCableCommand,
    UpdateCableCommand,
    DeleteCableCommand,

    # ========================================================
    # SWITCH
    # ========================================================
    CREATE_SWITCH,
    UPDATE_SWITCH,
    DELETE_SWITCH,
    OPEN_SWITCH,
    CLOSE_SWITCH,
    PUT_SWITCH_IN_SERVICE,
    TAKE_SWITCH_OUT_OF_SERVICE,
    CreateSwitchCommand,
    UpdateSwitchCommand,
    DeleteSwitchCommand,
    OpenSwitchCommand,
    CloseSwitchCommand,
    PutSwitchInServiceCommand,
    TakeSwitchOutOfServiceCommand,

    # ========================================================
    # DISCONNECTOR
    # ========================================================
    CREATE_DISCONNECTOR,
    UPDATE_DISCONNECTOR,
    DELETE_DISCONNECTOR,
    OPEN_DISCONNECTOR,
    CLOSE_DISCONNECTOR,
    PUT_DISCONNECTOR_IN_SERVICE,
    TAKE_DISCONNECTOR_OUT_OF_SERVICE,
    CreateDisconnectorCommand,
    UpdateDisconnectorCommand,
    DeleteDisconnectorCommand,
    OpenDisconnectorCommand,
    CloseDisconnectorCommand,
    PutDisconnectorInServiceCommand,
    TakeDisconnectorOutOfServiceCommand,

    # ========================================================
    # FUSE
    # ========================================================
    CREATE_FUSE,
    UPDATE_FUSE,
    DELETE_FUSE,
    BLOW_FUSE,
    RESET_FUSE,
    PUT_FUSE_IN_SERVICE,
    TAKE_FUSE_OUT_OF_SERVICE,
    CreateFuseCommand,
    UpdateFuseCommand,
    DeleteFuseCommand,
    BlowFuseCommand,
    ResetFuseCommand,
    PutFuseInServiceCommand,
    TakeFuseOutOfServiceCommand,
)


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    # ========================================================
    # BUS
    # ========================================================
    "CREATE_BUS",
    "DELETE_BUS",
    "CreateBusCommand",
    "DeleteBusCommand",

    # ========================================================
    # LINE
    # ========================================================
    "CREATE_LINE",
    "DELETE_LINE",
    "CreateLineCommand",
    "DeleteLineCommand",

    # ========================================================
    # TRANSFORMER
    # ========================================================
    "CREATE_TRANSFORMER",
    "DELETE_TRANSFORMER",
    "CreateTransformerCommand",
    "DeleteTransformerCommand",

    # ========================================================
    # LOAD
    # ========================================================
    "CREATE_LOAD",
    "DELETE_LOAD",
    "UPDATE_LOAD",
    "CreateLoadCommand",
    "DeleteLoadCommand",
    "UpdateLoadCommand",

    # ========================================================
    # GRID
    # ========================================================
    "CREATE_GRID",
    "DELETE_GRID",
    "UPDATE_GRID",
    "CreateGridCommand",
    "DeleteGridCommand",
    "UpdateGridCommand",

    # ========================================================
    # BRANCH
    # ========================================================
    "CREATE_BRANCH",
    "UPDATE_BRANCH",
    "DELETE_BRANCH",
    "CreateBranchCommand",
    "UpdateBranchCommand",
    "DeleteBranchCommand",

    # ========================================================
    # CABLE
    # ========================================================
    "CREATE_CABLE",
    "UPDATE_CABLE",
    "DELETE_CABLE",
    "CreateCableCommand",
    "UpdateCableCommand",
    "DeleteCableCommand",

    # ========================================================
    # SWITCH
    # ========================================================
    "CREATE_SWITCH",
    "UPDATE_SWITCH",
    "DELETE_SWITCH",
    "OPEN_SWITCH",
    "CLOSE_SWITCH",
    "PUT_SWITCH_IN_SERVICE",
    "TAKE_SWITCH_OUT_OF_SERVICE",
    "CreateSwitchCommand",
    "UpdateSwitchCommand",
    "DeleteSwitchCommand",
    "OpenSwitchCommand",
    "CloseSwitchCommand",
    "PutSwitchInServiceCommand",
    "TakeSwitchOutOfServiceCommand",

    # ========================================================
    # DISCONNECTOR
    # ========================================================
    "CREATE_DISCONNECTOR",
    "UPDATE_DISCONNECTOR",
    "DELETE_DISCONNECTOR",
    "OPEN_DISCONNECTOR",
    "CLOSE_DISCONNECTOR",
    "PUT_DISCONNECTOR_IN_SERVICE",
    "TAKE_DISCONNECTOR_OUT_OF_SERVICE",
    "CreateDisconnectorCommand",
    "UpdateDisconnectorCommand",
    "DeleteDisconnectorCommand",
    "OpenDisconnectorCommand",
    "CloseDisconnectorCommand",
    "PutDisconnectorInServiceCommand",
    "TakeDisconnectorOutOfServiceCommand",

    # ========================================================
    # FUSE
    # ========================================================
    "CREATE_FUSE",
    "UPDATE_FUSE",
    "DELETE_FUSE",
    "BLOW_FUSE",
    "RESET_FUSE",
    "PUT_FUSE_IN_SERVICE",
    "TAKE_FUSE_OUT_OF_SERVICE",
    "CreateFuseCommand",
    "UpdateFuseCommand",
    "DeleteFuseCommand",
    "BlowFuseCommand",
    "ResetFuseCommand",
    "PutFuseInServiceCommand",
    "TakeFuseOutOfServiceCommand",
]
