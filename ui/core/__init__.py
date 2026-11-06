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

Application boundary
--------------------

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
          core.application
                │
                ▼
               Core

The Application layer is the sole controlled bridge between
presentation intent and Core mutation. UI Core does not contain a
command manager, history implementation, transaction implementation,
or engineering mutation service.

Responsibilities
----------------

UI Core provides stable UI infrastructure and contracts for:

    - Presentation/UI controller access
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

Design Principles
-----------------

1. Core remains authoritative for engineering truth.
2. UI state must not become engineering state.
3. Application is the controlled Core↔UI mutation bridge.
4. Qt remains behind the UI Qt abstraction boundary.
5. Registries remain focused on their responsibilities.
6. Plugin loading remains explicit.
7. Concrete plugins and renderers are not implicitly imported here.
8. Selection is a UI projection of authoritative state.
9. UI infrastructure remains lightweight.
10. Dependencies remain acyclic.
11. No engineering computation belongs in ``ui.core``.
12. No duplicate engineering truth belongs in ``ui.core``.
13. No UI-side command manager or history implementation exists.
"""

__all__: list[str] = []
