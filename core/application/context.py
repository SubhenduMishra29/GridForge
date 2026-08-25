# ============================================================
# File: core/application/context.py
# GridForge V2 — Headless Application Context
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Headless Application Context
============================================

Defines the immutable dependency context used by the
GridForge V2 Application layer.

Architectural Position
----------------------

    Composition Root
           |
           v
    ApplicationContext
           |
           v
       Core Network
           |
           v
      Domain Model

ApplicationContext is an internal dependency boundary.

It provides already-constructed Core dependencies to
Application-layer components.

It does NOT:

    * construct the Core;
    * execute commands;
    * own command history;
    * manage undo/redo;
    * own UI state;
    * know about Qt;
    * know about SLD/canvas state;
    * render anything;
    * manage plugins;
    * perform domain calculations.

Core Authority
--------------

The Core remains authoritative for:

    * domain state;
    * topology;
    * validation;
    * electrical behavior;
    * calculations;
    * numerical state.

ApplicationContext merely supplies approved dependencies.

Application services must use the public APIs of those
dependencies and must not bypass Core invariants.

Dependency Injection
--------------------

The Composition Root constructs the Core objects first:

    network = Network(...)

and then constructs:

    context = ApplicationContext(
        network=network,
    )

ApplicationContext intentionally contains only explicit,
approved dependencies.

It must NOT become a generic service locator.

Headless Boundary
-----------------

This module has no dependency on:

    * PySide6;
    * PyQt;
    * Qt;
    * UI;
    * SLD;
    * canvas;
    * renderers;
    * plugins.

Python Compatibility
--------------------

GridForge V2 targets Python 3.10 and 3.11.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApplicationContext:
    """
    Immutable dependency context for the Headless Application
    layer.

    Parameters
    ----------
    network:
        Canonical, already-constructed Core Network.

    Notes
    -----
    The context deliberately starts small.

    New dependencies must only be introduced when an actual
    Application-layer component requires them.

    ApplicationContext is not a service locator and must not
    become a dynamically populated dependency container.
    """

    network: Any

    def __post_init__(self) -> None:
        """
        Validate the minimum context contract.

        ``network`` remains typed as ``Any`` so that the
        Application package does not acquire a hard import-time
        dependency on a particular Core Network implementation.

        The Composition Root is responsible for constructing and
        supplying the correct Network implementation.
        """

        if self.network is None:
            raise ValueError(
                "ApplicationContext network must not be None."
            )


__all__ = [
    "ApplicationContext",
]
