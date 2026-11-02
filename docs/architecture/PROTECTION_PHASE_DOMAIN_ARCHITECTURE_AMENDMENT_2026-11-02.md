# Protection and Phase-Domain Architecture Amendment — 2 November 2026

**Parent document:** [Protection Study and System Architecture](PROTECTION_STUDY_AND_SYSTEM_ARCHITECTURE.md)  
**Cross-layer authority:** [Current GridForge V2 Architecture](GRIDFORGE_V2_ARCHITECTURE_2026-11-02.md)  
**Mainline baseline:** `a9e07287c90667a7aae8bcc060e4e2d0cadf261e`  
**Purpose:** Record the merged PR #908 boundary and clarify how physical conductors, transformer representations, measurement and protection fit into the engineering model.

This amendment supplements the detailed Protection Study document. It does not create a new Core/Application architecture, new topology owner, new study lifecycle or alternate result store.

## 1. What PR #908 merged

PR #908 merged Protection Study scenario snapshots, supported ANSI 50N/51N residual measurement inputs, transformer sequence preparation, and phase-domain conductor network foundations.

The merged source scope includes:

- detached, Application-authorized CT terminal-current samples for explicitly supported Line/Cable and transformer sequence cases;
- tap-aware transformer sequence preparation and immutable terminal-current records with explicit `INTO_EQUIPMENT` direction;
- CT conversion checks for configured equipment endpoint, CT association, active CT identity, polarity, ratio, current basis, topology and project provenance;
- explicit residual source bindings and typed derived residual-current measurement for supported ANSI 50N/51N paths;
- transformer winding/neutral declarations and supported zero-sequence transformer cases;
- physical conductor inventories, topology associations and impedance preparation;
- phase-domain conductor graph, global admittance and fault-execution foundations;
- reversible Application commands and transaction handling for graph node/connection edits;
- connectivity persistence schema and migration for phase-domain graph collections.

This is an implementation increment, not a claim that every physical equipment family or Protection Study execution path is complete.

## 2. How conductors fit into the SLD

The SLD remains a two-dimensional engineering authoring and projection surface. The engineer should see equipment symbols, terminal connection points, conventional Simple Wire routes, and—when implemented—explicit phase-domain conductor/grounding representations through suitable editor tools and inspectors.

Do not draw a phase-domain graph as if it were a second independent electrical network. It is an explicit physical/study representation associated with the same canonical equipment and terminal identities.

### Conventional network path

```text
Bus / Equipment Terminal
  ↔ canonical Simple Wire relationship
  ↔ Equipment Terminal / Bus
```

A Simple Wire is a terminal-to-terminal connectivity relationship. Its SLD route is presentation geometry. It does not encode conductor phase, neutral, earth electrode impedance or physical return-path construction.

### Phase-domain physical path

```text
Equipment terminal / phase node
  → explicit conductor segment(s)
  → phase-domain node(s)
  → equipment terminal / phase node
```

Where neutral or earth return is required, the model must include the actual supported neutral/ground conductor path, its endpoint identities and applicable impedance. An earth connection must terminate through an explicit physical grounding/electrode path to the declared earth reference. A ground symbol or metadata flag alone is not sufficient.

### Authoring boundary

The Application graph-edit commands and persistence introduced by #908 are not a completed SLD editor. The future UI workflow must provide explicit creation, selection, inspection, validation and removal of supported phase-domain nodes and conductor segments, all routed through Application commands. Pixel snapping, route intersections or symbol placement must not synthesize graph edges.

## 3. Conductor identity and electrical semantics

A supported conductor record must preserve, as applicable:

- stable conductor/edge identity;
- source and destination node identities;
- phase or conductor role (A/B/C, neutral, protective earth, grounding/electrode or another explicitly supported type);
- owning equipment/circuit association where required;
- impedance/resistance/reactance and explicit units/bases;
- orientation/direction semantics where current results require them;
- in-service/availability state;
- provenance and supported solver applicability.

Do not infer a conductor's electrical role solely from its display label or SLD line style. Unsupported conductor families, missing impedance, ambiguous endpoints or invalid bases must produce explicit diagnostics and remain unavailable to the affected calculation.

## 4. Transformer model-to-study representations

The persistent transformer remains one physical Core equipment object. Sequence and phase-domain representations are derived, immutable study inputs generated from validated transformer data.

The producer must preserve the mapping between physical transformer terminals/windings and numerical ports, including:

- winding and terminal identity;
- winding connection and phase/neutral declarations;
- rated voltage and explicit study bases;
- positive-, negative- and zero-sequence data where supported;
- tap position and the supported tap model;
- polarity/vector-group/phase displacement semantics where represented by the source model;
- grounding/neutral impedance and explicit physical path requirements;
- provenance and precise unsupported-case diagnostics.

A multiport numerical model is not a replacement Transformer entity and must not be serialized as a second authoritative equipment model. A producer must reject incomplete or ambiguous source data instead of filling missing values from unrelated defaults.

Internal delta-loop circulating current is not external terminal line current. It is not automatically a current through an external CT aperture and must not be converted into a normal feeder CT measurement. A dedicated internal winding sensor would require a distinct physical measurement-source contract.

At the #908 baseline, transformer sequence preparation is present for explicitly supported cases; broader phase-domain transformer multiport coverage and internal winding-loop result support remain separate implementation/evidence items.

## 5. Protection measurement rules

The valid conceptual path is:

