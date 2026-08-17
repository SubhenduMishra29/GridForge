# ⚡ GridForge Plugins

## Extensible Plugin Architecture for GridForge V2

The **GridForge Plugin System** provides the controlled extension mechanism for GridForge V2.

It allows new capabilities to be added without modifying the architectural contracts of the existing application.

Plugins may extend:

* User-interface composition
* Engineering tools
* Visualization
* Protection functions
* Dynamic models
* Equipment models
* Analysis services
* Solver backends
* Application services
* Future digital-twin capabilities

The plugin architecture is governed by a fundamental rule:

> **Plugins extend GridForge through explicit contracts; they do not bypass GridForge's architectural ownership boundaries.**

---

# 1. Purpose

The plugin subsystem exists to make GridForge extensible while preserving the integrity of the core architecture.

Without a controlled plugin architecture, extensions can gradually introduce:

* Hidden dependencies
* Duplicate state
* Direct manipulation of internal objects
* Circular imports
* GUI/core coupling
* Uncontrolled initialization
* Non-deterministic application composition
* Architectural drift

The GridForge plugin system therefore treats extensibility as an architectural concern rather than simply a mechanism for dynamically importing Python modules.

---

# 2. Plugin Architecture Principle

The plugin system follows:

```text id="u7x0o3"
                 GridForge Application
                         │
                         ▼
                  Plugin Manager
                         │
                         ▼
                   Plugin Context
                         │
                         ▼
                  Plugin Contract
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          UI Plugin   Tool Plugin  Domain Plugin
             │           │           │
             └───────────┼───────────┘
                         ▼
                  Stable GridForge
                     Contracts
```

A plugin is an extension of the platform.

It is not a replacement for the platform architecture.

---

# 3. Core Architectural Rule

The most important plugin rule is:

> **A plugin may extend a subsystem only through the subsystem's established public contract.**

A plugin must not:

* Modify private state directly
* Circumvent validation
* Create a competing authoritative model
* Replace core ownership
* Bypass application controllers
* Directly manipulate unrelated plugin internals
* Introduce GUI dependencies into the core
* Introduce hidden imports into the plugin registry

The plugin system exists to preserve architectural boundaries while enabling extension.

---

# 4. Repository Structure

The GridForge plugin architecture is organized around explicit plugin infrastructure.

```text id="k5q4gc"
GridForge/
│
├── core/
│   └── ...
│
├── ui/
│   ├── ...
│   │
│   └── plugins/
│       ├── __init__.py
│       ├── canvas_plugin.py
│       ├── panels_plugin.py
│       ├── toolbar_plugin.py
│       ├── status_plugin.py
│       ├── plugin_loader.py
│       ├── plugin_registry.py
│       ├── plugin_manager.py
│       ├── plugin_context.py
│       ├── plugin_contract.py
│       ├── plugin_state.py
│       └── plugin_events.py
│
├── plugins/
│   └── ...
│
└── tests/
    └── ...
```

The architecture intentionally distinguishes:

```text id="7o6vkg"
ui/plugins/
```

from:

```text id="yl3hda"
plugins/
```

The first provides application/UI composition infrastructure.

The second is the broader extension namespace for GridForge plugins.

---

# 5. Plugin Categories

GridForge may support several plugin categories.

## UI Plugins

Extend application composition:

* Canvas
* Panels
* Toolbars
* Status areas
* Navigation
* UI services

## Tool Plugins

Extend engineering interaction:

* Editing tools
* Specialized engineering tools
* Visualization tools
* Study tools

## Renderer Plugins

Extend visualization:

* Equipment renderers
* Result renderers
* Protection visualization
* Specialized engineering overlays

## Engineering Plugins

Extend domain capabilities:

* Equipment models
* Protection functions
* Dynamic models
* Measurement devices

## Analysis Plugins

Extend engineering studies:

* Specialized analysis
* Study workflows
* Result processors

## Solver Plugins

Extend numerical execution:

