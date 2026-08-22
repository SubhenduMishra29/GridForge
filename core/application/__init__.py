# ============================================================
# File: core/application/__init__.py
# GridForge V2 — Headless Application Layer
# ============================================================
"""
GridForge V2
============

Package:
    core.application

Purpose
-------
The ``core.application`` package is the headless Application
boundary of GridForge V2.

This package sits between external consumers such as the UI,
plugins, automation, and the Core engineering/domain layers.

The Application layer is responsible for:

    * application commands;
    * command execution and history;
    * application context;
    * application services;
    * application events;
    * structured operation results;
    * structured application errors.

The Application layer is deliberately headless.

It MUST NOT depend on:

    * PySide6;
    * PyQt5;
    * PyQt6;
    * Qt;
    * UI widgets;
    * SLD/canvas objects;
    * renderers;
    * graphics scenes;
    * UI controllers;
    * presentation state.

Architectural Boundary
----------------------
The intended dependency direction is:

    UI / Plugins
          |
          v
    core.application
          |
          v
    Core Domain / Network / Analysis
          |
          v
    Solver / Numerical Infrastructure

The reverse dependency is forbidden:

    Core Domain
        X
        |
        v
    core.application

The Application layer orchestrates Core operations but does not
replace Core domain ownership or domain invariants.

Public API
----------
Only intentionally public Application contracts should eventually
be exported from this package.

Implementation modules remain internal unless explicitly promoted
to the public Application contract.

Current Status
--------------
This package is being implemented incrementally according to the
frozen GridForge V2 Headless Core/Application Boundary.

At this stage, the package establishes the Application error
contract. Additional contracts are introduced independently and
tested before being integrated.
"""

from __future__ import annotations

from .errors import (
    ApplicationError,
    DomainError,
    ExecutionError,
    ResourceError,
    ValidationError,
)

__all__ = [
    "ApplicationError",
    "ValidationError",
    "DomainError",
    "ResourceError",
    "ExecutionError",
]