```text
Primary conductor/equipment current or voltage
  → physical instrument primary terminals
  → instrument conversion and secondary circuit
  → physical secondary terminal/channel association
  → MeasurementChannel
  → RelayInput
  → ProtectionElement
```

The result-to-measurement adapter must prove the physical source path and preserve direction, phase, current/voltage basis, CT/PT ratio, polarity, instrument identity, project identity and source revision.

For ANSI 50N/51N, residual current must come from explicit configured residual-source bindings and supported typed phase-current samples. Phase samples are direction-normalized before complex phasor summation. Do not infer residual current from three unrelated values, metadata-only neutral declarations or a ground symbol.

Neutral CT and CBCT paths require their own physical construction and result coverage. A residual quantity derived from phase CTs is not interchangeable with a dedicated neutral CT/CBCT measurement. Unsupported cases remain fail-closed.

## 6. Protection decisions and switching

A protection function produces a typed decision. An explicit scheme/action mapping and Application authorization are required before any breaker or switching equipment state changes.

```text
RelayInput → ProtectionElement → ProtectionDecision
  → explicit action mapping → Application authorization
  → switching command/service → equipment state
```

No protection function, relay plugin, UI panel or solver may mutate breaker state directly. A decision is not an acknowledgement that a breaker operated. Physical feedback and postcondition evidence must be represented separately.

## 7. D15F-29–37 — physical switching and transformer multiport increments

The mainline Modification Register contains additional D15F implementation increments beyond the initial graph foundation:

| Increment | Implemented contract | Explicit limitation |
|---|---|---|
| D15F-29 | Explicit A/B/C/N inventories and state-gated terminal-to-terminal pole paths for Switch, Disconnector and Fuse | No per-pole discrepancy, fuse arc/melting, contact resistance or earthing-blade model; persistence/configurator gaps were recorded |
| D15F-30 | Common immutable PhysicalConductorConstruction/PhysicalConductorPath consumed by Breaker, Switch, Disconnector and Fuse | Two-terminal paths only; persistence/UI configuration not fully consolidated |
| D15F-31 | Explicit Transformer HV/LV winding construction, terminal roles, phase roles and neutral declarations | Metadata/construction contract only; no magnetic coupling or HV-LV galvanic continuity |
| D15F-32 | Reciprocal passive Transformer terminal-admittance multiport primitive in the phase-domain solver | Requires complete externally supplied matrix; no automatic model producer in this increment |
| D15F-33 | Transformer model-to-multiport producer with exact terminal inventory and tap/phase-shift provenance | Does not derive the matrix from scalar r/x or vector-group labels; persistence/configurator integration was outstanding |
| D15F-34 | SLD-derived graph builder creates Transformer winding terminal nodes and automatically prepares the multiport for short-circuit study | Requires explicit complete matrix; no implicit neutral/earth path; persistence/configurator gaps remain |
| D15F-35 | Explicit grounded-wye neutral electrode and earth-return graph paths with distinct impedances and current reconciliation | No inferred core response, PE/screen parallel division, multiple electrodes or soil-frequency model |
| D15F-36 | Matrix fingerprint binds zero-sequence core/delta coverage evidence to exact terminal order and matrix values | Evidence/provenance validation, not independent magnetic-core reconstruction |
| D15F-37 | Explicit internal delta-loop states solved as coupled MNA current unknowns; per-loop currents reported | Reduced internal coordinates, not individually placeable SLD conductors or thermal/core-limb states |

This closes the earlier blanket statement that transformer multiport graph integration and all switching-pole paths were absent. It does **not** establish universal source/equipment coverage or complete persistence/configurator/UI support. The transformer matrix remains an explicit externally supplied engineering input, with manufacturer/test provenance and exact evidence binding. A delta winding without explicit loop state fails closed.

## 8. Mainline limits and evidence

The PR #908 merge description explicitly retains these limitations:

- Grid/Generator/Motor phase-domain source equivalents are not automatically derived for every supported source model;
- dedicated phase-domain machine/load/arc-fault and unsupported switching primitives remain incomplete; D15F-29–37 provides the bounded switching and transformer cases listed above;
- NEUTRAL_CT and CBCT execution is supported only where explicit conductor graph, result coverage and construction contracts prove the physical current path;
- Application graph edits and SLD-derived equipment/winding graph construction exist for the supported D15F cases; a general-purpose user-facing graph editor and complete construction configurators remain outstanding;
- protection execution and production readiness are not established by these foundations.

The merge was reviewed through remote source inspection and integration review. No tests/CI, syntax/import checks, persistence round-trip, numerical fixtures or end-to-end runtime execution were run as part of that merge. Do not upgrade these evidence labels in documentation without new recorded evidence.

Open/draft follow-up PRs are not mainline capabilities. Reconcile each against the then-current `main` before changing this status.

## 9. Required future SLD workflow

1. Engineer selects a supported phase-domain authoring tool.
2. UI previews candidate nodes/segments without mutating Core.
3. Engineer selects actual equipment terminals and explicit phase/conductor roles.
4. UI gathers required physical/electrical properties and grounding construction.
5. Application validates endpoint identity, ownership, phase compatibility, bases and physical return paths.
6. Application commits the graph change transactionally.
7. Application publishes semantic network events and updated read models.
8. UI reprojects the canonical state and exposes unsupported/incomplete paths.
9. Save/reopen restores the graph through the versioned persistence contract.

No step may infer physical electrical connectivity from canvas coordinates.

---