* Alternative solver algorithms
* Numerical backends
* CPU/GPU implementations

## Application Plugins

Extend application-level services:

* Reports
* Export
* Automation
* Engineering workflows

The category of a plugin must not determine or weaken its architectural contract.

---

# 6. Plugin vs Core

The distinction between a plugin and the core is fundamental.

### Core

The core contains authoritative engineering infrastructure.

Examples:

```text id="7v0e0k"
Physical Model
Electrical Network
Analysis
Solver
Protection
Simulation
Validation
```

### Plugin

A plugin provides an extension to an established capability.

```text id="3a7lgo"
Plugin
   │
   ▼
Stable Contract
   │
   ▼
GridForge Subsystem
```

A plugin should not create a parallel architecture simply because an extension needs functionality that the core does not currently expose.

If the required capability is genuinely foundational, the architecture should be reviewed explicitly rather than hidden inside a plugin.

---

# 7. Plugin Contract

Every plugin should conform to an explicit contract.

A contract defines the expectations for:

* Identity
* Lifecycle
* Dependencies
* Capabilities
* Initialization
* Activation
* Deactivation
* Cleanup
* Context access
* Event communication

Conceptually:

```text id="ih8xqf"
PluginContract
     │
     ├── Identity
     ├── Metadata
     ├── Dependencies
     ├── Capabilities
     ├── Lifecycle
     └── Context
```

The contract is the boundary between GridForge and the extension.

---

# 8. Plugin Identity

Every plugin should have a stable identity.

A plugin identity should be distinct from:

* Python module path
* Class name
* Display name
* File name
* Runtime object identity

Conceptually:

```text id="t9i9az"
Plugin ID
   ≠
Python Module
   ≠
Plugin Class
   ≠
Display Name
```

Stable plugin identity enables:

* Deterministic registration
* Dependency resolution
* Configuration
* Diagnostics
* Persistence of plugin configuration
* Version compatibility

---

# 9. Plugin Metadata

Plugin metadata may describe:

* Plugin ID
* Name
* Version
* Description
* Author / vendor
* Plugin category
* Required GridForge version
* Dependencies
* Capabilities
* Compatibility information

Metadata should be declarative where possible.

Runtime behavior should not be required merely to discover basic plugin information.

---

# 10. Plugin Capabilities

A plugin may advertise capabilities.

Examples:

```text id="t1a8o7"
Canvas Extension
Renderer
Tool
Protection Function
Dynamic Model
Analysis Extension
Solver Backend
```

Capabilities allow the application to understand what a plugin provides without depending on undocumented implementation details.

---

# 11. Plugin Dependencies

Plugins may depend on other plugins or platform services.

Dependencies should be:

* Explicit
* Deterministic
* Validated before activation
* Version-aware where required

Conceptually:

```text id="f3qf8c"
Plugin A
   │
   ├── requires Plugin B
   └── requires GridForge API X
```

The plugin manager is responsible for determining whether dependencies can be satisfied.

Circular plugin dependencies should be rejected.

---

# 12. Plugin Lifecycle

A plugin has a controlled lifecycle.

A typical lifecycle is:

```text id="4k29h7"
Discovered
    │
    ▼
Registered
    │
    ▼
Validated
    │
    ▼
Loaded
    │
    ▼
Initialized
    │
    ▼
Activated
    │
    ▼
Running
    │
    ▼
Deactivated
    │
    ▼
Unloaded
```

The exact lifecycle may vary by plugin category, but lifecycle transitions should remain explicit.

---

# 13. Plugin Discovery

Plugin discovery identifies available extensions.

Discovery should answer:

* Which plugins exist?
* What are their identities?
* What capabilities do they provide?
* What dependencies do they require?
* Are they compatible with the current GridForge version?

Discovery should not automatically execute plugin behavior.

This distinction is important:

```text id="4a9l4s"
Discovery
   ≠
Execution
```

---

# 14. Plugin Loader

