# ============================================================
# File: core/application/__init__.py
# GridForge V2 — Headless Application Layer
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2
============

Package:
    core.application

Purpose
-------
The ``core.application`` package defines the headless Application
boundary of GridForge V2.

The Application layer sits between external consumers and the
Core engineering/domain layers.

External consumers include:

    * UI;
    * plugins;
    * automation;
    * command-line clients;
    * future headless integrations.

The Application layer translates external intent into controlled
Core operations without taking ownership of Core domain state.

Responsibilities
----------------
The Application layer provides:

    * the canonical Application façade;
    * Application commands;
    * command execution;
    * command handlers;
    * Application services;
    * command history;
    * reversible-command contracts;
    * Application events;
    * structured operation results;
    * structured Application errors;
    * Application context;
    * Application composition/bootstrap infrastructure.

Architectural Boundary
----------------------
The intended dependency direction is:

    UI / Plugins / Automation
              |
              v
        core.application
              |
              v
      Core Domain / Network
              |
              v
       Analysis / Protection
              |
              v
      Solver / Numerical Layer


Core Ownership
--------------
The Application layer does NOT become the owner of:

    * electrical domain state;
    * Network membership;
    * topology state;
    * Y-bus state;
    * engineering invariants;
    * analysis algorithms;
    * solver algorithms;
    * numerical infrastructure.

Those responsibilities remain in their respective Core layers.

Command Boundary
----------------
External consumers must modify Core through Application commands
and Application services.

The intended mutation path is:

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


The following bypass is forbidden:

    UI / Plugin
         |
         X
         |
         v
    Core internals


Headless Requirement
--------------------
This package MUST remain independent of presentation technology.

It MUST NOT depend on:

    * PySide6;
    * PyQt5;
    * PyQt6;
    * Qt;
    * QWidget or other UI widgets;
    * QGraphicsScene;
    * QGraphicsItem;
    * SLD/canvas implementation;
    * renderers;
    * UI controllers;
    * presentation state.

The Application layer must remain executable without a GUI.

Public API
----------
Only intentionally stable Application contracts are exported from
this package.

The following are public package-level contracts:

    Application
        Canonical headless Application façade.

    Command
        Base Application command contract.

    ApplicationResult
        Structured Application operation result.

    ApplicationError
        Base Application error contract.

    ValidationError
    DomainError
    ResourceError
    ExecutionError
        Structured Application error categories.

Implementation Infrastructure
------------------------------
The following remain implementation/composition modules and are
not automatically promoted to the package-level public API:

    * CommandManager;
    * CommandHistory;
    * command handlers;
    * ModelService;
    * command definitions;
    * bootstrap;
    * ApplicationContext;
    * event implementation infrastructure.

These modules may be imported directly by internal Application
components when required.

Events and Reversibility
------------------------
Application events represent facts produced by Application
operations.

Commands represent requested intent.

Reversible commands explicitly opt into reversibility through the
Application reversible-command contract.

Neither events nor reversibility grant direct access to Core
internals.

Architecture Status
-------------------
This package implements the frozen GridForge V2 Headless
Core/Application boundary.

The package-level exports are intentionally minimal so that the
public Application contract remains stable while implementation
details evolve internally.
"""

from __future__ import annotations

from .application import Application
from .command import Command
from .errors import (
    ApplicationError,
    DomainError,
    ExecutionError,
    ResourceError,
    ValidationError,
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
