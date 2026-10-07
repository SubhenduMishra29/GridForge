# GridForge V2 — SLD Subsystem

## Purpose

The SLD subsystem is the first-class electrical-network visual workflow
boundary of GridForge V2.

The Single Line Diagram is not treated as a secondary visualization.
It is the primary UI representation of the electrical network.

## Responsibilities

The SLD subsystem provides the domain-level UI structure for:

- SLD documents
- electrical visual nodes
- electrical visual connections
- SLD state
- SLD controller orchestration
- selection identity
- viewport-independent SLD state

## Architectural boundaries

The SLD subsystem does not directly own:

- Qt widgets
- QGraphicsScene
- QGraphicsView
- painting
- rendering
- mouse event processing
- concrete tools
- electrical calculations
- solver execution

Those responsibilities remain in the existing UI subsystems.

## Relationship with Canvas

```text
                 SLD
                  |
        +---------+---------+
        |                   |
    SLD Model          SLD State
        |                   |
        +---------+---------+
                  |
             SLD Controller
                  |
              UI Canvas
                  |
        +---------+---------+
        |         |         |
      Scene     View     Render

---

## Current Architecture Addendum — 2026-10-07

SLD is the canonical visual authoring/projection surface, not electrical truth.

Current insertion semantics support dragging already-placed equipment onto an existing Simple Wire. The preview identifies an insertion target; commit is an Application command and transaction. The resulting wire split and inserted terminals are reconciled from canonical state.

SLD route ownership, presentation ownership, authored node metadata, and projection provenance must survive insertion. QGraphics objects are disposable realizations of persistent SLD state.