The `plugin_loader.py` component is responsible for loading plugin implementations after discovery and validation.

Conceptually:

```text id="4v94p2"
Plugin Source
      │
      ▼
Plugin Loader
      │
      ▼
Plugin Object
      │
      ▼
Plugin Contract Validation
```

The loader should provide controlled imports rather than allowing arbitrary application-wide import side effects.

---

# 15. Explicit Loading

GridForge uses explicit plugin loading.

The plugin registry should not implicitly import every concrete plugin merely because it knows about the plugin contract.

The preferred architecture is:

```text id="gj9h9s"
Plugin Discovery
       │
       ▼
Explicit Loader
       │
       ▼
Concrete Plugin
       │
       ▼
Registration
```

rather than:

```text id="6r5b0p"
Registry Import
       │
       ├── imports Plugin A
       ├── imports Plugin B
       ├── imports Plugin C
       └── imports Plugin D
```

Explicit loading improves:

* Determinism
* Testability
* Import safety
* Startup diagnostics
* Dependency control

---

# 16. Plugin Registry

The plugin registry provides a controlled index of registered plugins.

Responsibilities include:

* Register plugin metadata
* Identify plugins
* Retrieve registered plugins
* Detect duplicate identities
* Expose plugin information

The registry should remain lightweight.

It should not become:

* A global application controller
* A hidden dependency injector
* A concrete plugin importer
* A replacement for the plugin manager

A useful conceptual separation is:

```text id="t8v8ez"
Registry
   │
   └── What plugins are registered?

Loader
   │
   └── How are plugins loaded?

Manager
   │
   └── How are plugins controlled?

Context
   │
   └── What services may plugins access?
```

---

# 17. Plugin Manager

The plugin manager coordinates plugin lifecycle.

Responsibilities include:

* Loading plugins
* Initializing plugins
* Resolving dependencies
* Activating plugins
* Deactivating plugins
* Unloading plugins
* Reporting plugin failures
* Managing plugin state

The manager is the lifecycle coordinator.

It should not become the owner of domain-specific engineering state.

---

# 18. Plugin Context

The plugin context provides controlled access to application services.

Conceptually:

```text id="g7r8qn"
                    Plugin
                      │
                      ▼
                PluginContext
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
    Application      UI           Services
      Access       Access         Access
```

The context should expose only the services that the plugin is contractually permitted to use.

This avoids giving every plugin unrestricted access to the entire application.

---

# 19. Context Boundary

A plugin should not need to know the internal structure of unrelated subsystems.

For example, a UI plugin may receive:

* Main application context
* Canvas service
* UI registry
* Tool registration service

It should not directly manipulate:

* Internal solver arrays
* Private network structures
* Internal protection state
* Unrelated plugin internals

The context therefore acts as an architectural security boundary within the application.

---

# 20. Plugin State

`plugin_state.py` represents runtime state associated with plugins.

Plugin state may include:

* Loaded
* Initialized
* Active
* Disabled
* Failed
* Deactivated

Conceptually:

```text id="8oy5z0"
Plugin
  │
  ▼
PluginState
  │
  ├── Discovered
  ├── Loaded
  ├── Initialized
  ├── Active
  ├── Failed
  └── Disabled
```

Plugin runtime state is not the same as engineering state.

---

# 21. Plugin Events

`plugin_events.py` provides controlled communication between plugin components and the application.

The preferred model is:

```text id="3r7z8c"
Plugin A
   │
   ▼
Defined Event
   │
   ▼
Application Event System
   │
   ▼
Plugin B
```

This is preferable to direct manipulation of another plugin's internal objects.

Events should be:

* Explicit
* Typed where practical
* Documented
* Predictable
* Observable

---

# 22. UI Composition Plugins

GridForge V2 currently uses a plugin-driven UI composition architecture.

The principal UI composition plugins are:

```text id="b1n2o6"
CanvasPlugin
PanelsPlugin
ToolbarPlugin
StatusPlugin
```

