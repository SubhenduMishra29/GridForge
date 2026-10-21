# GridForge V2 — SLD Subsystem

## Purpose

The SLD subsystem is the first-class visual authoring and projection workflow
for GridForge V2. It is the primary UI representation of the electrical
network, but it is not the authoritative electrical model.

## Responsibilities

The SLD subsystem provides the domain-level UI structure for:

- SLD documents and persisted presentation state
- visual nodes and visual connections
- controller/tool coordination
- selection and viewport-independent presentation state
- projections of authoritative Core identities and connectivity

Electrical equipment, terminal identity, connectivity, and topology remain
owned by Core. Persistent SLD presentation state and its lifecycle are
coordinated through the Application/document lifecycle; graphics are
disposable realizations, not persistence authority.

## Architectural boundaries

The SLD subsystem does not directly own:

- authoritative electrical equipment or topology
- Qt widgets
- QGraphicsScene or QGraphicsView
- painting or rendering implementation
- low-level mouse event processing
- electrical calculations or solver execution

Those responsibilities remain in Core, Application, or the corresponding UI
infrastructure according to the frozen V2 boundaries.

## Relationship with Canvas

```text
Core engineering identities / connectivity
                  |
          Application commands,
       services, transactions, events
                  |
       Persisted SLD presentation state
                  |
          SLDCanvasProjection
                  |
       Immutable canvas snapshot
                  |
       SLDCanvasRenderSystem / Qt
```

The diagram describes the intended ownership path. A complete production
relationship must be established from concrete callers and consumers; the
existence of a class or interface alone is not end-to-end integration proof.


---

## Current Architecture Addendum — 2026-10-07

SLD is the canonical visual authoring/projection surface, not electrical truth.

Current insertion semantics support dragging already-placed equipment onto an existing Simple Wire. The preview identifies an insertion target; commit is an Application command and transaction. The resulting wire split and inserted terminals are reconciled from canonical state.

SLD route ownership, presentation ownership, authored node metadata, and projection provenance must survive insertion. QGraphics objects are disposable realizations of persistent SLD state.
