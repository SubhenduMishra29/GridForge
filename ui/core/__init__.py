# ============================================================
# File: ui/core/__init__.py
# GridForge V2 — UI Core Package
# Author: Subhendu Mishra
# ============================================================
"""GridForge V2 UI Core — Presentation infrastructure.

The ``ui.core`` package provides foundational infrastructure and
coordination services shared by the graphical UI.

UI Core belongs to the Presentation layer. It may own UI state and
UI infrastructure, but it does not own Application or Core/domain
truth.

Current architectural position
------------------------------

    Presentation UI
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
                ▼
    Presentation Controllers / UI Services
                │
                ▼
    [future explicit UI ↔ Application interface]
                │
                ▼
            Application
                │
                ▼
               Core

The future UI↔Application interface is intentionally not implemented
in this package during the current UI-focused development phase.

Responsibilities
----------------

UI Core provides stable UI infrastructure and contracts for:

    - Presentation/UI controller access
    - UI command infrastructure
    - selection management
    - plugin infrastructure
    - panel registration
    - renderer registration
    - tool management
    - geometric snapping
    - Qt abstraction

UI Core does NOT own engineering truth.

Engineering state remains authoritative in the Core domain:

    core.model
    core.network
    core.analysis
    core.solver
    core.protection
    core.simulation
    ...

Ownership Boundary
------------------

UI Core may own or coordinate UI state such as:

    - active tool
    - selection projection/state
    - UI command history
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

The Application layer will provide the future controlled bridge
between Presentation intent and Core mutation.

Qt Boundary
-----------

GridForge V2 uses PySide6.

All Qt dependencies used by the UI subsystem must pass through:

    ui.core.qt

Concrete UI modules must not directly import PySide6, PyQt5,
PyQt6, or PySide2.

Public Service Boundary
-----------------------

Current UI infrastructure services include:

    CommandManager
    SelectionManager

Additional infrastructure remains exposed through dedicated
modules and focused registries rather than a universal manager.

Design Principles
-----------------

1. Core remains authoritative for engineering truth.
2. UI state must not become engineering state.
3. Application is the future controlled Core↔UI bridge.
4. Qt remains behind the UI Qt abstraction boundary.
5. Registries remain focused on their responsibilities.
6. Plugin loading remains explicit.
7. Concrete plugins and renderers are not implicitly imported here.
8. UI command infrastructure remains independent of Qt.
9. Selection is a UI projection of authoritative state.
10. UI infrastructure remains lightweight.
11. Dependencies remain acyclic.
12. No engineering computation belongs in ``ui.core``.
13. No duplicate engineering truth belongs in ``ui.core``.
"""

__all__: list[str] = []