These plugins are responsible for composing the application interface.

---

# 23. CanvasPlugin

`CanvasPlugin` composes the engineering visualization environment.

It may coordinate:

* Graphics View
* Scene
* Grid
* Coordinate system
* Snap system
* Interaction manager
* Navigation
* Render system

The plugin does not become the owner of the electrical network.

---

# 24. PanelsPlugin

`PanelsPlugin` composes application panels.

Potential panels include:

* Property inspector
* Equipment information
* Network hierarchy
* Analysis results
* Protection results
* Simulation results

Panels are UI representations of authoritative state.

They must not maintain competing engineering state.

---

# 25. ToolbarPlugin

`ToolbarPlugin` composes engineering tool presentation.

The current concrete tool baseline is:

```text id="r42dxy"
SelectTool
BusTool
LineTool
```

The toolbar presents these tools to the user.

It does not implement the engineering behavior of the tools.

---

# 26. StatusPlugin

`StatusPlugin` composes status and feedback UI.

It may display:

* Active tool
* Coordinates
* Selection information
* Interaction state
* Validation feedback
* Application messages
* Simulation state

Status information is presentation state.

---

# 27. Tool Plugins

Tools can be introduced as plugins where the architecture requires extensibility.

A tool plugin may provide:

* Tool identity
* Tool activation
* Tool deactivation
* Input handling
* Preview behavior
* Interaction contracts

The tool remains an interaction component.

It does not become the owner of engineering state.

---

# 28. Renderer Plugins

Renderer plugins may extend visualization.

Examples:

```text id="1eb6e4"
Bus Renderer
Line Renderer
Transformer Renderer
Generator Renderer
Protection Renderer
Result Renderer
```

The renderer consumes authoritative state.

It does not create a second engineering representation.

---

# 29. Engineering Domain Plugins

Future domain plugins may extend:

* Protection functions
* Dynamic models
* Equipment models
* Measurement devices
* Analysis methods

The architectural relationship remains:

```text id="j8q1bo"
Domain Plugin
      │
      ▼
Stable Core Contract
      │
      ▼
GridForge Core
```

If an extension requires changing a foundational ownership boundary, the change should be made explicitly at the architecture level rather than hidden inside a plugin.

---

# 30. Analysis Plugins

Analysis plugins may introduce specialized engineering studies.

A plugin may provide:

* Study definition
* Input specification
* Validation
* Result interpretation
* UI integration

Numerical execution should still use the established solver architecture.

Therefore:

```text id="h7yq6q"
Analysis Plugin
      │
      ▼
Analysis Contract
      │
      ▼
Solver Service
```

An analysis plugin should not embed a hidden numerical engine that bypasses the solver layer.

---

# 31. Solver Backend Plugins

Solver plugins may provide alternative computational backends.

For example:

```text id="u9g8qa"
Solver Contract
      │
      ├── CPU Backend
      ├── Sparse Backend
      └── GPU Backend
```

The engineering model remains backend-independent.

A solver plugin must not force the physical model to depend on:

* CUDA
* GPU-specific arrays
* Vendor-specific libraries
* Hardware-specific data structures

---

# 32. Protection Plugins

Protection extensions may provide specialized protection functions.

Examples include:

* Overcurrent
* Directional
* Distance
* Differential
* Voltage
* Frequency
* Breaker failure

The protection function must preserve the established decision boundary:

```text id="17ikrq"
Measurement
     │
     ▼
Protection Function
     │
     ▼
ProtectionDecision
     │
     ▼
Scheme / Control
     │
     ▼
BreakerManager
```

A protection plugin must not directly manipulate a physical breaker merely because it detects a trip condition.

---

# 33. Dynamic Model Plugins

Dynamic plugins may provide models for:

* Generators
* Governors
* AVRs
* PSS
* Motors
* Dynamic loads
* Other dynamic equipment

The plugin supplies the model contract.

The simulation engine owns runtime execution.

