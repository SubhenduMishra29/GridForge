# ============================================================
# File: core/application/context.py
# GridForge V2 — Headless Application Context
# ============================================================
"""
GridForge V2
============

Module:
    core.application.context

Purpose
-------
Defines the headless ApplicationContext used by GridForge V2
Application services and commands.

The ApplicationContext is the controlled dependency boundary
between the Application layer and the Core layer.

It provides access to already-constructed Core capabilities.

It does NOT construct the Core.
It does NOT own the UI.
It does NOT contain presentation state.

Architectural Position
----------------------

    Composition Root
           |
           v
    ApplicationContext
           |
           +------------------+
           |                  |
           v                  v
       Core Network       Core services
           |
           v
      Domain Model

The UI may receive an ApplicationContext or an Application
facade, but the context itself remains completely headless.

Responsibilities
----------------
ApplicationContext is responsible for:

    * holding approved Core dependencies;
    * exposing those dependencies to Application services;
    * providing a single controlled dependency surface;
    * preventing Application services from relying on global
      Core state.

ApplicationContext is NOT responsible for:

    * command execution;
    * command history;
    * undo/redo;
    * event dispatch;
    * UI state;
    * Qt;
    * project presentation;
    * SLD/canvas state;
    * rendering;
    * plugin lifecycle;
    * domain calculations.

Dependency Injection
--------------------
The Composition Root constructs the Core objects and then
constructs the ApplicationContext.

Example:

    network = Network(...)
    context = ApplicationContext(
        network=network,
    )

Application services receive the context rather than importing
global application state.

This makes the Application layer:

    * headless;
    * deterministic;
    * composable;
    * testable;
    * suitable for CLI/automation;
    * suitable for plugin use.

Core Boundary
-------------
The context exposes Core objects through explicit properties.

Application services may use those Core APIs.

They must NOT:

    * replace Core objects;
    * mutate private Core internals;
    * bypass Network public APIs;
    * directly manipulate topology internals;
    * manipulate Y-bus internals.

The Application layer coordinates Core; Core remains authoritative
for domain behavior.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.

This module therefore avoids Python 3.12-only generic syntax.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApplicationContext:
    """
    Immutable dependency context for the Headless Application layer.

    Parameters
    ----------
    network:
        Canonical assembled Core Network.

    Notes
    -----
    The context deliberately starts small.

    Additional dependencies should only be added when an actual
    Application service requires them.

    Do not use ApplicationContext as a general-purpose service
    locator.

    The frozen boundary requires explicit dependencies rather than
    a dynamically populated dictionary of arbitrary objects.
    """

    network: Any

    def __post_init__(self) -> None:
        """
        Validate the minimum ApplicationContext contract.

        ``network`` is intentionally typed as ``Any`` here so that
        this boundary does not force the Application package to
        depend on a concrete Network implementation at import time.

        Runtime validation is intentionally minimal.

        The Composition Root is responsible for supplying the
        correct Core Network implementation.
        """
        if self.network is None:
            raise ValueError(
                "ApplicationContext network must not be None."
            )


__all__ = [
    "ApplicationContext",
]
