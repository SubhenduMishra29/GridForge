# GridForge V2 — Presentation Controllers

**Author:** Subhendu Mishra

## Purpose

`ui/controllers/` contains **Presentation-layer controllers**. These controllers coordinate UI components and UI services; they are not the Application layer and are not the Core-to-UI bridge.

The authoritative architecture is:

```text
User / Qt Event
      ↓
Widget / Canvas
      ↓
Tool / Presentation Controller
      ↓
[future Application interface]
      ↓
Application
      ↓
Core
```

The Application layer remains outside `ui/`. It is the future controlled bridge between Presentation and Core.

## Responsibilities

Presentation controllers may:

- coordinate UI components;
- compose UI services;
- route UI intent toward the future Application boundary;
- coordinate canvas, navigation, rendering, selection, and tool services;
- expose UI-facing lifecycle and presentation operations;
- translate UI-level state into requests without owning engineering truth.

## Controllers must not own

Presentation controllers must not become owners of:

- Core engineering objects;
- electrical topology;
- solver state;
- protection state;
- simulation state;
- authoritative engineering validation;
- Core mutation;
- rendering implementation;
- viewport/navigation state when a dedicated canvas service owns it.

## Boundary rule

```text
Presentation Controller
        ↓
Future Application Contract
        ↓
Core
```

Do not bypass the future Application boundary with direct Core mutation.

## Canvas controller rule

`CanvasController` is a **presentation orchestration controller**. It coordinates existing Canvas services such as `GraphicsView`, `InteractionManager`, `RenderSystem`, `SelectionManager`, and navigation. It does not become an ApplicationController or engineering workflow engine.

## Registry rule

`ControllerRegistry` is only a deterministic registry of explicitly constructed Presentation controllers. It does not discover, instantiate, or own application/Core services.

## Current implementation phase

During the current UI-first implementation phase:

1. build and strengthen Presentation architecture;
2. keep Core/Application integration behind a future interface;
3. do not recreate `ui/application`;
4. do not move Application responsibilities into `ui/controllers`;
5. add integration tests later, after the UI architecture is implemented.

## Ownership summary

```text
Core              → engineering truth
Application       → controlled mutation / use-case orchestration
Presentation      → visualization + user interaction
UI Controller     → presentation coordination
Tool              → user intent
Projection        → UI-facing representation
Renderer          → visual realization
GraphicsItem      → Qt visual projection
Canvas            → viewport + navigation + interaction infrastructure
```