```text id="jpl6tb"
Dynamic Model Plugin
        │
        ▼
Dynamic Model Contract
        │
        ▼
Simulation Engine
        │
        ▼
Numerical Integrator
```

---

# 34. Plugin and Persistence

Plugin configuration may require persistence.

The correct relationship is:

```text id="gnqv5b"
Plugin
  │
  ▼
Plugin Configuration
  │
  ▼
Persistence Layer
  │
  ▼
Project File
```

Plugins must not introduce arbitrary file I/O into domain objects.

Plugin configuration should remain distinguishable from engineering state.

---

# 35. Plugin and GUI Separation

UI plugins may depend on UI infrastructure.

Core plugins must remain GUI-independent unless their contract explicitly belongs to the UI layer.

The dependency direction should remain:

```text id="17a1u8"
UI Plugin
    │
    ▼
Application / Core Services
```

not:

```text id="8d9nup"
Core
   │
   ▼
UI Plugin
```

This preserves headless operation.

---

# 36. Plugin and Engineering State Ownership

The plugin architecture does not change the GridForge state-ownership rules.

| State                 | Authority            |
| --------------------- | -------------------- |
| Physical equipment    | `core.model`         |
| Electrical topology   | `core.network`       |
| Y-bus                 | `core.network`       |
| Numerical computation | `core.solver`        |
| Study definition      | `core.analysis`      |
| Protection execution  | Protection subsystem |
| Protection decision   | `ProtectionDecision` |
| Runtime simulation    | `core.simulation`    |
| Validation            | `core.validation`    |
| GUI state             | UI subsystem         |
| Plugin runtime state  | Plugin subsystem     |
| Project persistence   | Persistence layer    |

A plugin may **consume or extend** authoritative state.

It must not silently replace the authoritative owner.

---

# 37. Plugin Identity vs Engineering Identity

Plugin identity must remain separate from engineering identity.

```text id="qz7yvl"
Plugin ID
   ≠
Asset ID
   ≠
Equipment ID
   ≠
Terminal ID
   ≠
Network Node ID
   ≠
Numerical Index
```

A plugin may create engineering objects, but those objects must receive their identity from the appropriate engineering subsystem.

---

# 38. Deterministic Plugin Composition

Plugin composition should be deterministic.

Given identical:

* GridForge version
* Plugin set
* Plugin versions
* Configuration
* Dependencies

the resulting plugin composition should be reproducible.

Determinism matters for:

* Testing
* Debugging
* Application startup
* UI composition
* Engineering workflows
* Deployment

Plugin loading order should be derived from explicit dependencies rather than accidental Python import order.

---

# 39. Plugin Failure Isolation

A plugin failure should be distinguishable from a core failure.

Examples:

```text id="8s2ynf"
Plugin discovery failed
Plugin dependency missing
Plugin contract invalid
Plugin initialization failed
Plugin activation failed
Plugin runtime failure
```

The plugin manager should report the affected plugin and lifecycle stage.

A defective optional plugin should not silently corrupt unrelated engineering state.

---

# 40. Plugin Validation

Before activation, plugins should be validated for:

* Identity
* Contract compliance
* Compatibility
* Dependencies
* Required capabilities
* Configuration
* Lifecycle requirements

Conceptually:

```text id="g9f6t8"
Plugin
  │
  ▼
Identity Validation
  │
  ▼
Contract Validation
  │
  ▼
Dependency Validation
  │
  ▼
Compatibility Validation
  │
  ▼
Activation
```

---

# 41. Security and Isolation Principles

Although GridForge plugins execute within the application process, the architecture should minimize unnecessary access.

Plugins should receive only the application services required by their contract.

The system should avoid:

* Global mutable state
* Unrestricted service access
* Direct access to private subsystem internals
* Hidden filesystem operations
* Undocumented cross-plugin dependencies

This reduces the probability of architectural corruption.

---

# 42. Testing Strategy

The plugin subsystem requires layered testing.

