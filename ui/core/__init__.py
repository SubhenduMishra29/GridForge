# ============================================================
# File: ui/core/__init__.py
# GridForge V2 — UI Core Package
# ============================================================
"""
GridForge V2 UI Core
====================

The ``ui.core`` package provides the foundational infrastructure
and coordination services shared by the GridForge graphical UI.

UI Core is an infrastructure layer.

It provides stable services and contracts for:

    - UI/application controller access
    - command execution and history
    - selection management
    - plugin infrastructure
    - panel registration
    - renderer registration
    - tool management
    - geometric snapping
    - Qt abstraction

UI Core does NOT own engineering truth.

Engineering state remains authoritative in:

    core.model
    core.network
    core.analysis
    core.solver
    core.protection
    core.simulation
    ...

Architectural Position
----------------------

    GridForge UI
        │
        ├── Canvas
        ├── Tools
        ├── Panels
        ├── Plugins
        └── Renderers
                │
                ▼
             ui.core
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
    Services  Registries Contracts
        │
        ▼
    Controllers
        │
        ▼
    GridForge Core


Ownership Boundary
------------------

UI Core may own or coordinate UI/application state such as:

    - active tool
    - selection
    - command history
    - plugin lifecycle
    - renderer registration
    - panel registration
    - UI service registration
    - snapping configuration

UI Core must never become the authoritative owner of:

    - buses
    - lines
    - transformers
    - generators
    - electrical topology
    - Y-bus
    - power-flow state
    - solver state
    - protection state
    - simulation state
    - persistent engineering state

The Controller/Core remains authoritative for engineering
operations and engineering state.

Qt Boundary
-----------

GridForge V2 uses PySide6.

All Qt dependencies used by the UI subsystem must pass through:

    ui.core.qt

Concrete UI modules must not directly import:

    PySide6
    PyQt5
    PyQt6
    PySide2

The ``ui.core`` package itself does not re-export Qt classes.
Consumers requiring Qt types should explicitly import them from:

    ui.core.qt

Public Service Boundary
-----------------------

The package exposes stable UI infrastructure services.

Current services include:

    CommandManager
    SelectionManager

Additional UI infrastructure is exposed through its dedicated
modules and registries rather than through a universal manager.

Design Principles
-----------------

1. Core remains authoritative.

2. UI state must not become engineering state.

3. Qt remains behind a single abstraction boundary.

4. Registries remain focused on their respective responsibilities.

5. Plugin loading remains explicit.

6. Concrete plugins and renderers are not implicitly imported
   by this package.

7. Command execution remains independent of Qt.

8. Selection is a projection of authoritative Controller state.

9. UI infrastructure must remain lightweight.

10. Dependencies must remain acyclic.

11. No engineering computation belongs in ``ui.core``.

12. No duplicate engineering state belongs in ``ui.core``.

Future Direction
----------------

The UI Core is intended to evolve into a stable infrastructure
layer supporting the complete GridForge V2 GUI.

Future capabilities may include:

    - unified UI service context
    - command registry and command discovery
    - keyboard shortcut infrastructure
    - workspace management
    - multi-canvas context management
    - navigation services
    - panel/dock registration
    - UI event infrastructure
    - application UI state management
    - renderer lifecycle management
    - tool lifecycle management
    - plugin dependency resolution
    - plugin capability discovery
    - persistent UI preferences
    - theme and presentation services
    - context-sensitive action infrastructure
    - UI diagnostics and service health reporting

These extensions must preserve the fundamental boundary:

    UI Infrastructure
          │
          ▼
    Controller
          │
          ▼
    GridForge Core

UI Core must never evolve into a second application Core.

Package Philosophy
------------------

The ``ui.core`` package is deliberately small in architectural
scope but broad in infrastructural usefulness.

It should provide the mechanisms that higher-level UI components
need without embedding the behavior of those components.

For example:

    SelectTool
        │
        ▼
    SelectionManager
        │
        ▼
    Controller
        │
        ▼
    GridForge Core

and:

    UI Command
        │
        ▼
    CommandManager
        │
        ▼
    Controller
        │
        ▼
    GridForge Core

The infrastructure coordinates the interaction, while the
authoritative application and engineering layers determine the
result.

Import Policy
-------------

Prefer explicit imports from the relevant UI Core module:

    from ui.core.command_manager import CommandManager
    from ui.core.selection_manager import SelectionManager

rather than importing implementation details from unrelated
UI packages.

The package-level namespace should remain intentionally small.

This prevents ``ui.core`` from becoming a universal namespace
or an implicit dependency aggregator.

GridForge V2 Guiding Principle
------------------------------

    Shared UI infrastructure belongs in ``ui.core``.
    Engineering truth belongs in ``core``.

This boundary is fundamental to maintaining a scalable,
testable, headless Core and a modular GUI architecture.
"""

from __future__ import annotations

# ============================================================
# Public UI Core Services
# ============================================================

from ui.core.command_manager import CommandManager
from ui.core.selection_manager import SelectionManager


# ============================================================
# Public API
# ============================================================

__all__ = [
    "CommandManager",
    "SelectionManager",
]