## Contract Tests

Verify that plugins satisfy:

* Required interfaces
* Metadata requirements
* Lifecycle requirements
* Capability declarations

## Registry Tests

Verify:

* Registration
* Duplicate detection
* Lookup
* Metadata retrieval
* Deterministic behavior

## Loader Tests

Verify:

* Explicit loading
* Import failures
* Invalid plugins
* Contract validation

## Manager Tests

Verify:

* Lifecycle transitions
* Dependency resolution
* Activation
* Deactivation
* Failure handling

## Context Tests

Verify:

* Service access
* Permission boundaries
* Context isolation

## Integration Tests

Verify:

```text id="7bpy6e"
Plugin
   │
   ▼
Plugin Manager
   │
   ▼
Application
   │
   ▼
GridForge Core / UI
```

without allowing plugins to violate architectural ownership.

---

# 43. Architectural Rules

The following rules govern the GridForge plugin subsystem.

|  # | Rule                                     | Requirement                                                                  |
| -: | ---------------------------------------- | ---------------------------------------------------------------------------- |
|  1 | **Explicit contracts**                   | Plugins interact through defined contracts                                   |
|  2 | **Stable identity**                      | Every plugin has a stable plugin identity                                    |
|  3 | **Explicit loading**                     | Concrete plugins are explicitly loaded                                       |
|  4 | **Registry separation**                  | Registry does not become a concrete-plugin importer                          |
|  5 | **Manager ownership**                    | Lifecycle belongs to PluginManager                                           |
|  6 | **Context boundary**                     | Plugins access application services through PluginContext                    |
|  7 | **No hidden state**                      | Plugins must not create competing authoritative state                        |
|  8 | **Dependency declaration**               | Plugin dependencies must be explicit                                         |
|  9 | **Deterministic activation**             | Plugin composition must be reproducible                                      |
| 10 | **Failure isolation**                    | Plugin failures must be identifiable and contained                           |
| 11 | **Core ownership remains authoritative** | Plugins do not replace core state ownership                                  |
| 12 | **No GUI leakage into core**             | UI plugins cannot force GUI dependencies into core                           |
| 13 | **No direct plugin internals**           | Plugins communicate through contracts/events                                 |
| 14 | **Persistence separation**               | Plugin configuration does not become arbitrary domain I/O                    |
| 15 | **Numerical backend independence**       | Solver plugins do not redesign the engineering model                         |
| 16 | **Protection decision boundary**         | Protection plugins produce decisions rather than directly operating breakers |
| 17 | **Testing before freeze**                | Plugin infrastructure must be audited and tested before finalization         |

---

# 44. Plugin Development Workflow

GridForge plugin development follows the broader V2 freeze process:

```text id="5f3bmx"
Architecture
     │
     ▼
Contract Definition
     │
     ▼
Implementation
     │
     ▼
Audit
     │
     ▼
Correction
     │
     ▼
Fresh Audit
     │
     ▼
Unit Tests
     │
     ▼
Integration Tests
     │
     ▼
Application Validation
     │
     ▼
Finalization
     │
     ▼
Freeze
```

The important principle is:

> **A plugin is finalized only after its implementation is shown to conform to the established contract.**

Tests should not be weakened merely to accommodate incorrect plugin behavior.

---

# 45. Current UI Plugin Baseline

The current GridForge V2 UI composition architecture defines four principal concrete composition plugins:

```text id="u9v6kn"
CanvasPlugin
PanelsPlugin
ToolbarPlugin
StatusPlugin
```

Supporting infrastructure includes:

```text id="0u8v0g"
PluginLoader
PluginRegistry
PluginManager
PluginContext
PluginContract
PluginState
PluginEvents
```

This infrastructure forms the current UI plugin baseline.

---

# 46. Current Tool Baseline

The UI plugin system currently composes a deliberately frozen concrete tool set:

```text id="q3n2f7"
SelectTool
BusTool
LineTool
```

The plugin architecture may eventually permit additional tools, but additions should occur through an explicit architectural decision.

The plugin system must not be used to bypass the current tool contract.

---

# 47. Example: UI Plugin Composition

The application composition flow is:

```text id="o1s2k4"
Application Startup
        │
        ▼
Plugin Loader
        │
        ▼
Plugin Registry
        │
        ▼
Plugin Manager
        │
        ▼
Plugin Context
        │
        ├──────────────┐
        ▼              ▼
 CanvasPlugin      PanelsPlugin
        │              │
        ├──────┐       │
        ▼      ▼       ▼
     Canvas  Tools   Panels
        │
        ├── ToolbarPlugin
        └── StatusPlugin
```

The `MainWindow` hosts the composed result rather than implementing every component itself.

---

# 48. Example: Domain Plugin

A future protection plugin may follow:

```text id="z1y7n2"
Protection Plugin
        │
        ▼
Protection Contract
        │
        ▼
Measurement Infrastructure
        │
        ▼
Protection Function
        │
        ▼
ProtectionDecision
        │
        ▼
Protection Scheme
        │
        ▼
BreakerManager
```

The plugin extends protection execution while preserving the existing protection decision boundary.

---

# 49. Example: Solver Plugin

A GPU solver extension may follow:

```text id="b9r4d1"
Power Flow Analysis
        │
        ▼
Solver Contract
        │
        ▼
GPU Solver Plugin
        │
        ▼
GPU Numerical Backend
        │
        ▼
Engineering Result
```

The plugin does not alter the physical model merely because GPU execution requires a different numerical representation.

---

# 50. What the Plugin System Is Not

The GridForge plugin subsystem is not:

* ❌ A global import mechanism
* ❌ A dependency bypass
* ❌ A second application architecture
* ❌ A replacement for the core
* ❌ A mechanism for hiding architectural defects
* ❌ A global mutable-state container
* ❌ A substitute for proper controllers
* ❌ A way to bypass validation
* ❌ A mechanism for directly manipulating unrelated plugins
* ❌ A license to create duplicate engineering state

The plugin system exists to **extend the architecture without breaking it**.

---

# 51. Final Plugin Architecture

The complete conceptual plugin architecture is:

```text id="5h8xj3"
                       GridForge Application
                                │
                                ▼
                         Plugin Manager
                                │
                 ┌──────────────┼──────────────┐
                 │              │              │
                 ▼              ▼              ▼
              Loader         Registry        Context
                 │              │              │
                 └──────────────┼──────────────┘
                                │
                                ▼
                         Plugin Contracts
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
      UI Plugins           Domain Plugins        Solver Plugins
          │                     │                     │
          ▼                     ▼                     ▼
       Canvas               Protection             CPU/GPU
       Panels               Dynamics               Backends
       Toolbar              Equipment
       Status               Analysis
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                ▼
                         GridForge Services
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
             Model           Network           Solver
               │                │                │
               └────────────────┼────────────────┘
                                ▼
                         Engineering Truth
```

---

# 52. Guiding Principle

The GridForge plugin system follows one overarching principle:

> ## **Extend through contracts, not through architectural shortcuts.**

Plugins provide extensibility.

Contracts provide stability.

The registry provides controlled discovery.

The loader provides explicit loading.

The manager controls lifecycle.

The context controls access.

Events provide controlled communication.

The GridForge Core remains the authority for engineering truth.

The UI remains the authority for presentation state.

The plugin architecture therefore enables GridForge to grow into a broad engineering platform while preserving the separation between:

```text id="6x8f0d"
Engineering Truth
       │
       ▼
Core Services
       │
       ▼
Application
       │
       ▼
Plugins
       │
       ▼
Specialized Extensions
```

The objective is not to make everything a plugin.

The objective is to make **legitimate extensions possible without compromising the architecture**.

---

<p align="center"><em>GridForge Plugins — extend the platform without breaking its engineering boundaries.</em></p>
